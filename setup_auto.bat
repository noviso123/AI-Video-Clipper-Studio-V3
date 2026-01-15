@echo off
REM ===========================================
REM AI Video Clipper - Setup AUTOMÁTICO (Non-Interactive)
REM ===========================================

echo.
echo ============================================================
echo  AI VIDEO CLIPPER - Setup Automatico (Auto-Mode)
echo ============================================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    exit /b 1
)

echo [OK] Python encontrado

REM Verificar FFmpeg (apenas aviso, não para)
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] FFmpeg nao encontrado! Continuando mesmo assim...
) else (
    echo [OK] FFmpeg encontrado
)

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo.
    echo [1/4] Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
) else (
    echo [OK] Ambiente virtual ja existe
)

REM Ativar para este prompt (não persiste para run_command seguinte, mas ok para o pip)
call venv\Scripts\activate.bat

REM Atualizar pip
echo.
echo [2/4] Atualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependencias
echo.
echo [3/4] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    exit /b 1
)

REM Criar .env
if not exist ".env" (
    echo.
    echo [SETUP] Criando arquivo .env...
    copy .env.example .env >nul
)

REM Criar diretorios
echo.
echo [SETUP] Criando diretorios...
if not exist "temp" mkdir temp
if not exist "exports" mkdir exports
if not exist "logs" mkdir logs

REM Executar testes de validação usando o python do venv
echo.
echo [4/4] Validando instalacao...
venv\Scripts\python tests\test_setup.py

echo.
echo ============================================================
echo  SETUP AUTOMATICO CONCLUIDO!
echo ============================================================
echo.
exit /b 0
