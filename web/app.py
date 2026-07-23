import json
import os

from flask import Flask
from flask_socketio import SocketIO

from config.settings import SECRET_KEY, FLASK_HOST, FLASK_PORT, FLASK_DEBUG

socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["LOCALES_DIR"] = os.path.join(os.path.dirname(__file__), "locales")

    from web.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    socketio.init_app(app, cors_allowed_origins="*")

    @app.context_processor
    def inject_locale():
        lang = "fr"
        locale_file = os.path.join(app.config["LOCALES_DIR"], f"{lang}.json")
        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                locale = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            locale = {}
        return dict(locale=locale, lang=lang)

    return app


def run_server():
    app = create_app()
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
