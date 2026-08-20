# ROSITA - Assistente Escolar

Projeto Python com backend Flask e frontend web, com suporte a provedores de IA:
- OpenRouter (API, nuvem) — provedor padrão
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
│  • Tema claro/escuro         │
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
   ▼           ▼
┌──────────┐ ┌──────────┐
│OpenRouter│ │ Gateway  │
│ (nuvem)  │ │ (custom) │
└──────────┘ └──────────┘
```

## Principais recursos

- **Autenticação** com senhas em hash (`werkzeug`), `secret_key` por ambiente e
  rate limiting em login/chat.
- **Histórico por usuário** persistido em SQLite (sobrevive a reinícios).
- **Chat em streaming** com indicador de "digitando", botão de parar/copiar e
  auto-scroll inteligente.
- **Tema claro/escuro** persistido em `localStorage` (`rosita-theme`), com
  fallback para `prefers-color-scheme` e troca pelo botão na sidebar. Tokens CSS
  em `web/styles/main.css`: o escuro fica em `:root`; o claro em
  `html[data-theme="light"]` (degradê suave e glassmorphism). O layout do
  compositor (largura alinhada à área de mensagens) é o mesmo nos dois temas.
- **Múltiplos provedores de IA** alternáveis em runtime pela interface admin.
- **Healthcheck** (`/api/health`) que verifica o provedor de IA.

## Estrutura padronizada

```txt
ROSITA/
├── .env.example
├── agent_cli.py
├── pytest.ini
├── backend/
│   ├── app.py             # entrypoint Flask (usa app_factory)
│   ├── Dockerfile
│   ├── compose-entrypoint.sh
│   ├── env.admin
│   ├── env.defaults
│   ├── requirements.txt
│   ├── data/
│   │   ├── agent_instructions.txt
│   │   └── regimento_ECIM.txt
│   └── src/rosita/
│       ├── core/          # agent.py, ai_client.py (OpenRouter, Gateway), prompt_builder.py
│       ├── api/           # routes.py (REST + SSE)
│       ├── utils/         # env_manager, file_loader, history_store, system_monitor, validators
│       ├── app_factory.py
│       ├── bootstrap.py
│       └── settings.py
├── docker-compose.yml
├── docker/
│   └── minios-vfs-daemon.json
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── ARQUITETURA.md
│   ├── implementation_plan.md
│   ├── linux_startup.md
│   └── PLANO_MELHORIAS.md
├── frontend/              # anotações e guias de implantação do frontend
├── requirements-dev.txt
├── scripts/
│   ├── enable-docker-vfs-minios.sh
│   ├── set_admin_password.py
│   ├── win_run_backend.bat
│   └── win_run_web.bat
├── start_system.bat
├── start_system.sh
├── tests/                 # HistoryStore, auth/API, validadores, proxy web, deploy
├── web/
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── README.md
│   ├── scripts/           # main.js, api_client.js, config.js, dev_server.py
│   └── styles/            # main.css (temas claro/escuro)
└── README.md
```

## Convenções adotadas

- nomes de pastas em minúsculo;
- nomes Python em `snake_case`;
- separação por camadas (core, api, utils, settings);
- instruções do agente fora do código.

## Instruções do agente (editável)

Arquivo: `backend/data/agent_instructions.txt`

Placeholder suportado: `{REGIMENTO}`.

## Configuração de provedores de IA

O backend suporta dois provedores (configurados no `.env`):

| Provedor | Variável principal | Uso |
|----------|-------------------|-----|
| **OpenRouter** | `ROSITA_OPENROUTER_API_KEY`, `ROSITA_OPENROUTER_MODEL` | Modelos na nuvem (https://openrouter.ai) — padrão |
| **Gateway** | `ROSITA_GATEWAY_URL`, `ROSITA_GATEWAY_MODEL`, `ROSITA_GATEWAY_API_KEY` | Servidor OpenAI-compatible no seu servidor (vLLM, LocalAI, LM Studio, etc.) |

Provedor ativo por padrão:

```env
ROSITA_AI_PROVIDER=openrouter
```

Valores aceitos: `openrouter` ou `gateway`.

Se mais de um provedor estiver configurado (ex.: OpenRouter + gateway local), o administrador pode alternar entre eles na interface ou via API (`GET /api/provedores`, `POST /api/provedores/trocar`).

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
# ROSITA_GATEWAY_API_KEY=chave-opcional-do-gateway
```

O gateway deve expor `GET /v1/models` e `POST /v1/chat/completions` (URL base **sem** `/v1` no final).

Copie `.env.example` para `.env` e preencha as variáveis do provedor desejado.

## Segurança e autenticação

