"""
AI Video Clipper V3 - Módulo de Transcrição (OTIMIZADO)
VOSK com otimizações de velocidade para CPU.
"""
import os
import sys
import ssl
import json
import wave
import subprocess
from pathlib import Path
from typing import List, Dict
import logging
import time

logger = logging.getLogger(__name__)

# Bypass SSL
os.environ["PYTHONHTTPSVERIFY"] = "0"
ssl._create_default_https_context = ssl._create_unverified_context

# Importar VOSK
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("⚠️ VOSK não instalado. Execute: pip install vosk")


class AudioTranscriber:
    """Transcritor VOSK otimizado para velocidade."""

    def __init__(self, model_path: str = "models/vosk-model-small-pt-0.3"):
        if not VOSK_AVAILABLE:
            raise RuntimeError("❌ VOSK não encontrado! pip install vosk")

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            logger.info("📥 Baixando modelo VOSK PT-BR...")
            self._download_model()

        logger.info(f"🚀 Carregando VOSK (PT-BR, otimizado)...")
        self.model = Model(str(self.model_path))
        logger.info("✅ VOSK carregado!")

    def _download_model(self):
        """Baixa modelo VOSK automaticamente."""
        import requests
        import zipfile
        from tqdm import tqdm

        url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
        Path("models").mkdir(exist_ok=True)
        zip_path = Path("models/vosk-pt.zip")

        response = requests.get(url, stream=True, verify=False, timeout=300)
        total = int(response.headers.get('content-length', 0))

        with open(zip_path, 'wb') as f:
            with tqdm(total=total, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
                    pbar.update(len(chunk))

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall("models/")
        zip_path.unlink()

    def _convert_to_wav(self, audio_path: Path) -> Path:
        """Converte para WAV 16kHz mono (rápido)."""
        wav_path = audio_path.with_suffix('.wav')

        if wav_path.exists() and wav_path.stat().st_mtime > audio_path.stat().st_mtime:
            return wav_path

        logger.info("   🔄 Convertendo áudio (FFmpeg)...")

        # Otimização: usar threads do FFmpeg
        cmd = [
            'ffmpeg', '-y',
            '-threads', '0',  # Usar todas as threads
            '-i', str(audio_path),
            '-ar', '16000',
            '-ac', '1',
            '-acodec', 'pcm_s16le',  # Formato mais rápido
            '-f', 'wav',
            str(wav_path)
        ]

        subprocess.run(cmd, capture_output=True)
        return wav_path

    def transcribe(self, audio_path: Path) -> List[Dict]:
        """
        Transcrição OTIMIZADA para velocidade.
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"❌ Áudio não encontrado: {audio_path}")

        logger.info(f"🎤 Transcrevendo: {audio_path.name}")
        logger.info("   🇧🇷 Idioma: Português (VOSK otimizado)")

        start_time = time.time()

        # Converter para WAV
        wav_path = self._convert_to_wav(audio_path)

        convert_time = time.time() - start_time
        logger.info(f"   ⚡ Conversão: {convert_time:.1f}s")

        # Abrir WAV
        wf = wave.open(str(wav_path), "rb")
        file_duration = wf.getnframes() / wf.getframerate()

        logger.info(f"   📊 Duração: {file_duration/60:.1f} minutos")

        # Criar reconhecedor
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)

        # ===== OTIMIZAÇÕES =====
        # Buffer maior = menos chamadas de sistema = mais rápido
        BUFFER_SIZE = 32000

        results = []
        processed = 0
        total_frames = wf.getnframes()
        last_log = 0

        trans_start = time.time()

        while True:
            data = wf.readframes(BUFFER_SIZE)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('result'):
                    results.append(result)

            processed += len(data) // 2

            # Log de progresso a cada 10%
            progress = (processed / total_frames) * 100
            if progress - last_log >= 10:
                elapsed = time.time() - trans_start
                speed = (processed / wf.getframerate()) / elapsed if elapsed > 0 else 0
                logger.info(f"   📈 Progresso: {progress:.0f}% ({speed:.1f}x real-time)")
                last_log = progress

        # Resultado final
        final = json.loads(rec.FinalResult())
        if final.get('result'):
            results.append(final)

        wf.close()

        total_time = time.time() - trans_start
        speed_ratio = file_duration / total_time
        logger.info(f"   ✅ VOSK Core: {total_time:.1f}s ({speed_ratio:.1f}x real-time)")

        # Formatar segmentos
        formatted = self._format_segments(results)

        total_words = sum(len(s.get('words', [])) for s in formatted)
        logger.info(f"✅ {len(formatted)} segmentos, {total_words} palavras")

        return formatted

    def _format_segments(self, results: list) -> List[Dict]:
        """Formata resultados em segmentos."""
        formatted = []

        for result in results:
            if 'result' not in result:
                continue

            words = result['result']
            segment_words = []
            segment_start = None

            for w in words:
                if segment_start is None:
                    segment_start = w['start']

                segment_words.append({
                    "word": w['word'],
                    "start": w['start'],
                    "end": w['end'],
                    "confidence": w.get('conf', 1.0)
                })

                # Segmentos de ~10 segundos
                if (w['end'] - segment_start > 10) or len(segment_words) >= 30:
                    formatted.append({
                        "start": segment_start,
                        "end": w['end'],
                        "text": " ".join(x['word'] for x in segment_words),
                        "words": segment_words.copy()
                    })
                    segment_words = []
                    segment_start = None

            # Resto
            if segment_words:
                formatted.append({
                    "start": segment_start,
                    "end": segment_words[-1]['end'],
                    "text": " ".join(x['word'] for x in segment_words),
                    "words": segment_words
                })

        return formatted


def transcribe_audio(audio_path: str) -> List[Dict]:
    """Função de conveniência."""
    return AudioTranscriber().transcribe(Path(audio_path))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = transcribe_audio(sys.argv[1])
        for seg in result[:5]:
            print(f"[{seg['start']:.1f}s] {seg['text'][:80]}...")
