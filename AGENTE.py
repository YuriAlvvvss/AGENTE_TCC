import ollama
import os
import sys
from datetime import datetime

def limpar_tela():
    os.system('cls')

def carregar_regimento():
    """Carrega o conteúdo do regimento ECIM"""
    try:
        with open('regimento_ECIM.txt', 'r', encoding='utf-8') as arquivo:
            return arquivo.read()
    except FileNotFoundError:
        return "Regimento não encontrado."

def validar_pergunta(pergunta):
    """Valida se a pergunta não está vazia"""
    return pergunta.strip() != ''

def construir_prompt_sistema(regimento):
    """Centraliza a construção do prompt do sistema"""
    return f'''Você é ROSITA, assistente da PEI Rosa Bonfiglioli.
Responda com máximo 3 linhas. Seja direto e amigável.

VALORES ECIM: Civismo, Dedicação, Excelência, Honestidade, Respeito

CONTATO: (11) 3609-6072 | Secretaria: 09h-18h (seg-sex)
AULAS: 7h10-14h10 (fund) | 14h20-21h30 (médio)

REGIMENTO:
{regimento}'''

print("🤖 ROSITA - Assistente Escolar")
print("=" * 40)

regimento = carregar_regimento()
historico = []  # Mantém contexto da conversa

while True:
    pergunta = input("\n👤 Você:").strip()
    
    if pergunta.lower() == 'sair':
        print("👋 Até logo!")
        break
    
    if not validar_pergunta(pergunta):
        print("⚠️  Digite algo válido!")
        continue
    
    historico.append({'role': 'user', 'content': pergunta})
    
    print(f"\n🤖 Rosita: ", end="", flush=True)
    
    try:
        resposta = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {'role': 'system', 'content': construir_prompt_sistema(regimento)}
            ] + historico[-5:],  # Últimas 5 mensagens para contexto
            stream=True,
            options={
                'num_predict': 128,
                'temperature': 0.7,
                'top_p': 0.9,
                'repeat_penalty': 1.1  # Evita repetições
            }
        )
        
        resposta_completa = ""
        for chunk in resposta:
            conteudo = chunk['message']['content']
            print(conteudo, end="", flush=True)
            resposta_completa += conteudo
        
        historico.append({'role': 'assistant', 'content': resposta_completa})
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        historico.pop()  # Remove pergunta se falhar
