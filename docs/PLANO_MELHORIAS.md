# 📋 Plano de Correções e Melhorias — ROSITA

> Consolidação das análises de **segurança/backend**, **design/UX visual** e **fluxo/usabilidade**.
> Cada item indica o arquivo de referência e a justificativa. Organizado por fases de prioridade.

---

## Fase 1 — 🔴 Segurança e correções críticas
*Base mínima antes de apresentar à banca ou publicar.*

| # | Item | Onde | Por quê | Status |
|---|------|------|---------|--------|
| 1.1 | Hash de senhas + comparação segura (`check_password_hash`) | `backend/src/rosita/settings.py`, `backend/src/rosita/api/routes.py` | Senhas em texto puro e vulneráveis a timing attack | ✅ |
| 1.2 | Remover senhas padrão do código; exigir via `.env` (hash) | `backend/src/rosita/settings.py`, `.env.example` | Defaults `admin123` embutidos | ✅ |
| 1.3 | `secret_key` aleatória obrigatória em produção | `backend/src/rosita/settings.py`, `.env.example` | Default `rosita-dev-secret` permite forjar sessão | ✅ |
| 1.4 | Remover credenciais de teste da tela de login | `web/index.html` | Expostas a qualquer visitante | ✅ |
| 1.5 | Rate limiting em `/api/chat` e `/api/auth/login` (`Flask-Limiter`) | `backend/src/rosita/app_factory.py`, `backend/src/rosita/api/routes.py` | Sem proteção contra abuso/DoS/força bruta | ✅ |

## Fase 2 — 🟠 Fluxo e usabilidade
*Onde o usuário realmente trava.*

| # | Item | Onde | Por quê | Status |
|---|------|------|---------|--------|
| 2.1 | Redirecionar ao login quando a sessão expira | `web/scripts/main.js` (verificarStatus) | Tela quebra silenciosamente no polling | ✅ |
| 2.2 | Botão "⏹ Parar" para abortar resposta (`AbortController`) | `web/scripts/main.js`, `web/scripts/api_client.js`, `web/styles/main.css` | Impossível cancelar streaming | ✅ |
| 2.3 | Tratar estado "sem modelo ativo": modelo padrão no boot + chat libera sozinho + aviso | `backend/.../agent.py`, `backend/.../bootstrap.py`, `web/scripts/main.js` | Usuário comum fica preso sem ação | ✅ |
| 2.4 | Confirmação + backup `.bak` ao sobrescrever o regimento | `web/scripts/main.js`, `backend/src/rosita/api/routes.py` | Ação mais destrutiva, sem rede de proteção | ✅ |
| 2.5 | Sistema de toasts (tirar erros de admin do chat) | `web/index.html`, `web/styles/main.css`, `web/scripts/main.js` | Erros poluem a conversa | ✅ |
| 2.6 | CTA de onboarding "Baixar modelo para começar" | `web/scripts/main.js`, `web/styles/main.css` | Admin novo não sabe o próximo passo | ✅ |

## Fase 3 — 🟡 Design e experiência visual
*Maior retorno de percepção de qualidade.*

