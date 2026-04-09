"""Ponto de entrada Flask do ROSITA."""

import logging

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from api.routes import init_routes
from config import API_HOST, API_PORT, DEBUG

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = Flask(__name__)
CORS(app)

init_routes(app)


@app.route("/", methods=["GET"])
def raiz():
    """Retorna confirmação de que a API está em execução."""
    return jsonify({"mensagem": "API ROSITA online"})


if __name__ == "__main__":
    print("🚀 Servidor iniciando em http://localhost:5000")
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG)
