@echo off
setlocal EnableExtensions
cd /d "%~dp0..\backend"
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERRO] Ambiente virtual nao encontrado: %PY%
    pause
    exit /b 1
)
if not defined ROSITA_API_HOST set "ROSITA_API_HOST=0.0.0.0"
if not defined ROSITA_API_PORT set "ROSITA_API_PORT=18500"
title ROSITA Backend
echo Iniciando backend em %ROSITA_API_HOST%:%ROSITA_API_PORT% ...
"%PY%" app.py
echo.
echo Backend encerrado.
pause
