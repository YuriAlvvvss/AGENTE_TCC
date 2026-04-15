#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

# ==========================================================
# ROSITA - Startup automático (Linux)
# Fluxo robusto para ambientes leves, inclusive MiniOS:
# 1) valida estrutura do projeto
# 2) detecta Python 3.8+ e instala dependências de sistema
# 3) cria/atualiza .venv e instala requirements com retry
# 4) garante Ollama em execução e baixa o modelo configurado
# 5) inicia backend e frontend com checagem real de saúde
# ==========================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$LOG_DIR/pids"
VENV_DIR="$ROOT_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
START_LOG="$LOG_DIR/startup.log"
BACKEND_LOG="$LOG_DIR/backend.log"
WEB_LOG="$LOG_DIR/web.log"
OLLAMA_LOG="$LOG_DIR/ollama.log"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
WEB_PID_FILE="$PID_DIR/web.pid"
OLLAMA_PID_FILE="$PID_DIR/ollama.pid"
BACKEND_PORT="${ROSITA_API_PORT:-5000}"
WEB_PORT="${ROSITA_WEB_PORT:-8080}"
OLLAMA_MODEL="${ROSITA_OLLAMA_MODEL:-llama3.1:8b}"
AUTO_YES=0
SKIP_BROWSER=0
NO_START=0
PY_CMD=""

mkdir -p "$LOG_DIR" "$PID_DIR"
: > "$START_LOG"

log() {
  local msg="$1"
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$START_LOG"
}

log_warn() {
  local msg="$1"
  printf '\n[AVISO - %s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$START_LOG"
}

log_error() {
  local msg="$1"
  printf '\n[ERRO - %s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$msg" | tee -a "$START_LOG" >&2
}

on_error() {
  local line_no="$1"
  local cmd="$2"
  local exit_code="$3"
  log_error "Falha na linha $line_no ao executar: $cmd"
  exit "$exit_code"
}
trap 'on_error "${LINENO}" "${BASH_COMMAND}" "$?"' ERR

fatal() {
  local msg="${1:-Processo interrompido devido a erro.}"
  log_error "$msg"
  exit 1
}

show_help() {
  cat <<EOF
Uso: ./start_system.sh [opções]

Opções:
  --yes, -y         aceita automaticamente instalações necessárias
  --skip-browser    não tenta abrir o navegador ao final
  --no-start        apenas valida e instala dependências, sem iniciar serviços
  --help, -h        mostra esta ajuda

Variáveis úteis:
  ROSITA_API_PORT       porta do backend (padrão: 5000)
  ROSITA_WEB_PORT       porta do frontend (padrão: 8080)
  ROSITA_OLLAMA_MODEL   modelo Ollama usado pelo sistema (padrão: llama3.1:8b)

Exemplo leve para MiniOS:
  ROSITA_OLLAMA_MODEL=llama3.2:3b ./start_system.sh --yes
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --yes|-y)
        AUTO_YES=1
        ;;
      --skip-browser)
        SKIP_BROWSER=1
        ;;
      --no-start)
        NO_START=1
        ;;
      --help|-h)
        show_help
        exit 0
        ;;
      *)
        fatal "Opção inválida: $1"
        ;;
    esac
    shift
  done
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

run_with_privileges() {
  if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
    "$@"
  elif command_exists sudo; then
    sudo "$@"
  else
    fatal "É necessário usar root ou ter sudo disponível para instalar pacotes."
  fi
}

ask_yes_no() {
  local prompt="$1"
  local response=""

  if (( AUTO_YES == 1 )); then
    log "$prompt -> resposta automática: sim"
    return 0
  fi

  if [[ ! -t 0 ]]; then
    log_warn "Sem terminal interativo. Use --yes para aprovar instalações automáticas."
    return 1
  fi

  while true; do
    read -r -p "$prompt (s/n): " response
    case "${response,,}" in
      s|sim|y|yes) return 0 ;;
      n|nao|não|no) return 1 ;;
      *) echo "Resposta inválida. Use s ou n." ;;
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
  elif command_exists apk; then
    echo "apk"
  else
    echo ""
  fi
}

install_packages() {
  local pkg_mgr="$1"
  shift

  case "$pkg_mgr" in
    apt)
      run_with_privileges apt-get update
      run_with_privileges apt-get install -y "$@"
      ;;
    dnf)
      run_with_privileges dnf install -y "$@"
      ;;
    yum)
      run_with_privileges yum install -y "$@"
      ;;
    pacman)
      run_with_privileges pacman -Sy --noconfirm "$@"
      ;;
    zypper)
      run_with_privileges zypper --non-interactive install "$@"
      ;;
    apk)
      run_with_privileges apk add --no-cache "$@"
      ;;
    *)
      return 1
      ;;
  esac
}

