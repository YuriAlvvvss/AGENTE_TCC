import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rosita.core.agent import RositaAgent
from rosita.settings import Settings


class AgentModelSelectionTests(unittest.TestCase):
    def make_settings(self, model: str = "llama3.1:8b") -> Settings:
        base_dir = ROOT / "backend"
        return Settings(
            base_dir=base_dir,
            data_dir=base_dir / "data",
            ollama_model=model,
            max_history=5,
            max_input_chars=1000,
            api_host="127.0.0.1",
            api_port=5000,
            debug=False,
            chat_options={},
        )

    @patch("rosita.core.agent.ollama.list")
    def test_uses_first_installed_model_when_configured_one_is_missing(self, mock_list):
        mock_list.return_value = {
            "models": [
                {"name": "qwen2.5:7b"},
                {"name": "llama3.2:3b"},
            ]
        }

        agent = RositaAgent(self.make_settings("modelo-inexistente"), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "llama3.2:3b")

    @patch("rosita.core.agent.ollama.list")
    def test_keeps_current_model_empty_when_no_model_is_installed(self, mock_list):
        mock_list.return_value = {"models": []}

        agent = RositaAgent(self.make_settings("modelo-inexistente"), "prompt")

        self.assertEqual(agent.obter_modelo_atual(), "")


if __name__ == "__main__":
    unittest.main()
