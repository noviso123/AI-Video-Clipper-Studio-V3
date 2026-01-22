#!/bin/bash

# ============================================================
# Setup Google Colab Environment for AI-Video-Clipper-Studio-V3
# Versão: 2.0 - Compatibilidade Total com Cloud
# ============================================================

echo "☁️  Iniciando Setup do Ambiente Google Colab..."
echo "📅 $(date)"

# 1. Atualizar e instalar dependências do sistema
echo ""
echo "📦 [1/6] Instalando dependências do sistema..."
apt-get update -qq
apt-get install -y -qq wget curl unzip libnss3 libgconf-2-4 libxi6 libgbm-dev ffmpeg libxss1 libasound2

# 2. Instalar Google Chrome (Versão Estável)
echo ""
echo "🌐 [2/6] Instalando Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt install -y -qq ./google-chrome-stable_current_amd64.deb
    rm google-chrome-stable_current_amd64.deb
    echo "   ✅ Google Chrome instalado!"
else
    echo "   ✅ Google Chrome já instalado."
fi

# 3. Instalar dependências Python para TODAS as plataformas (Versão Ultimate)
echo ""
echo "🐍 [3/6] Instalando pacotes Python..."
pip install -q undetected-chromedriver selenium webdriver-manager
pip install -q moviepy vosk pydantic pydub python-telegram-bot
pip install -q google-auth-oauthlib google-api-python-client google-generativeai
pip install -q instagrapi flask flask-cors pyngrok python-dotenv # Cloud & Web
pip install -q tiktok-uploader agno # Para TikTok e Agentes
pip install -q pillow numpy opencv-python psutil

# 4. Criar estrutura de pastas, baixar fontes e MODELOS DE IA
echo ""
echo "📁 [4/6] Configurando Assets e Modelos de IA..."
mkdir -p browser_profiles/cookies
mkdir -p temp
mkdir -p exports
mkdir -p assets/fonts
mkdir -p models

# Download Fontes Viral
wget -q https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf -O assets/fonts/Oswald-Bold.ttf
wget -q https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf -O assets/fonts/Montserrat-ExtraBold.ttf

# Auto-Download Vosk Model (Small PT) se necessário
if [ ! -d "models/vosk-model-small-pt-0.3" ]; then
    echo "   🎙️ Baixando modelo de voz Vosk PT-BR..."
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
    unzip -q vosk-model-small-pt-0.3.zip -d models/
    rm vosk-model-small-pt-0.3.zip
    echo "   ✅ Modelo Vosk instalado!"
fi
echo "   ✅ Fontes premium instaladas!"

# 5. Criar chrome_wrapper.sh otimizado para Colab
echo ""
echo "🔧 [5/6] Criando chrome_wrapper.sh..."
cat <<'EOF' > chrome_wrapper.sh
#!/bin/bash
# Chrome Wrapper otimizado para Google Colab
google-chrome \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-software-rasterizer \
    --headless=new \
    --remote-debugging-port=9222 \
    --window-size=1920,1080 \
    --disable-extensions \
    --disable-notifications \
    --disable-infobars \
    --disable-popup-blocking \
    "$@"
EOF
chmod +x chrome_wrapper.sh

# 6. Verificar instalação
echo ""
echo "✅ [6/6] Verificando instalação..."
echo "   Chrome: $(google-chrome --version 2>/dev/null || echo 'Não encontrado')"
echo "   Python: $(python --version 2>/dev/null || echo 'Não encontrado')"

echo ""
echo "============================================================"
echo "✨ SETUP NUCLEAR CONCLUÍDO COM SUCESSO!"
echo "============================================================"
echo ""
echo "📋 Próximos passos:"
echo "   1. O Maestro (run_ultimate_cloud.py) iniciará tudo automaticamente."
echo "   2. O robô postará em 3 redes simultaneamente."
echo ""
