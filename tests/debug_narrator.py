import sys
import os
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.modules.narrator import get_narrator

logging.basicConfig(level=logging.INFO)

def debug_narrator():
    print("🐛 Starting Narrator Debug...")

    narrator = get_narrator()
    print(f"🎤 Voice Profile Loaded: {narrator.has_custom_voice}")

    text = "Teste de depuração do sistema de voz híbrido."
    output = os.path.join(os.getcwd(), 'temp', 'debug_voice.mp3')

    def log_callback(msg):
        print(f"LOG: {msg}")

    print("🚀 Calling generate_narration...")
    try:
        success = narrator.generate_narration(text, output, log_callback=log_callback)

        if success:
            print("✅ SUCCESSO!")
        else:
            print("❌ FALHA (Return False)")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_narrator()