python_version_ok() {
  local py_bin="$1"
  "$py_bin" - <<'PY' >/dev/null 2>&1
import sys
sys.exit(0 if sys.version_info >= (3, 8) else 1)
PY
}

detect_python() {
  local candidate
  for candidate in python3 python; do
    if command_exists "$candidate" && python_version_ok "$candidate"; then
      PY_CMD="$candidate"
      log "Python compatível encontrado via comando \"$candidate\"."
      return 0
    fi
  done

  log_warn "Python 3.8+ não encontrado no sistema."
  if ! ask_yes_no "Deseja instalar o Python automaticamente agora?"; then
    return 1
  fi

  install_python_linux || return 1

  for candidate in python3 python; do
    if command_exists "$candidate" && python_version_ok "$candidate"; then
      PY_CMD="$candidate"
      log "Python instalado com sucesso."
      return 0
    fi
  done

  log_error "Python foi instalado, mas não ficou disponível nesta sessão."
  log_error "Abra um novo terminal e execute novamente este script."
  return 1
}

install_python_linux() {
  local pkg_mgr
  pkg_mgr="$(detect_pkg_manager)"
  if [[ -z "$pkg_mgr" ]]; then
    log_error "Nenhum gerenciador de pacotes suportado foi encontrado."
    log_error "Instale manualmente: Python 3, pip, venv, curl e ca-certificates."
    return 1
  fi

  log "Instalando dependências básicas do sistema com $pkg_mgr..."
  case "$pkg_mgr" in
    apt)
      install_packages "$pkg_mgr" python3 python3-venv python3-pip curl ca-certificates
      ;;
    dnf)
      install_packages "$pkg_mgr" python3 python3-pip python3-virtualenv curl ca-certificates
      ;;
    yum)
      install_packages "$pkg_mgr" python3 python3-pip curl ca-certificates
      ;;
    pacman)
      install_packages "$pkg_mgr" python python-pip curl ca-certificates
      ;;
    zypper)
      install_packages "$pkg_mgr" python3 python3-pip python3-virtualenv curl ca-certificates
      ;;
    apk)
      install_packages "$pkg_mgr" python3 py3-pip py3-virtualenv curl bash ca-certificates
      ;;
  esac
}

ensure_free_space_gb() {
  local required_gb="$1"
  local available_kb
  available_kb="$(df -Pk "$ROOT_DIR" | awk 'NR==2 {print $4}')"
  local available_gb=$((available_kb / 1024 / 1024))

  if (( available_gb < required_gb )); then
    log_error "Espaço livre insuficiente: ${available_gb}GB disponíveis, ${required_gb}GB recomendados."
    return 1
  fi

  log "Espaço livre verificado: ${available_gb}GB disponíveis."
}

wait_for_ollama() {
  local retries=0
  while (( retries < 20 )); do
    if ollama list >/dev/null 2>&1; then
      return 0
    fi
    retries=$((retries + 1))
    log "Aguardando Ollama iniciar... tentativa $retries/20"
    sleep 2
  done
  return 1
}

http_check() {
  local url="$1"

  if command_exists curl; then
    curl -fsS --max-time 5 "$url" >/dev/null 2>&1
    return $?
  fi

  "$PY_CMD" - "$url" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=5) as response:
    sys.exit(0 if response.status < 500 else 1)
PY
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local retries="${3:-25}"
  local pause_seconds="${4:-2}"
  local attempt=1

  while (( attempt <= retries )); do
    if http_check "$url"; then
      log "$label respondeu com sucesso em $url."
      return 0
    fi
    log "Aguardando $label responder... tentativa $attempt/$retries"
    attempt=$((attempt + 1))
    sleep "$pause_seconds"
  done

  return 1
}

port_in_use() {
  local port="$1"

  if command_exists ss; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)$port$"
    return $?
  fi
  if command_exists lsof; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  if command_exists netstat; then
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)$port$"
    return $?
  fi

  return 1
}

