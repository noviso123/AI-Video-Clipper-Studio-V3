#!/bin/bash

# ============================================================
# AI VIDEO CLIPPER - Setup Universal (Linux/macOS)
# ============================================================

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}  AI VIDEO CLIPPER - Setup Automático${NC}"
echo -e "${YELLOW}============================================================${NC}"

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERRO] Python 3 não encontrado!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Python encontrado: $(python3 --version)${NC}"

# 2. Verificar FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[AVISO] FFmpeg não encontrado no sistema!${NC}"
    echo -e "O sistema tentará usar a versão injetada via Python (imageio-ffmpeg)."
    
    # Dica de instalação baseada na distro
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v dnf &> /dev/null; then
            echo -e "Dica (Bazzite/Fedora): ${CYAN}sudo dnf install ffmpeg${NC}"
        elif command -v apt &> /dev/null; then
            echo -e "Dica (Ubuntu/Debian): ${CYAN}sudo apt install ffmpeg${NC}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "Dica (macOS): ${CYAN}brew install ffmpeg${NC}"
    fi
else
    echo -e "${GREEN}[OK] FFmpeg encontrado no sistema${NC}"
fi

# 3. Criar Ambiente Virtual
if [ ! -d "venv" ]; then
    echo -e "\n[1/4] Criando ambiente virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERRO] Falha ao criar ambiente virtual${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Ambiente virtual criado${NC}"
else
    echo -e "${GREEN}[OK] Ambiente virtual já existe${NC}"
fi

# 4. Instalar Dependências
echo -e "\n[2/4] Instalando dependências..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERRO] Falha ao instalar dependências${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Dependências instaladas${NC}"

# 5. Configurar .env
if [ ! -f ".env" ]; then
    echo -e "\n[3/4] Criando arquivo .env..."
    cp .env.example .env
    echo -e "${GREEN}[OK] Arquivo .env criado${NC}"
fi

# 6. Criar Diretórios
echo -e "\n[4/4] Criando diretórios necessários..."
mkdir -p temp exports logs src/assets/fonts src/assets/overlays
echo -e "${GREEN}[OK] Diretórios criados${NC}"

# 7. Validar Instalação
echo -e "\n============================================================"
echo -e "Validando instalação..."
python3 tests/test_setup.py

echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}  SETUP CONCLUÍDO COM SUCESSO!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e "\nPara iniciar a interface web:"
echo -e "  ./run_web.sh"
echo -e "\nPara rodar via linha de comando:"
echo -e "  source venv/bin/activate"
echo -e "  python3 main.py --url \"URL_DO_YOUTUBE\""
echo ""
