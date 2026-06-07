"""Validações de entrada para mensagens e parâmetros da API."""

import re
from typing import Any

# Caracteres de controle (exceto tab, nova linha e retorno de carro), que não
# deveriam aparecer numa mensagem digitada e podem indicar entrada maliciosa.
_CARACTERES_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Nome de modelo aceito (Ollama/OpenAI-compatible): letras, números e os
# separadores usuais. Ex.: "llama3.2:3b", "openai/gpt-4o-mini", "Llama-3.1-8B".
_NOME_MODELO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/\-]{0,127}$")


def validar_pergunta(pergunta: Any, max_chars: int) -> bool:
    """Retorna True se a pergunta for uma string válida e dentro do limite."""
    if not isinstance(pergunta, str):
        return False
    if _CARACTERES_CONTROLE.search(pergunta):
        return False
    texto = pergunta.strip()
    if not texto:
        return False
    return len(texto) <= max_chars


def validar_nome_modelo(modelo: Any) -> bool:
    """Valida o nome de um modelo recebido nas rotas administrativas."""
    if not isinstance(modelo, str):
        return False
    return bool(_NOME_MODELO.match(modelo.strip()))

