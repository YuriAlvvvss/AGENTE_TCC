"""Inicialização central de recursos do agente."""

from __future__ import annotations

from rosita.core.agent import RositaAgent
from rosita.core.prompt_builder import construir_prompt_sistema
from rosita.settings import Settings
from rosita.utils.file_loader import carregar_texto


def criar_agente(settings: Settings) -> RositaAgent:
    """Instancia agente carregando regimento e instruções de arquivos."""
    regimento_path = settings.data_dir / "regimento_ecim.txt"
    if not regimento_path.exists():
        regimento_path = settings.data_dir / "regimento_ECIM.txt"
    instrucoes_path = settings.data_dir / "agent_instructions.txt"

    regimento = carregar_texto(regimento_path, "Regimento não encontrado.")
    template = carregar_texto(
        instrucoes_path,
        (
            "Você é ROSITA, assistente da PEI Rosa Bonfiglioli.\n"
            "Responda com no máximo 3 linhas. Seja direto e amigável.\n\n"
            "REGIMENTO:\n{REGIMENTO}"
        ),
    )

    prompt_sistema = construir_prompt_sistema(template=template, regimento=regimento)
    return RositaAgent(settings=settings, prompt_sistema=prompt_sistema)

