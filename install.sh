#!/bin/bash
# ============================================
# AI Video Clipper V3 - Instalador Linux
# Funciona em: Ubuntu, Fedora, Bazzite, etc
# ============================================

set -e  # Parar em caso de erro

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🎬 AI VIDEO CLIPPER V3 - INSTALAÇÃO AUTOMÁTICA 🎬       ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Este script vai:                                           ║"
echo "║  1. Verificar Python                                        ║"
echo "║  2. Instalar FFmpeg (se necessário)                         ║"
echo "║  3. Criar ambiente virtual                                  ║"
echo "║  4. Instalar todas as dependências                          ║"
echo "║  5. Baixar modelo VOSK PT-BR (~50MB)                        ║"
echo "║  6. Configurar o sistema                                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ========================================
# 1. VERIFICAR PYTHON
# ========================================
echo "[1/6] 🔍 Verificando Python..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "❌ ERRO: Python não encontrado!"
    echo ""
    echo "Para instalar Python:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora/Bazzite: sudo dnf install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

$PYTHON_CMD --version
echo "✅ Python encontrado!"

# ========================================
# 2. VERIFICAR/INSTALAR FFMPEG
# ========================================
echo ""
echo "[2/6] 🎥 Verificando FFmpeg..."

if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg não encontrado. Tentando instalar..."

    # Detectar distro
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ffmpeg
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y ffmpeg
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm ffmpeg
    elif command -v rpm-ostree &> /dev/null; then
        # Bazzite/Fedora Silverblue
        echo "📦 Detectado sistema imutável (Bazzite/Silverblue)"
        echo "   Instalando FFmpeg via rpm-ostree (requer reboot)..."
        sudo rpm-ostree install ffmpeg || echo "⚠️ FFmpeg pode já estar instalado"
    else
        echo "❌ Não foi possível instalar FFmpeg automaticamente."
        echo "   Por favor, instale manualmente."
        exit 1
    fi
fi

ffmpeg -version | head -1
echo "✅ FFmpeg OK!"

# ========================================
# 3. CRIAR AMBIENTE VIRTUAL
# ========================================
echo ""
echo "[3/6] 📦 Criando ambiente virtual..."

if [ ! -d ".venv" ]; then
    $PYTHON_CMD -m venv .venv
    echo "✅ Ambiente virtual criado!"
else
    echo "⏭️ Ambiente virtual já existe."
fi

# Ativar ambiente
source .venv/bin/activate

# ========================================
# 4. INSTALAR DEPENDÊNCIAS
# ========================================
echo ""
echo "[4/6] 📥 Instalando dependências..."

# Atualizar pip
pip install --upgrade pip --quiet

# Instalar PyTorch CPU (mais leve)
echo "   ⚡ Instalando PyTorch CPU..."
pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet 2>/dev/null || pip install torch --quiet

# Instalar dependências
echo "   📚 Instalando bibliotecas..."
pip install -r requirements.txt --quiet

echo "✅ Dependências instaladas!"

# ========================================
# 5. BAIXAR MODELOS
# ========================================
echo ""
echo "[5/6] 🧠 Baixando modelo VOSK PT-BR (~50MB)..."

$PYTHON_CMD download_models.py

echo "✅ Modelo baixado!"

# ========================================
# 6. CONFIGURAR
# ========================================
echo ""
echo "[6/6] ⚙️ Configurando ambiente..."

if [ ! -f ".env" ]; then
    cp ".env.example" ".env" 2>/dev/null || echo "# Config vazia" > .env
    echo "✅ Arquivo .env criado!"
else
    echo "⏭️ Arquivo .env já existe."
fi

# Criar pastas
mkdir -p exports temp logs

# Tornar scripts executáveis
chmod +x *.sh 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO! ✅            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  Para iniciar o sistema:                                     ║"
echo "║  $ ./start.sh                                                ║"
echo "║  ou                                                          ║"
echo "║  $ source .venv/bin/activate && python app.py                ║"
echo "║                                                              ║"
echo "║  Acesse: http://localhost:5000                              ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
