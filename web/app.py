import json
import os

from flask import Flask

from config.settings import SECRET_KEY


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["LOCALES_DIR"] = os.path.join(os.path.dirname(__file__), "locales")

    from web.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

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
