from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(web_root: Optional[Path] = None, backend_url: Optional[str] = None) -> Flask:
    root = Path(web_root or Path(__file__).resolve().parent.parent)
    backend_target = backend_url or os.getenv("ROSITA_BACKEND_URL", "http://127.0.0.1:18500")

    app = Flask(__name__, static_folder=str(root), static_url_path="")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    @app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    def proxy_api(path: str) -> Response:
        target_url = f"{backend_target.rstrip('/')}/api/{path}"
        if request.query_string:
            target_url = f"{target_url}?{request.query_string.decode('utf-8')}"

        response = requests.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            data=request.get_data(),
            cookies=request.cookies,
            timeout=120,
            stream=True,
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() != "transfer-encoding"},
            content_type=response.headers.get("content-type"),
        )

    @app.route("/", defaults={"path": "index.html"})
    @app.route("/<path:path>")
    def serve(path: str) -> Response:
        full_path = (root / path).resolve()
        if full_path.exists() and full_path.is_file():
            return send_from_directory(str(root), path)
        return send_from_directory(str(root), "index.html")

    @app.errorhandler(404)
    def not_found(_error):
        return send_from_directory(str(root), "index.html")

    return app


if __name__ == "__main__":
    host = os.getenv("ROSITA_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("ROSITA_WEB_PORT", "18080"))
    create_app().run(host=host, port=port, debug=False)
