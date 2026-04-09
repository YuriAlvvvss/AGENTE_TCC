"""Validações de entrada para mensagens e parâmetros da API."""

from typing import Any


def validar_pergunta(pergunta: Any, max_chars: int) -> bool:
    """Retorna True se a pergunta for uma string válida e dentro do limite."""
    if not isinstance(pergunta, str):
        return False
    texto = pergunta.strip()
    if not texto:
        return False
    return len(texto) <= max_chars

