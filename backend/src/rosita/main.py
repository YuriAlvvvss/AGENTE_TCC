"""Aplicação Flask principal da ROSITA."""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from rosita.api.routes.credentials import credentials_bp
from rosita.settings import Settings


def criar_app() -> Flask:
    """Factory para criar e configurar a aplicação Flask."""
    app = Flask(__name__)
    
    # Configurações
    settings = Settings()
    app.config["JSON_SORT_KEYS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    })
    
    # Blueprints
    app.register_blueprint(credentials_bp)
    
    # Health check
    @app.route("/api/health", methods=["GET"])
    def health() -> dict:
        """Verifica saúde da API."""
        return jsonify({
            "status": "ok",
            "provider": settings.ai_provider,
            "version": "1.0.0",
        })
    
    # Error handlers
    @app.errorhandler(404)
    def nao_encontrado(error):
        return jsonify({"error": "Endpoint não encontrado"}), 404
    
    @app.errorhandler(500)
    def erro_interno(error):
        return jsonify({"error": "Erro interno do servidor"}), 500
    
    return app


def main() -> None:
    """Ponto de entrada da aplicação."""
    settings = Settings()
    app = criar_app()
    
    print(f"ROSITA iniciando...")
    print(f"Provider: {settings.ai_provider}")
    print(f"API rodando em http://0.0.0.0:{settings.api_port}")
    
    app.run(
        host="0.0.0.0",
        port=settings.api_port,
        debug=settings.debug,
        use_reloader=settings.debug,
    )


if __name__ == "__main__":
    main()
