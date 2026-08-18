@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==========================================================
REM ROSITA - Startup automatico (Windows)
REM 1) Detecta Python; tenta instalar via winget se ausente
REM 2) Valida o provedor de IA configurado (Open Router ou Gateway)
REM 3) Cria/usa .venv
REM 4) Instala dependencias
REM 5) Inicia backend e web em terminais separados
REM ==========================================================

cd /d "%~dp0"
set "ROOT_DIR=%cd%"
set "LOG_DIR=%ROOT_DIR%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
set "VENV_PY=%ROOT_DIR%\.venv\Scripts\python.exe"
set "START_LOG=%LOG_DIR%\startup.log"
set "PY_CMD="
set "BACKEND_PORT=18500"
set "WEB_PORT=18080"
set "AI_PROVIDER=openrouter"
set "OPENROUTER_API_KEY="
set "OPENROUTER_MODEL="
set "GATEWAY_URL="
set "NO_START=0"
set "SKIP_BROWSER=0"
set "SHOW_HELP=0"

call :parse_args %*
if "%SHOW_HELP%"=="1" goto :show_help_and_exit
call :load_env_file
call :resolve_runtime_config

call :log "============================================================"
call :log "ROSITA startup iniciado."
call :log "Raiz do projeto: %ROOT_DIR%"
call :log "Log em arquivo: %START_LOG%"
call :log "Backend local: %BACKEND_PORT%"
call :log "Frontend local: %WEB_PORT%"
call :log "Provider de IA: %AI_PROVIDER%"
call :log "============================================================"

call :log "PASSO 1/7 - Verificando Python no sistema..."
call :detect_python
if errorlevel 1 goto :fatal
call :log "PASSO 1/7 - OK."

call :log "PASSO 2/7 - Verificando provider de IA..."
if /I "%AI_PROVIDER%"=="openrouter" goto :step2_openrouter
if /I "%AI_PROVIDER%"=="gateway" goto :step2_gateway
call :log_error "ROSITA_AI_PROVIDER invalido: %AI_PROVIDER%. Use 'openrouter' ou 'gateway'."
goto :fatal

:step2_openrouter
call :verify_openrouter
if errorlevel 1 goto :fatal
call :log "PASSO 2/7 - OK (Open Router configurado)."
goto :step3

:step2_gateway
if "%GATEWAY_URL%"=="" (
    call :log_error "ROSITA_GATEWAY_URL nao configurada."
    call :log_error "Configure a variavel de ambiente ou no arquivo .env"
    goto :fatal
)
call :log "PASSO 2/7 - OK (Gateway local configurado: %GATEWAY_URL%)."
goto :step3

:step3
call :log "PASSO 3/7 - Criando ambiente virtual (.venv) se necessario..."
if exist "%VENV_PY%" goto :step3_exists
call :log "Ambiente virtual nao encontrado. Criando .venv..."
call :run_python -m venv ".venv"
if errorlevel 1 goto :step3_failed
goto :step3_done

:step3_exists
call :log "Ambiente virtual ja existe."

:step3_done
call :log "PASSO 3/7 - OK."

call :log "PASSO 4/7 - Atualizando pip no .venv..."
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :step4_failed
call :log "PASSO 4/7 - OK."

call :log "PASSO 5/7 - Instalando dependencias do backend..."
if not exist "backend\requirements.txt" goto :step5_missing
"%VENV_PY%" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :step5_failed
call :log "PASSO 5/7 - OK."

call :log "PASSO 6/7 - Validando estrutura minima do projeto..."
if not exist "backend\app.py" goto :step6_backend_missing
if not exist "web\index.html" goto :step6_web_missing
call :log "PASSO 6/7 - OK."

if "%NO_START%"=="1" goto :no_start_done

call :log "PASSO 7/7 - Iniciando servicos (backend/web)..."
call :export_service_env

set "BACKEND_URL=http://127.0.0.1:%BACKEND_PORT%/"
call :service_alive "%BACKEND_URL%"
if not errorlevel 1 goto :step7_web
call :port_in_use %BACKEND_PORT%
if not errorlevel 1 goto :step7_backend_busy
start "ROSITA Backend" cmd /k ""%ROOT_DIR%\scripts\win_run_backend.bat""
call :log "Backend iniciado em nova janela (porta %BACKEND_PORT%)."

