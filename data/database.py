import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

from config.settings import DATABASE_PATH, DB_PURGE_DAYS


class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        if not hasattr(self._local, "conn") or self._local.conn is None:
            Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
            self._local.conn = sqlite3.connect(DATABASE_PATH)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=DELETE")
        return self._local.conn

    def _init_db(self):
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            self._get_conn().executescript(f.read())
        self._get_conn().commit()

    def insert_mesure(self, source, voltage=0, current=0, power=0, energy=0,
                      soc=None, frequency=None, power_factor=None):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO mesures (source, voltage, current, power, energy, soc, frequency, power_factor)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, voltage, current, power, energy, soc, frequency, power_factor),
        )
        conn.commit()

    def insert_snapshot(self, mesures_dict, etat_data):
        conn = self._get_conn()
        for source, data in mesures_dict.items():
            conn.execute(
                """INSERT INTO mesures (source, voltage, current, power, energy, soc, frequency, power_factor)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (source, data.get("voltage", 0), data.get("current", 0),
                 data.get("power", 0), data.get("energy", 0), data.get("soc"),
                 data.get("frequency"), data.get("power_factor")),
            )
        conn.execute(
            """INSERT INTO etat_sources (source_active, batterie_soc, solaire_power,
               batterie_power, jirama_power, consommation_power, mode)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (etat_data["source_active"], etat_data["batterie_soc"],
             etat_data["solaire_power"], etat_data["batterie_power"],
             etat_data["jirama_power"], etat_data["conso_power"],
             etat_data["mode"]),
        )
        conn.commit()

    def insert_evenement(self, type_, message, level="info"):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO evenements (type, message, level) VALUES (?, ?, ?)",
            (type_, message, level),
        )
        conn.commit()

    def insert_etat(self, source_active, batterie_soc, solaire_power,
                    batterie_power, jirama_power, conso_power, mode="auto"):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO etat_sources (source_active, batterie_soc, solaire_power,
               batterie_power, jirama_power, consommation_power, mode)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (source_active, batterie_soc, solaire_power, batterie_power,
             jirama_power, conso_power, mode),
        )
        conn.commit()

    def insert_prevision(self, date_prev, couverture, irradiance,
                         production_estimee, recommandation=""):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO previsions (date_prev, couverture_nuageuse, irradiance,
               production_estimee, recommandation) VALUES (?, ?, ?, ?, ?)""",
            (date_prev, couverture, irradiance, production_estimee, recommandation),
        )
        conn.commit()

    def get_last_mesures(self, minutes=5):
        conn = self._get_conn()
        cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        rows = conn.execute(
            "SELECT * FROM mesures WHERE timestamp >= ? ORDER BY timestamp DESC",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_last_mesure_by_source(self, source):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM mesures WHERE source = ? ORDER BY id DESC LIMIT 1",
            (source,),
        ).fetchone()
        return dict(row) if row else {}

    def get_all_last_mesures(self):
        conn = self._get_conn()
        result = {}
        for source in ("solaire", "batterie", "jirama", "groupe", "consommation"):
            result[source] = dict(
                conn.execute(
                    "SELECT * FROM mesures WHERE source = ? ORDER BY id DESC LIMIT 1",
                    (source,),
                ).fetchone() or {}
            )
        return result

    def get_recent_mesures(self, source, limit=50):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT timestamp, power FROM mesures WHERE source = ? ORDER BY id DESC LIMIT ?",
            (source, limit),
        ).fetchall()
        rows.reverse()
        return [dict(r) for r in rows]

    def get_recent_etats(self, limit=50):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM etat_sources ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        rows.reverse()
        return [dict(r) for r in rows]

    def get_evenements(self, limit=50):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM evenements ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_dernier_etat(self):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM etat_sources ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else {}

    def get_status_snapshot(self):
        conn = self._get_conn()
        conn.execute("BEGIN")
        etat = conn.execute(
            "SELECT * FROM etat_sources ORDER BY id DESC LIMIT 1"
        ).fetchone()
        mesures = {}
        for source in ("solaire", "batterie", "jirama", "groupe", "consommation"):
            row = conn.execute(
                "SELECT * FROM mesures WHERE source = ? ORDER BY id DESC LIMIT 1",
                (source,),
            ).fetchone()
            mesures[source] = dict(row) if row else {}
        conn.execute("COMMIT")
        return dict(etat) if etat else {}, mesures

    def get_derniere_prevision(self):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM previsions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else {}

    def get_previsions(self, limit=5):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM previsions ORDER BY date_prev ASC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def purge_old_data(self):
        conn = self._get_conn()
        cutoff = (datetime.now() - timedelta(days=DB_PURGE_DAYS)).isoformat()
        conn.execute("DELETE FROM mesures WHERE timestamp < ?", (cutoff,))
        conn.execute("DELETE FROM evenements WHERE timestamp < ?", (cutoff,))
        conn.execute("DELETE FROM etat_sources WHERE timestamp < ?", (cutoff,))
        conn.commit()

    def clear_all(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM mesures")
        conn.execute("DELETE FROM evenements")
        conn.execute("DELETE FROM etat_sources")
        conn.execute("DELETE FROM previsions")
        conn.commit()

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
