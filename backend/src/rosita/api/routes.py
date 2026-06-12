"""Rotas REST e SSE da API ROSITA."""

from __future__ import annotations

import json
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator

from flask import Blueprint, Response, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from rosita.bootstrap import montar_contexto_agente
from rosita.core.agent import RositaAgent
from rosita.settings import Settings
from rosita.utils.env_manager import update_env_file
from rosita.utils.file_loader import garantir_documentos_padrao
from rosita.utils.system_monitor import get_system_snapshot
from rosita.utils.validators import validar_nome_modelo, validar_pergunta


logger = logging.getLogger("rosita.api")

# Hash descartável usado para igualar o tempo de resposta quando o usuário não
# existe, evitando enumeração de usuários por análise de tempo (timing attack).
_DUMMY_PASSWORD_HASH = generate_password_hash("rosita-dummy-password")


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
            "password_hash": settings.admin_password_hash,
            "role": "admin",
            "display_name": "Administrador",
        },
        _normalize_username(user_username): {
            "username": user_username,
            "password_hash": settings.user_password_hash,
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


def create_api_blueprint(
    agent: RositaAgent,
    settings: Settings,
    limiter: Any = None,
    history_store: Any = None,
) -> Blueprint:
    """Cria blueprint da API usando instância já inicializada do agente."""
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    def _usuario_atual() -> str:
        """Identifica o usuário logado para indexar o histórico."""
        return str(session.get("username") or "").strip()

    def _limit(regra: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Aplica o limite de taxa quando há um limiter disponível."""
        if limiter is None:
            return lambda func: func
        return limiter.limit(regra)

    @api_bp.route("/auth/session", methods=["GET"])
    def auth_session() -> Any:
        return jsonify(_session_payload())

    @api_bp.route("/auth/login", methods=["POST"])
    @_limit("10 per minute")
    def login() -> Any:
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        username = _normalize_username(dados.get("username"))
        password = str(dados.get("password") or "")
        user = _available_users(settings).get(username)

        if not username or not password:
            return jsonify({"erro": "Informe usuário e senha."}), 400

        # Compara o hash mesmo quando o usuário não existe, mantendo o tempo de
        # resposta constante (proteção contra timing attack / enumeração).
        senha_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
        senha_valida = check_password_hash(senha_hash, password)
        if user is None or not senha_valida:
            session.clear()
            return jsonify({"erro": "Usuário ou senha inválidos.", **_session_payload()}), 401
        if user["role"] != "admin":
            session.clear()
            return jsonify(
                {
                    "erro": "Acesso restrito ao administrador. O chat está disponível sem login.",
                    **_session_payload(),
                }
            ), 403

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
    @_limit("20 per minute")
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

        # Captura usuário e histórico fora do gerador (contexto de requisição).
        username = _usuario_atual()
        pergunta = str(mensagem).strip()
        historico_previo = (
            history_store.get(username, limit=settings.max_history) if history_store else []
        )

        def gerar_resposta() -> Generator[str, None, None]:
            resposta = ""
            try:
                for chunk in agent.processar_pergunta(pergunta, historico_previo):
                    resposta += chunk
                    yield _sse_chunk_payload(chunk)
                # Persiste pergunta e resposta apenas em caso de sucesso.
                if history_store and username:
                    history_store.append(username, "user", pergunta)
                    history_store.append(username, "assistant", resposta)
                yield "data: [FIM]\n\n"
            except Exception as exc:
                logger.exception("Erro ao gerar resposta do chat")
                yield f"data: [ERRO] {exc}\n\n"

        return Response(
            gerar_resposta(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @api_bp.route("/health", methods=["GET"])
    def health() -> Any:
        """Healthcheck que verifica a conectividade real com o provedor de IA.

        Retorna 200 quando o provedor responde e 503 quando está indisponível,
        permitindo que orquestradores (Docker/Coolify) detectem degradação.
        """
        ia = agent.verificar_provedor()
        payload = {
            "status": "ok" if ia["ok"] else "degraded",
            "agente": "ROSITA",
            "modelo_atual": agent.obter_modelo_atual(),
            "ia": ia,
        }
        return jsonify(payload), (200 if ia["ok"] else 503)

    @api_bp.route("/status", methods=["GET"])
    def status() -> Any:
        auth = _session_payload()
        payload = {
            "status": "online",
            "agente": "ROSITA",
            "modelo_atual": agent.obter_modelo_atual(),
            "ocupado": agent.is_busy,
            "provedor_ia": getattr(agent, "active_provider", settings.ai_provider),
            "servidor_ia": agent.settings.ollama_host,
            "gateway_url": agent.settings.gateway_url,
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
        if not validar_nome_modelo(model):
            return jsonify({"erro": "Nome de modelo inválido."}), 400

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
        if not validar_nome_modelo(model):
            return jsonify({"erro": "Nome de modelo inválido."}), 400

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
        if not validar_nome_modelo(model):
            return jsonify({"erro": "Nome de modelo inválido."}), 400

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

        # Backup do conteúdo anterior antes de sobrescrever (rede de segurança).
        if path.exists():
            try:
                backup_path = path.with_suffix(path.suffix + ".bak")
                backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            except OSError:
                # Falha no backup não deve impedir o salvamento em si.
                pass

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
        if history_store:
            history_store.clear(_usuario_atual())
        return jsonify({"mensagem": "Histórico limpo com sucesso."})

    @api_bp.route("/historico", methods=["GET"])
    def historico() -> Any:
        registros = history_store.get(_usuario_atual()) if history_store else []
        return jsonify({"historico": registros})

    @api_bp.route("/provedores", methods=["GET"])
    @_require_roles("admin")
    def provedores() -> Any:
        """Lista provedores de IA disponíveis."""
        try:
            return jsonify({
                "provedores": agent.obter_provedores_disponiveis(),
                "ativo": agent.active_provider,
            })
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/provedores/trocar", methods=["POST"])
    @_require_roles("admin")
    def trocar_provedor() -> Any:
        """Troca o provedor ativo e retorna modelos disponíveis."""
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        provedor = dados.get("provedor")
        if not isinstance(provedor, str) or not provedor.strip():
            return jsonify({"erro": "Campo 'provedor' é obrigatório."}), 400

        try:
            resultado = agent.trocar_provedor(provedor)
            return jsonify({
                "mensagem": f"Provedor alterado para {resultado['label']}",
                **resultado,
            })
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/credenciais", methods=["GET"])
    @_require_roles("admin")
    def obter_credenciais() -> Any:
        """Retorna a configuração atual do provedor de IA (sem expor a API key)."""
        try:
            return jsonify({
                **agent.obter_config(),
                "provedores": agent.obter_provedores_disponiveis(),
            })
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

    @api_bp.route("/credenciais", methods=["PUT", "POST"])
    @_require_roles("admin")
    def salvar_credenciais() -> Any:
        """Aplica e persiste a configuração do provedor (Ollama/OpenRouter/Gateway)."""
        dados = request.get_json(silent=True)
        if dados is None or not isinstance(dados, dict):
            return jsonify({"erro": "JSON inválido ou ausente."}), 400

        mudancas: dict[str, str] = {}
        for campo in (
            "ai_provider",
            "ollama_host",
            "ollama_model",
            "openrouter_model",
            "gateway_url",
            "gateway_model",
        ):
            valor = dados.get(campo)
            if isinstance(valor, str):
                mudancas[campo] = valor.strip()

        # O host do Ollama nunca deve ser apagado para vazio (deixaria o Ollama
        # sem endereço). Se vier em branco, mantém o valor atual.
        if not mudancas.get("ollama_host", "").strip():
            mudancas.pop("ollama_host", None)

        # As API keys só são alteradas quando enviadas e não-vazias, para não
        # apagar a credencial existente acidentalmente. Para limpar, use o
        # respectivo campo limpar_*.
        api_key = dados.get("openrouter_api_key")
        if isinstance(api_key, str) and api_key.strip():
            mudancas["openrouter_api_key"] = api_key.strip()
        if dados.get("limpar_openrouter_api_key") is True:
            mudancas["openrouter_api_key"] = ""

        gateway_key = dados.get("gateway_api_key")
        if isinstance(gateway_key, str) and gateway_key.strip():
            mudancas["gateway_api_key"] = gateway_key.strip()
        if dados.get("limpar_gateway_api_key") is True:
            mudancas["gateway_api_key"] = ""

        try:
            agent.reconfigurar(**mudancas)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409
        except Exception as exc:
            return jsonify({"erro": str(exc)}), 500

        config_atual = agent.obter_config()
        env_values = {
            "ROSITA_AI_PROVIDER": agent.active_provider,
            "ROSITA_OLLAMA_HOST": agent.settings.ollama_host,
            "ROSITA_OLLAMA_MODEL": agent.settings.ollama_model,
            "ROSITA_OPENROUTER_API_KEY": agent.settings.openrouter_api_key,
            "ROSITA_OPENROUTER_MODEL": agent.settings.openrouter_model,
            "ROSITA_GATEWAY_URL": agent.settings.gateway_url,
            "ROSITA_GATEWAY_MODEL": agent.settings.gateway_model,
            "ROSITA_GATEWAY_API_KEY": agent.settings.gateway_api_key,
        }
        try:
            update_env_file(agent.settings.base_dir / ".env", env_values)
        except Exception as exc:
            return jsonify({
                "mensagem": "Configuração aplicada, mas não foi possível persistir no .env.",
                "aviso": str(exc),
                **config_atual,
                "provedores": agent.obter_provedores_disponiveis(),
            })

        return jsonify({
            "mensagem": "Configuração salva e aplicada com sucesso.",
            **config_atual,
            "provedores": agent.obter_provedores_disponiveis(),
        })

    return api_bp

