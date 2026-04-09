"""Entrypoint da API Flask ROSITA."""

from pathlib import Path
import sys

from dotenv import load_dotenv

# Permite importar o pacote em backend/src sem instalar no ambiente.
BACKEND_DIR = Path(__file__).resolve().parent
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rosita.app_factory import create_app
from rosita.settings import load_settings

load_dotenv()

app = create_app()
settings = load_settings()


if __name__ == "__main__":
    print(f"Servidor iniciando em http://localhost:{settings.api_port}")
    app.run(host=settings.api_host, port=settings.api_port, debug=settings.debug)
