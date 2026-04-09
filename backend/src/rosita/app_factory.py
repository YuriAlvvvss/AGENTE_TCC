"""Factory da aplicação Flask."""

from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS

from rosita.api.routes import create_api_blueprint
from rosita.bootstrap import criar_agente
from rosita.settings import load_settings


def create_app() -> Flask:
    """Cria e configura a aplicação Flask."""
    settings = load_settings()
    agent = criar_agente(settings)

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(create_api_blueprint(agent, settings))

    @app.get("/")
    def raiz():
        return jsonify({"mensagem": "API ROSITA online"})

    return app

