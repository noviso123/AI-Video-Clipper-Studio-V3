#!/bin/bash

# ========================================================
# AI VIDEO CLIPPER - TELEGRAM BOT (Linux/macOS)
# ========================================================

# Cores
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${CYAN}========================================================${NC}"
echo -e "${CYAN}          AI VIDEO CLIPPER - TELEGRAM BOT${NC}"
echo -e "${CYAN}========================================================${NC}"
echo ""

if [ ! -d "venv" ]; then
    echo "Ambiente virtual não encontrado. Rode setup.sh primeiro."
    exit 1
fi

echo "[1] Ativando ambiente virtual..."
source venv/bin/activate

echo "[2] Verificando credenciais do Telegram..."
if ! grep -q "TELEGRAM_BOT_TOKEN" .env || [ -z "$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2)" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN não configurado no .env${NC}"
    exit 1
fi

echo "[3] Iniciando bot Telegram..."
echo -e "🤖 Bot Online! ${GREEN}Aguardando mensagens no Telegram...${NC}"
echo ""
echo "(Pressione CTRL+C para encerrar)"
echo ""

python3 src/bot/telegram_bot.py
