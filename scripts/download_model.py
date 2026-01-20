import os
import requests
import zipfile
import shutil
from pathlib import Path
from tqdm import tqdm

# Configurações
MODEL_VERSION = "vosk-model-small-pt-0.3"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_VERSION}.zip"
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
ZIP_PATH = MODELS_DIR / f"{MODEL_VERSION}.zip"

def download_file(url, filename):
    response = requests.get(url, stream=True, verify=False)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

def setup_vosk():
    print("🎤 Configurando modelo Vosk (Transcrição Offline)...")

    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(parents=True)

    # Verifica se já existe o modelo descompactado (qualquer pasta começando com vosk-model)
    existing_models = [d for d in MODELS_DIR.iterdir() if d.is_dir() and "vosk-model" in d.name]
    if existing_models:
        print(f"✅ Modelo já instalado: {existing_models[0].name}")
        return

    print(f"⬇️ Baixando modelo: {MODEL_VERSION}...")
    try:
        download_file(MODEL_URL, ZIP_PATH)

        print("📦 Extraindo...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(MODELS_DIR)

        # Limpeza
        os.remove(ZIP_PATH)
        print("✅ Modelo instalado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao baixar modelo: {e}")

if __name__ == "__main__":
    setup_vosk()
