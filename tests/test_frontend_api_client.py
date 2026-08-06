"""Testes estáticos para o cliente de API do frontend."""

from pathlib import Path
import re


def test_api_client_parse_error_uses_text_once():
    src = Path("web/scripts/api_client.js").read_text(encoding="utf-8")

    match = re.search(r"async _parseErro\(res\) \{([\s\S]*?)\n  \}", src)
    assert match is not None, "Função _parseErro não encontrada em web/scripts/api_client.js"

    body = match.group(1)
    assert "const text = await res.text();" in body
    assert "JSON.parse(text)" in body
    assert "await res.json()" not in body


def test_config_js_local_dev_api_base():
    src = Path("web/scripts/config.js").read_text(encoding="utf-8")
    assert "window.ROSITA_API_BASE_URL = `${window.location.protocol}//127.0.0.1:18500`;" in src
    assert "isDefaultWebPort = window.location.port === \"18080\"" in src