As credenciais e a chave de sessão vêm do `.env` (veja `.env.example`):

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
- O **login é restrito ao perfil admin**; o perfil de usuário comum usa o chat
  sem login (visita anônima com histórico isolado por sessão).
- Se `ROSITA_SECRET_KEY` ficar vazia, uma chave aleatória é gerada a cada início
  (as sessões não persistem entre reinícios) — defina-a em produção.
- Se os `_HASH` ficarem vazios, aceita-se a senha em texto via
  `ROSITA_ADMIN_PASSWORD` / `ROSITA_USER_PASSWORD`; na ausência de ambos, um hash
  temporário é gerado e o login administrativo fica indisponível por padrão —
  **não** use isso em produção.
- Para desenvolvimento local, você também pode definir credenciais em
  `.venv/admin_password.env` (gerado por `scripts/set_admin_password.py`), que é
  carregado automaticamente ao iniciar o backend local.
- `POST /api/auth/login` (10/min) e `POST /api/chat` (20/min) têm limite de taxa.

## Histórico por usuário

O histórico de conversa é persistido em **SQLite**, isolado por usuário (ou por
visitante anônimo, via ID de sessão), e sobrevive a reinícios do servidor. O
caminho do banco é configurável:

```env
ROSITA_HISTORY_DB=backend/rosita_history.sqlite3
```

## Ajustes opcionais

Variáveis adicionais disponíveis no `.env` (veja `.env.example`):

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `ROSITA_WEB_PORT` | `18080` | Porta pública da interface web |
| `ROSITA_API_PORT` | `18500` | Porta pública da API |
| `ROSITA_BACKEND_URL` | `http://127.0.0.1:18500` | URL do backend usada pelo servidor de desenvolvimento do frontend |
| `ROSITA_SESSION_COOKIE_SECURE` | `false` | Marque `true` quando servir por HTTPS (cookies de sessão só por TLS) |
| `ROSITA_MAX_HISTORY` | `5` | Quantidade de mensagens do histórico enviadas ao provedor |
| `ROSITA_MAX_INPUT_CHARS` | `1000` | Limite de caracteres por mensagem |
| `ROSITA_NUM_PREDICT` | `256` | Tamanho máximo da resposta gerada |
| `ROSITA_TEMPERATURE` | `0.75` | Criatividade do modelo |
| `ROSITA_TOP_P` | `0.92` | Amostragem *nucleus sampling* |
| `ROSITA_REPEAT_PENALTY` | `1.08` | Penalidade de repetição |
| `ROSITA_DEBUG` | `false` | Modo de depuração do Flask |

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Cobrem o `HistoryStore`, validação de entrada, autenticação/autorização, o núcleo
do agente (sem depender de um servidor de IA), o proxy do frontend
(`web/scripts/dev_server.py`) e checagens de deploy.

## Execução

### Inicialização automática (recomendado - Windows)

```bat
start_system.bat
```

O script:
- verifica Python no computador;
- tenta instalar Python automaticamente via `winget` se não encontrar;
- valida o provedor de IA configurado (Open Router ou Gateway);
- cria `.venv`;
- instala dependências do backend;
- inicia backend e web em terminais separados;
- usa as portas locais configuradas no `.env`, com padrão `18500` e `18080`;
- abre o navegador automaticamente no frontend local;
- gera logs de inicialização na pasta `logs/`.

### Inicialização automática (recomendado - Linux)

```bash
chmod +x start_system.sh
./start_system.sh
```

O script Linux foi reforçado para um cenário mais robusto:
- valida a estrutura do projeto antes de iniciar;
- verifica Python 3.8+ e instala dependências de sistema quando necessário;
- cria/usa `.venv` e reinstala pacotes com retry;
- valida o provedor de IA configurado (Open Router ou Gateway);
- valida backend e web por checagem real de resposta;
- grava logs persistentes na pasta `logs/`.

Para ambiente leve, como MiniOS, basta configurar o provedor no `.env`:

```bash
ROSITA_OPENROUTER_API_KEY=sk-or-... ./start_system.sh --yes
```

Guia detalhado: `docs/linux_startup.md`.

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Web (frontend)

Em produção o frontend é servido pelo Nginx (`web/Dockerfile`). Em desenvolvimento
local, `start_system.bat` / `start_system.sh` sobem o proxy em `web/scripts/dev_server.py`
(encaminha `/api` para o backend). O mesmo servidor pode ser iniciado à parte:

```bash
cd web
python scripts/dev_server.py
```

Porta padrão: `18080` (`ROSITA_WEB_PORT`). Backend padrão do proxy:
`http://127.0.0.1:18500` (`ROSITA_BACKEND_URL`). Detalhes: `web/README.md`.

