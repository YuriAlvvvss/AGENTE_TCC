"""Agente conversacional ROSITA integrado a Ollama ou Open Router."""

from __future__ import annotations

import shutil
from typing import Any, Dict, Generator, List

from rosita.core.ai_client import (
    AIClient,
    OllamaClient,
    create_ai_client,
)
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
    """Mantém histórico e gera respostas com streaming via Ollama ou Open Router."""

    def __init__(
        self,
        settings: Settings,
        prompt_sistema: str,
        documentos_contexto: List[str] | None = None,
    ) -> None:
        self.settings = settings
        self.prompt_sistema = prompt_sistema
        self.documentos_contexto = list(documentos_contexto or [])
        
        # Inicializar todos os clientes disponíveis
        self.ollama_client: AIClient | None = None
        self.openrouter_client: AIClient | None = None
        self.gateway_client: AIClient | None = None
        
        # Tentar inicializar Ollama
        try:
            self.ollama_client = OllamaClient(settings)
        except Exception:
            pass
        
        # Tentar inicializar Open Router
        try:
            if settings.openrouter_api_key:
                from rosita.core.ai_client import OpenRouterClient
                self.openrouter_client = OpenRouterClient(settings)
        except Exception:
            pass
        
        # Tentar inicializar Gateway
        try:
            if settings.gateway_url:
                from rosita.core.ai_client import GatewayClient
                self.gateway_client = GatewayClient(settings)
        except Exception:
            pass
        
        # Se nenhum foi inicializado, vamos criar pelo menos o padrão
        if self.ollama_client is None and self.openrouter_client is None and self.gateway_client is None:
            try:
                self.ollama_client = OllamaClient(settings)
            except Exception as exc:
                raise RuntimeError(f"Falha ao inicializar clientes de IA: {str(exc)}")
        
        # Determinar cliente ativo
        self.active_provider = self._get_initial_provider()
        
        self.historico: List[Dict[str, str]] = []
        self.current_model = self._resolver_modelo_inicial()
        self.is_busy = False
        self.is_downloading = False
        self.download_model = ""
        self.download_status = "idle"
        self.download_percent = 0

    def _get_initial_provider(self) -> str:
        """Determina qual provedor usar inicialmente."""
        # Respeitar a preferência inicial se disponível
        if self.settings.ai_provider == "gateway" and self.gateway_client:
            return "gateway"
        elif self.settings.ai_provider == "openrouter" and self.openrouter_client:
            return "openrouter"
        elif self.settings.ai_provider == "ollama" and self.ollama_client:
            return "ollama"
        
        # Fallback para o primeiro disponível
        if self.gateway_client:
            return "gateway"
        elif self.openrouter_client:
            return "openrouter"
        elif self.ollama_client:
            return "ollama"
        else:
            return "ollama"

    def _get_active_client(self) -> AIClient:
        """Retorna o cliente ativo atual."""
        if self.active_provider == "gateway" and self.gateway_client:
            return self.gateway_client
        elif self.active_provider == "openrouter" and self.openrouter_client:
            return self.openrouter_client
        elif self.ollama_client:
            return self.ollama_client
        raise RuntimeError("Nenhum cliente de IA disponível.")

    def _resolver_modelo_inicial(self) -> str:
        """Inicia sem modelo ativo para manter o controle totalmente manual pelo usuário."""
        return ""

    def _is_ollama(self) -> bool:
        """Verifica se o provedor atual é Ollama."""
        return isinstance(self._get_active_client(), OllamaClient)

    def processar_pergunta(self, pergunta: str) -> Generator[str, None, None]:
        """Valida a pergunta, faz streaming da resposta e persiste histórico."""
        if self.is_busy:
            raise RuntimeError("Agente ocupado processando outra requisição.")

        if not self.current_model:
            raise RuntimeError(
                "Nenhum modelo está ativo. Selecione um modelo instalado antes de enviar mensagens."
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
            client = self._get_active_client()
            stream = client.chat(
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

    def atualizar_contexto(self, prompt_sistema: str, documentos_contexto: List[str]) -> None:
        """Atualiza o contexto documental mantido em memória para respostas futuras."""
        self.prompt_sistema = prompt_sistema
        self.documentos_contexto = list(documentos_contexto)

    def listar_modelos_instalados(self) -> List[str]:
        """Lista modelos disponíveis."""
        try:
            client = self._get_active_client()
            return client.list_models()
        except Exception as exc:
            raise RuntimeError(f"Erro ao listar modelos: {str(exc)}") from exc

    def obter_modelos_recomendados(self) -> List[Dict[str, str]]:
        """Retorna uma lista curta de modelos recomendados para instalação."""
        return list(RECOMMENDED_MODELS)

    def obter_provedores_disponiveis(self) -> List[Dict[str, str]]:
        """Retorna lista de provedores disponíveis com status."""
        provedores = []
        
        if self.ollama_client:
            try:
                self.ollama_client.validate_connection()
                status = "disponível"
            except Exception:
                status = "indisponível"
            
            provedores.append({
                "provider": "ollama",
                "label": "Ollama",
                "status": status,
                "active": self.active_provider == "ollama",
            })
        
        if self.openrouter_client:
            try:
                self.openrouter_client.validate_connection()
                status = "disponível"
            except Exception:
                status = "indisponível"
            
            provedores.append({
                "provider": "openrouter",
                "label": "Open Router",
                "status": status,
                "active": self.active_provider == "openrouter",
            })
        
        if self.gateway_client:
            try:
                self.gateway_client.validate_connection()
                status = "disponível"
            except Exception:
                status = "indisponível"
            
            provedores.append({
                "provider": "gateway",
                "label": "Gateway Local",
                "status": status,
                "active": self.active_provider == "gateway",
            })
        
        return provedores

    def trocar_provedor(self, novo_provedor: str) -> Dict[str, str | List[str]]:
        """Troca o provedor ativo e retorna os modelos disponíveis."""
        if self.is_busy:
            raise RuntimeError("Não é possível trocar provedor durante uma resposta em andamento.")
        if self.is_downloading:
            raise RuntimeError("Aguarde o fim do download atual antes de trocar o provedor.")

        provedor = (novo_provedor or "").strip().lower()
        
        # Validar provedor
        if provedor == "ollama" and not self.ollama_client:
            raise ValueError("Ollama não está configurado ou disponível.")
        elif provedor == "openrouter" and not self.openrouter_client:
            raise ValueError("Open Router não está configurado ou disponível.")
        elif provedor == "gateway" and not self.gateway_client:
            raise ValueError("Gateway não está configurado ou disponível.")
        elif provedor not in ("ollama", "openrouter", "gateway"):
            raise ValueError(f"Provedor desconhecido: {provedor}")
        
        # Limpar modelo ativo ao trocar provedor
        self.current_model = ""
        self.active_provider = provedor
        
        label_map = {
            "ollama": "Ollama",
            "openrouter": "Open Router",
            "gateway": "Gateway Local",
        }
        
        return {
            "provedor": provedor,
            "label": label_map.get(provedor, provedor),
            "modelos": self.listar_modelos_instalados(),
        }

    def _descarregar_modelo_atual(self) -> None:
        """Libera o modelo ativo antes de carregar outro (apenas para Ollama)."""
        if not self.current_model or not self._is_ollama():
            return

        try:
            if isinstance(self.ollama_client, OllamaClient):
                self.ollama_client.generate_keep_alive_zero(self.current_model)
        except Exception:
            pass

    def descarregar_modelo_ativo(self) -> str:
        """Descarrega o modelo ativo e limpa a seleção atual."""
        if self.is_busy:
            raise RuntimeError("Não é possível descarregar o modelo durante uma resposta em andamento.")
        if self.is_downloading:
            raise RuntimeError("Aguarde o fim do download atual antes de descarregar o modelo.")

        if not self._is_ollama():
            raise RuntimeError("Descarregamento de modelo só é suportado com Ollama.")

        modelo = self.current_model
        if not modelo:
            raise ValueError("Nenhum modelo ativo para descarregar.")

        self._descarregar_modelo_atual()
        self.current_model = ""
        return modelo

    def excluir_modelo(self, modelo: str) -> str:
        """Remove um modelo instalado (apenas para Ollama)."""
        if self.is_busy:
            raise RuntimeError("Não é possível excluir modelo durante uma resposta em andamento.")
        if self.is_downloading:
            raise RuntimeError("Aguarde o fim do download atual antes de excluir o modelo.")

        if not self._is_ollama():
            raise RuntimeError("Exclusão de modelo só é suportada com Ollama.")

        nome_modelo = (modelo or "").strip()
        if not nome_modelo:
            raise ValueError("Modelo inválido.")

        instalados = self.listar_modelos_instalados()
        if nome_modelo not in instalados:
            raise ValueError("Modelo não encontrado entre os instalados.")

        if nome_modelo == self.current_model:
            self.descarregar_modelo_ativo()

        try:
            if isinstance(self.ollama_client, OllamaClient):
                self.ollama_client.delete_model(nome_modelo)
        except Exception as exc:
            raise RuntimeError(f"Erro ao excluir modelo: {str(exc)}") from exc
        return nome_modelo

    def baixar_modelo(self, novo_modelo: str) -> Generator[Dict[str, Any], None, None]:
        """Baixa um modelo no Ollama com eventos de progresso para o frontend."""
        if self.is_busy:
            raise RuntimeError("Aguarde o fim da resposta atual antes de baixar outro modelo.")
        if self.is_downloading:
            raise RuntimeError("Já existe um download de modelo em andamento.")

        if not self._is_ollama():
            raise RuntimeError("Download de modelo só é suportado com Ollama.")

        modelo = (novo_modelo or "").strip()
        if not modelo:
            raise ValueError("Modelo inválido.")

        self.is_downloading = True
        self.download_model = modelo
        self.download_status = "Preparando download"
        self.download_percent = 0

        try:
            if isinstance(self.ollama_client, OllamaClient):
                for evento in self.ollama_client.client.pull(model=modelo, stream=True):
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

                self.download_status = "Baixado. Selecione o modelo para ativar"
                self.download_percent = 100
                yield {
                    "status": "Baixado. Selecione o modelo para ativar",
                    "percentual": 100,
                    "modelo": modelo,
                    "finalizado": True,
                }
        except Exception as exc:
            self.download_status = "Falha no download"
            raise RuntimeError(f"Erro ao baixar modelo: {str(exc)}") from exc
        finally:
            self.is_downloading = False
            self.download_model = ""

    def trocar_modelo(self, novo_modelo: str) -> str:
        """
        Troca o modelo ativo.

        Para Ollama: descarrega o modelo atual e faz um preload leve no novo.
        Para Open Router: apenas atualiza a seleção.
        """
        if self.is_busy:
            raise RuntimeError("Não é possível trocar modelo durante uma resposta em andamento.")
        if self.is_downloading:
            raise RuntimeError("Aguarde o fim do download atual antes de trocar o modelo.")

        modelo = (novo_modelo or "").strip()
        if not modelo:
            raise ValueError("Modelo inválido.")

        instalados = self.listar_modelos_instalados()
        if modelo not in instalados:
            raise ValueError("Modelo não encontrado entre os instalados.")

        if modelo == self.current_model:
            return self.current_model

        if self.current_model:
            self._descarregar_modelo_atual()

        # Para Ollama, faz um preload leve
        if self._is_ollama():
            try:
                if isinstance(self.ollama_client, OllamaClient):
                    self.ollama_client.client.generate(
                        model=modelo, prompt=".", stream=False, options={"num_predict": 1}
                    )
            except Exception:
                pass

        self.current_model = modelo
        return self.current_model

