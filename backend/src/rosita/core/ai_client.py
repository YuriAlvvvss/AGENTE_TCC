"""Clientes abstratos para provedores de IA (Open Router e Gateway)."""

from __future__ import annotations

import socket
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List

import requests

from rosita.settings import Settings


def _tipos_erro_rede() -> tuple[type, ...]:
    """Reúne as classes de exceção de rede das bibliotecas HTTP em uso.

    Detectar por tipo é mais confiável do que procurar palavras na mensagem,
    que variam entre versões e idiomas. As chamadas REST usam ``requests``.
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
    provider = (settings.ai_provider or "openrouter").strip().lower()

    if provider == "openrouter":
        return OpenRouterClient(settings)
    elif provider == "gateway":
        return GatewayClient(settings)
    else:
        raise ValueError(
            f"Provedor de IA desconhecido: {provider}. Use 'openrouter' ou 'gateway'."
        )
