"""Configurações centralizadas do backend ROSITA."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolver_data_dir() -> Path:
    """Retorna o diretório de dados, permitindo override por ROSITA_DATA_DIR."""
    env = os.environ.get("ROSITA_DATA_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "data"


DATA_DIR = _resolver_data_dir()

OLLAMA_MODEL = "llama3.1:8b"

CHAT_CONFIG = {
    "num_predict": 128,
    "temperature": 0.7,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
}

MAX_HISTORY = 5

API_HOST = "0.0.0.0"
API_PORT = 5000
DEBUG = True
