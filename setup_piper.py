import os
import requests
import zipfile
import io

BASE_DIR = os.getcwd()
PIPER_DIR = os.path.join(BASE_DIR, 'bin', 'piper')
MODELS_DIR = os.path.join(BASE_DIR, 'models', 'piper')

os.makedirs(PIPER_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

def download_file(url, target_path):
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True, verify=False)
    if response.status_code == 200:
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Done.")
    else:
        print(f"Failed to download {url}")

def setup_piper():
    # 1. Download Piper Binary (Windows)
    # Using a known working release asset
    piper_url = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
    zip_path = os.path.join(PIPER_DIR, 'piper.zip')

    if not os.path.exists(os.path.join(PIPER_DIR, 'piper.exe')):
        download_file(piper_url, zip_path)
        print("Extracting Piper...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(PIPER_DIR)) # Extracts to bin/piper/piper/... usually

        # Adjust path if needed (move files up if nested)
        # Often extracts as piper/piper.exe. Let's verify structure later or just find it.
    else:
        print("Piper already installed.")

    # 2. Download PT-BR Model (Faber - Medium)
    model_name = "pt_BR-faber-medium"
    onnx_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/{model_name}.onnx?download=true"
    json_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/{model_name}.onnx.json?download=true"

    download_file(onnx_url, os.path.join(MODELS_DIR, f"{model_name}.onnx"))
    download_file(json_url, os.path.join(MODELS_DIR, f"{model_name}.onnx.json"))

if __name__ == "__main__":
    setup_piper()
