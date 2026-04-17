"""Helpers para leitura de arquivos de dados."""

from pathlib import Path

DOCUMENT_EXTENSIONS = {".txt", ".md"}


def _is_supported_doc(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in DOCUMENT_EXTENSIONS


def carregar_texto(filepath: Path, fallback: str, extra_paths: list[Path] | None = None) -> str:
    """Carrega conteúdo UTF-8 de arquivo com fallback quando não existe."""
    for path in [filepath, *(extra_paths or [])]:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
    return fallback


def garantir_documentos_padrao(
    data_dir: Path,
    fallback_dirs: list[Path | None] | tuple[Path | None, ...] = (),
) -> list[str]:
    """Garante documentos padrão quando o deploy publica a pasta de dados vazia."""
    data_dir.mkdir(parents=True, exist_ok=True)
    copiados: list[str] = []

    for fallback_dir in fallback_dirs:
        if fallback_dir is None:
            continue

        origem = Path(fallback_dir)
        if not origem.exists() or origem.resolve() == data_dir.resolve():
            continue

        for path in sorted(origem.iterdir()):
            if not _is_supported_doc(path):
                continue

            destino = data_dir / path.name
            if destino.exists():
                continue

            destino.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            copiados.append(destino.name)

        if copiados:
            break

    return copiados


def carregar_documentacao(
    data_dir: Path,
    skip_files: set[str] | None = None,
    extra_dirs: list[Path] | None = None,
) -> tuple[list[str], str]:
    """Lê todos os arquivos de documentação texto/markdown da pasta de dados."""
    skip_lookup = {item.lower() for item in (skip_files or set())}
    documentos: list[str] = []
    nomes: list[str] = []
    vistos: set[str] = set()

    for directory in [data_dir, *(extra_dirs or [])]:
        if not directory.exists():
            continue

        for path in sorted(directory.iterdir()):
            if not _is_supported_doc(path):
                continue
            if path.name.lower() in skip_lookup or path.name.lower() in vistos:
                continue

            conteudo = path.read_text(encoding="utf-8").strip()
            if not conteudo:
                continue

            vistos.add(path.name.lower())
            nomes.append(path.name)
            documentos.append(f"### {path.name}\n{conteudo}")

    return nomes, "\n\n".join(documentos)

