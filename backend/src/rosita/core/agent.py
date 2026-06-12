"""Agente conversacional ROSITA integrado a Ollama ou Open Router."""

from __future__ import annotations

import dataclasses
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

        # Inicializar todos os clientes disponíveis conforme as credenciais.
        self.ollama_client: AIClient | None = None
        self.openrouter_client: AIClient | None = None
        self.gateway_client: AIClient | None = None
        self._reinit_clients()

        # Se nenhum foi inicializado, vamos exigir ao menos o padrão (Ollama).
        if self.ollama_client is None and self.openrouter_client is None and self.gateway_client is None:
            try:
                self.ollama_client = OllamaClient(settings)
            except Exception as exc:
                raise RuntimeError(f"Falha ao inicializar clientes de IA: {str(exc)}")

        # Determinar cliente ativo
        self.active_provider = self._get_initial_provider()

        self.current_model = self._resolver_modelo_inicial()
        self.is_busy = False
        self.is_downloading = False
        self.download_model = ""
        self.download_status = "idle"
        self.download_percent = 0

    def _reinit_clients(self) -> None:
        """(Re)inicializa os clientes de IA conforme as credenciais atuais."""
        from rosita.core.ai_client import GatewayClient, OpenRouterClient

        # Ollama é sempre tentado (pode rodar local sem credencial).
        try:
            self.ollama_client = OllamaClient(self.settings)
        except Exception:
            self.ollama_client = None

        # Open Router só existe se houver API key.
        try:
            self.openrouter_client = (
                OpenRouterClient(self.settings) if self.settings.openrouter_api_key else None
            )
        except Exception:
            self.openrouter_client = None

        # Gateway custom só existe se houver URL.
        try:
            self.gateway_client = (
                GatewayClient(self.settings) if self.settings.gateway_url else None
            )
        except Exception:
            self.gateway_client = None

    def _provider_client(self, provider: str) -> AIClient | None:
        """Retorna o cliente correspondente a um provedor, se inicializado."""
        return {
            "ollama": self.ollama_client,
            "openrouter": self.openrouter_client,
            "gateway": self.gateway_client,
        }.get(provider)

    def _get_initial_provider(self) -> str:
        """Determina qual provedor usar inicialmente."""
        # Respeitar a preferência configurada, se o cliente existir.
        preferido = self.settings.ai_provider
        if preferido in ("ollama", "openrouter", "gateway") and self._provider_client(preferido):
            return preferido

        # Fallback para o primeiro disponível.
        for provedor in ("gateway", "openrouter", "ollama"):
            if self._provider_client(provedor):
                return provedor
        return "ollama"

    def _get_active_client(self) -> AIClient:
        """Retorna o cliente ativo atual."""
        cliente = self._provider_client(self.active_provider)
        if cliente:
            return cliente
        if self.ollama_client:
            return self.ollama_client
        raise RuntimeError("Nenhum cliente de IA disponível.")

    def reconfigurar(self, **mudancas: Any) -> None:
        """Aplica novas credenciais/configuração em runtime e recria os clientes.

        Campos aceitos: ai_provider, ollama_host, ollama_model,
        openrouter_api_key, openrouter_model, gateway_url, gateway_model.
        """
        if self.is_busy:
            raise RuntimeError("Não é possível alterar a configuração durante uma resposta em andamento.")
        if self.is_downloading:
            raise RuntimeError("Aguarde o fim do download atual antes de alterar a configuração.")

        campos_validos = {
            "ai_provider",
            "ollama_host",
            "ollama_model",
            "openrouter_api_key",
            "openrouter_model",
            "gateway_url",
            "gateway_model",
            "gateway_api_key",
        }
        aplicar: Dict[str, str] = {
            campo: valor
            for campo, valor in mudancas.items()
            if campo in campos_validos and valor is not None
        }

        # Normalizações.
        if "ai_provider" in aplicar:
            aplicar["ai_provider"] = str(aplicar["ai_provider"]).strip().lower()
        if "ollama_host" in aplicar:
            aplicar["ollama_host"] = str(aplicar["ollama_host"]).strip().rstrip("/")
        if "gateway_url" in aplicar:
            aplicar["gateway_url"] = str(aplicar["gateway_url"]).strip().rstrip("/")
        for campo in (
            "ollama_model",
            "openrouter_api_key",
            "openrouter_model",
            "gateway_model",
            "gateway_api_key",
        ):
            if campo in aplicar:
                aplicar[campo] = str(aplicar[campo]).strip()

        provedor_solicitado = aplicar.get("ai_provider")
        if provedor_solicitado and provedor_solicitado not in ("ollama", "openrouter", "gateway"):
            raise ValueError(f"Provedor desconhecido: {provedor_solicitado}")

        # Recriar settings (frozen dataclass) e reinstanciar os clientes.
        self.settings = dataclasses.replace(self.settings, **aplicar)
        self._reinit_clients()

        # Reavaliar o provedor ativo.
        desejado = provedor_solicitado or self.active_provider
        if not self._provider_client(desejado):
            desejado = self._get_initial_provider()

        if desejado != self.active_provider:
            self.active_provider = desejado
            self.current_model = self._resolver_modelo_inicial()
        elif not self.current_model:
            # Mesmo provedor: adota o modelo padrão se nenhum estiver ativo.
            self.current_model = self._resolver_modelo_inicial()

    def obter_config(self) -> Dict[str, Any]:
        """Retorna a configuração atual (sem expor a API key em texto puro)."""
        s = self.settings
        return {
            "ai_provider": self.active_provider,
            "ollama_host": s.ollama_host,
            "ollama_model": s.ollama_model,
            "openrouter_model": s.openrouter_model,
            "openrouter_api_key_set": bool(s.openrouter_api_key),
            "gateway_url": s.gateway_url,
            "gateway_model": s.gateway_model,
            "gateway_api_key_set": bool(s.gateway_api_key),
        }

    def _resolver_modelo_inicial(self) -> str:
        """Define modelo inicial conforme o provedor ativo."""
        if self.active_provider == "openrouter" and self.settings.openrouter_model:
            return self.settings.openrouter_model
        if self.active_provider == "gateway" and self.settings.gateway_model:
            return self.settings.gateway_model
        return ""

    def _is_ollama(self) -> bool:
        """Verifica se o provedor atual é Ollama."""
        return isinstance(self._get_active_client(), OllamaClient)

    def ativar_modelo_padrao(self) -> str:
        """Tenta ativar um modelo automaticamente no boot quando nenhum está ativo.

        Para Ollama: usa ``ROSITA_OLLAMA_MODEL`` se estiver instalado; caso
        contrário, ativa o primeiro modelo instalado. Falhas (servidor
        indisponível, nenhum modelo instalado) são silenciosas — o chat
        continua bloqueado até um modelo ficar disponível, e o frontend
        avisa o usuário. Retorna o modelo ativado (ou "" se nenhum).
        """
        if self.current_model:
            return self.current_model

        try:
            if not self._is_ollama():
                return self.current_model
        except Exception:
            return self.current_model

        try:
            instalados = self.listar_modelos_instalados()
        except Exception:
            return self.current_model

        if not instalados:
            return self.current_model

        preferido = (self.settings.ollama_model or "").strip()
        alvo = preferido if preferido in instalados else instalados[0]
        try:
            return self.trocar_modelo(alvo)
        except Exception:
            return self.current_model

    def processar_pergunta(
        self,
        pergunta: str,
        historico_previo: List[Dict[str, str]] | None = None,
    ) -> Generator[str, None, None]:
        """Faz streaming da resposta usando o histórico prévio do usuário.

        O agente não armazena mais o histórico — ele é mantido por usuário pela
        camada de rotas (``HistoryStore``) e passado em ``historico_previo``. A
        persistência da pergunta e da resposta é responsabilidade de quem chama
        (gravar apenas em caso de sucesso preserva o comportamento anterior).
        """
        if self.is_busy:
            raise RuntimeError("Agente ocupado processando outra requisição.")

        if not self.current_model:
            raise RuntimeError(
                "Nenhum modelo está ativo. Selecione um modelo instalado antes de enviar mensagens."
            )

        if not validar_pergunta(pergunta, self.settings.max_input_chars):
            raise ValueError("Mensagem inválida: texto vazio ou acima do limite permitido.")

        previo = list(historico_previo or [])
        combinado = previo + [{"role": "user", "content": pergunta.strip()}]
        mensagens = [{"role": "system", "content": self.prompt_sistema}] + combinado[
            -self.settings.max_history :
        ]

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
                    yield conteudo
        finally:
            self.is_busy = False

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

    def verificar_provedor(self) -> Dict[str, Any]:
        """Sonda a conectividade real com o provedor de IA ativo.

        Tenta listar os modelos (chamada de rede ao provedor). Serve de
        healthcheck: ``ok=True`` indica que o provedor está acessível.
        """
        info: Dict[str, Any] = {
            "provedor": self.active_provider,
            "ok": False,
            "modelos_disponiveis": 0,
            "erro": None,
        }
        try:
            modelos = self.listar_modelos_instalados()
            info["ok"] = True
            info["modelos_disponiveis"] = len(modelos)
        except Exception as exc:
            info["erro"] = str(exc)
        return info

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