Alternativa sem proxy (`python -m http.server`) não encaminha `/api`; nesse caso
ajuste `window.ROSITA_API_BASE_URL` em `web/scripts/config.js` se a API não
estiver na mesma origem.

Abra `http://127.0.0.1:18080`.

### CLI (opcional)

```bash
python agent_cli.py
```

## Deploy com Docker / Coolify

1. copie o arquivo `.env.example` para `.env`;
2. por padrão, o projeto usa **Open Router** como provedor de IA (nuvem); o `docker-compose.yml` não traz servidor de IA interno;
3. para usar OpenRouter, configure `ROSITA_AI_PROVIDER=openrouter`, `ROSITA_OPENROUTER_API_KEY` e `ROSITA_OPENROUTER_MODEL`;
4. para usar um gateway local (IA rodando no seu servidor), configure `ROSITA_AI_PROVIDER=gateway` e `ROSITA_GATEWAY_URL`;
5. suba a stack com o Compose:

```bash
docker compose up -d --build
```

O `docker-compose.yml` padrão não exige GPU e deve funcionar em CPUs mais lentas; o desempenho depende do modelo.

Se você tiver **placa NVIDIA** e o **NVIDIA Container Toolkit** instalado, crie seu próprio override GPU (não há `docker-compose.gpu.yml` incluído neste repositório).

### MiniOS e erro `overlay` / `invalid argument`

Em MiniOS ou live USB, o driver **overlay** do Docker pode falhar ao **criar** contêineres. Esse problema não é resolvido no `docker-compose.yml`. Para continuar usando **`docker compose`**, habilite o driver **`vfs`** no host com `sudo ./scripts/enable-docker-vfs-minios.sh` (detalhes em **`docs/linux_startup.md`**). Alternativa sem Docker: **`./start_system.sh`**.

Serviços padrão:
- Web: `http://SEU_SERVIDOR:18080`
- API: `http://SEU_SERVIDOR:18500`

Na primeira abertura, se ainda não houver modelo ativo, a própria interface web permite selecionar um modelo disponível no provedor configurado.
Nenhum modelo é baixado, ativado ou trocado automaticamente sem ação do usuário.
Os arquivos em backend/data também podem ser editados pela interface e salvos no ambiente em execução.

O desempenho depende do modelo escolhido no provedor configurado (Open Router ou gateway).

No Coolify, basta importar o repositório e usar o arquivo `docker-compose.yml` da raiz (CPU). Para GPU no Coolify, adicione um override próprio (ex.: `docker-compose.gpu.yml`) conforme a documentação da plataforma.

No **MiniOS ou máquina sem GPU**, prefira um gateway com modelo menor (ex.: `deepseek-chat`) para resposta aceitável em CPU, ou use o Open Router com um modelo leve.

## API

- `GET /` — JSON `{ "mensagem": "API ROSITA online" }`
- `GET /api/health` — healthcheck que verifica o provedor de IA (200 ok / 503 degradado)
- `GET /api/status` (inclui `provedor_ia`, `gateway_url` quando aplicável)
- `POST /api/auth/login` (rate limit 10/min; **apenas admin**), `POST /api/auth/logout`, `GET /api/auth/session`
- `POST /api/chat` (rate limit 20/min; resposta em SSE)
- `GET /api/historico`, `POST /api/limpar` (do usuário logado ou do visitante anônimo da sessão)
- `GET /api/provedores` (admin)
- `POST /api/provedores/trocar` (admin; body: `{ "provedor": "openrouter" | "gateway" }`)
- `GET /api/models`, `POST /api/models/select` (admin)
- `GET /api/credenciais`, `PUT /api/credenciais` (admin; configuração do provedor de IA, persistida no `.env`)
- `GET /api/config/files` (admin; lista os arquivos de dados editáveis)
- `GET /api/config/files/<nome>` (admin; lê um arquivo de dados)
- `PUT /api/config/files/<nome>` (admin; salva um arquivo de dados, com backup `.bak`)

O plano de melhorias e correções do projeto está em `docs/PLANO_MELHORIAS.md`.

## Documentação adicional

- `docs/architecture.md` — arquitetura, camadas e provedores de IA
- `docs/ARQUITETURA.md` — decisões de arquitetura do frontend (vanilla JS sem bundler)
- `docs/implementation_plan.md` — plano de implementação frontend-first
- `docs/linux_startup.md` — guia de execução no Linux/MiniOS
- `docs/PLANO_MELHORIAS.md` — plano de melhorias e correções
- `web/README.md` — como servir o frontend localmente (proxy e modo estático)
