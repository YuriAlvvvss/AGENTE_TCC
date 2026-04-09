"""Agente conversacional ROSITA integrado ao Ollama (streaming)."""

import logging
from typing import Any, Dict, Generator, List

import ollama

from config import CHAT_CONFIG, MAX_HISTORY, OLLAMA_MODEL
from utils.validators import validar_pergunta

logger = logging.getLogger(__name__)


class RositaAgent:
    """
    Agente ROSITA: mantém histórico e gera respostas via Ollama com streaming.

    Compatível com o fluxo de AGENTE.py (system prompt, últimas N mensagens,
    opções de chat e streaming).
    """

    def __init__(self, regimento: str) -> None:
        """
        Inicializa o agente com o texto do regimento e histórico vazio.

        Args:
            regimento: Conteúdo do regimento ECIM (ou mensagem de fallback).
        """
        self.regimento = regimento
        self.historico: List[Dict[str, str]] = []
        self._prompt_sistema = self._construir_prompt(regimento)

    def _construir_prompt(self, regimento: str) -> str:
        """
        Monta o prompt de sistema igual ao ``construir_prompt_sistema`` do AGENTE.py.

        Args:
            regimento: Texto do regimento inserido no contexto fixo.

        Returns:
            String do prompt de sistema para a role ``system``.
        """
        return (
            f"Você é ROSITA, assistente da PEI Rosa Bonfiglioli.\n"
            f"Responda com máximo 3 linhas. Seja direto e amigável.\n\n"
            f"VALORES ECIM: Civismo, Dedicação, Excelência, Honestidade, Respeito\n\n"
            f"CONTATO: (11) 3609-6072 | Secretaria: 09h-18h (seg-sex)\n"
            f"AULAS: 7h10-14h10 (fund) | 14h20-21h30 (médio)\n\n"
            f"REGIMENTO:\n{regimento}"
        )

    def processar_pergunta(self, pergunta: str) -> Generator[str, None, None]:
        """
        Valida a pergunta, chama o modelo em streaming e atualiza o histórico.

        Em caso de sucesso, acrescenta a mensagem do usuário e, ao final, a
        resposta completa do assistente. Em erro, remove a pergunta do histórico
        e propaga a exceção.

        Args:
            pergunta: Texto enviado pelo usuário.

        Yields:
            Fragmentos de texto (tokens/chunks) da resposta do modelo.

        Raises:
            ValueError: Se a pergunta não passar em ``validar_pergunta``.
            Exception: Erros propagados pelo cliente Ollama após rollback do histórico.
        """
        if not validar_pergunta(pergunta):
            raise ValueError("Pergunta inválida: verifique se não está vazia e o tamanho máximo.")

        self.historico.append({"role": "user", "content": pergunta.strip()})

        mensagens: List[Dict[str, str]] = (
            [{"role": "system", "content": self._prompt_sistema}] + self.historico[-MAX_HISTORY:]
        )

        resposta_completa = ""

        try:
            stream: Any = ollama.chat(
                model=OLLAMA_MODEL,
                messages=mensagens,
                stream=True,
                options=dict(CHAT_CONFIG),
            )

            for chunk in stream:
                conteudo = ""
                if isinstance(chunk, dict) and "message" in chunk:
                    conteudo = chunk["message"].get("content", "") or ""
                resposta_completa += conteudo
                if conteudo:
                    yield conteudo

            self.historico.append({"role": "assistant", "content": resposta_completa})

        except Exception:
            logger.exception("Falha ao processar pergunta com Ollama; revertendo entrada do usuário.")
            if self.historico and self.historico[-1].get("role") == "user":
                self.historico.pop()
            raise

    def limpar_historico(self) -> None:
        """Remove todas as mensagens do histórico da conversa."""
        self.historico.clear()

    def obter_historico(self) -> List[Dict[str, str]]:
        """
        Retorna uma cópia superficial do histórico atual.

        Returns:
            Lista de dicionários com ``role`` e ``content``.
        """
        return list(self.historico)
