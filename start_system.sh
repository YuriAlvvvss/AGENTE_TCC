#!/usr/bin/env bash

set -euo pipefail

# ==========================================================
# ROSITA - Startup automatico (Linux)
# 1) Detecta Python; tenta instalar via gerenciador de pacotes
# 2) Garante Ollama (instala opcional e inicia automatico)
# 3) Cria/usa .venv
# 4) Instala dependencias
# 5) Inicia backend e web em terminais separados (ou em background)
# ==========================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"
START_LOG="$ROOT_DIR/startup.log"
BACKEND_PORT="${ROSITA_API_PORT:-5000}"
WEB_PORT="${ROSITA_WEB_PORT:-8080}"

log() {
  local msg="$1"
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$START_LOG"
}

log_error() {
  local msg="$1"
  printf '\n[ERRO - %s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$START_LOG" >&2
}

fatal() {
  log_error "Processo interrompido devido a erro."
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ask_yes_no() {
  local prompt="$1"
  local response=""
  while true; do
    read -r -p "$prompt (s/n): " response
    case "${response,,}" in
      s|sim|y|yes) return 0 ;;
      n|nao|no) return 1 ;;
      *) echo "Resposta invalida. Use s ou n." ;;
    esac
  done
}

detect_pkg_manager() {
  if command_exists apt-get; then
    echo "apt"
  elif command_exists dnf; then
    echo "dnf"
  elif command_exists yum; then
    echo "yum"
  elif command_exists pacman; then
    echo "pacman"
  elif command_exists zypper; then
    echo "zypper"
  else
    echo ""
  fi
}

install_python_linux() {
  local pkg_mgr
  pkg_mgr="$(detect_pkg_manager)"
  if [[ -z "$pkg_mgr" ]]; then
    log_error "Nenhum gerenciador de pacotes suportado encontrado. Instale Python 3 manualmente."
    return 1
  fi

  log "Tentando instalar Python 3 com $pkg_mgr..."
  case "$pkg_mgr" in
    apt)
      sudo apt-get update
      sudo apt-get install -y python3 python3-venv python3-pip
      ;;
    dnf)
      sudo dnf install -y python3 python3-pip
      ;;
    yum)
      sudo yum install -y python3 python3-pip
      ;;
    pacman)
      sudo pacman -Sy --noconfirm python python-pip
      ;;
    zypper)
      sudo zypper --non-interactive install python3 python3-pip python3-virtualenv
      ;;
  esac
}

detect_python() {
  if command_exists python3; then
    PY_CMD="python3"
    log "Python encontrado via comando \"python3\"."
    return 0
  fi

  if command_exists python; then
    PY_CMD="python"
    log "Python encontrado via comando \"python\"."
    return 0
  fi

  log "Python nao encontrado no sistema."
  if ask_yes_no "Deseja instalar o Python automaticamente agora?"; then
    install_python_linux || return 1
  else
    log_error "Python e obrigatorio para o projeto. Inicializacao cancelada."
    return 1
  fi

  if command_exists python3; then
    PY_CMD="python3"
    log "Python instalado com sucesso."
    return 0
  fi

  if command_exists python; then
    PY_CMD="python"
    log "Python instalado com sucesso."
    return 0
  fi

  log_error "Python foi instalado, mas nao ficou disponivel nesta sessao."
  log_error "Abra um novo terminal e execute novamente este script."
  return 1
}

wait_ollama() {
  local retries=0
  while (( retries < 10 )); do
    if ollama list >/dev/null 2>&1; then
      return 0
    fi
    retries=$((retries + 1))
    log "Aguardando Ollama iniciar... tentativa $retries/10"
    sleep 2
  done
  return 1
}

install_ollama() {
  if ! command_exists curl; then
    log_error "curl nao encontrado. Instale curl para instalar o Ollama automaticamente."
    return 1
  fi

  log "Tentando instalar Ollama via script oficial..."
  curl -fsSL https://ollama.com/install.sh | sh
}

ensure_ollama() {
  if ! command_exists ollama; then
    log "Ollama nao encontrado no PATH."
    if ask_yes_no "Deseja instalar o Ollama automaticamente agora?"; then
      install_ollama || return 1
    else
      log_error "Ollama e obrigatorio para o projeto. Inicializacao cancelada."
      return 1
    fi
  else
    log "Ollama encontrado no sistema."
  fi

  log "Verificando se o Ollama esta em execucao..."
  if ! ollama list >/dev/null 2>&1; then
    log "Ollama instalado, mas nao esta em execucao. Iniciando automaticamente..."
    nohup ollama serve >/tmp/rosita_ollama.log 2>&1 &
    sleep 3
  else
    log "Ollama ja esta em execucao."
  fi

  wait_ollama || {
    log_error "Ollama nao respondeu apos tentativas de inicializacao."
    return 1
  }
  log "Ollama ativo e respondendo."
}

