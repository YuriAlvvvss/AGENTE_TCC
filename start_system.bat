@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==========================================================
REM ROSITA - Startup automatico (Windows)
REM 1) Detecta Python; tenta instalar via winget se ausente
REM 2) Garante Ollama (instala opcional e inicia automatico)
REM 3) Cria/usa .venv
REM 4) Instala dependencias
REM 5) Inicia backend e web em terminais separados
REM ==========================================================

cd /d "%~dp0"
set "ROOT_DIR=%cd%"
set "VENV_PY=%ROOT_DIR%\.venv\Scripts\python.exe"
set "START_LOG=%ROOT_DIR%\startup.log"
set "PY_CMD="

call :log "============================================================"
call :log "ROSITA startup iniciado."
call :log "Raiz do projeto: %ROOT_DIR%"
call :log "Log em arquivo: %START_LOG%"
call :log "============================================================"

call :log "PASSO 1/7 - Verificando Python no sistema..."
call :detect_python
if errorlevel 1 goto :fatal
call :log "PASSO 1/7 - OK."

call :log "PASSO 2/7 - Verificando Ollama..."
call :ensure_ollama
if errorlevel 1 goto :fatal
call :log "PASSO 2/7 - OK."

call :log "PASSO 3/7 - Criando ambiente virtual (.venv) se necessario..."
if not exist "%VENV_PY%" (
    call :log "Ambiente virtual nao encontrado. Criando .venv..."
    call :run_python -m venv ".venv"
    if errorlevel 1 (
        call :log_error "Falha ao criar o ambiente virtual."
        goto :fatal
    )
) else (
    call :log "Ambiente virtual ja existe."
)
call :log "PASSO 3/7 - OK."

call :log "PASSO 4/7 - Atualizando pip no .venv..."
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    call :log_error "Falha ao atualizar pip no ambiente virtual."
    goto :fatal
)
call :log "PASSO 4/7 - OK."

call :log "PASSO 5/7 - Instalando dependencias do backend..."
if not exist "backend\requirements.txt" (
    call :log_error "Arquivo backend\requirements.txt nao encontrado."
    goto :fatal
)
"%VENV_PY%" -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
    call :log_error "Falha ao instalar dependencias."
    goto :fatal
)
call :log "PASSO 5/7 - OK."

call :log "PASSO 6/7 - Validando estrutura minima do projeto..."
if not exist "backend\app.py" (
    call :log_error "Arquivo backend\app.py nao encontrado."
    goto :fatal
)
if not exist "web\index.html" (
    call :log_error "Arquivo web\index.html nao encontrado."
    goto :fatal
)
call :log "PASSO 6/7 - OK."

call :log "PASSO 7/7 - Iniciando servicos (backend/web)..."
start "ROSITA Backend" cmd /k "cd /d ""%ROOT_DIR%\backend"" && ""%VENV_PY%"" app.py"
if errorlevel 1 (
    call :log_error "Nao foi possivel iniciar o backend."
    goto :fatal
)
start "ROSITA Web" cmd /k "cd /d ""%ROOT_DIR%\web"" && ""%VENV_PY%"" -m http.server 8080"
if errorlevel 1 (
    call :log_error "Nao foi possivel iniciar o servidor web."
    goto :fatal
)
call :log "PASSO 7/7 - OK."

timeout /t 2 >nul
start "" "http://localhost:8080"
call :log "Navegador aberto em http://localhost:8080."

echo.
echo ============================================
echo Sistema iniciado com sucesso.
echo Backend: http://localhost:5000
echo Web:     http://localhost:8080
echo Ollama:  http://localhost:11434
echo Log:     %START_LOG%
echo ============================================
call :log "Inicializacao concluida com sucesso."
goto :eof

