# Plano de Implementacao - Frontend direto (sem prompt/CLI)

Objetivo: operar a ROSITA exclusivamente pelo frontend, sem executar `agent_cli.py`.

## Fase 1 - Estabilizar backend para consumo web

- Definir `.env` para configuracoes (`ROSITA_API_HOST`, `ROSITA_API_PORT`, `ROSITA_OLLAMA_MODEL`).
- Garantir health checks (`/` e `/api/status`) para monitoramento.
- Fixar contrato da API (`/api/chat`, `/api/historico`, `/api/limpar`).
- Adicionar tratamento consistente de erro no formato JSON/SSE.

## Fase 2 - Web como interface principal

- Centralizar chamadas HTTP/SSE em `web/scripts/api_client.js`.
- Melhorar estados de UI: carregando, offline, timeout, retry.
- Persistir historico no frontend (session/local storage) se necessario.
- Adicionar configuracao de URL da API via variavel de ambiente/build.

## Fase 3 - Execucao unificada (sem prompt manual)

- Criar script de inicializacao unico (`start_system.bat`) para subir backend e servir web.
- Opcao recomendada: usar um servidor web (Nginx/Caddy) para servir `web/` e encaminhar `/api` ao Flask.
- Manter CORS restrito por ambiente (dev vs producao).

## Fase 4 - Producao e confiabilidade

- Rodar Flask com Gunicorn/Waitress (nao usar debug em producao).
- Colocar backend como servico (Windows Service, Docker ou PM2 equivalente).
- Monitorar logs e disponibilidade.
- Definir estrategia de backup para arquivos de dados do agente.

## Fase 5 - Qualidade e seguranca

- Testes automatizados de API (status, chat, validacoes).
- Limite de taxa (rate limit) para evitar abuso.
- Sanitizacao e limite de tamanho de payload.
- Checklist de deploy com rollback.

## Critério de sucesso

- Usuario abre apenas o frontend no navegador.
- Sistema responde sem abrir terminal de chat/CLI.
- Backend inicia como servico/processo gerenciado.
- Instrucoes do agente seguem editaveis em `backend/data/agent_instructions.txt`.
