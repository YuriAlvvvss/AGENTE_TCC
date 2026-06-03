"""Configurações centralizadas do backend ROSITA."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Configurações de execução do agente e da API."""

    base_dir: Path
    data_dir: Path
    ai_provider: str
    ollama_model: str
    ollama_host: str
    openrouter_api_key: str
    openrouter_model: str
    gateway_url: str
    gateway_model: str
    gateway_api_key: str
    max_history: int
    max_input_chars: int
    api_host: str
    api_port: int
    debug: bool
    chat_options: dict[str, float | int]
    bundled_data_dir: Path | None = None
    secret_key: str = "rosita-dev-secret"
    session_cookie_secure: bool = False
    admin_username: str = "admin"
    admin_password: str = "admin123"
    user_username: str = "usuario"
    user_password: str = "usuario123"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """Carrega configurações com suporte a variáveis de ambiente."""
    backend_dir = Path(__file__).resolve().parents[2]
    package_dir = Path(__file__).resolve().parent
    default_data_dir = backend_dir / "data"

    data_dir = Path(os.getenv("ROSITA_DATA_DIR", str(default_data_dir))).expanduser()
    if not data_dir.is_absolute():
        data_dir = (backend_dir / data_dir).resolve()
    else:
        data_dir = data_dir.resolve()

    bundled_data_dir = Path(
        os.getenv("ROSITA_BUNDLED_DATA_DIR", str(package_dir / "default_data"))
    ).expanduser()
    if not bundled_data_dir.is_absolute():
        bundled_data_dir = (backend_dir / bundled_data_dir).resolve()
    else:
        bundled_data_dir = bundled_data_dir.resolve()

    ollama_host = (
        os.getenv("ROSITA_OLLAMA_HOST")
        or os.getenv("ROSITA_AI_SERVER_URL")
        or "http://127.0.0.1:11434"
    ).strip().rstrip("/")

    return Settings(
        base_dir=backend_dir,
        data_dir=data_dir,
        ai_provider=(os.getenv("ROSITA_AI_PROVIDER") or "ollama").strip().lower(),
        ollama_model=(os.getenv("ROSITA_OLLAMA_MODEL") or "").strip(),
        ollama_host=ollama_host,
        openrouter_api_key=(os.getenv("ROSITA_OPENROUTER_API_KEY") or "").strip(),
        openrouter_model=(os.getenv("ROSITA_OPENROUTER_MODEL") or "").strip(),
        gateway_url=(os.getenv("ROSITA_GATEWAY_URL") or "").strip().rstrip("/"),
        gateway_model=(os.getenv("ROSITA_GATEWAY_MODEL") or "").strip(),
        gateway_api_key=(os.getenv("ROSITA_GATEWAY_API_KEY") or "").strip(),
        max_history=int(os.getenv("ROSITA_MAX_HISTORY", "5")),
        max_input_chars=int(os.getenv("ROSITA_MAX_INPUT_CHARS", "1000")),
        api_host=(os.getenv("ROSITA_API_HOST") or "0.0.0.0").strip(),
        api_port=int((os.getenv("ROSITA_API_PORT") or "5000").strip()),
        debug=_env_bool("ROSITA_DEBUG", False),
        chat_options={
            "num_predict": int(os.getenv("ROSITA_NUM_PREDICT", "128")),
            "temperature": float(os.getenv("ROSITA_TEMPERATURE", "0.7")),
            "top_p": float(os.getenv("ROSITA_TOP_P", "0.9")),
            "repeat_penalty": float(os.getenv("ROSITA_REPEAT_PENALTY", "1.1")),
        },
        bundled_data_dir=bundled_data_dir,
        secret_key=(os.getenv("ROSITA_SECRET_KEY") or "rosita-dev-secret").strip(),
        session_cookie_secure=_env_bool("ROSITA_SESSION_COOKIE_SECURE", False),
        admin_username=(os.getenv("ROSITA_ADMIN_USERNAME") or "admin").strip(),
        admin_password=os.getenv("ROSITA_ADMIN_PASSWORD", "admin123"),
        user_username=(os.getenv("ROSITA_USER_USERNAME") or "usuario").strip(),
        user_password=os.getenv("ROSITA_USER_PASSWORD", "usuario123"),
    )

