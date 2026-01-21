#!/bin/bash
# ============================================
# AI Video Clipper V3 - Iniciar Sistema
# ============================================

echo "🎬 Iniciando AI Video Clipper V3..."

# Ativar ambiente virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Ambiente virtual não encontrado!"
    echo "   Execute primeiro: ./install.sh"
    exit 1
fi

# Criar pastas necessárias
mkdir -p exports temp logs

# Iniciar servidor
echo "🌐 Abrindo servidor em http://localhost:5000"
echo "   Pressione Ctrl+C para parar"
echo ""

python app.py
