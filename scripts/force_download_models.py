"""
Script de Download Forçado de Modelos (SSL Bypass)
Baixa o modelo Whisper e salva localmente para uso OFF-LIVE.
"""
import os
import requests
from pathlib import Path
from tqdm import tqdm

# Desativar avisos de SSL inseguro
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Config
MODEL_ID = "Systran/faster-distil-whisper-large-v3"
LOCAL_DIR = Path("models/faster-distil-whisper-large-v3")

# Arquivos necessários para CTranslate2/Faster-Whisper
FILES_TO_DOWNLOAD = [
    "config.json",
    "model.bin",
    "preprocessor_config.json",
    "tokenizer.json",
    "vocabulary.txt"
]

def download_file(url, local_path):
    response = requests.get(url, stream=True, verify=False) # <--- O SEGREDO (verify=False)
    total_size = int(response.headers.get('content-length', 0))

    with open(local_path, 'wb') as file, tqdm(
        desc=local_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def main():
    print(f"🚀 Iniciando download para: {LOCAL_DIR}")
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    base_url = f"https://huggingface.co/{MODEL_ID}/resolve/main"

    for filename in FILES_TO_DOWNLOAD:
        file_url = f"{base_url}/{filename}"
        local_path = LOCAL_DIR / filename

        if local_path.exists() and local_path.stat().st_size > 0:
            print(f"✅ {filename} já existe. Pulando.")
            continue

        print(f"⬇️ Baixando {filename}...")
        try:
            download_file(file_url, local_path)
            print(f"✅ Sucesso: {filename}")
        except Exception as e:
            print(f"❌ Falha ao baixar {filename}: {e}")

    print("\n📦 Download concluído!")
    print(f"📂 Caminho do modelo: {LOCAL_DIR.absolute()}")
    print("👉 Agora o Clipper vai carregar deste diretório localmente.")

if __name__ == "__main__":
    main()
