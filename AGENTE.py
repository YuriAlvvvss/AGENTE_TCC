import ollama
import os
import sys

def limpar_tela():
    os.system('cls')

def carregar_regimento():
    """Carrega o conteúdo do regimento ECIM"""
    try:
        with open('regimento_ECIM.txt', 'r', encoding='utf-8') as arquivo:
            return arquivo.read()
    except FileNotFoundError:
        return "Regimento não encontrado."

print("🤖 ROSITA - Assistente Escolar")
print("=" * 40)

# Carrega o regimento uma única vez
regimento = carregar_regimento()

while True:
    pergunta = input("\n👤 Você:")
    
    if pergunta.lower() == 'sair':
        print("👋 Até logo!")
        break
    
    print(f"\n🤖 Rosita: ", end="", flush=True)
    
    resposta = ollama.chat(
        model='llama3.1:8b',
        messages=[
            {
                'role': 'system',
                'content': f'''Você é ROSITA, assistente da PEI Rosa Bonfiglioli - Escola Cívico-Militar.
Responda com máximo 3 linhas. Seja direto e amigável.

INFORMAÇÕES GERAIS:
- Horário da secretaria: 09:00h às 18:00h (seg-sex)
- Telefone: (11) 3609-6072
- Aulas: 7:10h às 14:10h (fundamental) e 14:20h às 21:30h (médio)

REGIMENTO ECIM - Valores: Civismo, Dedicação, Excelência, Honestidade, Respeito

ORIENTAÇÕES:
✓ Uniforme obrigatório (azul escuro com brasão)
✓ Cabelo limpo, preto ou cores naturais
✓ Proibido celular em sala (Lei nº 18.058)
✓ Formaturas diárias com Hino Nacional

SISTEMA DE CRÉDITOS:
- Ingressa com 5,0 créditos
- Acréscimo: +0,25 a +2,0 (atitudes positivas)
- Decréscimo: -0,25 a -2,0 (faltas comportamentais)

---REGIMENTO COMPLETO---
{regimento}
---FIM DO REGIMENTO---

INSTRUÇÕES:
- Se a pergunta é sobre regimento, cite o artigo/seção específica
- Use "De acordo com o Regimento ECIM..." quando responder
- Responda em português simples e acolhedor
- Cite valores ECIM quando relevante'''
            },
            {'role': 'user', 'content': pergunta}
        ],
        stream=True
    )
    
    for chunk in resposta:
        print(chunk['message']['content'], end="", flush=True)
    
    print("\n")