"""Agente conversacional ROSITA integrado a Open Router ou Gateway."""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, Generator, List

from rosita.core.ai_client import AIClient
from rosita.settings import Settings
from rosita.utils.validators import validar_pergunta


class RositaAgent:
    """Mantém histórico e gera respostas com streaming via Open Router ou Gateway."""

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
        self.openrouter_client: AIClient | None = None
        self.gateway_client: AIClient | None = None
        self._reinit_clients()

        # Se nenhum foi inicializado, exigir ao menos um provedor configurado.
        if self.openrouter_client is None and self.gateway_client is None:
            raise RuntimeError(
                "Nenhum provedor de IA configurado. Defina ROSITA_OPENROUTER_API_KEY "
                "ou ROSITA_GATEWAY_URL no .env."
            )

        # Determinar cliente ativo
        self.active_provider = self._get_initial_provider()

        self.current_model = self._resolver_modelo_inicial()
        self.is_busy = False

    def _reinit_clients(self) -> None:
        """(Re)inicializa os clientes de IA conforme as credenciais atuais."""
        from rosita.core.ai_client import GatewayClient, OpenRouterClient

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
            "openrouter": self.openrouter_client,
            "gateway": self.gateway_client,
        }.get(provider)

    def _get_initial_provider(self) -> str:
        """Determina qual provedor usar inicialmente."""
        # Respeitar a preferência configurada, se o cliente existir.
        preferido = self.settings.ai_provider
        if preferido in ("openrouter", "gateway") and self._provider_client(preferido):
            return preferido

        # Fallback para o primeiro disponível.
        for provedor in ("openrouter", "gateway"):
            if self._provider_client(provedor):
                return provedor
        return ""

    def _get_active_client(self) -> AIClient:
        """Retorna o cliente ativo atual."""
        cliente = self._provider_client(self.active_provider)
        if cliente:
            return cliente
        raise RuntimeError("Nenhum cliente de IA disponível.")

    def reconfigurar(self, **mudancas: Any) -> None:
        """Aplica novas credenciais/configuração em runtime e recria os clientes.

        Campos aceitos: ai_provider, openrouter_api_key, openrouter_model,
        gateway_url, gateway_model.
        """
        if self.is_busy:
            raise RuntimeError("Não é possível alterar a configuração durante uma resposta em andamento.")

        campos_validos = {
            "ai_provider",
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
        if "gateway_url" in aplicar:
            aplicar["gateway_url"] = str(aplicar["gateway_url"]).strip().rstrip("/")
        for campo in (
            "openrouter_api_key",
            "openrouter_model",
            "gateway_model",
            "gateway_api_key",
        ):
            if campo in aplicar:
                aplicar[campo] = str(aplicar[campo]).strip()

        provedor_solicitado = aplicar.get("ai_provider")
        if provedor_solicitado and provedor_solicitado not in ("openrouter", "gateway"):
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

        provedor = (novo_provedor or "").strip().lower()
        
        # Validar provedor
        if provedor == "openrouter" and not self.openrouter_client:
            raise ValueError("Open Router não está configurado ou disponível.")
        elif provedor == "gateway" and not self.gateway_client:
            raise ValueError("Gateway não está configurado ou disponível.")
        elif provedor not in ("openrouter", "gateway"):
            raise ValueError(f"Provedor desconhecido: {provedor}")
        
        # Limpar modelo ativo ao trocar provedor
        self.current_model = ""
        self.active_provider = provedor
        
        label_map = {
            "openrouter": "Open Router",
            "gateway": "Gateway Local",
        }
        
        return {
            "provedor": provedor,
            "label": label_map.get(provedor, provedor),
            "modelos": self.listar_modelos_instalados(),
        }

    def trocar_modelo(self, novo_modelo: str) -> str:
        """
        Troca o modelo ativo.

        Para Open Router e Gateway: apenas atualiza a seleção.
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

        self.current_model = modelo
        return self.current_model

