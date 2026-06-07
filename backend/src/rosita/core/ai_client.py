"""Clientes abstratos para provedores de IA (Ollama e Open Router)."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List

import ollama
import requests

from rosita.settings import Settings


def _tipos_erro_rede() -> tuple[type, ...]:
    """Reúne as classes de exceção de rede das bibliotecas HTTP em uso.

    Detectar por tipo é mais confiável do que procurar palavras na mensagem,
    que variam entre versões e idiomas. As exceções do ``ollama`` propagam via
    ``httpx``; as chamadas REST usam ``requests``.
    """
    tipos: list[type] = [
        socket.gaierror,
        socket.timeout,
        ConnectionError,
        TimeoutError,
        OSError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ]
    try:
        import httpx

        # NetworkError e TimeoutException são as bases de conexão/timeout do httpx.
        tipos.extend([httpx.NetworkError, httpx.TimeoutException])
    except Exception:
        pass
    return tuple(tipos)


_NETWORK_ERROR_TYPES = _tipos_erro_rede()


def _is_network_error(exc: Exception) -> bool:
    """Identifica se é um erro de rede (DNS, conexão, timeout, etc)."""
    if isinstance(exc, _NETWORK_ERROR_TYPES):
        return True

    # Fallback defensivo por mensagem, para casos não cobertos pelos tipos acima.
    mensagem = str(exc).lower()
    sinais_rede = (
        "getaddrinfo failed",
        "connection refused",
        "actively refused",
        "failed to connect",
        "max retries exceeded",
        "timed out",
        "timeout",
        "connection error",
        "connection aborted",
        "connection reset",
        "broken pipe",
        "offline",
        "refused",
        "dns",
        "name resolution",
    )
    return any(sinal in mensagem for sinal in sinais_rede)


def _make_request_with_retry(
    method: str,
    url: str,
    max_retries: int = 2,
    backoff: float = 1.0,
    **kwargs: Any,
) -> requests.Response:
    """Faz requisição HTTP com retry e tratamento melhorado de erros de rede."""
    last_error = None
    
    for tentativa in range(max_retries):
        try:
            if method.lower() == "get":
                return requests.get(url, **kwargs)
            elif method.lower() == "post":
                return requests.post(url, **kwargs)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
        except Exception as exc:
            last_error = exc
            if not _is_network_error(exc):
                raise
            
            if tentativa < max_retries - 1:
                tempo_espera = backoff * (2 ** tentativa)
                time.sleep(tempo_espera)
            else:
                break
    
    if last_error:
        raise last_error
    raise RuntimeError("Falha ao fazer requisição após múltiplas tentativas")


class AIClient(ABC):
    """Interface abstrata para clientes de IA."""

    @abstractmethod
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True,
        options: dict | None = None,
    ) -> Generator[Dict[str, Any], None, None] | Dict[str, Any]:
        """Envia mensagens e retorna resposta com ou sem streaming."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Lista modelos disponíveis."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Valida se a conexão com o provedor está funcionando."""
        pass


class OllamaClient(AIClient):
    """Cliente para Ollama local ou remoto."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Suppress stderr durante inicialização do cliente para evitar
        # mensagens de erro de conexão que já são tratadas adequadamente
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            try:
                self.client = ollama.Client(host=self.settings.ollama_host)
            except TypeError:
                # Versões antigas do ollama podem não ter o parâmetro 'host'
                self.client = ollama.Client(self.settings.ollama_host)
        finally:
            sys.stderr = old_stderr

    def _usa_cli_local(self) -> bool:
        """Indica se faz sentido tentar usar a CLI local do Ollama."""
        host = (self.settings.ollama_host or "").lower()
        return any(token in host for token in ("127.0.0.1", "localhost")) and bool(
            shutil.which("ollama")
        )

    def _is_connection_error(self, exc: Exception) -> bool:
        """Identifica falhas transitórias de conexão com o servidor Ollama."""
        # Reutiliza a detecção tipada (com fallback defensivo) compartilhada.
        return _is_network_error(exc)

    def _formatar_erro_ollama(self, exc: Exception) -> str:
        """Converte erros de conexão do Ollama em mensagens mais claras."""
        detalhe = str(exc).strip()
        if self._usa_cli_local():
            base = (
                f"O Ollama local não está respondendo em {self.settings.ollama_host}. "
                "Abra o aplicativo Ollama ou execute 'ollama serve'."
            )
            return f"{base} Detalhes: {detalhe}" if detalhe else base
        return detalhe or f"Não foi possível conectar ao Ollama em {self.settings.ollama_host}."

    def _start_local_ollama(self) -> None:
        """Tenta iniciar o Ollama local em background."""
        kwargs: dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }

        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            if creationflags:
                kwargs["creationflags"] = creationflags
        else:
            kwargs["start_new_session"] = True

        subprocess.Popen(["ollama", "serve"], **kwargs)

    def _ensure_running(self) -> Any:
        """Garante que o servidor Ollama esteja acessível."""
        try:
            return self.client.list()
        except Exception as exc:
            if not self._usa_cli_local() or not self._is_connection_error(exc):
                raise RuntimeError(self._formatar_erro_ollama(exc)) from exc

        try:
            self._start_local_ollama()
        except Exception as exc:
            raise RuntimeError(self._formatar_erro_ollama(exc)) from exc

        ultimo_erro: Exception | None = None
        for _ in range(10):
            try:
                return self.client.list()
            except Exception as exc:
                ultimo_erro = exc
                time.sleep(1)

        raise RuntimeError(
            self._formatar_erro_ollama(ultimo_erro or RuntimeError("Ollama indisponível."))
        )

    def validate_connection(self) -> bool:
        """Valida conexão com Ollama."""
        try:
            self._ensure_running()
            return True
        except Exception:
            return False

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True,
        options: dict | None = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Envia mensagens para Ollama com streaming."""
        self._ensure_running()
        chat_options = dict(options or {})

        stream_result = self.client.chat(
            model=model,
            messages=messages,
            stream=stream,
            options=chat_options,
        )

        for chunk in stream_result:
            yield chunk

    def list_models(self) -> List[str]:
        """Lista modelos disponíveis no Ollama."""
        data = self._ensure_running()
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

    def delete_model(self, model: str) -> None:
        """Remove um modelo do Ollama."""
        self._ensure_running()
        self.client.delete(model)

    def generate_keep_alive_zero(self, model: str) -> None:
        """Descarrega um modelo do Ollama."""
        try:
            self.client.generate(
                model=model,
                prompt="",
                stream=False,
                keep_alive=0,
            )
        except Exception:
            if self._usa_cli_local():
                try:
                    subprocess.run(
                        ["ollama", "stop", model],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                except Exception:
                    pass


class OpenRouterClient(AIClient):
    """Cliente para Open Router API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_key = settings.openrouter_api_key
        if not self.api_key:
            raise ValueError("ROSITA_OPENROUTER_API_KEY não configurada")

    def validate_connection(self) -> bool:
        """Valida conexão com Open Router."""
        try:
            response = _make_request_with_retry(
                "get",
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
                max_retries=1,
            )
            return response.status_code == 200
        except Exception as exc:
            if isinstance(exc, (socket.gaierror, TimeoutError)) or _is_network_error(exc):
                return False
            return False

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True,
        options: dict | None = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Envia mensagens para Open Router com streaming."""
        chat_options = dict(options or {})

        # Mapear opções do ROSITA para OpenRouter
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": chat_options.get("temperature", 0.7),
            "top_p": chat_options.get("top_p", 0.9),
        }

        # Open Router não suporta num_predict e repeat_penalty, então ignoramos

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://rosita.local",
        }

        try:
            response = _make_request_with_retry(
                "post",
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                stream=stream,
                timeout=60,
                max_retries=2,
            )
            response.raise_for_status()

            if stream:
                for line in response.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            import json

                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    yield {
                                        "message": {
                                            "content": choice["delta"]["content"]
                                        }
                                    }
                        except Exception:
                            pass
            else:
                import json

                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    yield {
                        "message": {
                            "content": data["choices"][0].get("message", {}).get("content", "")
                        }
                    }

        except socket.gaierror as exc:
            raise RuntimeError(
                f"Erro de DNS ao conectar com Open Router (openrouter.ai): {str(exc)}. "
                "Verifique sua conexão de internet e configuração de DNS."
            ) from exc
        except (socket.timeout, TimeoutError) as exc:
            raise RuntimeError(
                f"Timeout ao conectar com Open Router: {str(exc)}. "
                "O servidor está respondendo lentamente. Tente novamente."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Erro ao conectar com Open Router: {str(exc)}"
            ) from exc

    def list_models(self) -> List[str]:
        """Lista modelos disponíveis no Open Router."""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = _make_request_with_retry(
                "get",
                f"{self.BASE_URL}/models",
                headers=headers,
                timeout=10,
                max_retries=2,
            )
            response.raise_for_status()

            data = response.json()
            modelos = []
            for item in data.get("data", []):
                if "id" in item:
                    modelos.append(item["id"])
            return sorted(modelos)

        except socket.gaierror as exc:
            raise RuntimeError(
                f"Erro de DNS ao listar modelos (openrouter.ai): {str(exc)}. "
                "Verifique sua conexão de internet e configuração de DNS."
            ) from exc
        except (socket.timeout, TimeoutError) as exc:
            raise RuntimeError(
                f"Timeout ao listar modelos do Open Router: {str(exc)}. "
                "O servidor está respondendo lentamente."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Erro ao listar modelos do Open Router: {str(exc)}"
            ) from exc


class GatewayClient(AIClient):
    """Cliente genérico para gateways de IA locais compatíveis com OpenAI API.
    
    Funciona com:
    - vLLM
    - LocalAI
    - LM Studio
    - Text Generation WebUI
    - Qualquer servidor OpenAI-compatible
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.gateway_url
        if not self.base_url:
            raise ValueError("ROSITA_GATEWAY_URL não configurada")
        self.api_key = settings.gateway_api_key

    def _auth_headers(self, extra: dict | None = None) -> dict:
        """Monta cabeçalhos, incluindo Authorization quando há API key."""
        headers = dict(extra or {})
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def validate_connection(self) -> bool:
        """Valida conexão com o gateway."""
        try:
            response = _make_request_with_retry(
                "get",
                f"{self.base_url}/v1/models",
                headers=self._auth_headers(),
                timeout=5,
                max_retries=1,
            )
            return response.status_code == 200
        except Exception:
            return False

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = True,
        options: dict | None = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Envia mensagens para o gateway (OpenAI-compatible)."""
        chat_options = dict(options or {})

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": chat_options.get("temperature", 0.7),
            "top_p": chat_options.get("top_p", 0.9),
            "max_tokens": chat_options.get("num_predict", 128),
        }

        headers = self._auth_headers({"Content-Type": "application/json"})

        try:
            response = _make_request_with_retry(
                "post",
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=stream,
                timeout=120,
                max_retries=2,
            )
            response.raise_for_status()

            if stream:
                for line in response.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            import json

                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    yield {
                                        "message": {
                                            "content": choice["delta"]["content"]
                                        }
                                    }
                        except Exception:
                            pass
            else:
                import json

                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    yield {
                        "message": {
                            "content": data["choices"][0].get("message", {}).get("content", "")
                        }
                    }

        except socket.gaierror as exc:
            raise RuntimeError(
                f"Erro de DNS ao conectar com o gateway em {self.base_url}: {str(exc)}. "
                "Verifique o hostname/IP e resolução de DNS."
            ) from exc
        except (socket.timeout, TimeoutError) as exc:
            raise RuntimeError(
                f"Timeout ao conectar com o gateway em {self.base_url}: {str(exc)}. "
                "O gateway está respondendo lentamente."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Erro ao conectar com o gateway em {self.base_url}: {str(exc)}"
            ) from exc

    def list_models(self) -> List[str]:
        """Lista modelos disponíveis no gateway."""
        try:
            response = _make_request_with_retry(
                "get",
                f"{self.base_url}/v1/models",
                headers=self._auth_headers(),
                timeout=10,
                max_retries=2,
            )
            response.raise_for_status()

            data = response.json()
            modelos = []
            for item in data.get("data", []):
                if "id" in item:
                    modelos.append(item["id"])
            return sorted(modelos)

        except socket.gaierror as exc:
            raise RuntimeError(
                f"Erro de DNS ao listar modelos do gateway: {str(exc)}. "
                "Verifique o hostname/IP e resolução de DNS."
            ) from exc
        except (socket.timeout, TimeoutError) as exc:
            raise RuntimeError(
                f"Timeout ao listar modelos do gateway: {str(exc)}. "
                "O gateway está respondendo lentamente."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Erro ao listar modelos do gateway: {str(exc)}"
            ) from exc


def create_ai_client(settings: Settings) -> AIClient:
    """Factory para criar o cliente de IA apropriado."""
    provider = (settings.ai_provider or "ollama").strip().lower()

    if provider == "openrouter":
        return OpenRouterClient(settings)
    elif provider == "gateway":
        return GatewayClient(settings)
    elif provider == "ollama":
        return OllamaClient(settings)
    else:
        raise ValueError(
            f"Provedor de IA desconhecido: {provider}. Use 'ollama', 'openrouter' ou 'gateway'."
        )
