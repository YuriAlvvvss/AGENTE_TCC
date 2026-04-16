# ROSITA - Assistente Escolar

Projeto Python com backend Flask + Ollama local ou externo e frontend web.

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
- usa as portas locais configuradas no `.env`, com padrão `18500` e `18080`;
- abre o navegador automaticamente no frontend local;
- gera logs de inicializacao na pasta `logs/`.

### Inicializacao automatica (recomendado - Linux)

```bash
chmod +x start_system.sh
./start_system.sh
```

O script Linux foi reforçado para um cenário mais robusto:
- valida a estrutura do projeto antes de iniciar;
- verifica Python 3.8+ e instala dependências de sistema quando necessário;
- cria/usa `.venv` e reinstala pacotes com retry;
- garante Ollama ativo sem baixar ou ativar modelos automaticamente;
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
python -m http.server 18080
```

Abra `http://127.0.0.1:18080`.

### CLI (opcional)

```bash
python agent_cli.py
```

## Deploy com Docker / Coolify

1. copie o arquivo `.env.example` para `.env`;
2. por padrão, o projeto já sobe com um Ollama interno no próprio `docker-compose`;
3. se quiser usar um servidor de IA externo, ajuste `ROSITA_OLLAMA_HOST` no `.env`;
4. suba a stack:

```bash
docker compose up --build -d
```

Serviços padrão:
- Web: `http://SEU_SERVIDOR:18080`
- API: `http://SEU_SERVIDOR:18500`
- Ollama interno: acessível apenas dentro da stack por padrão

Na primeira abertura, se ainda não houver modelo instalado, a própria interface web permite baixar modelos recomendados e acompanhar o progresso em tempo real.
Nenhum modelo é baixado, ativado ou trocado automaticamente sem ação do usuário.
Os arquivos em backend/data também podem ser editados pela interface e salvos no ambiente em execução.

Em servidor com placa NVIDIA, o Ollama interno já está preparado para usar GPU automaticamente via suporte nativo do Docker. Para isso, deixe instalados o driver NVIDIA e o NVIDIA Container Toolkit no host.

No Coolify, basta importar o repositório e usar o arquivo `docker-compose.yml` da raiz.

## API

- `GET /`
- `GET /api/status`
- `POST /api/chat`
- `GET /api/historico`
- `POST /api/limpar`

## Documentacao adicional

- `docs/architecture.md`
- `docs/implementation_plan.md`
