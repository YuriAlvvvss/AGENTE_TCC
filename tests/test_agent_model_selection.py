"""Testes do núcleo do agente (RositaAgent), sem depender de um servidor Ollama.

Substitui a versão antiga, que mockava `rosita.core.agent.ollama.Client` — uma
estrutura interna que deixou de existir após a abstração de provedores em
`rosita.core.ai_client`.
"""

from pathlib import Path

import pytest

from rosita.core.agent import RositaAgent
from rosita.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def make_settings(**overrides) -> Settings:
    """Cria um Settings completo para testes, com valores neutros por padrão."""
    base_dir = ROOT / "backend"
    valores = dict(
        base_dir=base_dir,
        data_dir=base_dir / "data",
        history_db_path=base_dir / "test_history.sqlite3",
        ai_provider="ollama",
        ollama_model="",
        ollama_host="http://127.0.0.1:11434",
        openrouter_api_key="",
        openrouter_model="",
        gateway_url="",
        gateway_model="",
        gateway_api_key="",
        max_history=5,
        max_input_chars=1000,
        api_host="127.0.0.1",
        api_port=5000,
        debug=False,
        chat_options={},
    )
    valores.update(overrides)
    return Settings(**valores)


class FakeClient:
    """Cliente de IA falso que devolve chunks pré-definidos."""

    def __init__(self, chunks):
        self._chunks = chunks
        self.mensagens_recebidas = None

    def chat(self, model, messages, stream, options):
        self.mensagens_recebidas = messages
        for c in self._chunks:
            yield {"message": {"content": c}}


def test_ollama_sem_modelo_inicia_vazio():
    agent = RositaAgent(make_settings(), "prompt do sistema")
    assert agent.obter_modelo_atual() == ""


def test_processar_pergunta_sem_modelo_ativo_levanta_erro():
    agent = RositaAgent(make_settings(), "prompt do sistema")
    with pytest.raises(RuntimeError):
        list(agent.processar_pergunta("Olá"))


def test_processar_pergunta_faz_streaming_e_usa_contexto():
    agent = RositaAgent(make_settings(), "PROMPT-SISTEMA")
    agent.current_model = "fake-model"
    fake = FakeClient(["Olá", " mundo"])
    agent._get_active_client = lambda: fake

    historico_previo = [
        {"role": "user", "content": "pergunta anterior"},
        {"role": "assistant", "content": "resposta anterior"},
    ]
    chunks = list(agent.processar_pergunta("Nova pergunta", historico_previo))

    assert "".join(chunks) == "Olá mundo"
    # A primeira mensagem é o system; a última é a nova pergunta do usuário.
    msgs = fake.mensagens_recebidas
    assert msgs[0] == {"role": "system", "content": "PROMPT-SISTEMA"}
    assert msgs[-1] == {"role": "user", "content": "Nova pergunta"}
    # O histórico prévio deve estar incluído no contexto enviado.
    assert {"role": "assistant", "content": "resposta anterior"} in msgs


def test_processar_pergunta_respeita_max_history():
    agent = RositaAgent(make_settings(max_history=3), "SYS")
    agent.current_model = "fake-model"
    fake = FakeClient(["ok"])
    agent._get_active_client = lambda: fake

    previo = [{"role": "user", "content": f"m{i}"} for i in range(10)]
    list(agent.processar_pergunta("atual", previo))

    # system + 3 mensagens (limite). A nova pergunta é a última.
    msgs = fake.mensagens_recebidas
    assert msgs[0]["role"] == "system"
    assert len(msgs) == 1 + 3
    assert msgs[-1] == {"role": "user", "content": "atual"}


def test_ativar_modelo_padrao_sem_servidor_mantem_vazio():
    agent = RositaAgent(make_settings(), "SYS")
    # Sem servidor Ollama, listar modelos falha e nenhum modelo é ativado.
    agent.listar_modelos_instalados = lambda: (_ for _ in ()).throw(RuntimeError("offline"))
    assert agent.ativar_modelo_padrao() == ""
