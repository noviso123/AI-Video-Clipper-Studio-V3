import os
import requests
from pathlib import Path

def download_file(url, output_path):
    print(f"⬇️ Baixando {output_path.name}...")
    try:
        response = requests.get(url, verify=False) # Ignorar erro SSL (Zscaler, etc)
        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print("✅ Sucesso!")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Falha crítica: {e}")
        return False

def main():
    fonts_dir = Path("src/assets/fonts")
    fonts_dir.mkdir(parents=True, exist_ok=True)

    # Anton (Google Fonts - Similar to Impact)
    url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    output = fonts_dir / "Anton-Regular.ttf"

    if not output.exists():
        download_file(url, output)
    else:
        print("✅ Fonte Oswald-Bold já existe.")

if __name__ == "__main__":
    main()
