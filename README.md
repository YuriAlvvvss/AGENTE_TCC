# ROSITA — Assistente Escolar (PEI Rosa Bonfiglioli)

Aplicação web que replica o comportamento do assistente em linha de comando (`AGENTE.py`), com backend **Flask**, modelo **Ollama** (`llama3.1:8b`) em modo streaming e frontend **HTML/CSS/JavaScript** consumindo a API REST e eventos SSE.

## Requisitos

- Python 3.10+ recomendado
- [Ollama](https://ollama.com/) instalado e em execução, com o modelo `llama3.1:8b` disponível (`ollama pull llama3.1:8b`)

## Instalação

Na raiz do projeto:

```bash
cd backend
pip install -r requirements.txt
```

Opcional: crie um ambiente virtual (`python -m venv venv`) antes do `pip install`.

## Executar o backend

```bash
cd backend
python app.py
```

O servidor sobe em **http://localhost:5000** (host `0.0.0.0`, porta `5000`, modo debug conforme `config.py`).

- Raiz: `GET /` — JSON confirmando que a API está online
- Documentação dos endpoints da API: ver seção [API](#api-rest) abaixo

## Frontend

1. Com o backend em execução, abra o arquivo `frontend/index.html` no navegador **ou**
2. Sirva a pasta `frontend` com um servidor HTTP local, por exemplo:

```bash
cd frontend
python -m http.server 8080
```

Acesse **http://localhost:8080**. O cliente JavaScript usa por padrão `http://localhost:5000` como URL da API.

**Boas práticas:** em produção, sirva o frontend e o backend sob o mesmo domínio ou configure CORS de forma restritiva; use HTTPS e variáveis de ambiente para segredos (nunca commite `.env`).

## Estrutura de pastas

```
AGENTE_TCC/
├── AGENTE.py                 # CLI original (mantido)
├── backend/
│   ├── app.py                # Flask entrypoint
│   ├── config.py             # Configurações
│   ├── requirements.txt
│   ├── data/
│   │   └── regimento_ECIM.txt
│   ├── core/
│   │   └── agent.py          # RositaAgent + Ollama streaming
│   ├── api/
│   │   └── routes.py         # Blueprint /api
│   └── utils/
│       ├── file_handler.py
│       └── validators.py
├── frontend/
│   ├── index.html
│   ├── styles/main.css
│   └── scripts/
│       ├── api_client.js
│       └── main.js
├── .gitignore
└── README.md
```

## API REST

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Mensagem JSON: API online |
| `GET` | `/api/status` | `status`, `agente` |
| `POST` | `/api/chat` | Body JSON `{"mensagem": "..."}` — resposta **SSE** (`text/event-stream`) |
| `GET` | `/api/historico` | Histórico atual (lista de mensagens) |
| `POST` | `/api/limpar` | Limpa o histórico do agente |

O streaming em `/api/chat` envia linhas `data: ...` no formato SSE; o término é sinalizado com `data: [FIM]`.

## Boas práticas adotadas

- Separação entre configuração, rotas, núcleo do agente e utilitários
- Validação de entrada no backend e no cliente
- Logging em Python (`INFO` / erros com stack)
- CORS habilitado para desenvolvimento local
- Histórico limitado às últimas 5 trocas no prompt (igual ao `AGENTE.py`)
- Opções Ollama alinhadas ao CLI: `num_predict`, `temperature`, `top_p`, `repeat_penalty`

## Licença / uso

Uso interno do projeto escolar conforme contexto da PEI Rosa Bonfiglioli.
