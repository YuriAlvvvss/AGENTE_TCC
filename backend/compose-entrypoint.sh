#!/bin/sh
set -eu
cd /app/backend
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --worker-class gthread \
  --workers 1 \
  --threads 8 \
  --timeout 0 \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile - \
  app:app
