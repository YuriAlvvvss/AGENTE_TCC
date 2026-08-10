"""Configurações centralizadas do backend ROSITA."""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from werkzeug.security import generate_password_hash

logger = logging.getLogger("rosita.settings")

_DOLLAR_SIGN: Final[str] = "$"


@dataclass(frozen=True)
class Settings:
    """Configurações de execução do agente e da API."""

    base_dir: Path
    data_dir: Path
    history_db_path: Path
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
    admin_password_hash: str = ""
    user_username: str = "usuario"
    user_password_hash: str = ""


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _strip_env_quotes(value: str) -> str:
    """Remove aspas simples ou duplas de valores lidos do ambiente."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _resolve_password_hash(hash_env: str, plain_env: str, dev_default: str | None, label: str) -> str:
    """Resolve o hash de senha de um perfil.

    Ordem de prioridade:
    1. Hash pronto em ``<hash_env>`` (recomendado — gerado uma vez e salvo no .env).
    2. Senha em texto em ``<plain_env>`` (menos seguro — gera o hash em tempo de execução e
       registra um aviso informando que o hash deve ser definido).
    3. Se nenhum estiver presente, gera **um hash aleatório temporário** e emite aviso
       para forçar configuração explícita em produção. Isto evita ter senhas padrão
       conhecidas no código-fonte (ex.: "admin123").
    """
    hash_value = _strip_env_quotes((os.getenv(hash_env) or "").strip())
    if hash_value:
        return hash_value

    plain = os.getenv(plain_env)
    if plain:
        logger.warning(
            "Senha em texto detectada em %s — gerando hash em tempo de execução. "
            "Recomenda-se gerar o hash com 'werkzeug.security.generate_password_hash' e definir %s no .env.",
            plain_env,
            hash_env,
        )
        return generate_password_hash(plain)

    logger.warning(
        "Senha do perfil '%s' não configurada (%s e %s ausentes). "
        "Gerando hash temporário; defina %s no .env para uso em produção.",
        label,
        hash_env,
        plain_env,
        hash_env,
    )
    return generate_password_hash(secrets.token_urlsafe(16))


def _resolve_secret_key() -> str:
    """Obtém a SECRET_KEY do ambiente ou gera uma aleatória (com aviso)."""
    secret_key = (os.getenv("ROSITA_SECRET_KEY") or "").strip()
    if secret_key:
        return secret_key

    logger.warning(
        "ROSITA_SECRET_KEY não definida — gerando uma chave aleatória. "
        "As sessões NÃO persistem entre reinícios; defina ROSITA_SECRET_KEY no .env."
    )
    return secrets.token_hex(32)


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

    history_db_path = Path(
        os.getenv("ROSITA_HISTORY_DB", str(backend_dir / "rosita_history.sqlite3"))
    ).expanduser()
    if not history_db_path.is_absolute():
        history_db_path = (backend_dir / history_db_path).resolve()
    else:
        history_db_path = history_db_path.resolve()

    return Settings(
        base_dir=backend_dir,
        data_dir=data_dir,
        history_db_path=history_db_path,
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
            "num_predict": int(os.getenv("ROSITA_NUM_PREDICT", "256")),
            "temperature": float(os.getenv("ROSITA_TEMPERATURE", "0.75")),
            "top_p": float(os.getenv("ROSITA_TOP_P", "0.92")),
            "repeat_penalty": float(os.getenv("ROSITA_REPEAT_PENALTY", "1.08")),
        },
        bundled_data_dir=bundled_data_dir,
        secret_key=_resolve_secret_key(),
        session_cookie_secure=_env_bool("ROSITA_SESSION_COOKIE_SECURE", False),
        admin_username=(os.getenv("ROSITA_ADMIN_USERNAME") or "admin").strip(),
        admin_password_hash=_resolve_password_hash(
            "ROSITA_ADMIN_PASSWORD_HASH", "ROSITA_ADMIN_PASSWORD", None, "admin"
        ),
        user_username=(os.getenv("ROSITA_USER_USERNAME") or "usuario").strip(),
        user_password_hash=_resolve_password_hash(
            "ROSITA_USER_PASSWORD_HASH", "ROSITA_USER_PASSWORD", None, "usuario"
        ),
    )

