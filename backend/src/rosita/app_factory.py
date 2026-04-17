"""Factory da aplicação Flask."""

from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from rosita.api.routes import create_api_blueprint
from rosita.bootstrap import criar_agente
from rosita.settings import load_settings


def create_app() -> Flask:
    """Cria e configura a aplicação Flask."""
    settings = load_settings()
    agent = criar_agente(settings)

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = settings.session_cookie_secure
    CORS(app, supports_credentials=True)
    app.register_blueprint(create_api_blueprint(agent, settings))

    @app.get("/")
    def raiz():
        return jsonify({"mensagem": "API ROSITA online"})

    return app

