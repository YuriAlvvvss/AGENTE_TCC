"""Utilitários para leitura de arquivos de dados (regimento, etc.)."""

import logging

logger = logging.getLogger(__name__)


def carregar_regimento(filepath: str) -> str:
    """
    Carrega o conteúdo textual do regimento a partir do caminho informado.

    Args:
        filepath: Caminho absoluto ou relativo do arquivo UTF-8 (ex.: regimento ECIM).

    Returns:
        Conteúdo completo do arquivo como string, ou a mensagem
        "Regimento não encontrado." se o arquivo não existir.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as arquivo:
            conteudo = arquivo.read()
        logger.info("Regimento carregado com sucesso de %s", filepath)
        return conteudo
    except FileNotFoundError:
        logger.error("Arquivo de regimento não encontrado: %s", filepath)
        return "Regimento não encontrado."
