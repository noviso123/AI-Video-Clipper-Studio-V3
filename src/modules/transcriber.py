"""
Módulo de Transcrição (Whisper tiny com timestamps de palavras)
Retorna transcrição precisa com timing de cada palavra.
"""
import logging
from pathlib import Path
from typing import List, Dict
from ..core.logger import setup_logger

logger = setup_logger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.error("❌ Whisper não instalado! Execute: pip install openai-whisper")


class AudioTranscriber:
    """Transcritor com Whisper (tiny) e timestamps de palavras."""

    def __init__(self, model_name: str = "tiny"):
        if not WHISPER_AVAILABLE:
            raise RuntimeError(
                "❌ Whisper não está instalado!\n"
                "Execute: pip install openai-whisper"
            )

        self.model_name = model_name
        logger.info(f"🚀 Carregando Whisper ({model_name})...")
        self.model = whisper.load_model(model_name)
        logger.info(f"✅ Whisper carregado: {model_name}")

    def transcribe(self, audio_path: Path) -> List[Dict]:
        """
        Transcreve áudio com Whisper retornando timestamps precisos.
        Retorna lista de segmentos com palavras e seus timestamps.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"❌ Áudio não encontrado: {audio_path}")

        logger.info(f"🎤 Transcrevendo: {audio_path.name}")
        logger.info("   ⚡ Usando Whisper com timestamps de palavras...")

        # Transcrever com word_timestamps=True para precisão
        result = self.model.transcribe(
            str(audio_path),
            language="pt",
            verbose=False,
            word_timestamps=True  # <-- IMPORTANTE: timestamps de palavras
        )

        segments = []
        for seg in result.get("segments", []):
            segment_data = {
                "text": seg["text"].strip(),
                "start": seg["start"],
                "end": seg["end"],
                "words": []
            }

            # Extrair palavras com timestamps precisos
            if "words" in seg:
                for word_info in seg["words"]:
                    segment_data["words"].append({
                        "word": word_info.get("word", "").strip(),
                        "start": word_info.get("start", 0),
                        "end": word_info.get("end", 0),
                        "probability": word_info.get("probability", 1.0)
                    })

            segments.append(segment_data)

        total_words = sum(len(s.get("words", [])) for s in segments)
        logger.info(f"✅ Transcrição: {len(segments)} segmentos, {total_words} palavras")
        return segments

    def get_words_for_clip(self, segments: List[Dict], clip_start: float, clip_end: float) -> List[Dict]:
        """
        Extrai todas as palavras dentro do intervalo do clip.
        Ajusta timestamps para serem relativos ao início do clip.
        """
        words = []

        for segment in segments:
            # Verificar se segmento está no intervalo
            if segment["end"] < clip_start or segment["start"] > clip_end:
                continue

            # Se tem palavras individuais, usar elas
            if segment.get("words"):
                for w in segment["words"]:
                    w_start = w["start"]
                    w_end = w["end"]

                    # Palavra está no intervalo do clip?
                    if w_start >= clip_start and w_end <= clip_end:
                        words.append({
                            "word": w["word"],
                            "start": w_start - clip_start,  # Relativo ao clip
                            "end": w_end - clip_start,
                            "probability": w.get("probability", 1.0)
                        })
            else:
                # Fallback: dividir texto em palavras com timing estimado
                text_words = segment["text"].split()
                if text_words:
                    duration = segment["end"] - segment["start"]
                    word_duration = duration / len(text_words)

                    for i, word in enumerate(text_words):
                        w_start = segment["start"] + (i * word_duration)
                        w_end = w_start + word_duration

                        if w_start >= clip_start and w_end <= clip_end:
                            words.append({
                                "word": word,
                                "start": w_start - clip_start,
                                "end": w_end - clip_start,
                                "probability": 0.7  # Estimado
                            })

        return words
