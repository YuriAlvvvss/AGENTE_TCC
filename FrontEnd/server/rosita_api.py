"""API HTTP para o agente ROSITA (Ollama).

Na pasta server:  python rosita_api.py
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import ollama

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_NAME = "llama3.1:8b"
_REGIMENTO_CANDIDATES = ("regimento-ecim.txt", "regimento_ecim.txt", "regimento_ECIM.txt")


def carregar_regimento():
    for name in _REGIMENTO_CANDIDATES:
        path = PROJECT_ROOT / name
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return "Regimento não encontrado."


def construir_prompt_sistema(regimento: str) -> str:
    return f"""Você é ROSITA, assistente da PEI Rosa Bonfiglioli.
Responda com máximo 3 linhas. Seja direto e amigável.

VALORES ECIM: Civismo, Dedicação, Excelência, Honestidade, Respeito

CONTATO: (11) 3609-6072 | Secretaria: 09h-18h (seg-sex)
AULAS: 7h10-14h10 (fund) | 14h20-21h30 (médio)

REGIMENTO:
{regimento}"""


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: dict):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_POST(self):
        if self.path != "/chat":
            self._send_json(404, {"error": "rota não encontrada"})
            return
        try:
            content_len = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_len).decode("utf-8")
            data = json.loads(body) if body else {}
            pergunta = (data.get("message") or "").strip()
            historico = data.get("history") or []

            if not pergunta:
                self._send_json(400, {"error": "mensagem vazia"})
                return

            regimento = carregar_regimento()
            messages = [{"role": "system", "content": construir_prompt_sistema(regimento)}]
            messages += historico[-5:]
            messages += [{"role": "user", "content": pergunta}]

            resposta = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                stream=False,
                options={
                    "num_predict": 128,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                },
            )
            texto = (resposta.get("message", {}).get("content") or "").strip()
            if not texto:
                raise RuntimeError("resposta vazia")

            novo_historico = (
                historico + [{"role": "user", "content": pergunta}, {"role": "assistant", "content": texto}]
            )[-12:]
            self._send_json(200, {"reply": texto, "history": novo_historico})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 5050), Handler)
    print("ROSITA API em http://127.0.0.1:5050/chat  (Ctrl+C para parar)")
    server.serve_forever()
