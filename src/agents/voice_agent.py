"""
Agente de Voz (Fase 17)
Gera narrações usando Edge-TTS (Gratuito) ou ElevenLabs (Premium).
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional, List
import edge_tts

logger = logging.getLogger(__name__)

class VoiceAgent:
    """
    Gerencia a síntese de voz para o vídeo.
    """

    # Vozes recomendadas do Edge-TTS (Português)
    VOICES = {
        'male': 'pt-BR-AntonioNeural',
        'female': 'pt-BR-FranciscaNeural'
    }

    def __init__(self):
        logger.info("🎙️ Agente de Voz: Inicializado (Backend: Edge-TTS)")

    async def _generate_audio_async(self, text: str, voice: str, output_path: Path) -> bool:
        """Gera áudio assincronamente"""
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            logger.error(f"❌ Erro na geração de voz: {e}")
            return False

    def generate_narration(self, text: str, output_path: Path, gender: str = 'male') -> Optional[Path]:
        """
        Gera um arquivo de áudio com a narração.

        Args:
            text: Texto para narrar
            output_path: Caminho para salvar o mp3
            gender: 'male' ou 'female'

        Returns:
            Path do arquivo gerado ou None se falhar
        """
        voice = self.VOICES.get(gender, self.VOICES['male'])
        logger.info(f"🎙️ Gerando narração ({voice}): '{text[:30]}...'")

        try:
            # Executar função async em contexto sync
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self._generate_audio_async(text, voice, output_path))
            loop.close()

            if success:
                logger.info(f"   ✅ Áudio salvo: {output_path.name}")
                return output_path
            return None

        except Exception as e:
            logger.error(f"❌ Falha fatal no Voice Agent: {e}")
            return None

    def get_available_voices(self) -> List[str]:
        """Retorna lista de vozes disponíveis (simulado por enquanto)"""
        return list(self.VOICES.values())
