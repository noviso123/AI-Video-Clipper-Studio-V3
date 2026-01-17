#!/bin/bash

# ========================================================
# AI VIDEO CLIPPER - INTERFACE WEB (Linux/macOS)
# ========================================================

# Cores
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================================${NC}"
echo -e "${CYAN}          AI VIDEO CLIPPER - INTERFACE WEB${NC}"
echo -e "${CYAN}========================================================${NC}"
echo ""

if [ ! -d "venv" ]; then
    echo "Ambiente virtual não encontrado. Rodando setup primeiro..."
    bash setup.sh
fi

echo "[1] Ativando ambiente virtual..."
source venv/bin/activate

echo "[2] Iniciando servidor..."
echo -e "🚀 Acesse no navegador: ${CYAN}http://127.0.0.1:5000${NC}"
echo ""
echo "(Pressione CTRL+C para encerrar)"
echo ""

python3 app.py
