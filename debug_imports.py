import sys
import os

print("🔍 Iniciando Diagnóstico de Imports...")
print(f"🐍 Python: {sys.version}")
print(f"📂 CWD: {os.getcwd()}")

modules = [
    "cv2",
    "moviepy.editor",
    "kokoro_onnx",
    "soundfile",
    "flask",
    "faster_whisper",
    "PIL"
]

print("\n📦 Testando bibliotecas críticas:")
for mod in modules:
    try:
        __import__(mod)
        print(f"   ✅ {mod}: OK")
    except ImportError as e:
        print(f"   ❌ {mod}: FALHA ({e})")
    except Exception as e:
        print(f"   ⚠️ {mod}: ERRO GENÉRICO ({e})")

print("\n🚀 Teste concluído. Se houver falhas acima, o app.py não iniciará.")
