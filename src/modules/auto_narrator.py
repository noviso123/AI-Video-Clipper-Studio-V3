"""
Módulo de Narração Automática
Detecta silêncios no vídeo e adiciona narração automaticamente.

Funcionalidades:
- Detecção de silêncios
- Geração de texto para narração baseado no contexto
- Síntese de voz (TTS)
- Mixagem de áudio
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SilenceSegment:
    """Segmento de silêncio detectado."""
    start: float
    end: float
    duration: float
    context_before: str = ""
    context_after: str = ""
    suggested_narration: str = ""


class SilenceDetector:
    """Detecta silêncios no áudio do vídeo."""
    
    def __init__(self, silence_threshold: float = 0.01, min_silence_duration: float = 1.0):
        """
        Args:
            silence_threshold: Limiar de volume para considerar silêncio (0-1)
            min_silence_duration: Duração mínima em segundos para considerar silêncio
        """
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        
        logger.info("🔇 Silence Detector: Inicializado")
        logger.info(f"   Threshold: {silence_threshold}")
        logger.info(f"   Duração mínima: {min_silence_duration}s")
    
    def detect_silences(self, video_path: Path) -> List[SilenceSegment]:
        """
        Detecta segmentos de silêncio no vídeo.
        
        Returns:
            Lista de SilenceSegment
        """
        logger.info(f"🔍 Detectando silêncios em: {video_path.name}")
        
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(str(video_path))
            
            if clip.audio is None:
                logger.warning("   ⚠️ Vídeo não tem áudio")
                clip.close()
                return []
            
            # Extrair áudio
            audio_array = clip.audio.to_soundarray(fps=22050)
            fps = 22050
            
            # Calcular volume por janela
            window_size = int(fps * 0.1)  # 100ms
            silences = []
            
            in_silence = False
            silence_start = 0
            
            for i in range(0, len(audio_array) - window_size, window_size):
                window = audio_array[i:i + window_size]
                volume = np.abs(window).mean()
                
                timestamp = i / fps
                
                if volume < self.silence_threshold:
                    if not in_silence:
                        in_silence = True
                        silence_start = timestamp
                else:
                    if in_silence:
                        silence_end = timestamp
                        duration = silence_end - silence_start
                        
                        if duration >= self.min_silence_duration:
                            silences.append(SilenceSegment(
                                start=silence_start,
                                end=silence_end,
                                duration=duration
                            ))
                        
                        in_silence = False
            
            # Verificar silêncio no final
            if in_silence:
                silence_end = len(audio_array) / fps
                duration = silence_end - silence_start
                
                if duration >= self.min_silence_duration:
                    silences.append(SilenceSegment(
                        start=silence_start,
                        end=silence_end,
                        duration=duration
                    ))
            
            clip.close()
            
            logger.info(f"   ✅ {len(silences)} silêncios detectados")
            for s in silences[:5]:  # Mostrar primeiros 5
                logger.info(f"      {s.start:.1f}s - {s.end:.1f}s ({s.duration:.1f}s)")
            
            return silences
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao detectar silêncios: {e}")
            return []


class NarrationGenerator:
    """Gera texto de narração baseado no contexto."""
    
    def __init__(self):
        logger.info("📝 Narration Generator: Inicializado")
    
    def generate_narration_text(
        self,
        silence: SilenceSegment,
        transcription: List[Dict] = None,
        video_context: str = ""
    ) -> str:
        """
        Gera texto de narração para um segmento de silêncio.
        
        Args:
            silence: Segmento de silêncio
            transcription: Transcrição do vídeo
            video_context: Contexto geral do vídeo
            
        Returns:
            Texto sugerido para narração
        """
        # Encontrar contexto antes e depois do silêncio
        context_before = ""
        context_after = ""
        
        if transcription:
            for segment in transcription:
                seg_end = segment.get('end', 0)
                seg_start = segment.get('start', 0)
                text = segment.get('text', '')
                
                # Contexto antes
                if seg_end <= silence.start and seg_end > silence.start - 5:
                    context_before = text
                
                # Contexto depois
                if seg_start >= silence.end and seg_start < silence.end + 5:
                    context_after = text
                    break
        
        silence.context_before = context_before
        silence.context_after = context_after
        
        # Gerar narração baseada no contexto
        # TODO: Usar LLM para gerar narração mais inteligente
        
        if context_before and context_after:
            narration = f"Continuando sobre {context_before[:50]}..."
        elif context_before:
            narration = "Vamos ver mais sobre isso..."
        else:
            narration = ""
        
        silence.suggested_narration = narration
        return narration


class TextToSpeech:
    """Converte texto em áudio de voz."""
    
    def __init__(self):
        self.available = False
        
        # Tentar importar bibliotecas de TTS
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.available = True
            self.method = 'pyttsx3'
            logger.info("🔊 Text-to-Speech: Inicializado (pyttsx3)")
        except:
            try:
                from gtts import gTTS
                self.available = True
                self.method = 'gtts'
                logger.info("🔊 Text-to-Speech: Inicializado (gTTS)")
            except:
                logger.warning("🔊 Text-to-Speech: Não disponível")
                self.method = None
    
    def synthesize(self, text: str, output_path: Path, language: str = 'pt-br') -> Optional[Path]:
        """
        Sintetiza texto em áudio.
        
        Args:
            text: Texto para sintetizar
            output_path: Caminho do arquivo de saída
            language: Idioma
            
        Returns:
            Caminho do arquivo de áudio ou None
        """
        if not self.available or not text:
            return None
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.method == 'pyttsx3':
                self.engine.save_to_file(text, str(output_path))
                self.engine.runAndWait()
                return output_path
            
            elif self.method == 'gtts':
                from gtts import gTTS
                tts = gTTS(text=text, lang=language[:2])
                tts.save(str(output_path))
                return output_path
            
        except Exception as e:
            logger.error(f"   ❌ Erro na síntese de voz: {e}")
            return None


class AutoNarrator:
    """Adiciona narração automática em silêncios do vídeo."""
    
    def __init__(self):
        self.silence_detector = SilenceDetector()
        self.narration_generator = NarrationGenerator()
        self.tts = TextToSpeech()
        
        logger.info("🎤 Auto Narrator: Inicializado")
    
    def process_video(
        self,
        video_path: Path,
        output_path: Path,
        transcription: List[Dict] = None,
        add_narration: bool = True
    ) -> Path:
        """
        Processa vídeo adicionando narração em silêncios.
        
        Args:
            video_path: Vídeo de entrada
            output_path: Vídeo de saída
            transcription: Transcrição do vídeo
            add_narration: Se deve adicionar narração
            
        Returns:
            Caminho do vídeo processado
        """
        logger.info(f"🎬 Processando narração automática: {video_path.name}")
        
        if not add_narration:
            return video_path
        
        # Detectar silêncios
        silences = self.silence_detector.detect_silences(video_path)
        
        if not silences:
            logger.info("   ℹ️ Nenhum silêncio significativo detectado")
            return video_path
        
        # Gerar narrações
        narrations = []
        for silence in silences:
            text = self.narration_generator.generate_narration_text(
                silence, transcription
            )
            if text:
                narrations.append((silence, text))
        
        if not narrations:
            logger.info("   ℹ️ Nenhuma narração gerada")
            return video_path
        
        # Sintetizar e mixar
        if not self.tts.available:
            logger.warning("   ⚠️ TTS não disponível, pulando narração")
            return video_path
        
        # TODO: Implementar mixagem de áudio
        logger.info(f"   ✅ {len(narrations)} narrações preparadas")
        
        return video_path
    
    def get_silence_segments(self, video_path: Path) -> List[SilenceSegment]:
        """Retorna segmentos de silêncio do vídeo."""
        return self.silence_detector.detect_silences(video_path)


if __name__ == "__main__":
    narrator = AutoNarrator()
    print("Auto Narrator inicializado com sucesso!")
    print(f"TTS disponível: {narrator.tts.available}")
