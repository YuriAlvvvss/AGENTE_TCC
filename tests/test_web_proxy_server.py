from __future__ import annotations

import threading
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.serving import make_server

from web.scripts.dev_server import create_app


def _start_test_server(app: Flask, host: str = "127.0.0.1"):
    server = make_server(host, 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port, thread


def test_proxy_forwards_api_requests_to_backend(tmp_path: Path):
    backend_app = Flask(__name__)

    @backend_app.post("/api/test")
    def backend_handler():
        return jsonify({"ok": True, "payload": request.get_json()})

    server, port, _ = _start_test_server(backend_app)
    try:
        proxy_app = create_app(web_root=tmp_path, backend_url=f"http://127.0.0.1:{port}")
        client = proxy_app.test_client()

        response = client.post(
            "/api/test",
            json={"message": "hello"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.get_json() == {"ok": True, "payload": {"message": "hello"}}
    finally:
        server.shutdown()


def test_serves_index_html_for_spa_routes(tmp_path: Path):
    index_html = tmp_path / "index.html"
    index_html.write_text("<h1>ok</h1>", encoding="utf-8")

    proxy_app = create_app(web_root=tmp_path, backend_url="http://127.0.0.1:1")
    client = proxy_app.test_client()

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.data.decode("utf-8") == "<h1>ok</h1>"
