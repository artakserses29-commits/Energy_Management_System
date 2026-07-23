CREATE TABLE IF NOT EXISTS mesures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
    source TEXT NOT NULL,
    voltage REAL DEFAULT 0,
    current REAL DEFAULT 0,
    power REAL DEFAULT 0,
    energy INTEGER DEFAULT 0,
    soc REAL,
    frequency REAL,
    power_factor REAL
);

CREATE TABLE IF NOT EXISTS evenements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT DEFAULT 'info'
);

CREATE TABLE IF NOT EXISTS etat_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
    source_active TEXT NOT NULL,
    batterie_soc REAL,
    solaire_power REAL,
    batterie_power REAL,
    jirama_power REAL,
    consommation_power REAL,
    mode TEXT DEFAULT 'auto'
);

CREATE TABLE IF NOT EXISTS previsions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
    date_prev DATE NOT NULL,
    couverture_nuageuse REAL,
    irradiance REAL,
    production_estimee REAL,
    recommandation TEXT
);

CREATE INDEX IF NOT EXISTS idx_mesures_timestamp ON mesures(timestamp);
CREATE INDEX IF NOT EXISTS idx_mesures_source ON mesures(source);
CREATE INDEX IF NOT EXISTS idx_evenements_timestamp ON evenements(timestamp);
