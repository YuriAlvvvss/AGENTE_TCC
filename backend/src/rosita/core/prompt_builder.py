"""Construção de prompt do sistema com template externo."""


def construir_prompt_sistema(template: str, regimento: str, documentacao: str) -> str:
    """Substitui placeholders do template por documentação oficial carregada na memória."""
    prompt = template.replace("{REGIMENTO}", regimento)
    prompt = prompt.replace("{DOCUMENTACAO}", documentacao)

    if "{DOCUMENTACAO}" in template or documentacao in prompt:
        return prompt

    return f"{prompt}\n\nDOCUMENTAÇÃO OFICIAL EM MEMÓRIA:\n{documentacao}"

