"""Inicialização central de recursos do agente."""

from __future__ import annotations

from rosita.core.agent import RositaAgent
from rosita.core.prompt_builder import construir_prompt_sistema
from rosita.settings import Settings
from rosita.utils.file_loader import carregar_documentacao, carregar_texto


def montar_contexto_agente(settings: Settings) -> tuple[str, list[str]]:
    """Carrega instruções e documentação oficial da pasta de dados para a memória do agente."""
    regimento_path = settings.data_dir / "regimento_ecim.txt"
    if not regimento_path.exists():
        regimento_path = settings.data_dir / "regimento_ECIM.txt"
    instrucoes_path = settings.data_dir / "agent_instructions.txt"

    regimento = carregar_texto(regimento_path, "Regimento não encontrado.")
    template = carregar_texto(
        instrucoes_path,
        (
            "Você é ROSITA, assistente da PEI Rosa Bonfiglioli.\n"
            "Antes de responder, consulte a documentação oficial carregada em memória.\n"
            "Se a resposta não estiver nela, diga isso claramente.\n"
            "Responda com no máximo 3 linhas. Seja direto e amigável.\n\n"
            "DOCUMENTAÇÃO OFICIAL EM MEMÓRIA:\n{DOCUMENTACAO}"
        ),
    )

    documentos_carregados, documentacao = carregar_documentacao(
        settings.data_dir,
        skip_files={"agent_instructions.txt"},
    )
    documentos_carregados = [instrucoes_path.name] + documentos_carregados

    if not documentacao:
        documentos_carregados = [instrucoes_path.name, regimento_path.name]
        documentacao = regimento

    prompt_sistema = construir_prompt_sistema(
        template=template,
        regimento=regimento,
        documentacao=documentacao,
    )
    return prompt_sistema, documentos_carregados


def criar_agente(settings: Settings) -> RositaAgent:
    """Instancia agente carregando toda a documentação oficial da pasta de dados."""
    prompt_sistema, documentos_carregados = montar_contexto_agente(settings)
    return RositaAgent(
        settings=settings,
        prompt_sistema=prompt_sistema,
        documentos_contexto=documentos_carregados,
    )

