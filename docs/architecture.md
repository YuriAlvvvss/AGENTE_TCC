# Arquitetura ROSITA

## Camadas

- `backend/src/rosita/core`: regras de negocio do agente.
- `backend/src/rosita/api`: camada HTTP (Flask + SSE).
- `backend/src/rosita/utils`: utilitarios de validacao e I/O.
- `backend/src/rosita/settings.py`: configuracao por ambiente.
- `web/`: interface web para usuarios finais.

## Fluxo de requisicao

1. Frontend envia `POST /api/chat` com `{ "mensagem": "..." }`.
2. API valida entrada.
3. `RositaAgent` monta prompt com instrucoes + regimento.
4. Ollama responde em streaming.
5. API retorna SSE para frontend renderizar em tempo real.

## Arquivos de dados editaveis

- `backend/data/agent_instructions.txt`: comportamento do agente.
- `backend/data/regimento_ECIM.txt`: base de conhecimento institucional.
