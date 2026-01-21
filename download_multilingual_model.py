"""
Download Multilingual Whisper Model (large-v3 - supports Portuguese)
Manual download with SSL bypass for corporate networks.
"""
import os
import ssl
import urllib3
import requests
from pathlib import Path
from tqdm import tqdm

# Disable ALL SSL verification
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Model files for Systran/faster-whisper-large-v3
MODEL_REPO = "Systran/faster-whisper-large-v3"
LOCAL_DIR = Path("models/faster-whisper-large-v3")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

# Essential model files
FILES = [
    "config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.json",
    "vocabulary.txt"
]

def download_file(filename):
    """Download a single file with progress bar"""
    url = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{filename}"
    local_path = LOCAL_DIR / filename

    if local_path.exists():
        print(f"⏭️ {filename} already exists, skipping...")
        return True

    print(f"⬇️ Downloading: {filename}")
    try:
        response = requests.get(url, stream=True, verify=False, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(local_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"✅ {filename} downloaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

print(f"🌍 Downloading multilingual model: {MODEL_REPO}")
print(f"📂 Destination: {LOCAL_DIR}")
print("⏳ This is ~3GB, please wait...\n")

success_count = 0
for file in FILES:
    if download_file(file):
        success_count += 1

print(f"\n{'='*50}")
if success_count == len(FILES):
    print("🎉 All files downloaded successfully!")
    print("🇧🇷 Portuguese transcription is now supported!")
else:
    print(f"⚠️ Downloaded {success_count}/{len(FILES)} files.")
    print("Some files may need to be re-downloaded.")
