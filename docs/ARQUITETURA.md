# Arquitetura e decisões — Frontend sem bundler

Por que manter `vanilla JS` sem bundler neste TCC

- Complexidade reduzida: evitar pipeline de build (Vite/Webpack) simplifica o fluxo
  de desenvolvimento e implantação em ambiente académico.
- Transparência: código-fonte entregue em arquivos legíveis facilita avaliação
  e correção manual durante a defesa do TCC.
- Consumo de recursos: bundlers adicionam dependências e etapas que nem sempre
  são necessárias para uma prova de conceito / protótipo de escopo limitado.

Riscos e trabalho futuro

- Modularização: hoje `main.js` concentra responsabilidades (auth, chat, admin,
  status). Trabalho futuro: separar em módulos `auth.js`, `chat.js`, `admin.js`,
  `status.js` e importar esses módulos por um bundler.

- Bundler e pipeline: adotar Vite (recomendado) para:
  - HMR (hot module replacement) durante desenvolvimento
  - Transpiler (se usar sintaxes futuras) e minificação em produção
  - Geração de assets versionados com hash para cache busting

- Testes automatizados: incluir testes unitários/end-to-end com Vitest/Jest + Playwright.
  - Testes unitários para funções puras do frontend.
  - Testes de integração/E2E para fluxo de login, chat e operações administrativas.

- Segurança e deploy: mover `config.js` para servir valores de runtime por ambiente
  (ex.: configurar `ROSITA_API_BASE_URL` via servidor de deploy). Em produção,
  servir `config.js` gerado pelo pipeline ou por variáveis de ambiente do servidor.

Conclusão

Manter vanilla JS é adequado para o propósito de um TCC que prioriza clareza,
rapidez de desenvolvimento e facilidade de revisão. Para produção, recomendo
modularizar e adotar Vite + testes antes de escalar a aplicação.
