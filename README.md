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