:step7_web
set "WEB_URL=http://127.0.0.1:%WEB_PORT%/"
call :service_alive "%WEB_URL%"
if not errorlevel 1 goto :step7_done
call :port_in_use %WEB_PORT%
if not errorlevel 1 goto :step7_web_busy
start "ROSITA Web" cmd /k ""%ROOT_DIR%\scripts\win_run_web.bat""
call :log "Frontend iniciado em nova janela (porta %WEB_PORT%)."

:step7_done
call :log "PASSO 7/7 - OK."

if "%SKIP_BROWSER%"=="1" goto :skip_browser
call :sleep_seconds 5
set "URL=http://127.0.0.1:%WEB_PORT%"
start "" "%URL%"
call :log "Navegador aberto em %URL%."
goto :print_success

:skip_browser
call :log "Abertura automatica do navegador foi desativada."

:print_success
echo.
echo ============================================
echo Sistema iniciado com sucesso.
echo Backend: http://127.0.0.1:%BACKEND_PORT%
echo Web:     http://127.0.0.1:%WEB_PORT%
echo Provider: %AI_PROVIDER%
if /I "%AI_PROVIDER%"=="openrouter" (
    echo Model: %OPENROUTER_MODEL%
) else (
    echo Gateway: %GATEWAY_URL%
)
echo Log:     %START_LOG%
echo ============================================
call :log "Inicializacao concluida com sucesso."
goto :eof

:step3_failed
call :log_error "Falha ao criar o ambiente virtual."
goto :fatal

:step4_failed
call :log_error "Falha ao atualizar pip no ambiente virtual."
goto :fatal

:step5_missing
call :log_error "Arquivo backend\requirements.txt nao encontrado."
goto :fatal

:step5_failed
call :log_error "Falha ao instalar dependencias."
goto :fatal

:step6_backend_missing
call :log_error "Arquivo backend\app.py nao encontrado."
goto :fatal

:step6_web_missing
call :log_error "Arquivo web\index.html nao encontrado."
goto :fatal

:no_start_done
echo.
echo ============================================
echo Validacao concluida com sucesso.
echo Backend local: %BACKEND_PORT%
echo Web local:     %WEB_PORT%
echo Provider:      %AI_PROVIDER%
if /I "%AI_PROVIDER%"=="openrouter" (
    echo Modelo: %OPENROUTER_MODEL%
) else (
    echo Gateway: %GATEWAY_URL%
    echo Modelos: selecao manual via interface
)
echo Log:           %START_LOG%
echo ============================================
call :log "Validacao concluida sem iniciar servicos (--no-start)."
goto :eof

:step7_backend_busy
call :log_error "A porta do backend (%BACKEND_PORT%) ja esta em uso por outro processo."
call :log_error "Feche o processo antigo ou altere ROSITA_API_PORT no .env"
goto :fatal

:step7_web_busy
call :log_error "A porta do frontend (%WEB_PORT%) ja esta em uso por outro processo."
call :log_error "Feche o processo antigo ou altere ROSITA_WEB_PORT no .env"
goto :fatal

:show_help_and_exit
call :show_help
goto :eof

:parse_args
if "%~1"=="" goto :parse_args_done
if /I "%~1"=="--no-start" set "NO_START=1"
if /I "%~1"=="--skip-browser" set "SKIP_BROWSER=1"
if /I "%~1"=="--help" set "SHOW_HELP=1"
shift
goto :parse_args

:parse_args_done
exit /b 0

:show_help
echo Uso: start_system.bat [--no-start] [--skip-browser]
exit /b 0

:load_env_file
if not exist "%ROOT_DIR%\.env" exit /b 0
for /f "usebackq eol=# tokens=1* delims==" %%A in ("%ROOT_DIR%\.env") do (
    if not "%%~A"=="" if not defined %%~A set "%%~A=%%~B"
)
exit /b 0

:resolve_runtime_config
if defined ROSITA_API_PORT set "BACKEND_PORT=%ROSITA_API_PORT%"
if defined ROSITA_WEB_PORT set "WEB_PORT=%ROSITA_WEB_PORT%"
if defined ROSITA_AI_PROVIDER set "AI_PROVIDER=%ROSITA_AI_PROVIDER%"
if defined ROSITA_OPENROUTER_API_KEY set "OPENROUTER_API_KEY=%ROSITA_OPENROUTER_API_KEY%"
if defined ROSITA_OPENROUTER_MODEL set "OPENROUTER_MODEL=%ROSITA_OPENROUTER_MODEL%"
if defined ROSITA_GATEWAY_URL set "GATEWAY_URL=%ROSITA_GATEWAY_URL%"
exit /b 0

