"""
AI Video Clipper V3 - Módulo de Transcrição
Usa VOSK para transcrição offline em Português Brasileiro.
VOSK é mais leve, confiável e funciona perfeitamente com PT-BR.
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

logger = logging.getLogger(__name__)

# Bypass SSL para redes corporativas
os.environ["PYTHONHTTPSVERIFY"] = "0"
ssl._create_default_https_context = ssl._create_unverified_context

# Tentar importar VOSK
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)  # Silenciar logs do Vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("⚠️ VOSK não instalado. Execute: pip install vosk")


class AudioTranscriber:
    """Transcritor usando VOSK (offline, leve, confiável)."""

    def __init__(self, model_path: str = "models/vosk-model-small-pt-0.3"):
        """
        Inicializa o modelo VOSK.

        Args:
            model_path: Caminho para o modelo VOSK de Português
        """
        if not VOSK_AVAILABLE:
            raise RuntimeError("❌ Biblioteca VOSK não encontrada! Execute: pip install vosk")

        self.model_path = Path(model_path)

        # Verificar se modelo existe
        if not self.model_path.exists():
            logger.info("📥 Modelo VOSK PT-BR não encontrado. Baixando...")
            self._download_model()

        logger.info(f"🚀 Carregando VOSK (Português Brasileiro)...")
        logger.info(f"   📂 Modelo: {self.model_path}")

        try:
            self.model = Model(str(self.model_path))
            logger.info("✅ Modelo VOSK carregado com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo VOSK: {e}")
            raise

    def _download_model(self):
        """Baixa o modelo VOSK de Português Brasileiro automaticamente."""
        import requests
        import zipfile
        from tqdm import tqdm

        url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
        zip_path = Path("models/vosk-pt.zip")

        # Criar pasta models
        Path("models").mkdir(exist_ok=True)

        logger.info(f"⬇️ Baixando modelo VOSK PT-BR (~50MB)...")

        try:
            response = requests.get(url, stream=True, verify=False, timeout=300)
            total_size = int(response.headers.get('content-length', 0))

            with open(zip_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Download") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            # Extrair
            logger.info("📦 Extraindo modelo...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("models/")

            # Limpar
            zip_path.unlink()
            logger.info("✅ Modelo VOSK PT-BR instalado!")

        except Exception as e:
            logger.error(f"❌ Erro ao baixar modelo: {e}")
            raise

    def _convert_to_wav(self, audio_path: Path) -> Path:
        """Converte áudio para WAV 16kHz mono (formato VOSK)."""
        wav_path = audio_path.with_suffix('.wav')

        if wav_path.exists():
            return wav_path

        logger.info(f"   🔄 Convertendo para WAV 16kHz...")

        cmd = [
            'ffmpeg', '-y', '-i', str(audio_path),
            '-ar', '16000',  # Sample rate 16kHz
            '-ac', '1',       # Mono
            '-f', 'wav',
            str(wav_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Erro FFmpeg: {result.stderr}")

        return wav_path

    def transcribe(self, audio_path: Path) -> List[Dict]:
        """
        Transcreve áudio usando VOSK.

        Args:
            audio_path: Caminho para o arquivo de áudio

        Returns:
            Lista de segmentos com texto e timestamps
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"❌ Áudio não encontrado: {audio_path}")

        logger.info(f"🎤 Transcrevendo: {audio_path.name}")
        logger.info("   🇧🇷 Idioma: Português Brasileiro (VOSK)")

        # Converter para WAV se necessário
        if audio_path.suffix.lower() != '.wav':
            wav_path = self._convert_to_wav(audio_path)
        else:
            wav_path = audio_path

        logger.info("   ⚡ Processando com VOSK (offline)...")

        # Abrir arquivo WAV
        wf = wave.open(str(wav_path), "rb")

        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            logger.warning("⚠️ Formato de áudio pode não ser ideal. Convertendo...")
            wf.close()
            wav_path = self._convert_to_wav(audio_path)
            wf = wave.open(str(wav_path), "rb")

        # Criar reconhecedor
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)  # Habilitar timestamps por palavra

        # Processar áudio
        results = []
        total_frames = wf.getnframes()
        processed_frames = 0

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('result'):
                    results.append(result)

            processed_frames += 4000

        # Resultado final
        final = json.loads(rec.FinalResult())
        if final.get('result'):
            results.append(final)

        wf.close()

        # Formatar segmentos
        formatted_segments = []

        for result in results:
            if 'result' in result:
                words = result['result']

                # Agrupar palavras em segmentos de ~10 segundos
                segment_words = []
                segment_start = None

                for word_info in words:
                    if segment_start is None:
                        segment_start = word_info['start']

                    segment_words.append({
                        "word": word_info['word'],
                        "start": word_info['start'],
                        "end": word_info['end'],
                        "confidence": word_info.get('conf', 1.0)
                    })

                    # Criar segmento a cada ~10 segundos ou 30 palavras
                    if (word_info['end'] - segment_start > 10) or len(segment_words) >= 30:
                        segment = {
                            "start": segment_start,
                            "end": word_info['end'],
                            "text": " ".join(w['word'] for w in segment_words),
                            "words": segment_words.copy()
                        }
                        formatted_segments.append(segment)
                        segment_words = []
                        segment_start = None

                # Segmento final
                if segment_words:
                    segment = {
                        "start": segment_start,
                        "end": segment_words[-1]['end'],
                        "text": " ".join(w['word'] for w in segment_words),
                        "words": segment_words
                    }
                    formatted_segments.append(segment)

        total_words = sum(len(s.get('words', [])) for s in formatted_segments)
        logger.info(f"✅ Transcrição concluída: {len(formatted_segments)} segmentos, {total_words} palavras")

        return formatted_segments


# Função de conveniência para uso direto
def transcribe_audio(audio_path: str, model_path: str = "models/vosk-model-small-pt-0.3") -> List[Dict]:
    """Transcreve áudio usando VOSK."""
    transcriber = AudioTranscriber(model_path)
    return transcriber.transcribe(Path(audio_path))


if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) > 1:
        result = transcribe_audio(sys.argv[1])
        for seg in result[:5]:
            print(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
    else:
        print("Uso: python transcriber.py <arquivo_audio>")
