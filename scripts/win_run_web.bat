@echo off
setlocal EnableExtensions
cd /d "%~dp0..\web"
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERRO] Ambiente virtual nao encontrado: %PY%
    pause
    exit /b 1
)
if not defined ROSITA_WEB_PORT set "ROSITA_WEB_PORT=18080"
title ROSITA Web
echo Servindo interface em http://127.0.0.1:%ROSITA_WEB_PORT% ...
"%PY%" -m http.server %ROSITA_WEB_PORT%
echo.
echo Servidor web encerrado.
pause
