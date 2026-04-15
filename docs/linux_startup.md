# Execução no Linux com Script Automático

Este guia descreve a inicialização da ROSITA no Linux usando o script de partida robusto do projeto.

## O que foi reforçado

O fluxo agora está mais estável para ambientes leves, inclusive MiniOS rodando no pendrive:

1. valida a estrutura mínima do projeto antes de iniciar;
2. verifica Python 3.8+ e tenta instalar os pacotes necessários pelo gerenciador do sistema;
3. cria ou reaproveita a pasta do ambiente virtual;
4. atualiza pip, setuptools e wheel com tentativas de repetição;
5. instala as dependências do backend;
6. garante que o Ollama esteja ativo;
7. verifica se o modelo configurado já existe e faz o download quando necessário;
8. inicia backend e frontend com checagem real de saúde;
9. grava logs persistentes na pasta de logs do projeto.

## Requisitos recomendados para MiniOS

- Linux com bash;
- acesso a sudo ou conta root para instalar dependências;
- internet na primeira execução;
- pelo menos 6 GB livres em disco para o modelo padrão;
- idealmente 8 GB de RAM para o modelo padrão.

> Em máquinas mais limitadas, prefira um modelo menor para maior estabilidade.

## Uso recomendado

Na raiz do projeto:

```bash
chmod +x start_system.sh
./start_system.sh
```

## Uso recomendado no MiniOS

Se o sistema for mais leve ou tiver pouca RAM, use um modelo menor:

```bash
ROSITA_OLLAMA_MODEL=llama3.2:3b ./start_system.sh --yes
```

## Modo somente validação

Para instalar e validar tudo sem iniciar os serviços ainda:

```bash
./start_system.sh --no-start --yes
```

## Opções suportadas

```bash
./start_system.sh --help
```

Opções principais:

- `--yes`: aprova automaticamente instalações necessárias;
- `--skip-browser`: não abre navegador automaticamente;
- `--no-start`: apenas valida e instala dependências.

## Endereços após a inicialização

- Backend: http://127.0.0.1:5000
- Web: http://127.0.0.1:8080
- Ollama: http://127.0.0.1:11434

## Logs

Os logs agora ficam dentro da pasta do projeto:

- `logs/startup.log`
- `logs/backend.log`
- `logs/web.log`
- `logs/ollama.log`

## Encerramento dos serviços

Se estiverem em terminais separados, basta fechar os terminais.

Se estiverem em background:

```bash
pkill -f "app.py"
pkill -f "http.server 8080"
pkill -f "ollama serve"
```

## Ajuste de portas

Você pode alterar as portas sem editar o código:

```bash
ROSITA_API_PORT=5001 ROSITA_WEB_PORT=8081 ./start_system.sh --yes
```

O script informa as portas efetivas no final da execução.
