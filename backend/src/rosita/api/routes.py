"""Rotas REST e SSE da API ROSITA."""

from __future__ import annotations

import json
from typing import Any, Generator

from flask import Blueprint, Response, jsonify, request

from rosita.core.agent import RositaAgent
from rosita.settings import Settings
from rosita.utils.validators import validar_pergunta


def _sse_chunk_payload(texto: str) -> str:
    return f"data: {json.dumps(texto)}\n\n"


def create_api_blueprint(agent: RositaAgent, settings: Settings) -> Blueprint:
    """Cria blueprint da API usando instância já inicializada do agente."""
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    @api_bp.route("/chat", methods=["POST"])
    def chat() -> Any:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        mensagem = dados.get("mensagem")
        if mensagem is None:
            return jsonify({"erro": "Campo 'mensagem' é obrigatório."}), 400
        if not validar_pergunta(mensagem, settings.max_input_chars):
            return jsonify({"erro": "Mensagem inválida."}), 400

        def gerar_resposta() -> Generator[str, None, None]:
            try:
                for chunk in agent.processar_pergunta(str(mensagem)):
                    yield _sse_chunk_payload(chunk)
                yield "data: [FIM]\n\n"
            except Exception as exc:
                yield f"data: [ERRO] {exc}\n\n"

        return Response(
            gerar_resposta(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @api_bp.route("/status", methods=["GET"])
    def status() -> Any:
        return jsonify(
            {
                "status": "online",
                "agente": "ROSITA",
                "modelo_atual": agent.obter_modelo_atual(),
                "ocupado": agent.is_busy,
            }
        )

    @api_bp.route("/models", methods=["GET"])
    def models() -> Any:
        try:
            return jsonify(
                {
                    "models": agent.listar_modelos_instalados(),
                    "current_model": agent.obter_modelo_atual(),
                }
            )
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/models/select", methods=["POST"])
    def select_model() -> Any:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        model = dados.get("model")
        if not isinstance(model, str) or not model.strip():
            return jsonify({"erro": "Campo 'model' é obrigatório."}), 400

        try:
            current = agent.trocar_modelo(model)
            return jsonify({"mensagem": "Modelo alterado com sucesso.", "current_model": current})
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/limpar", methods=["POST"])
    def limpar() -> Any:
        agent.limpar_historico()
        return jsonify({"mensagem": "Histórico limpo com sucesso."})

    @api_bp.route("/historico", methods=["GET"])
    def historico() -> Any:
        return jsonify({"historico": agent.obter_historico()})

    return api_bp

