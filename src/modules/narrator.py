"""
Módulo de Narração Simplificado (Stage 4.5)
100% OFFLINE - Português Brasileiro.
"""
import logging
from pathlib import Path
from gtts import gTTS
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class VoiceNarrator:
    """Gerador de voz simples e robusto para narrações curtas."""

    def __init__(self):
        self.lang = 'pt'
        self.tld = 'com.br'

    def generate_narration(self, text: str, output_path: Path) -> bool:
        """Gera áudio em PT-BR usando gTTS (Simples e Eficaz)."""
        try:
            logger.info(f"🎙️ Gerando narração (PT-BR): '{text[:30]}...'")
            tts = gTTS(text=text, lang=self.lang, tld=self.tld, slow=False)
            tts.save(str(output_path))
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao gerar voz: {e}")
            return False

def get_narrator():
    return VoiceNarrator()
