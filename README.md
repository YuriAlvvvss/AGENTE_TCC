# ROSITA - Assistente Escolar

Projeto Python com backend Flask e frontend web, com suporte a provedores de IA:
- Ollama (local ou externo)
- OpenRouter (API)
- Gateway local (servidor OpenAI-compatible na sua rede)

A ROSITA é um assistente que responde dúvidas sobre o regimento e os procedimentos
da escola, baseando-se na documentação oficial carregada em memória.

## Arquitetura

```txt
┌──────────────────────────────┐
│  Frontend (web/) — Nginx     │
│  HTML + CSS + JS (vanilla)   │
│  • Login / sessão            │
│  • Chat com streaming (SSE)  │
│  • Markdown + tema claro/escuro
│  • Painel admin / status     │
└──────────────┬───────────────┘
               │  REST + SSE  (/api/*, cookie de sessão)
┌──────────────▼───────────────┐
│  Backend (Flask + Gunicorn)  │
│  • Rotas/auth (hash + rate-limit)
│  • RositaAgent (orquestração)│
│  • HistoryStore (SQLite, por usuário)
└──────────────┬───────────────┘
               │
   ┌───────────┼───────────┐
   ▼           ▼           ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│ Ollama │ │OpenRouter│ │ Gateway  │
│ (local)│ │ (nuvem)  │ │ (custom) │
└────────┘ └──────────┘ └──────────┘
```

## Principais recursos

- **Autenticação** com senhas em hash (`werkzeug`), `secret_key` por ambiente e
  rate limiting em login/chat.
- **Histórico por usuário** persistido em SQLite (sobrevive a reinícios).
- **Chat em streaming** com renderização de Markdown, indicador de "digitando",
  botão de parar/copiar e auto-scroll inteligente.
- **Tema claro/escuro** com persistência e respeito ao `prefers-color-scheme`.
- **Múltiplos provedores de IA** alternáveis em runtime pela interface admin.
- **Healthcheck** (`/api/health`) que verifica o provedor de IA.

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
│       ├── core/          # agent.py, ai_client.py (Ollama, OpenRouter, Gateway)
│       ├── api/
│       ├── utils/
│       └── settings.py
├── docker-compose.yml
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

## Configuracao de provedores de IA

O backend suporta tres provedores (configurados no `.env`):

