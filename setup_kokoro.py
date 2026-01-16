import os
import requests
import json

BASE_DIR = os.getcwd()
KOKORO_DIR = os.path.join(BASE_DIR, 'models', 'kokoro')
os.makedirs(KOKORO_DIR, exist_ok=True)

def download_file(url, target_path):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, stream=True, verify=False)
        if response.status_code == 200:
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Done.")
        else:
            print(f"Failed to download {url}: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def setup_kokoro():
    # 1. Download Model (v0.19 ONNX)
    model_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
    model_path = os.path.join(KOKORO_DIR, 'kokoro-v0_19.onnx')

    if not os.path.exists(model_path):
        download_file(model_url, model_path)
    else:
        print("Model already exists.")

    # 2. Download Voices BIN
    voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin"
    voices_path = os.path.join(KOKORO_DIR, 'voices.bin')

    if not os.path.exists(voices_path):
        download_file(voices_url, voices_path)
    else:
        print("Voices JSON already exists.")

if __name__ == "__main__":
    setup_kokoro()
