"""Factory da aplicação Flask."""

from __future__ import annotations

import os

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

    cors_origins = [
        "http://127.0.0.1:18080",
        "http://localhost:18080",
        f"http://127.0.0.1:{settings.api_port}",
        f"http://localhost:{settings.api_port}",
    ]
    web_port = (os.getenv("ROSITA_WEB_PORT") or "18080").strip()
    if web_port not in ("80", "443", ""):
        cors_origins.extend(
            [
                f"http://127.0.0.1:{web_port}",
                f"http://localhost:{web_port}",
            ]
        )

    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    app.register_blueprint(create_api_blueprint(agent, settings))

    @app.get("/")
    def raiz():
        return jsonify({"mensagem": "API ROSITA online"})

    return app

