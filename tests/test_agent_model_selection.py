"""Testes do núcleo do agente (RositaAgent), sem depender de servidores de IA reais.

Os clientes são os provedores Open Router e Gateway (OpenAI-compatible) —
o provedor Ollama foi removido do projeto.
"""

from pathlib import Path
import dataclasses
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from werkzeug.security import generate_password_hash

from rosita.api.routes import create_api_blueprint
from rosita.bootstrap import criar_agente
from rosita.core.agent import RositaAgent
from rosita.core.ai_client import GatewayClient
from rosita.settings import Settings, load_settings
from rosita.utils.history_store import HistoryStore
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class AgentModelSelectionTests(unittest.TestCase):
    def make_settings(
        self,
        model: str = "",
        url: str = "http://ia-externa:8000",
        provider: str = "gateway",
        openrouter_key: str = "",
    ) -> Settings:
        base_dir = ROOT / "backend"
        return Settings(
            base_dir=base_dir,
            data_dir=base_dir / "data",
            history_db_path=base_dir / "data" / "history.sqlite3",
            ai_provider=provider,
            openrouter_api_key=openrouter_key,
            openrouter_model=model if provider == "openrouter" else "",
            gateway_url=url,
            gateway_model=model if provider == "gateway" else "",
            gateway_api_key="",
            max_history=5,
            max_input_chars=1000,
            api_host="127.0.0.1",
            api_port=5000,
            debug=False,
            chat_options={},
            admin_password_hash=generate_password_hash("admin123"),
            user_password_hash=generate_password_hash("usuario123"),
        )

    def test_does_not_auto_select_model_on_startup(self):
        agent = RositaAgent(self.make_settings(), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "")

    def test_keeps_current_model_empty_when_no_model_configured(self):
        agent = RositaAgent(self.make_settings(), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "")

    def test_initializes_gateway_client_with_configured_url(self):
        agent = RositaAgent(self.make_settings(), "prompt")

        self.assertIsInstance(agent.gateway_client, GatewayClient)
        self.assertEqual(agent.gateway_client.base_url, "http://ia-externa:8000")
        self.assertIsNone(agent.openrouter_client)

    def test_initializes_openrouter_client_with_api_key(self):
        agent = RositaAgent(
            self.make_settings(provider="openrouter", openrouter_key="sk-teste", url=""),
            "prompt",
        )

        self.assertIsNotNone(agent.openrouter_client)
        self.assertIsNone(agent.gateway_client)
        self.assertEqual(agent.active_provider, "openrouter")

    def test_agent_raises_without_provider_configured(self):
        with self.assertRaises(RuntimeError):
            RositaAgent(self.make_settings(url="", openrouter_key=""), "prompt")

    def test_load_settings_defaults_to_openrouter_provider(self):
        with patch.dict(os.environ, {"ROSITA_AI_PROVIDER": ""}, clear=False):
            settings = load_settings()

        self.assertEqual(settings.ai_provider, "openrouter")

    def test_load_settings_reads_gateway_url(self):
        with patch.dict(
            os.environ,
            {"ROSITA_GATEWAY_URL": "https://meu-gateway.exemplo.com"},
            clear=False,
        ):
            settings = load_settings()

        self.assertEqual(settings.gateway_url, "https://meu-gateway.exemplo.com")

    def test_agent_preloads_all_text_docs_from_data_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "agent_instructions.txt").write_text(
                "Você é ROSITA. Use a documentação oficial abaixo.\n\n{DOCUMENTACAO}",
                encoding="utf-8",
            )
            (data_dir / "regimento_ECIM.txt").write_text(
                "Documento A: regimento escolar oficial.",
                encoding="utf-8",
            )
            (data_dir / "contatos.txt").write_text(
                "Documento B: telefone da secretaria 12345.",
                encoding="utf-8",
            )

            settings = dataclasses.replace(self.make_settings(), data_dir=data_dir)

            agent = criar_agente(settings)

        self.assertIn("Documento A: regimento escolar oficial.", agent.prompt_sistema)
        self.assertIn("Documento B: telefone da secretaria 12345.", agent.prompt_sistema)

    def test_agent_recovers_default_references_when_runtime_data_dir_is_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_data_dir = Path(tmpdir) / "data"
            empty_data_dir.mkdir()

            settings = dataclasses.replace(self.make_settings(), data_dir=empty_data_dir)

            agent = criar_agente(settings)

        self.assertIn("PROGRAMA ESCOLA CÍVICO-MILITAR", agent.prompt_sistema)
        self.assertIn("agent_instructions.txt", agent.documentos_contexto)
        self.assertIn("regimento_ECIM.txt", agent.documentos_contexto)

    def test_config_files_endpoint_lists_default_txt_files_when_runtime_data_dir_is_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_data_dir = Path(tmpdir) / "data"
            empty_data_dir.mkdir()

            settings = dataclasses.replace(self.make_settings(), data_dir=empty_data_dir)

            app = Flask(__name__)
            app.secret_key = "test-secret"
            agent = criar_agente(settings)
            app.register_blueprint(create_api_blueprint(agent, settings))
            client = app.test_client()
            client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "admin123"},
            )

            response = client.get("/api/config/files")

        self.assertEqual(response.status_code, 200)
        self.assertIn("agent_instructions.txt", response.get_json()["files"])
        self.assertIn("regimento_ECIM.txt", response.get_json()["files"])

    def test_list_models_uses_gateway_provider(self):
        agent = RositaAgent(self.make_settings(), "prompt")
        agent.gateway_client.list_models = MagicMock(return_value=["deepseek-chat"])

        modelos = agent.listar_modelos_instalados()

        self.assertEqual(modelos, ["deepseek-chat"])
        agent.gateway_client.list_models.assert_called_once()

    def test_gateway_client_list_models_parses_api_response(self):
        cliente = GatewayClient(self.make_settings())
        fake = _FakeResponse({"data": [{"id": "modelo-b"}, {"id": "modelo-a"}]})

        with patch("rosita.core.ai_client._make_request_with_retry", return_value=fake):
            modelos = cliente.list_models()

        self.assertEqual(modelos, ["modelo-a", "modelo-b"])

    def test_switching_model_only_updates_selection(self):
        agent = RositaAgent(self.make_settings(), "prompt")
        agent.gateway_client.list_models = MagicMock(
            return_value=["modelo-a", "modelo-b"]
        )

        agent.trocar_modelo("modelo-a")
        agent.trocar_modelo("modelo-b")

        self.assertEqual(agent.obter_modelo_atual(), "modelo-b")
        self.assertEqual(agent.gateway_client.list_models.call_count, 2)

    def test_trocar_modelo_rejects_unknown_model(self):
        agent = RositaAgent(self.make_settings(), "prompt")
        agent.gateway_client.list_models = MagicMock(return_value=["modelo-a"])

        with self.assertRaises(ValueError):
            agent.trocar_modelo("modelo-inexistente")

    def test_trocar_provedor_switches_between_openrouter_and_gateway(self):
        agent = RositaAgent(
            self.make_settings(provider="openrouter", openrouter_key="sk-teste"),
            "prompt",
        )
        agent.openrouter_client.list_models = MagicMock(return_value=["or-modelo"])
        agent.gateway_client.list_models = MagicMock(return_value=["gw-modelo"])

        resultado = agent.trocar_provedor("gateway")

        self.assertEqual(agent.active_provider, "gateway")
        self.assertEqual(resultado["label"], "Gateway Local")
        self.assertEqual(resultado["modelos"], ["gw-modelo"])

        resultado = agent.trocar_provedor("openrouter")

        self.assertEqual(agent.active_provider, "openrouter")
        self.assertEqual(resultado["modelos"], ["or-modelo"])

    def test_config_api_lists_editable_data_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "agent_instructions.txt").write_text("Instruções\n{DOCUMENTACAO}", encoding="utf-8")
            (data_dir / "regimento_ECIM.txt").write_text("Regimento oficial", encoding="utf-8")
            (data_dir / "observacoes.md").write_text("Notas", encoding="utf-8")
            (data_dir / "logo.png").write_bytes(b"png")

            settings = dataclasses.replace(self.make_settings(), data_dir=data_dir)
            agent = criar_agente(settings)

            app = Flask(__name__)
            app.secret_key = "test-secret"
            app.register_blueprint(create_api_blueprint(agent, settings))
            client = app.test_client()
            client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "admin123"},
            )
            res = client.get("/api/config/files")

        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertIn("agent_instructions.txt", payload["files"])
        self.assertIn("regimento_ECIM.txt", payload["files"])
        self.assertNotIn("observacoes.md", payload["files"])
        self.assertNotIn("logo.png", payload["files"])

    def test_saving_config_file_updates_agent_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "agent_instructions.txt").write_text("Base oficial:\n{DOCUMENTACAO}", encoding="utf-8")
            (data_dir / "regimento_ECIM.txt").write_text("Regimento original", encoding="utf-8")
            (data_dir / "faq.txt").write_text("Conteúdo antigo", encoding="utf-8")

            settings = dataclasses.replace(self.make_settings(), data_dir=data_dir)
            agent = criar_agente(settings)

            app = Flask(__name__)
            app.secret_key = "test-secret"
            app.register_blueprint(create_api_blueprint(agent, settings))
            client = app.test_client()
            client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "admin123"},
            )
            res = client.put(
                "/api/config/files/faq.txt",
                json={"content": "Conteúdo novo e oficial"},
            )

            updated_text = (data_dir / "faq.txt").read_text(encoding="utf-8")
            prompt = agent.prompt_sistema

        self.assertEqual(res.status_code, 200)
        self.assertEqual(updated_text, "Conteúdo novo e oficial")
        self.assertIn("Conteúdo novo e oficial", prompt)

    def test_status_api_returns_system_and_gpu_summary(self):
        settings = self.make_settings()
        agent = RositaAgent(settings, "prompt")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(create_api_blueprint(agent, settings))
        client = app.test_client()
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        res = client.get("/api/status")

        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertIn("sistema", payload)
        self.assertIsInstance(payload["sistema"]["cpu"], dict)
        self.assertIsInstance(payload["sistema"]["memoria"], dict)
        self.assertIsInstance(payload["sistema"]["gpu"], dict)
        self.assertIn("uso_percentual", payload["sistema"]["cpu"])
        self.assertIn("percentual", payload["sistema"]["memoria"])
        self.assertIn("disponivel", payload["sistema"]["gpu"])
        self.assertIn("memoria_total", payload["sistema"]["gpu"])
        self.assertIn("memoria_usada", payload["sistema"]["gpu"])
        self.assertIn("memoria_percentual", payload["sistema"]["gpu"])

    def test_login_endpoint_creates_admin_session(self):
        settings = self.make_settings()
        agent = RositaAgent(settings, "prompt")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(create_api_blueprint(agent, settings))
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["role"], "admin")
        self.assertTrue(payload["authenticated"])

    def test_regular_user_login_is_rejected(self):
        settings = self.make_settings()
        agent = RositaAgent(settings, "prompt")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(create_api_blueprint(agent, settings))
        client = app.test_client()

        login = client.post(
            "/api/auth/login",
            json={"username": "usuario", "password": "usuario123"},
        )

        self.assertEqual(login.status_code, 403)
        payload = login.get_json()
        self.assertIn("administrador", payload["erro"].lower())

    def test_guest_cannot_access_admin_settings(self):
        settings = self.make_settings()
        agent = RositaAgent(settings, "prompt")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(create_api_blueprint(agent, settings))
        client = app.test_client()

        res = client.get("/api/config/files")

        self.assertEqual(res.status_code, 401)

    def test_guest_status_hides_hardware_snapshot(self):
        settings = self.make_settings()
        agent = RositaAgent(settings, "prompt")

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.register_blueprint(create_api_blueprint(agent, settings))
        client = app.test_client()

        res = client.get("/api/status")

        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertEqual(payload["role"], "guest")
        self.assertNotIn("sistema", payload)

    def test_guest_can_clear_chat_history(self):
        settings = self.make_settings()
        agent = RositaAgent(settings, "prompt")

        tmpdir = Path(tempfile.mkdtemp())
        try:
            store = HistoryStore(tmpdir / "hist.sqlite3")
            store.append("guest:visitante", "user", "teste")

            app = Flask(__name__)
            app.secret_key = "test-secret"
            app.register_blueprint(create_api_blueprint(agent, settings, history_store=store))
            client = app.test_client()
            with client.session_transaction() as sess:
                sess["guest_id"] = "visitante"

            res = client.post("/api/limpar")

            self.assertEqual(res.status_code, 200)
            self.assertEqual(store.get("guest:visitante"), [])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()