| # | Item | Onde | Por quê | Status |
|---|------|------|---------|--------|
| 3.1 | Renderizar Markdown nas respostas (`marked` + `DOMPurify`, servidos local em `web/scripts/vendor/`) | `web/index.html`, `web/scripts/main.js`, `web/styles/main.css` | IA responde em Markdown que aparece cru | ✅ |
| 3.2 | Trocar `<input>` por `<textarea>` (Enter envia / Shift+Enter quebra; `keydown`; auto-resize) | `web/index.html`, `web/scripts/main.js`, `web/styles/main.css` | Sem perguntas multilinha; evento depreciado | ✅ |
| 3.3 | Indicador de "digitando" durante o streaming | `web/scripts/main.js`, `web/styles/main.css` | Sem feedback de processamento | ✅ |
| 3.4 | Auto-scroll inteligente + botão "↓ novas mensagens" | `web/index.html`, `web/scripts/main.js`, `web/styles/main.css` | Puxa o usuário para baixo ao reler | ✅ |
| 3.5 | Dark mode (toggle + prefers-color-scheme + localStorage, sem flash) | `web/index.html`, `web/scripts/main.js`, `web/styles/main.css` | Acessibilidade + impacto visual barato | ✅ |
| 3.6 | Botão "copiar" nas respostas | `web/scripts/main.js`, `web/styles/main.css` | Útil para colar respostas | ✅ |
| 3.7 | Itens de menu mortos ("Histórico"/"Regimento") removidos | `web/index.html`, `web/styles/main.css` | Botões que não fazem nada | ✅ |
| 3.8 | Acessibilidade: `:focus-visible` e contraste do `--color-text-muted` | `web/styles/main.css` | Abaixo de AA sobre branco | ✅ |

## Fase 4 — 🟢 Robustez, qualidade e TCC
*Rende boa escrita na monografia e defesa.*

| # | Item | Onde | Por quê | Status |
|---|------|------|---------|--------|
| 4.1 | Persistir histórico de chat **por usuário** (SQLite) | `backend/.../utils/history_store.py`, `agent.py`, `routes.py`, `app_factory.py`, `settings.py`, `web/scripts/*` | Reiniciar perde tudo + histórico era compartilhado entre usuários | ✅ |
| 4.2 | Testes com `pytest` (store, agente, auth, validação) — 35 testes verdes | `tests/`, `pytest.ini`, `requirements-dev.txt` | Só 2 testes triviais hoje (suíte legada quebrada) | ✅ |
| 4.3 | Detecção de erro de rede por exceção tipada (requests/httpx; string só como fallback) | `backend/src/rosita/core/ai_client.py` | Frágil e quebradiço | ✅ |
| 4.4 | Validação de entrada mais robusta (caracteres de controle + nome de modelo nas rotas) | `backend/src/rosita/utils/validators.py`, `backend/src/rosita/api/routes.py` | Hoje só checa tipo/tamanho | ✅ |
| 4.5 | Logging estruturado (`logging`) + log de erro no `/chat` | `backend/app.py`, `backend/src/rosita/main.py`, `backend/src/rosita/api/routes.py` | Hoje usa `print` | ✅ |
| 4.6 | Remover código morto do contador de tokens | `web/scripts/main.js` | Tokeniza e descarta a cada chunk | ✅ |
| 4.7 | Healthcheck `/api/health` que verifica o provedor de IA (200/503) | `backend/src/rosita/api/routes.py`, `backend/src/rosita/core/agent.py` | Só testa o Flask, não a IA | ✅ |
| 4.8 | README com diagrama de arquitetura, segurança, histórico, testes e API | `README.md` | Material para a banca | ✅ |

---

## ✅ Status final — todos os itens concluídos

| Fase | Itens | Status |
|------|-------|--------|
| Fase 1 — Segurança | 1.1–1.5 | ✅ 5/5 |
| Fase 2 — Fluxo e usabilidade | 2.1–2.6 | ✅ 6/6 |
| Fase 3 — Design e UX | 3.1–3.8 | ✅ 8/8 |
| Fase 4 — Robustez e TCC | 4.1–4.8 | ✅ 8/8 |
| **Total** | **27 itens** | **✅ 27/27** |

Validação: **53 testes pytest verdes**; sintaxe JS e boot do backend OK.

> Decisões registradas no caminho: senhas como **hash no `.env`**; estado "sem modelo"
> resolvido por **boot + aviso**; **histórico por usuário** (em vez de global); libs de
> Markdown **servidas localmente** (offline); menus mortos **removidos**.

### Melhoria futura sugerida
- Histórico por **sessão/conversa** (várias conversas por usuário) e item "Histórico" na
  sidebar reintroduzido para navegá-las.

### Legenda de status
- ⬜ pendente
- 🟦 em andamento
- ✅ concluído
