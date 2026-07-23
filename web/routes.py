import json

from flask import Blueprint, jsonify, render_template, request

from core.energy_manager import EnergyManager
from data.database import Database

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)

manager = EnergyManager()
db = Database()


@main_bp.route("/")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/lang/<lang>")
def set_lang(lang):
    locale_file = f"web/locales/{lang}.json"
    try:
        with open(locale_file, "r", encoding="utf-8") as f:
            locale = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        locale = {}
    return jsonify(locale)


@api_bp.route("/status")
def get_status():
    status = manager.get_status()
    mesures = db.get_all_last_mesures()
    return jsonify({"status": status, "mesures": mesures})


@api_bp.route("/mesures")
def get_mesures():
    source = request.args.get("source")
    limit = int(request.args.get("limit", 50))
    if source:
        data = db.get_recent_mesures(source, limit)
    else:
        data = {}
        for s in ("solaire", "batterie", "jirama", "groupe", "consommation"):
            data[s] = db.get_recent_mesures(s, limit)
    return jsonify(data)


@api_bp.route("/etats")
def get_etats():
    limit = int(request.args.get("limit", 50))
    return jsonify(db.get_recent_etats(limit))


@api_bp.route("/evenements")
def get_evenements():
    limit = int(request.args.get("limit", 50))
    return jsonify(db.get_evenements(limit))


@api_bp.route("/previsions")
def get_previsions():
    return jsonify(db.get_previsions(5))


@api_bp.route("/mode", methods=["POST"])
def set_mode():
    data = request.get_json()
    mode = data.get("mode", "auto")
    source = data.get("source")
    manager.set_mode(mode, source)
    db.insert_evenement("mode", f"Mode: {mode} source: {source}", "info")
    return jsonify({"success": True})


@api_bp.route("/derniere-prevision")
def derniere_prevision():
    prev = db.get_derniere_prevision()
    return jsonify(prev)
