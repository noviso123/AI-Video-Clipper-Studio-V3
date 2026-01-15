@echo off
REM ===========================================
REM AI Video Clipper - Script de Setup Rápido
REM ===========================================

echo.
echo ============================================================
echo  AI VIDEO CLIPPER - Setup Automatico
echo ============================================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.10+ e adicione ao PATH
    pause
    exit /b 1
)

echo [OK] Python encontrado

REM Verificar se FFmpeg está instalado
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] FFmpeg nao encontrado!
    echo Por favor, instale FFmpeg: https://ffmpeg.org/download.html
    echo.
    set /p continue="Deseja continuar mesmo assim? (s/n): "
    if /i not "%continue%"=="s" exit /b 1
)

echo [OK] FFmpeg encontrado

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo.
    echo [1/4] Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
) else (
    echo [OK] Ambiente virtual ja existe
)

REM Ativar ambiente virtual
echo.
echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Atualizar pip
echo.
echo [3/4] Atualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependências
echo.
echo [4/4] Instalando dependencias (isso pode demorar 5-10 min)...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)

REM Criar arquivo .env se não existir
if not exist ".env" (
    echo.
    echo [SETUP] Criando arquivo .env...
    copy .env.example .env >nul
    echo [OK] Arquivo .env criado
)

REM Criar diretórios necessários
echo.
echo [SETUP] Criando diretorios...
if not exist "temp" mkdir temp
if not exist "exports" mkdir exports
if not exist "logs" mkdir logs

REM Executar testes
echo.
echo ============================================================
echo Executando testes de validacao...
echo ============================================================
python tests\test_setup.py

echo.
echo ============================================================
echo  SETUP CONCLUIDO COM SUCESSO!
echo ============================================================
echo.
echo Proximo passo:
echo   python main.py --url "URL_DO_YOUTUBE" --clips 3
echo.
echo Para ajuda:
echo   python main.py --help
echo.
echo Guias detalhados:
echo   - SETUP.md   (instalacao completa)
echo   - USAGE.md   (guia de uso)
echo   - README.md  (visao geral)
echo.
pause