:ensure_ollama
where ollama >nul 2>&1
if errorlevel 1 (
    call :log "Ollama nao encontrado no PATH."
    set "INSTALL_OLLAMA="
    set /p INSTALL_OLLAMA="Deseja instalar o Ollama automaticamente agora? (S/N): "
    if /I "!INSTALL_OLLAMA!"=="S" (
        call :install_ollama
        if errorlevel 1 exit /b 1
    ) else (
        if /I "!INSTALL_OLLAMA!"=="Y" (
            call :install_ollama
            if errorlevel 1 exit /b 1
        ) else (
            call :log_error "Ollama e obrigatorio para o projeto. Inicializacao cancelada."
            exit /b 1
        )
    )
) else (
    call :log "Ollama encontrado no sistema."
)

call :log "Verificando se o Ollama esta em execucao (porta 11434)..."
netstat -ano | findstr /R /C:":11434" >nul
if errorlevel 1 (
    call :log "Ollama instalado, mas nao esta em execucao. Iniciando automaticamente..."
    start "ROSITA Ollama" cmd /k "ollama serve"
    timeout /t 3 >nul
) else (
    call :log "Ollama ja esta em execucao."
)

call :wait_ollama
if errorlevel 1 (
    call :log_error "Ollama nao respondeu apos tentativas de inicializacao."
    exit /b 1
)
call :log "Ollama ativo e respondendo."
exit /b 0

:wait_ollama
set /a OLLAMA_RETRY=0
:wait_ollama_loop
set /a OLLAMA_RETRY+=1
ollama list >nul 2>&1
if not errorlevel 1 exit /b 0
if !OLLAMA_RETRY! GEQ 10 exit /b 1
call :log "Aguardando Ollama iniciar... tentativa !OLLAMA_RETRY!/10"
timeout /t 2 >nul
goto :wait_ollama_loop

:install_ollama
call :log "Tentando instalar Ollama via winget..."
where winget >nul 2>&1
if errorlevel 1 (
    call :log_error "winget nao disponivel. Instale o Ollama manualmente e execute novamente."
    exit /b 1
)

winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements --silent
if errorlevel 1 (
    call :log_error "Nao foi possivel instalar Ollama automaticamente com winget."
    exit /b 1
)

where ollama >nul 2>&1
if errorlevel 1 (
    call :log_error "Ollama foi instalado, mas nao ficou disponivel nesta sessao."
    call :log_error "Feche e abra o terminal, depois rode novamente este script."
    exit /b 1
)
call :log "Ollama instalado com sucesso."
exit /b 0

:detect_python
set "PY_CMD="

where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    call :run_python --version >nul 2>&1
    if not errorlevel 1 (
        call :log "Python encontrado via comando ""python""."
        exit /b 0
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    call :run_python --version >nul 2>&1
    if not errorlevel 1 (
        call :log "Python encontrado via launcher ""py -3""."
        exit /b 0
    )
)

call :log "Python nao encontrado. Tentando instalar via winget..."
where winget >nul 2>&1
if errorlevel 1 (
    call :log_error "winget nao disponivel. Instale Python manualmente e execute novamente."
    exit /b 1
)

winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
if errorlevel 1 (
    call :log_error "Nao foi possivel instalar Python automaticamente com winget."
    exit /b 1
)

REM Recarrega shell PATH em nova deteccao
set "PY_CMD="
where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    call :run_python --version >nul 2>&1
    if not errorlevel 1 (
        call :log "Python instalado com sucesso."
        exit /b 0
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    call :run_python --version >nul 2>&1
    if not errorlevel 1 (
        call :log "Python instalado com sucesso."
        exit /b 0
    )
)

call :log_error "Python foi instalado, mas nao ficou disponivel nesta sessao."
call :log_error "Feche e abra o terminal, depois rode novamente este script."
exit /b 1

:run_python
if "%PY_CMD%"=="" exit /b 1
call %PY_CMD% %*
exit /b %errorlevel%

:log
set "MSG=%~1"
echo.
echo [%date% %time%] !MSG!
>> "%START_LOG%" echo [%date% %time%] !MSG!
exit /b 0

:log_error
set "MSG=%~1"
echo.
echo [ERRO - %date% %time%] !MSG!
>> "%START_LOG%" echo [ERRO - %date% %time%] !MSG!
exit /b 0

:fatal
call :log_error "Processo interrompido devido a erro."
exit /b 1

