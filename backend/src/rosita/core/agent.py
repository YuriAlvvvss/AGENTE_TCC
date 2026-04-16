"""Agente conversacional ROSITA integrado ao Ollama local ou externo."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, Generator, List

import ollama

from rosita.settings import Settings
from rosita.utils.validators import validar_pergunta


RECOMMENDED_MODELS: list[dict[str, str]] = [
    {
        "name": "llama3.2:3b",
        "label": "Llama 3.2 3B",
        "size": "~2 GB",
        "description": "Boa opção padrão para respostas rápidas.",
    },
    {
        "name": "qwen2.5:3b",
        "label": "Qwen 2.5 3B",
        "size": "~2 GB",
        "description": "Leve e eficiente para servidores modestos.",
    },
    {
        "name": "mistral:7b",
        "label": "Mistral 7B",
        "size": "~4 GB",
        "description": "Mais capacidade de raciocínio, exige mais memória.",
    },
]


class RositaAgent:
    """Mantém histórico e gera respostas com streaming via Ollama."""

    def __init__(self, settings: Settings, prompt_sistema: str) -> None:
        self.settings = settings
        self.prompt_sistema = prompt_sistema
        self.client = ollama.Client(host=self.settings.ollama_host)
        self.historico: List[Dict[str, str]] = []
        self.current_model = self._resolver_modelo_inicial()
        self.is_busy = False
        self.is_downloading = False
        self.download_model = ""
        self.download_status = "idle"
        self.download_percent = 0

    def _usa_cli_local(self) -> bool:
        """Indica se faz sentido tentar usar a CLI local do Ollama."""
        host = (self.settings.ollama_host or "").lower()
        return any(token in host for token in ("127.0.0.1", "localhost")) and bool(
            shutil.which("ollama")
        )

    def _resolver_modelo_inicial(self) -> str:
        """Seleciona um modelo realmente disponível ao iniciar o agente."""
        configurado = (self.settings.ollama_model or "").strip()

        try:
            instalados = self.listar_modelos_instalados()
        except Exception:
            return configurado

        if configurado and configurado in instalados:
            return configurado

        if instalados:
            return instalados[0]

        return ""

    def processar_pergunta(self, pergunta: str) -> Generator[str, None, None]:
        """Valida a pergunta, faz streaming da resposta e persiste histórico."""
        if self.is_busy:
            raise RuntimeError("Agente ocupado processando outra requisição.")

        if not self.current_model:
            raise RuntimeError(
                "Nenhum modelo Ollama está ativo. Selecione um modelo instalado antes de enviar mensagens."
            )

        if not validar_pergunta(pergunta, self.settings.max_input_chars):
            raise ValueError("Mensagem inválida: texto vazio ou acima do limite permitido.")

        self.historico.append({"role": "user", "content": pergunta.strip()})
        mensagens = [{"role": "system", "content": self.prompt_sistema}] + self.historico[
            -self.settings.max_history :
        ]

        resposta_completa = ""
        self.is_busy = True
        try:
            stream = self.client.chat(
                model=self.current_model,
                messages=mensagens,
                stream=True,
                options=dict(self.settings.chat_options),
            )

            for chunk in stream:
                conteudo = ""
                if isinstance(chunk, dict) and "message" in chunk:
                    conteudo = chunk["message"].get("content", "") or ""
                if conteudo:
                    resposta_completa += conteudo
                    yield conteudo

            self.historico.append({"role": "assistant", "content": resposta_completa})
        except Exception:
            if self.historico and self.historico[-1].get("role") == "user":
                self.historico.pop()
            raise
        finally:
            self.is_busy = False

    def limpar_historico(self) -> None:
        """Limpa o histórico atual."""
        self.historico.clear()

    def obter_historico(self) -> List[Dict[str, str]]:
        """Retorna uma cópia superficial do histórico."""
        return list(self.historico)

    def obter_modelo_atual(self) -> str:
        """Retorna o nome do modelo atual do agente."""
        return self.current_model

    def listar_modelos_instalados(self) -> List[str]:
        """Lista modelos disponíveis localmente no Ollama."""
        data = self.client.list()
        if isinstance(data, dict):
            entries = data.get("models", [])
        else:
            entries = getattr(data, "models", []) or []

        modelos = []
        for item in entries:
            if isinstance(item, dict):
                nome = item.get("model") or item.get("name")
            else:
                nome = getattr(item, "model", None) or getattr(item, "name", None)
            if nome:
                modelos.append(nome)
        return sorted(set(modelos))

    def obter_modelos_recomendados(self) -> List[Dict[str, str]]:
        """Retorna uma lista curta de modelos recomendados para instalação."""
        return list(RECOMMENDED_MODELS)

    def baixar_modelo(self, novo_modelo: str) -> Generator[Dict[str, Any], None, None]:
        """Baixa um modelo no Ollama com eventos de progresso para o frontend."""
        if self.is_busy:
            raise RuntimeError("Aguarde o fim da resposta atual antes de baixar outro modelo.")
        if self.is_downloading:
            raise RuntimeError("Já existe um download de modelo em andamento.")

        modelo = (novo_modelo or "").strip()
        if not modelo:
            raise ValueError("Modelo inválido.")

        self.is_downloading = True
        self.download_model = modelo
        self.download_status = "Preparando download"
        self.download_percent = 0

        try:
            for evento in self.client.pull(model=modelo, stream=True):
                status = "Baixando modelo"
                total = None
                completed = None

                if isinstance(evento, dict):
                    status = str(evento.get("status") or status)
                    total = evento.get("total")
                    completed = evento.get("completed")

                percentual = self.download_percent
                if isinstance(total, (int, float)) and total:
                    percentual = int((float(completed or 0) / float(total)) * 100)
                    percentual = max(0, min(100, percentual))
                elif status.lower() in {
                    "success",
                    "verifying sha256 digest",
                    "writing manifest",
                    "removing any unused layers",
                }:
                    percentual = 100

                self.download_status = status
                self.download_percent = percentual
                yield {
                    "status": status,
                    "percentual": percentual,
                    "modelo": modelo,
                }

            self.current_model = modelo
            self.download_status = "Concluído"
            self.download_percent = 100
            yield {
                "status": "Concluído",
                "percentual": 100,
                "modelo": modelo,
                "finalizado": True,
            }
        except Exception:
            self.download_status = "Falha no download"
            raise
        finally:
            self.is_downloading = False
            self.download_model = ""

    def trocar_modelo(self, novo_modelo: str) -> str:
        """
        Troca o modelo ativo.

        Para desenvolvimento: descarrega o modelo atual via `ollama stop`
        e faz um preload leve no novo modelo.
        """
        if self.is_busy:
            raise RuntimeError("Não é possível trocar modelo durante uma resposta em andamento.")

        modelo = (novo_modelo or "").strip()
        if not modelo:
            raise ValueError("Modelo inválido.")

        instalados = self.listar_modelos_instalados()
        if modelo not in instalados:
            raise ValueError("Modelo não encontrado entre os instalados.")

        if modelo == self.current_model:
            return self.current_model

        if self.current_model and self._usa_cli_local():
            try:
                subprocess.run(
                    ["ollama", "stop", self.current_model],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                # Não bloqueia a troca em dev caso o stop falhe.
                pass

        self.client.generate(model=modelo, prompt=".", stream=False, options={"num_predict": 1})
        self.current_model = modelo
        return self.current_model

