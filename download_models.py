#!/usr/bin/env python3
"""
AI Video Clipper V3 - Download de Modelos
Baixa o modelo VOSK para Português Brasileiro.
"""
import os
import sys
import ssl
import zipfile
from pathlib import Path

# Bypass SSL
os.environ["PYTHONHTTPSVERIFY"] = "0"
ssl._create_default_https_context = ssl._create_unverified_context

import requests
from tqdm import tqdm

# ====================================
# CONFIGURAÇÃO
# ====================================

VOSK_MODEL = {
    "name": "vosk-model-small-pt-0.3",
    "url": "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip",
    "size": "50MB",
    "description": "VOSK Português Brasileiro (leve e rápido)"
}

def download_file(url: str, dest: Path, desc: str = None) -> bool:
    """Baixa um arquivo com barra de progresso"""
    try:
        response = requests.get(url, stream=True, verify=False, timeout=600)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(dest, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=desc or dest.name, ncols=80) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("🧠 AI VIDEO CLIPPER V3 - DOWNLOAD DE MODELOS")
    print("   Usando VOSK (leve, confiável, PT-BR nativo)")
    print("=" * 60)

    # Criar pasta models
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / VOSK_MODEL["name"]

    # Verificar se já existe
    if model_path.exists():
        print(f"\n✅ Modelo já instalado: {model_path}")
        return 0

    print(f"\n🌍 Baixando: {VOSK_MODEL['description']}")
    print(f"   Tamanho: ~{VOSK_MODEL['size']}")

    zip_path = models_dir / "vosk-pt.zip"

    # Baixar
    if not download_file(VOSK_MODEL["url"], zip_path, "   Download"):
        return 1

    # Extrair
    print("\n📦 Extraindo modelo...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        zip_path.unlink()  # Limpar zip
        print(f"✅ Modelo extraído para: {model_path}")
    except Exception as e:
        print(f"❌ Erro ao extrair: {e}")
        return 1

    print("\n" + "=" * 60)
    print("✅ MODELO VOSK PT-BR INSTALADO COM SUCESSO!")
    print("🇧🇷 Transcrição em Português Brasileiro pronta!")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