:verify_openrouter
if "!OPENROUTER_API_KEY!"=="" goto :verify_openrouter_no_key
if "!OPENROUTER_MODEL!"=="" goto :verify_openrouter_no_model
call :log "Open Router configurado com sucesso."
call :log "API Key: **** (primeiros 4 caracteres: !OPENROUTER_API_KEY:~0,4!)"
call :log "Modelo: !OPENROUTER_MODEL!"
exit /b 0

:verify_openrouter_no_key
call :log_error "ROSITA_OPENROUTER_API_KEY nao configurada."
call :log_error "Configure a variavel de ambiente ou no arquivo .env"
exit /b 1

:verify_openrouter_no_model
call :log_error "ROSITA_OPENROUTER_MODEL nao configurada."
call :log_error "Exemplo: gpt-4-turbo, gpt-3.5-turbo, claude-3-opus, etc"
exit /b 1

:sleep_seconds
set /a _SLEEP_SEC=%~1
if not defined _SLEEP_SEC set /a _SLEEP_SEC=1
set /a _SLEEP_PING=_SLEEP_SEC+1
ping -n !_SLEEP_PING! 127.0.0.1 >nul
exit /b 0

:detect_python
set "PY_CMD="

where python >nul 2>&1
if errorlevel 1 goto :detect_python_try_py
set "PY_CMD=python"
call :run_python --version >nul 2>&1
if errorlevel 1 goto :detect_python_try_py
call :log "Python encontrado via comando ""python""."
exit /b 0

:detect_python_try_py
where py >nul 2>&1
if errorlevel 1 goto :detect_python_install
set "PY_CMD=py -3"
call :run_python --version >nul 2>&1
if errorlevel 1 goto :detect_python_install
call :log "Python encontrado via launcher ""py -3""."
exit /b 0

:detect_python_install
call :log "Python nao encontrado. Tentando instalar via winget..."
where winget >nul 2>&1
if errorlevel 1 goto :detect_python_no_winget

winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
if errorlevel 1 goto :detect_python_winget_failed

set "PY_CMD="
where python >nul 2>&1
if errorlevel 1 goto :detect_python_after_install_try_py
set "PY_CMD=python"
call :run_python --version >nul 2>&1
if errorlevel 1 goto :detect_python_after_install_try_py
call :log "Python instalado com sucesso."
exit /b 0

:detect_python_after_install_try_py
where py >nul 2>&1
if errorlevel 1 goto :detect_python_after_install_failed
set "PY_CMD=py -3"
call :run_python --version >nul 2>&1
if errorlevel 1 goto :detect_python_after_install_failed
call :log "Python instalado com sucesso."
exit /b 0

:detect_python_after_install_failed
call :log_error "Python foi instalado, mas nao ficou disponivel nesta sessao."
call :log_error "Feche e abra o terminal, depois rode novamente este script."
exit /b 1

:detect_python_no_winget
call :log_error "winget nao disponivel. Instale Python manualmente e execute novamente."
exit /b 1

:detect_python_winget_failed
call :log_error "Nao foi possivel instalar Python automaticamente com winget."
exit /b 1

:run_python
if not defined PY_CMD exit /b 1
%PY_CMD% %*
exit /b %errorlevel%

:export_service_env
set "PYTHONUNBUFFERED=1"
set "ROSITA_API_HOST=0.0.0.0"
set "ROSITA_API_PORT=%BACKEND_PORT%"
set "ROSITA_WEB_PORT=%WEB_PORT%"
set "ROSITA_AI_PROVIDER=%AI_PROVIDER%"
set "ROSITA_OPENROUTER_API_KEY=%OPENROUTER_API_KEY%"
set "ROSITA_OPENROUTER_MODEL=%OPENROUTER_MODEL%"
set "ROSITA_GATEWAY_URL=%GATEWAY_URL%"
exit /b 0

:service_alive
"%VENV_PY%" -c "import urllib.request; urllib.request.urlopen(r'%~1', timeout=3)" >nul 2>&1
exit /b %errorlevel%

:port_in_use
netstat -ano | findstr /C:":%~1 " | findstr /I "LISTENING" >nul
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
echo.
echo Verifique o log: %START_LOG%
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
exit /b 1