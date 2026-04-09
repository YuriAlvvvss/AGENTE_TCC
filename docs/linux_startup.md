# Execucao no Linux com Script Automatico

Este guia descreve como iniciar a ROSITA no Linux usando o script `start_system.sh`.

## O que o script faz

Ao executar o script, ele:

1. verifica Python no sistema e oferece instalacao automatica quando ausente;
2. verifica Ollama e oferece instalacao automatica quando ausente;
3. inicia o Ollama automaticamente quando estiver instalado, mas parado;
4. cria o ambiente virtual `.venv` (quando necessario);
5. atualiza `pip`;
6. instala dependencias de `backend/requirements.txt`;
7. inicia backend e frontend;
8. tenta abrir o navegador em `http://localhost:8080`;
9. registra o processo em `startup.log`.

## Pre-requisitos

- Linux com `bash`;
- permissao para executar `sudo` (apenas se precisar instalar Python/Ollama);
- internet (para instalar pacotes e dependencias na primeira execucao).

## Como usar

No diretorio raiz do projeto:

```bash
chmod +x start_system.sh
./start_system.sh
```

## Enderecos apos inicializacao

- Backend: `http://localhost:5000`
- Web: `http://localhost:8080`
- Ollama: `http://localhost:11434`

## Logs

- Log principal de inicializacao: `startup.log`
- Quando o terminal grafico nao estiver disponivel, os servicos podem iniciar em background:
  - backend: `/tmp/rosita_backend.log`
  - web: `/tmp/rosita_web.log`
  - ollama: `/tmp/rosita_ollama.log`

## Parar os servicos

Se iniciado em terminais separados, feche os terminais.

Se iniciado em background:

```bash
pkill -f "app.py"
pkill -f "http.server 8080"
pkill -f "ollama serve"
```

## Variaveis opcionais

Voce pode alterar portas sem editar codigo:

```bash
ROSITA_API_PORT=5001 ROSITA_WEB_PORT=8081 ./start_system.sh
```

O script mostra as portas efetivas no final da execucao.
