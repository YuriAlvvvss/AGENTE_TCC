# ROSITA - Assistente Escolar

Projeto Python com backend Flask + Ollama e frontend web.

## Estrutura padronizada

```txt
AGENTE_TCC/
├── agent_cli.py
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── agent_instructions.txt
│   │   └── regimento_ECIM.txt
│   └── src/rosita/
├── web/
│   ├── index.html
│   ├── scripts/
│   └── styles/
├── docs/
│   ├── README.md
│   ├── architecture.md
│   └── implementation_plan.md
└── README.md
```

## Convencoes adotadas

- nomes de pastas em minusculo;
- nomes Python em `snake_case`;
- separacao por camadas (core, api, utils, settings);
- instrucoes do agente fora do codigo.

## Instrucoes do agente (editavel)

Arquivo: `backend/data/agent_instructions.txt`

Placeholder suportado: `{REGIMENTO}`.

## Execucao

### Inicializacao automatica (recomendado - Windows)

```bat
start_system.bat
```

O script:
- verifica Python no computador;
- tenta instalar Python automaticamente via `winget` se nao encontrar;
- verifica se o Ollama esta instalado;
- pergunta se deseja instalar o Ollama automaticamente quando ausente;
- inicia o Ollama automaticamente quando instalado e parado;
- cria `.venv`;
- instala dependencias do backend;
- inicia backend e web em terminais separados;
- abre o navegador em `http://localhost:8080`;
- gera logs de inicializacao em `startup.log`.

### Inicializacao automatica (recomendado - Linux)

```bash
chmod +x start_system.sh
./start_system.sh
```

O script Linux foi reforçado para um cenário mais robusto:
- valida a estrutura do projeto antes de iniciar;
- verifica Python 3.8+ e instala dependências de sistema quando necessário;
- cria/usa `.venv` e reinstala pacotes com retry;
- garante Ollama ativo e baixa o modelo configurado;
- valida backend e web por checagem real de resposta;
- grava logs persistentes na pasta `logs/`.

Para ambiente leve, como MiniOS, você pode usar um modelo menor:

```bash
ROSITA_OLLAMA_MODEL=llama3.2:3b ./start_system.sh --yes
```

Guia detalhado: `docs/linux_startup.md`.

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Web (frontend)

```bash
cd web
python -m http.server 8080
```

Abra `http://localhost:8080`.

### CLI (opcional)

```bash
python agent_cli.py
```

## API

- `GET /`
- `GET /api/status`
- `POST /api/chat`
- `GET /api/historico`
- `POST /api/limpar`

## Documentacao adicional

- `docs/architecture.md`
- `docs/implementation_plan.md`
