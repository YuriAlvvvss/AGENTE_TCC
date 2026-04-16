import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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
    def test_uses_first_installed_model_when_configured_one_is_missing(self, mock_client):
        mock_client.return_value.list.return_value = {
            "models": [
                {"name": "qwen2.5:7b"},
                {"name": "llama3.2:3b"},
            ]
        }

        agent = RositaAgent(self.make_settings("modelo-inexistente"), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "llama3.2:3b")

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
    def test_download_model_streams_progress_and_updates_current_model(self, mock_client):
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
        self.assertEqual(agent.obter_modelo_atual(), "llama3.2:3b")
        self.assertTrue(any(evento["percentual"] == 25 for evento in eventos))

    @patch("rosita.core.agent.ollama.Client")
    def test_download_model_rejects_empty_name(self, mock_client):
        mock_client.return_value.list.return_value = {"models": []}
        agent = RositaAgent(self.make_settings(""), "prompt")

        with self.assertRaises(ValueError):
            list(agent.baixar_modelo("  "))


if __name__ == "__main__":
    unittest.main()
