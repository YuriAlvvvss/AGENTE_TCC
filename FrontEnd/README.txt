Projeto ROSITA — convenções de pastas e arquivos
================================================

Pastas (minúsculas, sem espaços):
  assets/     Imagens, vídeos e outros arquivos estáticos
  legacy/     Versões antigas do site (referência)
  scripts/    JavaScript (entrada: main.js)
  server/     Backend Python (API local Ollama)
  styles/     CSS (entrada: main.css)

Arquivos na raiz do projeto:
  index.html  Página principal (único HTML ativo)

Nomenclatura:
  - HTML/CSS/JS: kebab-case (ex.: video-bg.mp4, main.css, main.js)
  - Python: snake_case (ex.: rosita_api.py)
  - Texto do regimento: regimento-ecim.txt (opcional; o servidor aceita também nomes antigos)

Como rodar a API:
  cd server
  python rosita_api.py

Abrir o site:
  Abra index.html no navegador (ou use um servidor HTTP simples na pasta rosita).
