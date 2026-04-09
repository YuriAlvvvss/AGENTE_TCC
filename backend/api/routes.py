"""Rotas REST e SSE do ROSITA."""

import json
import logging
from typing import Any, Generator, Optional

from flask import Blueprint, Response, jsonify, request

from config import DATA_DIR
from core.agent import RositaAgent
from utils.file_handler import carregar_regimento
from utils.validators import validar_pergunta

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")

agent: Optional[RositaAgent] = None


def init_routes(app: Any) -> None:
    """
    Carrega o regimento, instancia o agente e registra o blueprint na aplicação.

    Args:
        app: Instância Flask.
    """
    global agent
    caminho_regimento = DATA_DIR / "regimento_ECIM.txt"
    texto_regimento = carregar_regimento(str(caminho_regimento))
    agent = RositaAgent(texto_regimento)
    app.register_blueprint(api_bp)
    logger.info("Rotas API registradas; agente ROSITA inicializado.")


def _sse_chunk_payload(texto: str) -> str:
    """Serializa um fragmento de texto em uma linha SSE segura (JSON)."""
    return f"data: {json.dumps(texto)}\n\n"


@api_bp.route("/chat", methods=["POST"])
def chat() -> Any:
    """
    Recebe uma mensagem em JSON e devolve a resposta do modelo em SSE (streaming).

    Body JSON esperado: ``{"mensagem": "..."}``.

    Returns:
        ``Response`` com ``text/event-stream`` ou erro JSON 4xx/5xx.
    """
    global agent
    if agent is None:
        logger.error("Agente não inicializado ao acessar /api/chat.")
        return jsonify({"erro": "Agente não inicializado."}), 500

    try:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        mensagem = dados.get("mensagem")
        if mensagem is None:
            return jsonify({"erro": "Campo 'mensagem' é obrigatório."}), 400

        if not validar_pergunta(mensagem):
            return jsonify(
                {
                    "erro": "Mensagem inválida: deve ser texto não vazio "
                    "e com no máximo 1000 caracteres.",
                }
            ), 400

        def gerar_resposta() -> Generator[str, None, None]:
            assert agent is not None
            try:
                for chunk in agent.processar_pergunta(str(mensagem)):
                    yield _sse_chunk_payload(chunk)
                yield "data: [FIM]\n\n"
            except ValueError as exc:
                logger.warning("Validação no agente: %s", exc)
                yield f"data: [ERRO] {exc}\n\n"
            except Exception as exc:
                logger.exception("Erro no streaming /api/chat.")
                yield f"data: [ERRO] {exc}\n\n"

        return Response(
            gerar_resposta(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as exc:
        logger.exception("Erro geral em /api/chat.")
        return jsonify({"erro": str(exc)}), 500


@api_bp.route("/status", methods=["GET"])
def status() -> Any:
    """
    Indica se a API está no ar e qual agente está ativo.

    Returns:
        JSON com ``status`` e ``agente``.
    """
    return jsonify({"status": "online", "agente": "ROSITA"})


@api_bp.route("/limpar", methods=["POST"])
def limpar() -> Any:
    """
    Limpa o histórico de conversa do agente.

    Returns:
        JSON com mensagem de sucesso ou erro.
    """
    global agent
    if agent is None:
        return jsonify({"erro": "Agente não inicializado."}), 500
    try:
        agent.limpar_historico()
        return jsonify({"mensagem": "Histórico limpo com sucesso."})
    except Exception as exc:
        logger.exception("Erro ao limpar histórico.")
        return jsonify({"erro": str(exc)}), 500


@api_bp.route("/historico", methods=["GET"])
def historico() -> Any:
    """
    Retorna o histórico atual da conversa (cópia).

    Returns:
        JSON com lista de mensagens ou erro.
    """
    global agent
    if agent is None:
        return jsonify({"erro": "Agente não inicializado."}), 500
    try:
        return jsonify({"historico": agent.obter_historico()})
    except Exception as exc:
        logger.exception("Erro ao obter histórico.")
        return jsonify({"erro": str(exc)}), 500
