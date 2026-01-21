"""
Script de Configuração Automática para Google Colab
- Instala dependências do sistema (FFmpeg, ImageMagick, Node.js)
- Instala/Inicia Ollama (IA Local)
- Configura Fontes e Assets
"""
import os
import subprocess
import time
import requests
from pathlib import Path
import shutil
import platform

# Configurações
BASE_DIR = Path("/content/AI-Video-Clipper-Studio-V3")  # Caminho padrão no Colab
FONTS_DIR = BASE_DIR / "src/assets/fonts"
FONTS_URLS = {
    "Anton-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
    "Oswald-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf"
}

def run_command(command, desc):
    print(f"🚀 {desc}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {desc} conclúido!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {desc}: {e}")

def setup_system():
    print("🔧 Configurando Sistema...")

    # 1. Update e Instalação de Deps
    run_command("apt-get update -qq", "Atualizando APT")
    run_command("apt-get install -y ffmpeg imagemagick ghostscript", "Instalando FFmpeg e ImageMagick")

    # 2. Fix ImageMagick Policy (Para MoviePy)
    # Remove restrições de segurança que impedem edição de texto
    run_command("sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml", "Aplicando Patch no ImageMagick")

def setup_python():
    print("🐍 Configurando Python...")
    run_command("pip install -r colab_requirements.txt", "Instalando Requirements")

def setup_ollama():
    print("🦙 Configurando Ollama (IA Local)...")

    # Verifica se já está instalado
    if not shutil.which("ollama"):
        run_command("curl -fsSL https://ollama.com/install.sh | sh", "Instalando Ollama")

    # Iniciar servidor em background
    print("⏳ Iniciando servidor Ollama...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)  # Esperar inicialização

    # Puxar o modelo (Llama3)
    try:
        run_command("ollama pull llama3", "Baixando Modelo Llama3")
    except:
        print("⚠️ Falha ao baixar llama3. O script tentará novamente durante a execução.")

def setup_assets():
    print("🎨 Configurando Assets (Fontes)...")
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in FONTS_URLS.items():
        path = FONTS_DIR / name
        if not path.exists():
            print(f"⬇️ Baixando fonte: {name}")
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(path, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                print(f"⚠️ Erro ao baixar fonte {name}: {e}")

def main():
    print("=== AUTO SETUP GOOGLE COLAB ===")

    # Check Platform
    if platform.system() == "Windows":
        print("⚠️ Este script foi otimizado para Google Colab (Linux).")
        print("   No Windows, certifique-se de instalar FFmpeg, Node.js e Ollama manualmente.")
        print("   Pulando instalação de dependências do sistema...")
        setup_python()
        setup_assets()
        return

    start_time = time.time()

    setup_system()
    setup_python()
    setup_ollama()
    setup_assets()

    print(f"\n✨ Setup Finalizado em {time.time() - start_time:.1f}s!")
    print("👉 Agora você pode rodar: !python main.py ...")

if __name__ == "__main__":
    main()
