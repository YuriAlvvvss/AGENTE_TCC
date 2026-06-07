"""Configuração compartilhada dos testes (pytest)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
