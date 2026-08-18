"""Persistência de credenciais/configuração em um arquivo .env.

Usado pelo painel administrativo para salvar a configuração do provedor de IA
(Open Router ou Gateway custom) de forma que ela sobreviva a reinícios.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping

# Chaves gerenciadas pela interface administrativa.
MANAGED_KEYS = (
    "ROSITA_AI_PROVIDER",
    "ROSITA_OPENROUTER_API_KEY",
    "ROSITA_OPENROUTER_MODEL",
    "ROSITA_GATEWAY_URL",
    "ROSITA_GATEWAY_MODEL",
)


def _quote(value: str) -> str:
    """Escapa o valor para o formato .env, usando aspas quando necessário."""
    value = "" if value is None else str(value)
    # Valores com "$" (hashes scrypt, chaves de API) exigem aspas SIMPLES: o
    # Docker Compose expande "$ALGO" em valores sem aspas ou com aspas duplas,
    # inclusive nos arquivos carregados via env_file, corrompendo o valor.
    if "$" in value and "'" not in value and "\n" not in value:
        return f"'{value}'"
    if value == "" or any(ch in value for ch in ' #"\'\t\n'):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def update_env_file(path: str | Path, values: Mapping[str, str]) -> Path:
    """Atualiza (ou cria) um arquivo .env preservando linhas existentes.

    Chaves já presentes são reescritas no lugar; as demais são acrescentadas ao
    final. Comentários e linhas em branco são mantidos.
    """
    path = Path(path)
    pendentes: Dict[str, str] = {k: ("" if v is None else str(v)) for k, v in values.items()}

    linhas_originais: list[str] = []
    if path.exists():
        linhas_originais = path.read_text(encoding="utf-8").splitlines()

    novas_linhas: list[str] = []
    for linha in linhas_originais:
        stripped = linha.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            novas_linhas.append(linha)
            continue

        chave = stripped.split("=", 1)[0].strip()
        if chave in pendentes:
            valor = pendentes.pop(chave)
            novas_linhas.append(f"{chave}={_quote(valor)}")
        else:
            novas_linhas.append(linha)

    for chave, valor in pendentes.items():
        novas_linhas.append(f"{chave}={_quote(valor)}")

    conteudo = "\n".join(novas_linhas).strip("\n")
    path.write_text(conteudo + "\n", encoding="utf-8")
    return path
