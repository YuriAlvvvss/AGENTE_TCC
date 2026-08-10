"""Testes de autenticação, autorização e histórico por usuário via API."""

import pytest

from rosita.app_factory import create_app
from rosita.settings import load_settings
from rosita.utils.history_store import HistoryStore
from werkzeug.security import generate_password_hash


@pytest.fixture()
def contexto(tmp_path, monkeypatch):
    """App isolado: banco de histórico temporário e credenciais conhecidas."""
    db_path = tmp_path / "hist.sqlite3"
    monkeypatch.setenv("ROSITA_HISTORY_DB", str(db_path))
    monkeypatch.setenv("ROSITA_SECRET_KEY", "chave-de-teste")
    # Set password hashes instead of plaintext passwords for tests
    monkeypatch.setenv("ROSITA_ADMIN_PASSWORD_HASH", generate_password_hash("admin123"))
    monkeypatch.setenv("ROSITA_USER_PASSWORD_HASH", generate_password_hash("usuario123"))
    app = create_app()
    app.config.update(TESTING=True)
    return app, db_path


def _login(client, username, password):
    return client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )


def test_login_sucesso(contexto):
    app, _ = contexto
    client = app.test_client()
    resp = _login(client, "admin", "admin123")
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados["authenticated"] is True
    assert dados["role"] == "admin"


def test_load_settings_preserva_hash_entre_aspas_e_dolares(monkeypatch):
    hash_com_dolares = "scrypt:32768:8:1$abc$def"
    monkeypatch.setenv("ROSITA_ADMIN_PASSWORD_HASH", f'"{hash_com_dolares}"')
    monkeypatch.delenv("ROSITA_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ROSITA_USER_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("ROSITA_USER_PASSWORD", raising=False)

    settings = load_settings()

    assert settings.admin_password_hash == hash_com_dolares


def test_login_senha_errada(contexto):
    app, _ = contexto
    resp = _login(app.test_client(), "admin", "senha-errada")
    assert resp.status_code == 401
    assert resp.get_json()["authenticated"] is False


def test_login_campos_faltando(contexto):
    app, _ = contexto
    resp = app.test_client().post("/api/auth/login", json={"username": "admin"})
    assert resp.status_code == 400


def test_chat_liberado_sem_login(contexto):
    app, _ = contexto
    resp = app.test_client().post("/api/chat", json={"mensagem": "oi"})
    assert resp.status_code == 200
    assert b"[ERRO]" in resp.data or b"[FIM]" in resp.data


def test_historico_acessivel_sem_login(contexto):
    app, _ = contexto
    resp = app.test_client().get("/api/historico")
    assert resp.status_code == 200
    assert resp.get_json()["historico"] == []


def test_historico_isolado_por_usuario(contexto):
    app, db_path = contexto
    store = HistoryStore(db_path)
    store.append("admin", "user", "ola do admin")
    store.append("admin", "assistant", "oi admin")
    store.append("guest:visitante", "user", "ola do visitante")

    ca = app.test_client()
    _login(ca, "admin", "admin123")
    cg = app.test_client()
    with cg.session_transaction() as sess:
        sess["guest_id"] = "visitante"

    hist_admin = ca.get("/api/historico").get_json()["historico"]
    hist_guest = cg.get("/api/historico").get_json()["historico"]

    assert [m["content"] for m in hist_admin] == ["ola do admin", "oi admin"]
    assert [m["content"] for m in hist_guest] == ["ola do visitante"]


def test_limpar_afeta_apenas_o_proprio_usuario(contexto):
    app, db_path = contexto
    store = HistoryStore(db_path)
    store.append("admin", "user", "a")
    store.append("guest:visitante", "user", "b")

    ca = app.test_client()
    _login(ca, "admin", "admin123")
    assert ca.post("/api/limpar").status_code == 200

    assert store.get("admin") == []
    assert len(store.get("guest:visitante")) == 1


def test_health_e_publico_e_tem_estrutura(contexto):
    app, _ = contexto
    resp = app.test_client().get("/api/health")
    # Público (sem login). 200 se o provedor responde; 503 se indisponível.
    assert resp.status_code in (200, 503)
    dados = resp.get_json()
    assert dados["status"] in ("ok", "degraded")
    assert "ia" in dados and "ok" in dados["ia"]
    assert (resp.status_code == 200) == dados["ia"]["ok"]


def test_rate_limit_no_login(contexto):
    pytest.importorskip("flask_limiter")
    app, _ = contexto
    client = app.test_client()
    codigos = [
        _login(client, "x", "y").status_code for _ in range(11)
    ]
    assert 429 in codigos
