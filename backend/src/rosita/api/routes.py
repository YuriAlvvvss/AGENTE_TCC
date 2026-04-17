"""Rotas REST e SSE da API ROSITA."""

from __future__ import annotations

import json
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator

from flask import Blueprint, Response, jsonify, request, session

from rosita.bootstrap import montar_contexto_agente
from rosita.core.agent import RositaAgent
from rosita.settings import Settings
from rosita.utils.file_loader import garantir_documentos_padrao
from rosita.utils.system_monitor import get_system_snapshot
from rosita.utils.validators import validar_pergunta


def _sse_chunk_payload(payload: Any) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _normalize_username(value: Any) -> str:
    return str(value or "").strip().lower()


def _available_users(settings: Settings) -> dict[str, dict[str, str]]:
    admin_username = settings.admin_username.strip() or "admin"
    user_username = settings.user_username.strip() or "usuario"
    return {
        _normalize_username(admin_username): {
            "username": admin_username,
            "password": settings.admin_password,
            "role": "admin",
            "display_name": "Administrador",
        },
        _normalize_username(user_username): {
            "username": user_username,
            "password": settings.user_password,
            "role": "user",
            "display_name": "Usuário",
        },
    }


def _permissions_for_role(role: str) -> list[str]:
    if role == "admin":
        return ["chat", "models", "settings", "telemetry"]
    if role == "user":
        return ["chat"]
    return []


def _session_payload() -> dict[str, Any]:
    role = str(session.get("role") or "guest")
    username = str(session.get("username") or "")
    authenticated = bool(username) and role in {"admin", "user"}
    return {
        "authenticated": authenticated,
        "username": username,
        "role": role,
        "display_name": str(session.get("display_name") or "Visitante"),
        "permissions": _permissions_for_role(role),
    }


def _require_roles(*roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            auth = _session_payload()
            if not auth["authenticated"]:
                return jsonify({"erro": "Faça login para continuar.", **auth}), 401
            if auth["role"] not in roles:
                return jsonify({"erro": "Acesso restrito ao administrador.", **auth}), 403
            return func(*args, **kwargs)

        return wrapped

    return decorator


def _is_editable_data_file(filename: str) -> bool:
    path = Path(filename)
    return bool(filename) and path.name == filename and path.suffix.lower() in {".txt"}


def _resolve_data_file(data_dir: Path, filename: str) -> Path:
    if not _is_editable_data_file(filename):
        raise ValueError("Arquivo inválido para edição.")
    return data_dir / filename


def _candidate_data_dirs(settings: Settings) -> list[Path]:
    directories: list[Path] = []
    for directory in [settings.data_dir, settings.bundled_data_dir, settings.base_dir / "data"]:
        if directory is None or directory in directories:
            continue
        directories.append(directory)
    return directories


def _ensure_data_dir_ready(settings: Settings) -> None:
    garantir_documentos_padrao(settings.data_dir, fallback_dirs=_candidate_data_dirs(settings)[1:])


def _list_editable_files(settings: Settings) -> list[str]:
    _ensure_data_dir_ready(settings)
    nomes: list[str] = []
    vistos: set[str] = set()
    for directory in _candidate_data_dirs(settings):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or not _is_editable_data_file(path.name):
                continue
            lower_name = path.name.lower()
            if lower_name in vistos:
                continue
            vistos.add(lower_name)
            nomes.append(path.name)
    return nomes


def _get_existing_data_file(settings: Settings, filename: str) -> Path:
    _ensure_data_dir_ready(settings)
    for directory in _candidate_data_dirs(settings):
        path = _resolve_data_file(directory, filename)
        if path.exists():
            return path
    return _resolve_data_file(settings.data_dir, filename)


def create_api_blueprint(agent: RositaAgent, settings: Settings) -> Blueprint:
    """Cria blueprint da API usando instância já inicializada do agente."""
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    @api_bp.route("/auth/session", methods=["GET"])
    def auth_session() -> Any:
        return jsonify(_session_payload())

    @api_bp.route("/auth/login", methods=["POST"])
    def login() -> Any:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        username = _normalize_username(dados.get("username"))
        password = str(dados.get("password") or "")
        user = _available_users(settings).get(username)

        if not username or not password:
            return jsonify({"erro": "Informe usuário e senha."}), 400
        if user is None or password != user["password"]:
            session.clear()
            return jsonify({"erro": "Usuário ou senha inválidos.", **_session_payload()}), 401

        session.clear()
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["display_name"] = user["display_name"]
        return jsonify({"mensagem": "Login realizado com sucesso.", **_session_payload()})

    @api_bp.route("/auth/logout", methods=["POST"])
    def logout() -> Any:
        session.clear()
        return jsonify(
            {
                "mensagem": "Sessão encerrada com sucesso.",
                "authenticated": False,
                "username": "",
                "role": "guest",
                "display_name": "Visitante",
                "permissions": [],
            }
        )

    @api_bp.route("/chat", methods=["POST"])
    @_require_roles("admin", "user")
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
        auth = _session_payload()
        payload = {
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
            **auth,
        }
        if auth["role"] == "admin":
            payload["sistema"] = get_system_snapshot()
        return jsonify(payload)

    @api_bp.route("/models", methods=["GET"])
    @_require_roles("admin")
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
    @_require_roles("admin")
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

    @api_bp.route("/models/unload", methods=["POST"])
    @_require_roles("admin")
    def unload_model() -> Any:
        try:
            previous_model = agent.descarregar_modelo_ativo()
            return jsonify(
                {
                    "mensagem": "Modelo descarregado com sucesso.",
                    "previous_model": previous_model,
                    "current_model": agent.obter_modelo_atual(),
                }
            )
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/models/delete", methods=["POST"])
    @_require_roles("admin")
    def delete_model() -> Any:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        model = dados.get("model")
        if not isinstance(model, str) or not model.strip():
            return jsonify({"erro": "Campo 'model' é obrigatório."}), 400

        try:
            removed_model = agent.excluir_modelo(model)
            return jsonify(
                {
                    "mensagem": "Modelo excluído com sucesso.",
                    "removed_model": removed_model,
                    "current_model": agent.obter_modelo_atual(),
                }
            )
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/models/download", methods=["POST"])
    @_require_roles("admin")
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
    @_require_roles("admin")
    def list_config_files() -> Any:
        return jsonify({"files": _list_editable_files(settings)})

    @api_bp.route("/config/files/<path:filename>", methods=["GET"])
    @_require_roles("admin")
    def get_config_file(filename: str) -> Any:
        try:
            path = _get_existing_data_file(settings, filename)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400

        if not path.exists():
            return jsonify({"erro": "Arquivo não encontrado."}), 404

        return jsonify({"filename": path.name, "content": path.read_text(encoding="utf-8")})

    @api_bp.route("/config/files/<path:filename>", methods=["PUT"])
    @_require_roles("admin")
    def save_config_file(filename: str) -> Any:
        _ensure_data_dir_ready(settings)
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
    @_require_roles("admin", "user")
    def limpar() -> Any:
        agent.limpar_historico()
        return jsonify({"mensagem": "Histórico limpo com sucesso."})

    @api_bp.route("/historico", methods=["GET"])
    @_require_roles("admin", "user")
    def historico() -> Any:
        return jsonify({"historico": agent.obter_historico()})

    return api_bp

