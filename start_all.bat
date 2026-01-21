@echo off
title AI Video Clipper Launcher

echo ==================================================
echo 🚀 AI Video Clipper Studio V3 - Launcher
echo ==================================================

if not exist ".env" (
    echo ❌ Arquivo .env nao encontrado!
    pause
    exit /b
)

echo.
echo 🌐 Iniciando Servidor Web...
start "AI Clipper Web" cmd /k ".venv\Scripts\python app.py"

echo.
echo 🤖 Iniciando Bot Telegram...
start "AI Clipper Bot" cmd /k ".venv\Scripts\python src/bot/telegram_bot.py"

echo.
echo ✅ Sistemas iniciados em janelas separadas.
echo Pressione qualquer tecla para sair deste launcher.
pause >nul
