from src.modules.narrator import get_narrator
from pathlib import Path
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def test_tts():
    print("🚀 Testando Edge-TTS...")
    n = get_narrator()
    output = Path("test_voice_gen.mp3")

    if output.exists():
        output.unlink()

    success = n.generate_narration(
        "Olá! Esta é uma demonstração do novo sistema de narração ultra-rápido usando Edge TTS.",
        output
    )

    if success and output.exists():
        print(f"✅ Sucesso! Arquivo criado: {output} ({output.stat().st_size} bytes)")
    else:
        print("❌ Falha na geração.")

if __name__ == "__main__":
    test_tts()
