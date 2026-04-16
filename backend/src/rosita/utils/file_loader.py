"""Helpers para leitura de arquivos de dados."""

from pathlib import Path


def carregar_texto(filepath: Path, fallback: str) -> str:
    """Carrega conteúdo UTF-8 de arquivo com fallback quando não existe."""
    try:
        return filepath.read_text(encoding="utf-8")
    except FileNotFoundError:
        return fallback


def carregar_documentacao(data_dir: Path, skip_files: set[str] | None = None) -> tuple[list[str], str]:
    """Lê todos os arquivos de documentação texto/markdown da pasta de dados."""
    skip_lookup = {item.lower() for item in (skip_files or set())}
    documentos: list[str] = []
    nomes: list[str] = []

    if not data_dir.exists():
        return nomes, ""

    for path in sorted(data_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.lower() in skip_lookup:
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue

        conteudo = path.read_text(encoding="utf-8").strip()
        if not conteudo:
            continue

        nomes.append(path.name)
        documentos.append(f"### {path.name}\n{conteudo}")

    return nomes, "\n\n".join(documentos)

