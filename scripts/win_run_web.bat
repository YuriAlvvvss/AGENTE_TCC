@echo off
setlocal EnableExtensions
cd /d "%~dp0..\web"
set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERRO] Ambiente virtual nao encontrado: %PY%
    pause
    exit /b 1
)
call :load_env_file
if not defined ROSITA_WEB_PORT set "ROSITA_WEB_PORT=18080"
title ROSITA Web
echo Servindo interface em http://127.0.0.1:%ROSITA_WEB_PORT% ...
"%PY%" -m http.server %ROSITA_WEB_PORT%
echo.
echo Servidor web encerrado.
pause
exit /b 0

:load_env_file
set "ROOT_DIR=%~dp0.."
if not exist "%ROOT_DIR%\.env" exit /b 0
for /f "usebackq eol=# tokens=1* delims==" %%A in ("%ROOT_DIR%\.env") do (
    if not "%%~A"=="" if not defined %%~A set "%%~A=%%~B"
)
exit /b 0
