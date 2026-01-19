#!/bin/bash
# AI Video Clipper Studio V3 - Server Startup Script
# Este script mantém o servidor rodando continuamente

cd "$(dirname "$0")"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🎬 AI Video Clipper Studio V3${NC}"
echo "================================="

# Matar processos antigos
echo -e "${YELLOW}Limpando processos anteriores...${NC}"
pkill -9 -f "python.*app.py" 2>/dev/null
fuser -k 5005/tcp 2>/dev/null
sleep 1

# Verificar venv
if [ ! -f "venv/bin/python" ]; then
    echo -e "${RED}Erro: venv não encontrado!${NC}"
    exit 1
fi

# Rodar servidor
echo -e "${GREEN}Iniciando servidor na porta 5005...${NC}"
echo "Acesse: http://localhost:5005"
echo ""
echo "Pressione Ctrl+C para parar"
echo "================================="
echo ""

# Executar com unbuffered output
exec ./venv/bin/python -u app.py
