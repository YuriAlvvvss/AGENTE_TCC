"""Testes da validação de perguntas do chat e de nomes de modelo."""

import pytest

from rosita.utils.validators import validar_nome_modelo, validar_pergunta


@pytest.mark.parametrize(
    "texto",
    ["Olá", "Qual o horário?", "a", "  texto com espaços  "],
)
def test_perguntas_validas(texto):
    assert validar_pergunta(texto, max_chars=1000) is True


@pytest.mark.parametrize(
    "texto",
    ["", "   ", "\n\t  "],
)
def test_rejeita_vazio_ou_so_espacos(texto):
    assert validar_pergunta(texto, max_chars=1000) is False


def test_rejeita_acima_do_limite():
    assert validar_pergunta("x" * 1001, max_chars=1000) is False


def test_aceita_no_limite_exato():
    assert validar_pergunta("x" * 1000, max_chars=1000) is True


@pytest.mark.parametrize("valor", [None, 123, [], {}, 3.14])
def test_rejeita_nao_string(valor):
    assert validar_pergunta(valor, max_chars=1000) is False


@pytest.mark.parametrize("texto", ["oi\x00mundo", "a\x07b", "x\x1f"])
def test_rejeita_caracteres_de_controle(texto):
    assert validar_pergunta(texto, max_chars=1000) is False


def test_aceita_quebras_de_linha_e_tab():
    assert validar_pergunta("linha1\nlinha2\tfim", max_chars=1000) is True


@pytest.mark.parametrize(
    "modelo",
    ["llama3.2:3b", "openai/gpt-4o-mini", "Llama-3.1-8B-Instruct", "mistral", "phi3.5"],
)
def test_nomes_de_modelo_validos(modelo):
    assert validar_nome_modelo(modelo) is True


@pytest.mark.parametrize(
    "modelo",
    ["", "   ", "bad name!", "a; rm -rf /", "x" * 200, None, 123, "../etc/passwd"],
)
def test_nomes_de_modelo_invalidos(modelo):
    assert validar_nome_modelo(modelo) is False
