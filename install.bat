@echo off
chcp 65001 >nul
title AI Video Clipper V3 - Instalador Automático
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     🎬 AI VIDEO CLIPPER V3 - INSTALAÇÃO AUTOMÁTICA 🎬       ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Este script vai:                                           ║
echo ║  1. Verificar Python                                        ║
echo ║  2. Criar ambiente virtual                                  ║
echo ║  3. Instalar todas as dependências                          ║
echo ║  4. Baixar modelos de IA (Whisper multilíngue ~3GB)         ║
echo ║  5. Configurar FFmpeg                                       ║
echo ║  6. Criar arquivos de configuração                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause

:: ========================================
:: 1. VERIFICAR PYTHON
:: ========================================
echo.
echo [1/6] 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo.
    echo Por favor instale Python 3.10+ de: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalação!
    pause
    exit /b 1
)
python --version
echo ✅ Python encontrado!

:: ========================================
:: 2. CRIAR AMBIENTE VIRTUAL
:: ========================================
echo.
echo [2/6] 📦 Criando ambiente virtual...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ Ambiente virtual criado!
) else (
    echo ⏭️ Ambiente virtual já existe.
)

:: ========================================
:: 3. ATIVAR E INSTALAR DEPENDÊNCIAS
:: ========================================
echo.
echo [3/6] 📥 Instalando dependências (pode demorar alguns minutos)...
call .venv\Scripts\activate.bat

:: Atualizar pip primeiro
python -m pip install --upgrade pip --quiet

:: Instalar PyTorch CPU (mais leve)
echo    ⚡ Instalando PyTorch CPU...
pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet

:: Instalar resto das dependências
echo    📚 Instalando bibliotecas...
pip install -r requirements.txt --quiet

echo ✅ Dependências instaladas!

:: ========================================
:: 4. BAIXAR MODELOS
:: ========================================
echo.
echo [4/6] 🧠 Baixando modelos de IA (Whisper multilíngue ~3GB)...
echo    ⚠️ Isso pode demorar dependendo da sua conexão...

python download_models.py

echo ✅ Modelos baixados!

:: ========================================
:: 5. VERIFICAR/INSTALAR FFMPEG
:: ========================================
echo.
echo [5/6] 🎥 Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ FFmpeg não encontrado no PATH.
    echo.
    echo Para instalar FFmpeg:
    echo   1. Baixe de: https://www.gyan.dev/ffmpeg/builds/
    echo   2. Extraia o ZIP
    echo   3. Adicione a pasta "bin" ao PATH do sistema
    echo.
    echo Ou use: winget install ffmpeg
    echo.
) else (
    echo ✅ FFmpeg encontrado!
)

:: ========================================
:: 6. CRIAR .ENV SE NÃO EXISTIR
:: ========================================
echo.
echo [6/6] ⚙️ Configurando ambiente...
if not exist ".env" (
    copy ".env.example" ".env" >nul 2>&1
    echo ✅ Arquivo .env criado! Edite com suas chaves de API.
) else (
    echo ⏭️ Arquivo .env já existe.
)

:: Criar pastas necessárias
if not exist "exports" mkdir exports
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO! ✅            ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  Para iniciar o sistema:                                     ║
echo ║  > start_system.bat                                         ║
echo ║                                                              ║
echo ║  Acesse: http://localhost:5000                              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause
