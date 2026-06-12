"""Factory da aplicação Flask."""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from rosita.api.routes import create_api_blueprint
from rosita.bootstrap import criar_agente
from rosita.settings import load_settings
from rosita.utils.history_store import HistoryStore

logger = logging.getLogger("rosita.app")


class _NoopLimiter:
    """Limiter inerte usado quando o Flask-Limiter não está instalado.

    Mantém a aplicação funcional (sem limitação de taxa) em vez de quebrar a
    inicialização. Para ativar a limitação, instale ``flask-limiter``.
    """

    def limit(self, *_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

    def init_app(self, _app) -> None:  # noqa: D401 - interface compatível
        return None


def _build_limiter():
    """Cria o limiter real ou um substituto inerte com aviso."""
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
    except ImportError:
        logger.warning(
            "flask-limiter não instalado — limitação de taxa desativada. "
            "Rode 'pip install -r requirements.txt' para ativá-la."
        )
        return _NoopLimiter()

    return Limiter(
        key_func=get_remote_address,
        default_limits=["240 per hour"],
        storage_uri="memory://",
    )


def create_app() -> Flask:
    """Cria e configura a aplicação Flask."""
    settings = load_settings()
    agent = criar_agente(settings)
    history_store = HistoryStore(settings.history_db_path)

    app = Flask(__name__)
    limiter = _build_limiter()
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
    app.register_blueprint(create_api_blueprint(agent, settings, limiter, history_store))
    limiter.init_app(app)

    @app.get("/")
    def raiz():
        return jsonify({"mensagem": "API ROSITA online"})

    return app

