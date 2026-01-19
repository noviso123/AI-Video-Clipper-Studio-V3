"""
Agente de Voz (Offline Wrapper)
Redireciona para o VoiceNarrator (Kokoro TTS)
"""
import logging
from pathlib import Path
from typing import Optional, List
from ..modules.narrator import get_narrator

logger = logging.getLogger(__name__)

class VoiceAgent:
    """Wrapper para o sistema de narração offline"""

    def __init__(self):
        logger.info("🎙️ Agente de Voz: Inicializado (Backend: Kokoro Offline)")
        self.narrator = get_narrator()

    def generate_narration(self, text: str, output_path: Path, gender: str = 'male') -> Optional[Path]:
        """Gera narração usando Kokoro"""
        
        # Mapear gênero para voz do Kokoro
        voice_map = {
            'male': 'am_michael',
            'female': 'af_bella'
        }
        voice = voice_map.get(gender, 'am_michael')
        
        # Como o narrator.generate_narration usa "neutral" ou config interna, 
        # vamos usar o método interno _generate_kokoro se quisermos forçar uma voz específica,
        # ou usar a API pública. A API pública é mais segura.
        
        # Se o narrador já tem uma voz customizada, ele vai usar ela independente do gênero pedido aqui.
        # Se não, ele usa a neutral. Vamos tentar forçar o gênero se não tiver custom.
        
        try:
            if self.narrator.has_custom_voice:
                success = self.narrator.generate_narration(text, output_path)
            else:
                # Acesso direto ao método interno para escolher voz específica do Kokoro
                success = self.narrator._generate_kokoro(text, str(output_path), voice=voice)
                
            if success:
                logger.info(f"   ✅ Áudio salvo (Kokoro): {output_path.name}")
                return output_path
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de voz: {e}")
            return None

    def get_available_voices(self) -> List[str]:
        return list(self.narrator.VOICES.keys())
