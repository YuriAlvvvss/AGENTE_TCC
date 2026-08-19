# Web Client ROSITA

Interface web oficial do projeto.

## Executar localmente (proxy com o backend)

```bash
cd web
python scripts/dev_server.py
```

O servidor de desenvolvimento serve o frontend e faz proxy de `/api/*` para o
backend. Para apontar para outro backend, defina `ROSITA_BACKEND_URL`
(padrão: `http://127.0.0.1:18500`). Porta padrão: `18080` (configure com
`ROSITA_WEB_PORT`).

## Alternativa simples (sem proxy)

```bash
cd web
python -m http.server 18080
```

Acesse `http://localhost:18080`. Nesse modo, o frontend chama o backend
diretamente; configure `window.ROSITA_API_BASE_URL` em `scripts/config.js`
se o backend não estiver na mesma origem.