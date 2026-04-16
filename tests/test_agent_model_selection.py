import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rosita.api.routes import create_api_blueprint
from rosita.bootstrap import criar_agente
from rosita.core.agent import RositaAgent
from rosita.settings import Settings, load_settings


class AgentModelSelectionTests(unittest.TestCase):
    def make_settings(
        self,
        model: str = "llama3.1:8b",
        host: str = "http://ia-externa:11434",
    ) -> Settings:
        base_dir = ROOT / "backend"
        return Settings(
            base_dir=base_dir,
            data_dir=base_dir / "data",
            ollama_model=model,
            ollama_host=host,
            max_history=5,
            max_input_chars=1000,
            api_host="127.0.0.1",
            api_port=5000,
            debug=False,
            chat_options={},
        )

    @patch("rosita.core.agent.ollama.Client")
    def test_does_not_auto_select_installed_model_on_startup(self, mock_client):
        mock_client.return_value.list.return_value = {
            "models": [
                {"name": "qwen2.5:7b"},
                {"name": "llama3.2:3b"},
            ]
        }

        agent = RositaAgent(self.make_settings("modelo-inexistente"), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "")

    @patch("rosita.core.agent.ollama.Client")
    def test_keeps_current_model_empty_when_no_model_is_installed(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}

        agent = RositaAgent(self.make_settings("modelo-inexistente"), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "")

    @patch("rosita.core.agent.ollama.Client")
    def test_initializes_ollama_client_with_configured_host(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}

        RositaAgent(self.make_settings(), "prompt")

        mock_client.assert_called_once_with(host="http://ia-externa:11434")

    @patch("rosita.core.agent.ollama.Client")
    def test_falls_back_to_positional_client_base_url_when_host_kwarg_is_unsupported(self, mock_client):
        primary_client = unittest.mock.Mock()
        primary_client.list.return_value = {"models": []}

        def side_effect(*args, **kwargs):
            if kwargs.get("host"):
                raise TypeError("unexpected keyword argument 'host'")
            return primary_client

        mock_client.side_effect = side_effect

        agent = RositaAgent(self.make_settings(), "prompt")

        self.assertEqual(mock_client.call_args_list[0], unittest.mock.call(host="http://ia-externa:11434"))
        self.assertEqual(mock_client.call_args_list[1], unittest.mock.call("http://ia-externa:11434"))
        self.assertIs(agent.client, primary_client)

    def test_load_settings_prefers_manual_external_ai_server_address(self):
        with patch.dict(
            os.environ,
            {
                "ROSITA_OLLAMA_HOST": "https://meu-servidor-ia.exemplo.com",
                "ROSITA_AI_SERVER_URL": "https://ignorado.exemplo.com",
            },
            clear=False,
        ):
            settings = load_settings()

        self.assertEqual(settings.ollama_host, "https://meu-servidor-ia.exemplo.com")

    @patch("rosita.core.agent.ollama.Client")
    def test_agent_preloads_all_text_docs_from_data_folder(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}

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

            settings = self.make_settings("")
            settings = Settings(
                base_dir=settings.base_dir,
                data_dir=data_dir,
                ollama_model=settings.ollama_model,
                ollama_host=settings.ollama_host,
                max_history=settings.max_history,
                max_input_chars=settings.max_input_chars,
                api_host=settings.api_host,
                api_port=settings.api_port,
                debug=settings.debug,
                chat_options=settings.chat_options,
            )

            agent = criar_agente(settings)

        self.assertIn("Documento A: regimento escolar oficial.", agent.prompt_sistema)
        self.assertIn("Documento B: telefone da secretaria 12345.", agent.prompt_sistema)

    @patch("rosita.core.agent.ollama.Client")
    def test_download_model_streams_progress_without_auto_activating_model(self, mock_client):
        client = mock_client.return_value
        client.list.return_value = {"models": []}
        client.pull.return_value = iter(
            [
                {"status": "pulling manifest"},
                {"status": "downloading", "completed": 25, "total": 100},
                {"status": "success"},
            ]
        )

        agent = RositaAgent(self.make_settings(""), "prompt")
        eventos = list(agent.baixar_modelo("llama3.2:3b"))

        client.pull.assert_called_once_with(model="llama3.2:3b", stream=True)
        self.assertEqual(agent.obter_modelo_atual(), "")
        self.assertTrue(any(evento["percentual"] == 25 for evento in eventos))

    @patch("rosita.core.agent.ollama.Client")
    def test_switching_model_unloads_current_before_loading_next(self, mock_client):
        client = mock_client.return_value
        client.list.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "qwen2.5:3b"},
            ]
        }

        agent = RositaAgent(self.make_settings(""), "prompt")
        agent.trocar_modelo("llama3.2:3b")
        client.generate.reset_mock()

        agent.trocar_modelo("qwen2.5:3b")

        self.assertEqual(
            client.generate.call_args_list,
            [
                unittest.mock.call(
                    model="llama3.2:3b",
                    prompt="",
                    stream=False,
                    keep_alive=0,
                ),
                unittest.mock.call(
                    model="qwen2.5:3b",
                    prompt=".",
                    stream=False,
                    options={"num_predict": 1},
                ),
            ],
        )

    @patch("rosita.core.agent.ollama.Client")
    def test_download_model_rejects_empty_name(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}
        agent = RositaAgent(self.make_settings(""), "prompt")

        with self.assertRaises(ValueError):
            list(agent.baixar_modelo("  "))

    @patch("rosita.core.agent.ollama.Client")
    def test_config_api_lists_editable_data_files(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "agent_instructions.txt").write_text("Instruções\n{DOCUMENTACAO}", encoding="utf-8")
            (data_dir / "regimento_ECIM.txt").write_text("Regimento oficial", encoding="utf-8")
            (data_dir / "observacoes.md").write_text("Notas", encoding="utf-8")
            (data_dir / "logo.png").write_bytes(b"png")

            settings = self.make_settings("")
            settings = Settings(
                base_dir=settings.base_dir,
                data_dir=data_dir,
                ollama_model=settings.ollama_model,
                ollama_host=settings.ollama_host,
                max_history=settings.max_history,
                max_input_chars=settings.max_input_chars,
                api_host=settings.api_host,
                api_port=settings.api_port,
                debug=settings.debug,
                chat_options=settings.chat_options,
            )
            agent = criar_agente(settings)

            app = Flask(__name__)
            app.register_blueprint(create_api_blueprint(agent, settings))
            client = app.test_client()
            res = client.get("/api/config/files")

        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertIn("agent_instructions.txt", payload["files"])
        self.assertIn("regimento_ECIM.txt", payload["files"])
        self.assertNotIn("observacoes.md", payload["files"])
        self.assertNotIn("logo.png", payload["files"])

    @patch("rosita.core.agent.ollama.Client")
    def test_saving_config_file_updates_agent_context(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "agent_instructions.txt").write_text("Base oficial:\n{DOCUMENTACAO}", encoding="utf-8")
            (data_dir / "regimento_ECIM.txt").write_text("Regimento original", encoding="utf-8")
            (data_dir / "faq.txt").write_text("Conteúdo antigo", encoding="utf-8")

            settings = self.make_settings("")
            settings = Settings(
                base_dir=settings.base_dir,
                data_dir=data_dir,
                ollama_model=settings.ollama_model,
                ollama_host=settings.ollama_host,
                max_history=settings.max_history,
                max_input_chars=settings.max_input_chars,
                api_host=settings.api_host,
                api_port=settings.api_port,
                debug=settings.debug,
                chat_options=settings.chat_options,
            )
            agent = criar_agente(settings)

            app = Flask(__name__)
            app.register_blueprint(create_api_blueprint(agent, settings))
            client = app.test_client()
            res = client.put(
                "/api/config/files/faq.txt",
                json={"content": "Conteúdo novo e oficial"},
            )

            updated_text = (data_dir / "faq.txt").read_text(encoding="utf-8")
            prompt = agent.prompt_sistema

        self.assertEqual(res.status_code, 200)
        self.assertEqual(updated_text, "Conteúdo novo e oficial")
        self.assertIn("Conteúdo novo e oficial", prompt)


if __name__ == "__main__":
    unittest.main()
