"""Helpers para leitura de arquivos de dados."""

from pathlib import Path


def carregar_texto(filepath: Path, fallback: str) -> str:
    """Carrega conteúdo UTF-8 de arquivo com fallback quando não existe."""
    try:
        return filepath.read_text(encoding="utf-8")
    except FileNotFoundError:
        return fallback

