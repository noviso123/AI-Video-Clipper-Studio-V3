
import os
import sys
import traceback

log_file = "status_tts.txt"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")
    print(msg)

if os.path.exists(log_file):
    os.remove(log_file)

log("Checking TTS environment...")

try:
    base_dir = os.getcwd()
    model_path = os.path.join(base_dir, 'models', 'kokoro', 'kokoro-v0_19.onnx')
    voices_path = os.path.join(base_dir, 'models', 'kokoro', 'voices.bin')

    if not os.path.exists(model_path):
        log(f"❌ Model missing: {model_path}")
        sys.exit(1)
    else:
        log(f"✅ Model found: {os.path.getsize(model_path)} bytes")

    if not os.path.exists(voices_path):
        log(f"❌ Voices missing: {voices_path}")
        sys.exit(1)
    else:
        log(f"✅ Voices found: {os.path.getsize(voices_path)} bytes")

    log("Importing kokoro_onnx...")
    from kokoro_onnx import Kokoro
    import soundfile as sf
    log("✅ kokoro-onnx imported successfully")
    
    kokoro = Kokoro(model_path, voices_path)
    log("✅ Kokoro initialized")
    
    text = "Teste de voz."
    samples, rate = kokoro.create(text, voice="am_michael", speed=1.0, lang="pt-br")
    log(f"✅ Audio generated: {len(samples)} samples @ {rate}Hz")
    
    sf.write('test_tts.wav', samples, rate)
    log("✅ Audio saved to test_tts.wav")
    
except Exception as e:
    log(f"❌ Error: {e}")
    log(traceback.format_exc())
    sys.exit(1)
