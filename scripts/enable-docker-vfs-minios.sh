#!/usr/bin/env bash
# Ativa o driver de armazenamento "vfs" no Docker (MiniOS / overlay com EINVAL).
# Uso: sudo ./scripts/enable-docker-vfs-minios.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE="$ROOT/docker/minios-vfs-daemon.json"

if [[ "${EUID:-}" -ne 0 ]]; then
  echo "Execute com sudo, por exemplo: sudo $0" >&2
  exit 1
fi

if [[ ! -f "$EXAMPLE" ]]; then
  echo "Ficheiro em falta: $EXAMPLE" >&2
  exit 1
fi

install -d /etc/docker

if [[ -f /etc/docker/daemon.json ]]; then
  bak="/etc/docker/daemon.json.bak.$(date +%s)"
  cp -a /etc/docker/daemon.json "$bak"
  echo "Cópia de segurança: $bak"
  if command -v jq >/dev/null 2>&1; then
    jq -s '.[0] * .[1]' /etc/docker/daemon.json "$EXAMPLE" > /etc/docker/daemon.json.new
    mv /etc/docker/daemon.json.new /etc/docker/daemon.json
    echo "Fusão com jq: adicionado storage-driver vfs ao daemon.json existente."
  else
    echo ""
    echo "AVISO: já existe /etc/docker/daemon.json e o comando jq não está instalado."
    echo "Instale jq e volte a correr este script, OU edite manualmente o JSON e acrescente:"
    echo '  "storage-driver": "vfs"'
    echo ""
    cat "$EXAMPLE"
    exit 2
  fi
else
  cp -a "$EXAMPLE" /etc/docker/daemon.json
  echo "Criado /etc/docker/daemon.json a partir do exemplo do projeto."
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl restart docker
  echo "Serviço docker reiniciado."
else
  echo "Reinicie o serviço Docker manualmente (ex.: service docker restart)."
fi

echo ""
echo "Teste na pasta do projeto: docker compose up -d"
