# Arquitetura ROSITA

## Camadas

- `backend/src/rosita/core`: regras de negocio do agente (`RositaAgent` em `agent.py`).
- `backend/src/rosita/core/ai_client.py`: clientes de IA (OpenRouter, Gateway OpenAI-compatible).
- `backend/src/rosita/api`: camada HTTP (Flask + SSE).
- `backend/src/rosita/utils`: utilitarios de validacao e I/O.
- `backend/src/rosita/settings.py`: configuracao por ambiente.
- `backend/src/rosita/bootstrap.py`: montagem de contexto e instanciacao do agente.
- `web/`: interface web para usuarios finais.

## Provedores de IA

O agente abstrai dois provedores via `create_ai_client()`:

| Provedor | Classe | Configuracao (.env) |
|----------|--------|---------------------|
| OpenRouter | `OpenRouterClient` | `ROSITA_OPENROUTER_API_KEY`, `ROSITA_OPENROUTER_MODEL` |
| Gateway | `GatewayClient` | `ROSITA_GATEWAY_URL`, `ROSITA_GATEWAY_MODEL` |

Provedor inicial: `ROSITA_AI_PROVIDER` (`openrouter` por padrao ou `gateway`). O administrador pode alternar provedores em runtime quando mais de um estiver configurado.

## Fluxo de requisicao

1. Frontend envia `POST /api/chat` com `{ "mensagem": "..." }`.
2. API valida entrada.
3. `RositaAgent` monta prompt com instrucoes + regimento.
4. O cliente do provedor ativo (OpenRouter ou Gateway) responde em streaming.
5. API retorna SSE para frontend renderizar em tempo real.

## Arquivos de dados editaveis

- `backend/data/agent_instructions.txt`: comportamento do agente.
- `backend/data/regimento_ECIM.txt`: base de conhecimento institucional.