install_ollama() {
  local pkg_mgr
  pkg_mgr="$(detect_pkg_manager)"

  if ! command_exists curl; then
    if [[ -n "$pkg_mgr" ]]; then
      log "curl não encontrado. Instalando dependências de rede..."
      case "$pkg_mgr" in
        apt) install_packages "$pkg_mgr" curl ca-certificates ;;
        dnf) install_packages "$pkg_mgr" curl ca-certificates ;;
        yum) install_packages "$pkg_mgr" curl ca-certificates ;;
        pacman) install_packages "$pkg_mgr" curl ca-certificates ;;
        zypper) install_packages "$pkg_mgr" curl ca-certificates ;;
        apk) install_packages "$pkg_mgr" curl ca-certificates ;;
      esac
    fi
  fi

  command_exists curl || fatal "curl é obrigatório para instalar o Ollama automaticamente."

  log "Tentando instalar Ollama via script oficial..."
  curl -fsSL https://ollama.com/install.sh | sh
}

ensure_ollama_model() {
  local installed_models
  installed_models="$(ollama list 2>/dev/null | awk 'NR>1 {print $1}')"

  if grep -Fxq "$OLLAMA_MODEL" <<< "$installed_models"; then
    log "Modelo Ollama já disponível: $OLLAMA_MODEL"
    return 0
  fi

  log_warn "Modelo configurado não está instalado: $OLLAMA_MODEL"
  ensure_free_space_gb 6 || return 1

  if ! ask_yes_no "Deseja baixar o modelo $OLLAMA_MODEL agora?"; then
    log_error "Sem o modelo configurado, o chat não funcionará corretamente."
    return 1
  fi

  log "Baixando modelo $OLLAMA_MODEL. Isso pode demorar alguns minutos..."
  ollama pull "$OLLAMA_MODEL"
  log "Modelo $OLLAMA_MODEL instalado com sucesso."
}

ensure_ollama() {
  if ! command_exists ollama; then
    log_warn "Ollama não encontrado no PATH."
    if ask_yes_no "Deseja instalar o Ollama automaticamente agora?"; then
      install_ollama || return 1
    else
      log_error "Ollama é obrigatório para o projeto."
      return 1
    fi
  else
    log "Ollama encontrado no sistema."
  fi

  log "Verificando se o Ollama está em execução..."
  if ! ollama list >/dev/null 2>&1; then
    log "Ollama instalado, mas parado. Iniciando serviço local..."
    nohup ollama serve >"$OLLAMA_LOG" 2>&1 &
    echo $! > "$OLLAMA_PID_FILE"
  else
    log "Ollama já está em execução."
  fi

  wait_for_ollama || {
    log_error "Ollama não respondeu após as tentativas de inicialização."
    return 1
  }

  ensure_ollama_model || return 1
  log "Ollama ativo e pronto para uso."
}

