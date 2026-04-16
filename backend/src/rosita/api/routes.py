"""Rotas REST e SSE da API ROSITA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator

from flask import Blueprint, Response, jsonify, request

from rosita.bootstrap import montar_contexto_agente
from rosita.core.agent import RositaAgent
from rosita.settings import Settings
from rosita.utils.system_monitor import get_system_snapshot
from rosita.utils.validators import validar_pergunta


def _sse_chunk_payload(payload: Any) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _is_editable_data_file(filename: str) -> bool:
    path = Path(filename)
    return bool(filename) and path.name == filename and path.suffix.lower() in {".txt"}


def _resolve_data_file(data_dir: Path, filename: str) -> Path:
    if not _is_editable_data_file(filename):
        raise ValueError("Arquivo inválido para edição.")
    return data_dir / filename


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
                "servidor_ia": settings.ollama_host,
                "baixando_modelo": agent.is_downloading,
                "status_download": agent.download_status,
                "progresso_download": agent.download_percent,
                "documentos_contexto": agent.documentos_contexto,
                "contexto_carregado": bool(agent.prompt_sistema.strip()),
                "sistema": get_system_snapshot(),
            }
        )

    @api_bp.route("/models", methods=["GET"])
    def models() -> Any:
        try:
            return jsonify(
                {
                    "models": agent.listar_modelos_instalados(),
                    "current_model": agent.obter_modelo_atual(),
                    "recommended_models": agent.obter_modelos_recomendados(),
                    "downloading": agent.is_downloading,
                    "download_model": agent.download_model,
                    "download_status": agent.download_status,
                    "download_percent": agent.download_percent,
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

    @api_bp.route("/models/download", methods=["POST"])
    def download_model() -> Any:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        model = dados.get("model")
        if not isinstance(model, str) or not model.strip():
            return jsonify({"erro": "Campo 'model' é obrigatório."}), 400

        def gerar_download() -> Generator[str, None, None]:
            try:
                for evento in agent.baixar_modelo(model):
                    yield _sse_chunk_payload(evento)
                yield "data: [FIM]\n\n"
            except Exception as exc:
                yield f"data: [ERRO] {exc}\n\n"

        return Response(
            gerar_download(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @api_bp.route("/config/files", methods=["GET"])
    def list_config_files() -> Any:
        files = [
            path.name
            for path in sorted(settings.data_dir.iterdir())
            if path.is_file() and _is_editable_data_file(path.name)
        ]
        return jsonify({"files": files})

    @api_bp.route("/config/files/<path:filename>", methods=["GET"])
    def get_config_file(filename: str) -> Any:
        try:
            path = _resolve_data_file(settings.data_dir, filename)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

        if not path.exists():
            return jsonify({"erro": "Arquivo não encontrado."}), 404

        return jsonify({"filename": path.name, "content": path.read_text(encoding="utf-8")})

    @api_bp.route("/config/files/<path:filename>", methods=["PUT"])
    def save_config_file(filename: str) -> Any:
        try:
            path = _resolve_data_file(settings.data_dir, filename)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        content = dados.get("content")
        if not isinstance(content, str):
            return jsonify({"erro": "Campo 'content' é obrigatório."}), 400
        if len(content) > 300000:
            return jsonify({"erro": "Arquivo excede o limite permitido para edição."}), 400

        path.write_text(content, encoding="utf-8")
        prompt_sistema, documentos_carregados = montar_contexto_agente(settings)
        agent.atualizar_contexto(prompt_sistema, documentos_carregados)

        return jsonify(
            {
                "mensagem": "Arquivo salvo com sucesso.",
                "filename": path.name,
                "documentos_contexto": agent.documentos_contexto,
            }
        )

    @api_bp.route("/limpar", methods=["POST"])
    def limpar() -> Any:
        agent.limpar_historico()
        return jsonify({"mensagem": "Histórico limpo com sucesso."})

    @api_bp.route("/historico", methods=["GET"])
    def historico() -> Any:
        return jsonify({"historico": agent.obter_historico()})

    return api_bp

