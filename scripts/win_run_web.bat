@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERRO] Ambiente virtual nao encontrado: %PY%
    pause
    exit /b 1
)
if not defined ROSITA_WEB_PORT set "ROSITA_WEB_PORT=18080"
if not defined ROSITA_BACKEND_URL set "ROSITA_BACKEND_URL=http://127.0.0.1:18500"
if not defined ROSITA_WEB_HOST set "ROSITA_WEB_HOST=127.0.0.1"
title ROSITA Web
echo Servindo interface em http://127.0.0.1:%ROSITA_WEB_PORT% ...
echo Encaminhando /api para %ROSITA_BACKEND_URL%
"%PY%" -c "from web.scripts.dev_server import create_app; import os; app=create_app(web_root=r'%~dp0..\web', backend_url=os.getenv('ROSITA_BACKEND_URL','http://127.0.0.1:18500')); app.run(host=os.getenv('ROSITA_WEB_HOST','127.0.0.1'), port=int(os.getenv('ROSITA_WEB_PORT','18080')), debug=False)"
echo.
echo Servidor web encerrado.
pause
