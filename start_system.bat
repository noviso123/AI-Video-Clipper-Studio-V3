@echo off
title AI Clipper Studio - Offline System
echo ===========================================
echo 🚀 INICIANDO SISTEMA COMPLETO (OFFLINE/CPU)
echo ===========================================
echo.

:: 1. Iniciar Interface WEB
echo [1/2] Iniciando Interface Web (http://localhost:5000)...
start "AI Clipper WEB UI" cmd /k "python app.py"

:: 2. Bot Telegram DESATIVADO (SSL Error)
:: echo [2/2] Iniciando Bot Telegram...
:: start "AI Clipper TELEGRAM" cmd /k "python src/bot/telegram_bot.py"

echo.
echo ✅ TUDO RODANDO!
echo - Acesse o site: http://localhost:5000
echo - Ou use o Telegram
echo.
echo Mantenha as janelas abertas.
pause
