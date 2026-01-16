from kokoro_onnx import Kokoro
import os

onnx_path = "models/kokoro/kokoro-v0_19.onnx"
voices_path = "models/kokoro/voices.bin"

if os.path.exists(onnx_path) and os.path.exists(voices_path):
    kokoro = Kokoro(onnx_path, voices_path)
    test_text = "Olá, testando o sotaque."

    langs = ["pt", "pt-br", "pt-pt", "es", "en-us"]
    for l in langs:
        try:
            # Inspecting phonemes (internal access usually)
            # Actually, let's just see if it errors or what it prints
            phonemes = kokoro.tokenizer.phonemize(test_text, l)
            print(f"Lang: {l} -> Phonemes: {phonemes[:50]}")
        except Exception as e:
            print(f"Lang: {l} -> Failed: {e}")
else:
    print("Files missing")
