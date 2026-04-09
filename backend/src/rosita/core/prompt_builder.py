"""Construção de prompt do sistema com template externo."""


def construir_prompt_sistema(template: str, regimento: str) -> str:
    """
    Substitui placeholder no template de instruções.

    Use ``{REGIMENTO}`` no arquivo de instruções para inserir o texto do regimento.
    """
    return template.replace("{REGIMENTO}", regimento)

