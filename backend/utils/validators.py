"""Validações de entrada para mensagens e parâmetros da API."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_PERGUNTA_CHARS = 1000


def validar_pergunta(pergunta: Any) -> bool:
    """
    Verifica se a pergunta é uma entrada aceitável para o agente.

    Regras: deve ser string não vazia após remoção de espaços nas extremidades
    e não pode exceder MAX_PERGUNTA_CHARS caracteres.

    Args:
        pergunta: Valor enviado pelo usuário (esperado: str).

    Returns:
        True se todas as regras forem atendidas; caso contrário False.
    """
    if not isinstance(pergunta, str):
        logger.warning("Validação falhou: pergunta não é string (tipo=%s)", type(pergunta))
        return False

    texto = pergunta.strip()
    if not texto:
        logger.warning("Validação falhou: pergunta vazia após strip()")
        return False

    if len(pergunta) > MAX_PERGUNTA_CHARS:
        logger.warning(
            "Validação falhou: pergunta excede %s caracteres (recebido: %s)",
            MAX_PERGUNTA_CHARS,
            len(pergunta),
        )
        return False

    logger.debug("Validação da pergunta OK (%s caracteres)", len(texto))
    return True