| Provedor | Variavel principal | Uso |
|----------|-------------------|-----|
| **Ollama** | `ROSITA_OLLAMA_HOST`, `ROSITA_OLLAMA_MODEL` | IA local ou remota via Ollama |
| **OpenRouter** | `ROSITA_OPENROUTER_API_KEY`, `ROSITA_OPENROUTER_MODEL` | Modelos na nuvem (https://openrouter.ai) |
| **Gateway** | `ROSITA_GATEWAY_URL`, `ROSITA_GATEWAY_MODEL` | Servidor OpenAI-compatible no seu servidor (vLLM, LocalAI, LM Studio, etc.) |

Provedor ativo por padrao:

```env
ROSITA_AI_PROVIDER=ollama
```

Valores aceitos: `ollama`, `openrouter` ou `gateway`.

Se mais de um provedor estiver configurado (ex.: Ollama + chave OpenRouter), o administrador pode alternar entre eles na interface ou via API (`GET /api/provedores`, `POST /api/provedores/trocar`).

Exemplo OpenRouter:

```env
ROSITA_AI_PROVIDER=openrouter
ROSITA_OPENROUTER_API_KEY=sk-or-v1-xxxxx
ROSITA_OPENROUTER_MODEL=openai/gpt-4o
```

Exemplo Gateway (IA local no servidor):

```env
ROSITA_AI_PROVIDER=gateway
ROSITA_GATEWAY_URL=http://127.0.0.1:8000
ROSITA_GATEWAY_MODEL=seu-modelo
```

O gateway deve expor `GET /v1/models` e `POST /v1/chat/completions` (URL base **sem** `/v1` no final).

Copie `.env.example` para `.env` e preencha as variaveis do provedor desejado.

## Seguranca e autenticacao

As credenciais e a chave de sessao vem do `.env` (veja `.env.example`):

```env
# Gere a chave: python -c "import secrets; print(secrets.token_hex(32))"
ROSITA_SECRET_KEY=

# Nome de usuário dos perfis de acesso.
ROSITA_ADMIN_USERNAME=ADM
ROSITA_USER_USERNAME=usuario

# Gere o hash: python -c "from werkzeug.security import generate_password_hash as g; print(g('SUA_SENHA'))"
ROSITA_ADMIN_PASSWORD_HASH=
ROSITA_USER_PASSWORD_HASH=
```

- As senhas são verificadas por **hash** (`scrypt`/`werkzeug`), com comparação de
  tempo constante (proteção contra timing attack).
- Se `ROSITA_SECRET_KEY` ficar vazia, uma chave aleatória é gerada a cada início
  (as sessões não persistem entre reinícios) — defina-a em produção.
- Se os `_HASH` ficarem vazios, aceita-se a senha em texto via
  `ROSITA_ADMIN_PASSWORD` / `ROSITA_USER_PASSWORD`; na ausência de ambos, um hash
  temporário é gerado e o login administrativo fica indisponível por padrão —
  **não** use isso em produção.
- Para desenvolvimento local, você também pode definir credenciais em
  `.venv/admin_password.env`, que será carregado automaticamente ao ativar o
  ambiente virtual local.
- `POST /api/auth/login` (10/min) e `POST /api/chat` (20/min) tem limite de taxa.

## Historico por usuario

O historico de conversa e persistido em **SQLite**, isolado por usuario, e
sobrevive a reinicios do servidor. O caminho do banco e configuravel:

```env
ROSITA_HISTORY_DB=backend/rosita_history.sqlite3
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Cobrem o `HistoryStore`, validacao de entrada, autenticacao/autorizacao e o nucleo
do agente (sem depender de um servidor de IA).

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

O frontend já é servido pelo Nginx em `web/Dockerfile` ou via `start_system.bat` /
`start_system.sh`. Para testes locais simples, você também pode usar:

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
2. por padrão, o projeto usa um provedor de IA externo ou local configurado no `.env`; o `docker-compose.yml` não traz Ollama interno;
3. se quiser usar um servidor de IA externo, ajuste `ROSITA_OLLAMA_HOST` no `.env` ou use `ROSITA_AI_PROVIDER=gateway`;
4. para usar OpenRouter, configure `ROSITA_AI_PROVIDER=openrouter`, `ROSITA_OPENROUTER_API_KEY` e `ROSITA_OPENROUTER_MODEL`;
5. para usar um gateway local (IA rodando no seu servidor), configure `ROSITA_AI_PROVIDER=gateway` e `ROSITA_GATEWAY_URL`;
6. suba a stack com o Compose:

```bash
docker compose up -d --build
```

O `docker-compose.yml` padrão não exige GPU e deve funcionar em CPUs mais lentas; o desempenho depende do modelo.

Se você tiver **placa NVIDIA** e o **NVIDIA Container Toolkit** instalado, use um arquivo de override GPU customizado de sua infraestrutura (não há `docker-compose.gpu.yml` incluído neste repositório).

### MiniOS e erro `overlay` / `invalid argument`

Em MiniOS ou live USB, o driver **overlay** do Docker pode falhar ao **criar** contêineres. Esse problema não é resolvido no `docker-compose.yml`. Para continuar usando **`docker compose`**, habilite o driver **`vfs`** no host com `sudo ./scripts/enable-docker-vfs-minios.sh` (detalhes em **`docs/linux_startup.md`**). Alternativa sem Docker: **`./start_system.sh`**.

Serviços padrão:
- Web: `http://SEU_SERVIDOR:18080`
- API: `http://SEU_SERVIDOR:18500`

Na primeira abertura, se ainda não houver modelo instalado, a própria interface web permite baixar modelos recomendados e acompanhar o progresso em tempo real.
Nenhum modelo é baixado, ativado ou trocado automaticamente sem ação do usuário.
Os arquivos em backend/data também podem ser editados pela interface e salvos no ambiente em execução.

Com GPU, o ficheiro `docker-compose.gpu.yml` acima expõe o Ollama e o backend ao driver NVIDIA (requer toolkit no host).

No Coolify, basta importar o repositório e usar o arquivo `docker-compose.yml` da raiz (CPU). Para GPU no Coolify, acrescente o override `docker-compose.gpu.yml` conforme a documentação da plataforma.

No **MiniOS ou máquina sem GPU**, ignore `docker-compose.gpu.yml` e prefira modelos Ollama **menores** (ex.: `llama3.2:3b`) para resposta aceitável em CPU.

## API

- `GET /`
- `GET /api/health` — healthcheck que verifica o provedor de IA (200 ok / 503 degradado)
- `GET /api/status` (inclui `provedor_ia`, `gateway_url` quando aplicavel)
- `POST /api/auth/login` (rate limit 10/min), `POST /api/auth/logout`, `GET /api/auth/session`
- `POST /api/chat` (rate limit 20/min; resposta em SSE)
- `GET /api/historico` (do usuario logado), `POST /api/limpar` (do usuario logado)
- `GET /api/provedores` (admin)
- `POST /api/provedores/trocar` (admin; body: `{ "provedor": "ollama" | "openrouter" | "gateway" }`)
- `GET /api/models`, `POST /api/models/select` (admin)

O plano de melhorias e correcoes do projeto esta em `docs/PLANO_MELHORIAS.md`.

## Documentacao adicional

- `docs/architecture.md`
- `docs/implementation_plan.md`