validate_structure() {
  [[ -f "$ROOT_DIR/backend/app.py" ]] || fatal "Arquivo obrigatório ausente: backend/app.py"
  [[ -f "$ROOT_DIR/backend/requirements.txt" ]] || fatal "Arquivo obrigatório ausente: backend/requirements.txt"
  [[ -f "$ROOT_DIR/web/index.html" ]] || fatal "Arquivo obrigatório ausente: web/index.html"
  [[ -f "$ROOT_DIR/backend/data/agent_instructions.txt" ]] || fatal "Arquivo obrigatório ausente: backend/data/agent_instructions.txt"
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

pip_install_with_retry() {
  local description="$1"
  shift

  local attempt=1
  local max_attempts=3

  while (( attempt <= max_attempts )); do
    if "$VENV_PY" -m pip install --disable-pip-version-check --retries 5 --timeout 100 "$@"; then
      log "$description concluído com sucesso."
      return 0
    fi

    log_warn "Falha ao executar: $description (tentativa $attempt/$max_attempts)."
    attempt=$((attempt + 1))
    sleep 2
  done

  return 1
}

prepare_virtualenv() {
  if [[ ! -x "$VENV_PY" ]]; then
    log "Ambiente virtual não encontrado. Criando .venv..."
    "$PY_CMD" -m venv "$VENV_DIR"
  else
    log "Ambiente virtual já existe."
  fi

  pip_install_with_retry "Atualização do pip/setuptools/wheel" --upgrade pip setuptools wheel || return 1
  pip_install_with_retry "Instalação das dependências do backend" -r "$ROOT_DIR/backend/requirements.txt" || return 1
}

start_backend() {
  local backend_url="http://127.0.0.1:$BACKEND_PORT/"
  local backend_cmd="cd \"$ROOT_DIR/backend\" && export PYTHONUNBUFFERED=1 && \"$VENV_PY\" app.py"

  if http_check "$backend_url"; then
    log "Backend já está respondendo em $backend_url"
    return 0
  fi

  if port_in_use "$BACKEND_PORT"; then
    fatal "A porta do backend ($BACKEND_PORT) já está em uso por outro processo."
  fi

  : > "$BACKEND_LOG"
  if open_terminal_with_command "ROSITA Backend" "$backend_cmd | tee -a \"$BACKEND_LOG\""; then
    log "Backend iniciado em novo terminal."
  else
    nohup bash -lc "$backend_cmd" >"$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    log "Backend iniciado em background. Log: $BACKEND_LOG"
  fi

  wait_for_http "$backend_url" "Backend" 25 2 || {
    log_error "Backend não respondeu corretamente. Verifique o log em $BACKEND_LOG"
    return 1
  }
}

start_web() {
  local web_url="http://127.0.0.1:$WEB_PORT/"
  local web_cmd="cd \"$ROOT_DIR/web\" && export PYTHONUNBUFFERED=1 && \"$VENV_PY\" -m http.server $WEB_PORT"

  if http_check "$web_url"; then
    log "Frontend web já está respondendo em $web_url"
    return 0
  fi

  if port_in_use "$WEB_PORT"; then
    fatal "A porta do frontend ($WEB_PORT) já está em uso por outro processo."
  fi

  : > "$WEB_LOG"
  if open_terminal_with_command "ROSITA Web" "$web_cmd | tee -a \"$WEB_LOG\""; then
    log "Frontend iniciado em novo terminal."
  else
    nohup bash -lc "$web_cmd" >"$WEB_LOG" 2>&1 &
    echo $! > "$WEB_PID_FILE"
    log "Frontend iniciado em background. Log: $WEB_LOG"
  fi

  wait_for_http "$web_url" "Frontend" 20 2 || {
    log_error "Frontend não respondeu corretamente. Verifique o log em $WEB_LOG"
    return 1
  }
}

start_services() {
  start_backend
  start_web
}

open_browser() {
  local url="http://127.0.0.1:$WEB_PORT"

  if (( SKIP_BROWSER == 1 )); then
    log "Abertura automática do navegador foi desativada. URL: $url"
    return 0
  fi

  if command_exists xdg-open; then
    xdg-open "$url" >/dev/null 2>&1 || log_warn "Não foi possível abrir o navegador automaticamente. Use: $url"
  else
    log_warn "xdg-open não encontrado. Abra manualmente: $url"
  fi
}

main() {
  parse_args "$@"

  log "============================================================"
  log "ROSITA startup iniciado."
  log "Raiz do projeto: $ROOT_DIR"
  log "Logs em: $LOG_DIR"
  log "Modelo Ollama configurado: $OLLAMA_MODEL"
  log "============================================================"

  log "PASSO 1/6 - Validando estrutura mínima do projeto..."
  validate_structure
  log "PASSO 1/6 - OK."

  log "PASSO 2/6 - Verificando Python e dependências básicas..."
  detect_python || fatal "Python 3.8+ é obrigatório para continuar."
  log "PASSO 2/6 - OK."

  log "PASSO 3/6 - Criando ambiente virtual e instalando requirements..."
  prepare_virtualenv || fatal "Falha ao preparar o ambiente virtual ou instalar dependências."
  log "PASSO 3/6 - OK."

  log "PASSO 4/6 - Verificando Ollama e modelo configurado..."
  ensure_ollama || fatal "Falha ao configurar o Ollama."
  log "PASSO 4/6 - OK."

  if (( NO_START == 1 )); then
    log "PASSO 5/6 - Modo de validação concluído sem iniciar serviços (--no-start)."
    cat <<EOF

============================================
Dependências validadas com sucesso.
Backend configurado na porta: $BACKEND_PORT
Web configurada na porta:     $WEB_PORT
Modelo Ollama:                $OLLAMA_MODEL
Logs:                         $LOG_DIR
============================================
EOF
    exit 0
  fi

  log "PASSO 5/6 - Iniciando backend e frontend..."
  start_services || fatal "Falha ao iniciar backend ou frontend."
  log "PASSO 5/6 - OK."

  log "PASSO 6/6 - Abrindo navegador (quando disponível)..."
  open_browser
  log "PASSO 6/6 - OK."

  cat <<EOF

============================================
Sistema iniciado com sucesso.
Backend: http://127.0.0.1:$BACKEND_PORT
Web:     http://127.0.0.1:$WEB_PORT
Ollama:  http://127.0.0.1:11434
Modelo:  $OLLAMA_MODEL
Logs:    $LOG_DIR
============================================
EOF
  log "Inicialização concluída com sucesso."
}

main "$@"