validate_structure() {
  [[ -f "$ROOT_DIR/backend/app.py" ]] || {
    log_error "Arquivo backend/app.py nao encontrado."
    return 1
  }
  [[ -f "$ROOT_DIR/backend/requirements.txt" ]] || {
    log_error "Arquivo backend/requirements.txt nao encontrado."
    return 1
  }
  [[ -f "$ROOT_DIR/web/index.html" ]] || {
    log_error "Arquivo web/index.html nao encontrado."
    return 1
  }
}

open_terminal_with_command() {
  local title="$1"
  local cmd="$2"

  if command_exists gnome-terminal; then
    gnome-terminal --title="$title" -- bash -lc "$cmd; exec bash" >/dev/null 2>&1 &
    return 0
  fi
  if command_exists x-terminal-emulator; then
    x-terminal-emulator -T "$title" -e bash -lc "$cmd; exec bash" >/dev/null 2>&1 &
    return 0
  fi
  if command_exists konsole; then
    konsole --new-tab -p tabtitle="$title" -e bash -lc "$cmd; exec bash" >/dev/null 2>&1 &
    return 0
  fi
  if command_exists xfce4-terminal; then
    xfce4-terminal --title="$title" --command "bash -lc '$cmd; exec bash'" >/dev/null 2>&1 &
    return 0
  fi
  if command_exists xterm; then
    xterm -T "$title" -e bash -lc "$cmd; exec bash" >/dev/null 2>&1 &
    return 0
  fi

  return 1
}

start_services() {
  local backend_cmd="cd \"$ROOT_DIR/backend\" && \"$VENV_PY\" app.py"
  local web_cmd="cd \"$ROOT_DIR/web\" && \"$VENV_PY\" -m http.server $WEB_PORT"

  if open_terminal_with_command "ROSITA Backend" "$backend_cmd"; then
    log "Backend iniciado em novo terminal."
  else
    nohup bash -lc "$backend_cmd" >/tmp/rosita_backend.log 2>&1 &
    log "Backend iniciado em background (log: /tmp/rosita_backend.log)."
  fi

  if open_terminal_with_command "ROSITA Web" "$web_cmd"; then
    log "Web iniciada em novo terminal."
  else
    nohup bash -lc "$web_cmd" >/tmp/rosita_web.log 2>&1 &
    log "Web iniciada em background (log: /tmp/rosita_web.log)."
  fi
}

open_browser() {
  local url="http://localhost:$WEB_PORT"
  if command_exists xdg-open; then
    xdg-open "$url" >/dev/null 2>&1 || true
    log "Navegador aberto em $url."
  else
    log "xdg-open nao encontrado. Abra manualmente: $url"
  fi
}

main() {
  : >"$START_LOG"
  log "============================================================"
  log "ROSITA startup iniciado."
  log "Raiz do projeto: $ROOT_DIR"
  log "Log em arquivo: $START_LOG"
  log "============================================================"

  log "PASSO 1/7 - Verificando Python no sistema..."
  detect_python || fatal
  log "PASSO 1/7 - OK."

  log "PASSO 2/7 - Verificando Ollama..."
  ensure_ollama || fatal
  log "PASSO 2/7 - OK."

  log "PASSO 3/7 - Criando ambiente virtual (.venv) se necessario..."
  if [[ ! -x "$VENV_PY" ]]; then
    log "Ambiente virtual nao encontrado. Criando .venv..."
    "$PY_CMD" -m venv "$ROOT_DIR/.venv" || {
      log_error "Falha ao criar o ambiente virtual."
      fatal
    }
  else
    log "Ambiente virtual ja existe."
  fi
  log "PASSO 3/7 - OK."

  log "PASSO 4/7 - Atualizando pip no .venv..."
  "$VENV_PY" -m pip install --upgrade pip || {
    log_error "Falha ao atualizar pip no ambiente virtual."
    fatal
  }
  log "PASSO 4/7 - OK."

  log "PASSO 5/7 - Instalando dependencias do backend..."
  "$VENV_PY" -m pip install -r "$ROOT_DIR/backend/requirements.txt" || {
    log_error "Falha ao instalar dependencias."
    fatal
  }
  log "PASSO 5/7 - OK."

  log "PASSO 6/7 - Validando estrutura minima do projeto..."
  validate_structure || fatal
  log "PASSO 6/7 - OK."

  log "PASSO 7/7 - Iniciando servicos (backend/web)..."
  start_services || fatal
  log "PASSO 7/7 - OK."

  sleep 2
  open_browser

  cat <<EOF

============================================
Sistema iniciado com sucesso.
Backend: http://localhost:$BACKEND_PORT
Web:     http://localhost:$WEB_PORT
Ollama:  http://localhost:11434
Log:     $START_LOG
============================================
EOF
  log "Inicializacao concluida com sucesso."
}

PY_CMD=""
main "$@"
