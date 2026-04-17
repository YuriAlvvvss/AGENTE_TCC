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
    ollama_model: str
    ollama_host: str
    max_history: int
    max_input_chars: int
    api_host: str
    api_port: int
    debug: bool
    chat_options: dict[str, float | int]
    bundled_data_dir: Path | None = None
    secret_key: str = "rosita-dev-secret"
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
        ollama_model=(os.getenv("ROSITA_OLLAMA_MODEL") or "").strip(),
        ollama_host=ollama_host,
        max_history=int(os.getenv("ROSITA_MAX_HISTORY", "5")),
        max_input_chars=int(os.getenv("ROSITA_MAX_INPUT_CHARS", "1000")),
        api_host=os.getenv("ROSITA_API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("ROSITA_API_PORT", "5000")),
        debug=_env_bool("ROSITA_DEBUG", False),
        chat_options={
            "num_predict": int(os.getenv("ROSITA_NUM_PREDICT", "128")),
            "temperature": float(os.getenv("ROSITA_TEMPERATURE", "0.7")),
            "top_p": float(os.getenv("ROSITA_TOP_P", "0.9")),
            "repeat_penalty": float(os.getenv("ROSITA_REPEAT_PENALTY", "1.1")),
        },
        bundled_data_dir=bundled_data_dir,
        secret_key=(os.getenv("ROSITA_SECRET_KEY") or "rosita-dev-secret").strip(),
        admin_username=(os.getenv("ROSITA_ADMIN_USERNAME") or "admin").strip(),
        admin_password=os.getenv("ROSITA_ADMIN_PASSWORD", "admin123"),
        user_username=(os.getenv("ROSITA_USER_USERNAME") or "usuario").strip(),
        user_password=os.getenv("ROSITA_USER_PASSWORD", "usuario123"),
    )

