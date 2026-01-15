"""
Módulo de Legendas Inteligentes
Adiciona legendas automaticamente onde não existem.

Funcionalidades:
- Detecção de legendas existentes
- Posicionamento inteligente (evita sobreposição)
- Estilos dinâmicos baseados no conteúdo
- Sincronização com áudio
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import cv2
import numpy as np
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class CaptionSegment:
    """Segmento de legenda."""
    start: float
    end: float
    text: str
    position: str  # 'top', 'center', 'bottom'
    style: str  # 'default', 'emphasis', 'whisper'
    has_existing_subtitle: bool = False


class SmartCaptionGenerator:
    """Gerador de legendas inteligentes."""
    
    # Estilos de legenda
    STYLES = {
        'default': {
            'fontsize': 50,
            'color': 'white',
            'font': 'Arial-Bold',
            'stroke_color': 'black',
            'stroke_width': 2,
            'bg_color': None
        },
        'emphasis': {
            'fontsize': 60,
            'color': 'yellow',
            'font': 'Arial-Bold',
            'stroke_color': 'black',
            'stroke_width': 3,
            'bg_color': None
        },
        'whisper': {
            'fontsize': 40,
            'color': 'lightgray',
            'font': 'Arial',
            'stroke_color': 'black',
            'stroke_width': 1,
            'bg_color': None
        },
        'tiktok': {
            'fontsize': 55,
            'color': 'white',
            'font': 'Arial-Bold',
            'stroke_color': 'black',
            'stroke_width': 2,
            'bg_color': 'rgba(0,0,0,0.5)'
        },
        'hormozi': {
            'fontsize': 65,
            'color': 'white',
            'font': 'Impact',
            'stroke_color': 'black',
            'stroke_width': 3,
            'bg_color': None
        }
    }
    
    # Posições de legenda
    POSITIONS = {
        'top': 0.1,      # 10% do topo
        'upper': 0.25,   # 25% do topo
        'center': 0.45,  # Centro
        'lower': 0.65,   # 65% do topo
        'bottom': 0.85   # 85% do topo (perto da base)
    }
    
    def __init__(self, default_style: str = 'default'):
        self.default_style = default_style
        self.target_width = Config.OUTPUT_RESOLUTION[0]
        self.target_height = Config.OUTPUT_RESOLUTION[1]
        
        logger.info(f"📝 Smart Caption Generator: Inicializado")
        logger.info(f"   Estilo padrão: {default_style}")
    
    def analyze_existing_subtitles(
        self,
        video_path: Path,
        timestamps: List[float]
    ) -> Dict[float, Dict]:
        """
        Analisa legendas existentes em timestamps específicos.
        
        Returns:
            Dict mapeando timestamp para info de legenda existente
        """
        results = {}
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            
            for timestamp in timestamps:
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    results[timestamp] = {'has_subtitle': False}
                    continue
                
                # Analisar frame para legendas
                subtitle_info = self._detect_subtitle_in_frame(frame)
                results[timestamp] = subtitle_info
            
            cap.release()
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao analisar legendas: {e}")
        
        return results
    
    def _detect_subtitle_in_frame(self, frame: np.ndarray) -> Dict:
        """Detecta legenda em um frame."""
        h, w = frame.shape[:2]
        
        # Verificar regiões
        regions = {
            'top': frame[:int(h*0.2), :],
            'center': frame[int(h*0.35):int(h*0.65), :],
            'bottom': frame[int(h*0.75):, :]
        }
        
        max_score = 0
        detected_position = None
        
        for name, region in regions.items():
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Detectar texto (alto contraste)
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            white_ratio = np.sum(binary > 0) / binary.size
            
            # Detectar bordas
            edges = cv2.Canny(gray, 50, 150)
            edge_ratio = np.sum(edges > 0) / edges.size
            
            score = white_ratio * 0.5 + edge_ratio * 0.5
            
            if score > max_score and score > 0.1:
                max_score = score
                detected_position = name
        
        return {
            'has_subtitle': detected_position is not None,
            'position': detected_position,
            'confidence': max_score
        }
    
    def determine_best_position(
        self,
        existing_subtitle_position: str = None,
        frame_type: str = None
    ) -> str:
        """Determina a melhor posição para nova legenda."""
        
        # Se já tem legenda, posicionar em outro lugar
        if existing_subtitle_position:
            if existing_subtitle_position == 'bottom':
                return 'upper'
            elif existing_subtitle_position == 'top':
                return 'lower'
            elif existing_subtitle_position == 'center':
                return 'bottom'
        
        # Posição padrão
        return 'bottom'
    
    def determine_style(
        self,
        text: str,
        audio_volume: float = 0.5,
        is_emphasis: bool = False
    ) -> str:
        """Determina o estilo da legenda baseado no contexto."""
        
        # Texto em caps = ênfase
        if text.isupper():
            return 'emphasis'
        
        # Volume baixo = sussurro
        if audio_volume < 0.2:
            return 'whisper'
        
        # Ênfase explícita
        if is_emphasis:
            return 'emphasis'
        
        return self.default_style
    
    def create_caption_clips(
        self,
        transcription: List[Dict],
        video_duration: float,
        existing_subtitles: Dict[float, Dict] = None
    ) -> List[CaptionSegment]:
        """
        Cria segmentos de legenda a partir da transcrição.
        
        Args:
            transcription: Lista de {start, end, text}
            video_duration: Duração do vídeo
            existing_subtitles: Info de legendas existentes
            
        Returns:
            Lista de CaptionSegment
        """
        segments = []
        
        for item in transcription:
            start = item.get('start', 0)
            end = item.get('end', start + 1)
            text = item.get('text', '').strip()
            
            if not text:
                continue
            
            # Verificar se já tem legenda neste momento
            has_existing = False
            existing_position = None
            
            if existing_subtitles:
                # Procurar legenda existente próxima
                for ts, info in existing_subtitles.items():
                    if start <= ts <= end and info.get('has_subtitle'):
                        has_existing = True
                        existing_position = info.get('position')
                        break
            
            # Determinar posição e estilo
            position = self.determine_best_position(existing_position)
            style = self.determine_style(text)
            
            segments.append(CaptionSegment(
                start=start,
                end=end,
                text=text,
                position=position,
                style=style,
                has_existing_subtitle=has_existing
            ))
        
        return segments
    
    def render_captions_on_video(
        self,
        video_clip: VideoFileClip,
        caption_segments: List[CaptionSegment],
        skip_existing: bool = True
    ) -> VideoFileClip:
        """
        Renderiza legendas no vídeo.
        
        Args:
            video_clip: Clip de vídeo
            caption_segments: Segmentos de legenda
            skip_existing: Pular frames que já têm legenda
            
        Returns:
            Clip com legendas
        """
        clips = [video_clip]
        
        for segment in caption_segments:
            # Pular se já tem legenda
            if skip_existing and segment.has_existing_subtitle:
                continue
            
            # Obter estilo
            style = self.STYLES.get(segment.style, self.STYLES['default'])
            
            # Calcular posição Y
            y_ratio = self.POSITIONS.get(segment.position, 0.85)
            y_pos = int(self.target_height * y_ratio)
            
            try:
                # Criar clip de texto
                txt_clip = TextClip(
                    segment.text,
                    fontsize=style['fontsize'],
                    color=style['color'],
                    font=style.get('font', 'Arial-Bold'),
                    stroke_color=style.get('stroke_color', 'black'),
                    stroke_width=style.get('stroke_width', 2),
                    method='caption',
                    size=(self.target_width - 100, None)
                )
                
                # Posicionar
                txt_clip = txt_clip.set_position(('center', y_pos))
                txt_clip = txt_clip.set_start(segment.start)
                txt_clip = txt_clip.set_duration(segment.end - segment.start)
                
                clips.append(txt_clip)
                
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao criar legenda: {e}")
                continue
        
        if len(clips) > 1:
            return CompositeVideoClip(clips)
        
        return video_clip
    
    def add_captions_to_video(
        self,
        video_path: Path,
        output_path: Path,
        transcription: List[Dict],
        style: str = None
    ) -> Path:
        """
        Adiciona legendas a um vídeo.
        
        Args:
            video_path: Vídeo de entrada
            output_path: Vídeo de saída
            transcription: Transcrição
            style: Estilo das legendas
            
        Returns:
            Caminho do vídeo com legendas
        """
        logger.info(f"📝 Adicionando legendas: {video_path.name}")
        
        if style:
            self.default_style = style
        
        try:
            # Carregar vídeo
            clip = VideoFileClip(str(video_path))
            
            # Analisar legendas existentes
            timestamps = [item.get('start', 0) for item in transcription]
            existing = self.analyze_existing_subtitles(video_path, timestamps)
            
            # Criar segmentos de legenda
            segments = self.create_caption_clips(
                transcription, clip.duration, existing
            )
            
            logger.info(f"   {len(segments)} legendas a adicionar")
            
            # Renderizar
            final_clip = self.render_captions_on_video(clip, segments)
            
            # Exportar
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            final_clip.write_videofile(
                str(output_path),
                fps=clip.fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                logger=None
            )
            
            clip.close()
            final_clip.close()
            
            logger.info(f"   ✅ Legendas adicionadas: {output_path.name}")
            return output_path
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao adicionar legendas: {e}")
            return video_path


class WordByWordCaptions:
    """Legendas palavra por palavra (estilo TikTok/Reels)."""
    
    def __init__(self):
        self.target_width = Config.OUTPUT_RESOLUTION[0]
        self.target_height = Config.OUTPUT_RESOLUTION[1]
        
        logger.info("📝 Word-by-Word Captions: Inicializado")
    
    def create_word_clips(
        self,
        transcription: List[Dict],
        highlight_color: str = 'yellow',
        base_color: str = 'white'
    ) -> List[TextClip]:
        """
        Cria clips de texto palavra por palavra.
        
        Args:
            transcription: Lista com {start, end, text, words}
            highlight_color: Cor da palavra atual
            base_color: Cor das outras palavras
            
        Returns:
            Lista de TextClips
        """
        clips = []
        
        for segment in transcription:
            words = segment.get('words', [])
            
            if not words:
                # Se não tem palavras individuais, usar texto completo
                text = segment.get('text', '')
                start = segment.get('start', 0)
                end = segment.get('end', start + 1)
                
                try:
                    txt = TextClip(
                        text,
                        fontsize=55,
                        color=base_color,
                        font='Arial-Bold',
                        stroke_color='black',
                        stroke_width=2,
                        method='caption',
                        size=(self.target_width - 100, None)
                    )
                    txt = txt.set_position(('center', int(self.target_height * 0.8)))
                    txt = txt.set_start(start)
                    txt = txt.set_duration(end - start)
                    clips.append(txt)
                except:
                    pass
                
                continue
            
            # Criar clip para cada palavra
            for word_info in words:
                word = word_info.get('word', '')
                start = word_info.get('start', 0)
                end = word_info.get('end', start + 0.3)
                
                try:
                    txt = TextClip(
                        word.upper(),
                        fontsize=65,
                        color=highlight_color,
                        font='Impact',
                        stroke_color='black',
                        stroke_width=3,
                        method='caption',
                        size=(self.target_width - 100, None)
                    )
                    txt = txt.set_position(('center', int(self.target_height * 0.75)))
                    txt = txt.set_start(start)
                    txt = txt.set_duration(end - start)
                    clips.append(txt)
                except:
                    pass
        
        return clips


if __name__ == "__main__":
    generator = SmartCaptionGenerator()
    print("Smart Caption Generator inicializado com sucesso!")
    print(f"Estilos disponíveis: {list(generator.STYLES.keys())}")
    print(f"Posições disponíveis: {list(generator.POSITIONS.keys())}")
