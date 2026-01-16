from kokoro_onnx import Kokoro
import soundfile as sf
import os
import numpy as np

# Monkeypatch verify fix
# _old_load = np.load
# np.load = lambda *a,**k: _old_load(*a, allow_pickle=True, **k)

try:
    # Pointing to voices.bin
    kokoro = Kokoro("models/kokoro/kokoro-v0_19.onnx", "models/kokoro/voices.bin")
    text = "Olá, isto é um teste da voz Kokoro falando em português."
    print("Generating...")
    # Using 'bm_lewis' as generic male
    samples, sample_rate = kokoro.create(text, voice="bm_lewis", speed=1.0, lang="pt-br")
    sf.write("test_kokoro.wav", samples, sample_rate)
    print("Success! Saved test_kokoro.wav")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
