# Web Client ROSITA

Interface web oficial do projeto (HTML, CSS e JavaScript sem bundler).

## Temas

A interface tem **tema claro** e **tema escuro**, controlados pelo atributo
`data-theme` em `<html>` (`light` ou `dark`). **Cada abertura inicia no tema
escuro.** O botão na sidebar alterna os temas na sessão atual; o tema claro não
é restaurado automaticamente na próxima visita.

Estilos: `styles/main.css`. Tokens do escuro em `:root`; tokens e efeitos do
claro (degradê, vidro) só em `html[data-theme="light"]`. O layout (sidebar,
chat, compositor) é compartilhado.

## Executar localmente (proxy com o backend)

```bash
cd web
python scripts/dev_server.py
```

O servidor de desenvolvimento serve o frontend e faz proxy de `/api/*` para o
backend. Para apontar para outro backend, defina `ROSITA_BACKEND_URL`
(padrão: `http://127.0.0.1:18500`). Porta padrão: `18080` (configure com
`ROSITA_WEB_PORT`).

Este é o mesmo mecanismo usado por `start_system.bat`, `start_system.sh` e
`scripts/win_run_web.bat`.

## Alternativa simples (sem proxy)

```bash
cd web
python -m http.server 18080
```

Acesse `http://localhost:18080`. Nesse modo, o frontend chama o backend
diretamente; configure `window.ROSITA_API_BASE_URL` em `scripts/config.js`
se o backend não estiver na mesma origem.