@echo off
setlocal EnableExtensions
cd /d "%~dp0..\backend"
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERRO] Ambiente virtual nao encontrado: %PY%
    pause
    exit /b 1
)
call :load_env_file
if not defined ROSITA_API_HOST set "ROSITA_API_HOST=0.0.0.0"
if not defined ROSITA_API_PORT set "ROSITA_API_PORT=18500"
title ROSITA Backend
echo Iniciando backend em %ROSITA_API_HOST%:%ROSITA_API_PORT% ...
"%PY%" app.py
echo.
echo Backend encerrado.
pause
exit /b 0

:load_env_file
set "ROOT_DIR=%~dp0.."
if not exist "%ROOT_DIR%\.env" exit /b 0
for /f "usebackq eol=# tokens=1* delims==" %%A in ("%ROOT_DIR%\.env") do (
    if not "%%~A"=="" if not defined %%~A set "%%~A=%%~B"
)
exit /b 0
