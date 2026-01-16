import requests
import time
import sys

def test_voice_generation():
    url = "http://127.0.0.1:5000/api/voice/test"
    payload = {
        "text": "Olá! Este é um teste automatizado do sistema de voz híbrido. Verificando capacidade offline e online."
    }

    print(f"Testing {url}...")
    try:
        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            print("✅ Success! API returned 200 OK.")
            print("Response:", response.json())
            return True
        else:
            print(f"❌ Failed! Status Code: {response.status_code}")
            print("Response:", response.text)
            return False

    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

if __name__ == "__main__":
    if test_voice_generation():
        sys.exit(0)
    else:
        sys.exit(1)
