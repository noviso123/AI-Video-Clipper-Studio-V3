"""
Módulo de Legendas Dinâmicas (Fase 7) - VERSÃO 2.0
Cria legendas word-level animadas estilo Hormozi

MELHORIAS V2:
- Detecta legendas existentes e evita sobreposição
- Posicionamento inteligente baseado no conteúdo do vídeo
- Suporte a múltiplas posições dinâmicas
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from moviepy.editor import VideoClip, TextClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import numpy as np
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Import opcional do detector de legendas
try:
    from .subtitle_detector import SubtitleDetector
    SUBTITLE_DETECTOR_AVAILABLE = True
except ImportError:
    SUBTITLE_DETECTOR_AVAILABLE = False


class DynamicCaptions:
    """Cria legendas dinâmicas word-level com posicionamento inteligente"""

    # Estilos de legenda predefinidos
    STYLES = {
        'hormozi': {
            'fontsize': 70,
            'font': 'Arial-Bold',
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 3,
            'method': 'caption',
            'align': 'center'
        },
        'mr_beast': {
            'fontsize': 80,
            'font': 'Impact',
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 4,
            'method': 'caption',
            'align': 'center'
        },
        'minimal': {
            'fontsize': 60,
            'font': 'Arial',
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'method': 'caption',
            'align': 'center'
        },
        'tiktok': {
            'fontsize': 65,
            'font': 'Arial-Bold',
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 3,
            'method': 'caption',
            'align': 'center',
            'bg_color': 'rgba(0,0,0,0.5)'
        }
    }
    
    # Posições Y em porcentagem da altura do vídeo
    POSITIONS = {
        'top': 0.12,
        'upper': 0.25,
        'center': 0.50,
        'lower': 0.65,
        'bottom': 0.82
    }

    def __init__(self, style: str = 'hormozi'):
        """
        Inicializa o criador de legendas

        Args:
            style: Estilo de legenda ('hormozi', 'mr_beast', 'minimal', 'tiktok')
        """
        self.style_name = style
        self.style = self.STYLES.get(style, self.STYLES['hormozi'])
        
        # Inicializar detector de legendas
        self.subtitle_detector = None
        if SUBTITLE_DETECTOR_AVAILABLE:
            self.subtitle_detector = SubtitleDetector()
        
        logger.info(f"📝 Dynamic Captions inicializado (estilo: {style})")
        logger.info(f"   Detecção de legendas existentes: {'Ativo' if self.subtitle_detector else 'Inativo'}")

    def create_captions(
        self,
        video_clip: VideoClip,
        words: List[Dict],
        position: str = 'auto',
        video_path: Path = None
    ) -> VideoClip:
        """
        Adiciona legendas dinâmicas ao vídeo com posicionamento inteligente

        Args:
            video_clip: Clip de vídeo original
            words: Lista de palavras com timestamps
            position: Posição das legendas ('auto', 'top', 'center', 'bottom')
            video_path: Caminho do vídeo (para detectar legendas existentes)

        Returns:
            Vídeo com legendas
        """
        logger.info(f"📝 Criando legendas dinâmicas (estilo: {self.style_name})")
        logger.info(f"   Total de palavras: {len(words)}")

        if not words:
            logger.warning("   Nenhuma palavra fornecida, retornando vídeo sem legendas")
            return video_clip

        # Determinar posição ideal
        actual_position = self._determine_optimal_position(
            position, video_path, video_clip.size
        )
        
        logger.info(f"   Posição das legendas: {actual_position}")

        try:
            # Criar clips de texto para cada palavra
            text_clips = []

            for word_data in words:
                text_clip = self._create_word_clip(
                    word_data['word'],
                    word_data['start'],
                    word_data['end'],
                    video_clip.size,
                    actual_position
                )

                if text_clip:
                    text_clips.append(text_clip)

            if not text_clips:
                logger.warning("   Nenhum clip de texto criado")
                return video_clip

            # Combinar vídeo + legendas
            final_video = CompositeVideoClip([video_clip] + text_clips)

            logger.info(f"✅ {len(text_clips)} legendas adicionadas")

            return final_video

        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip

    def _determine_optimal_position(
        self,
        requested_position: str,
        video_path: Path,
        video_size: Tuple[int, int]
    ) -> str:
        """
        Determina a posição ideal para as legendas.
        
        Se 'auto', detecta legendas existentes e escolhe posição que evita sobreposição.
        """
        if requested_position != 'auto':
            return requested_position
        
        # Tentar detectar legendas existentes
        if self.subtitle_detector and video_path:
            try:
                result = self.subtitle_detector.detect_subtitle_regions(video_path, sample_count=5)
                
                if result.get('has_subtitles'):
                    existing_pos = result.get('subtitle_position')
                    suggested = result.get('suggested_new_position', 'bottom')
                    
                    logger.info(f"   🔍 Legendas existentes detectadas em: {existing_pos}")
                    logger.info(f"   📍 Usando posição alternativa: {suggested}")
                    
                    return suggested
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao detectar legendas existentes: {e}")
        
        # Padrão: bottom para vídeos verticais, center para horizontais
        video_w, video_h = video_size
        if video_h > video_w:  # Vertical
            return 'bottom'
        else:  # Horizontal
            return 'lower'

    def _create_word_clip(
        self,
        word: str,
        start: float,
        end: float,
        video_size: Tuple[int, int],
        position: str
    ) -> Optional[TextClip]:
        """
        Cria clip de texto para uma palavra

        Args:
            word: Palavra a exibir
            start: Tempo de início
            end: Tempo de fim
            video_size: Tamanho do vídeo (largura, altura)
            position: Posição da legenda

        Returns:
            TextClip ou None se houver erro
        """
        try:
            # Criar texto
            txt_clip = TextClip(
                word,
                fontsize=self.style['fontsize'],
                font=self.style['font'],
                color=self.style['color'],
                stroke_color=self.style['stroke_color'],
                stroke_width=self.style['stroke_width'],
                method=self.style['method']
            )

            # Definir duração e posição temporal
            txt_clip = txt_clip.set_start(start).set_duration(end - start)

            # Calcular posição na tela
            video_w, video_h = video_size
            y_pct = self.POSITIONS.get(position, self.POSITIONS['bottom'])
            y_pos = video_h * y_pct

            txt_clip = txt_clip.set_position(('center', y_pos))

            # Adicionar fade in/out suave (0.1s)
            fade_duration = min(0.1, (end - start) / 2)
            txt_clip = fadein(txt_clip, fade_duration)
            txt_clip = fadeout(txt_clip, fade_duration)

            return txt_clip

        except Exception as e:
            # Tentar fallback com PIL se o erro for de ImageMagick
            if "ImageMagick" in str(e) or "WinError 2" in str(e):
                logger.warning(f"   ⚠️ ImageMagick não encontrado. Usando fallback PIL para '{word}'")
                return self._create_word_clip_pil(word, start, end, video_size, position)

            logger.warning(f"   Erro ao criar clip para '{word}': {e}")
            return None

    def _create_word_clip_pil(
        self,
        word: str,
        start: float,
        end: float,
        video_size: Tuple[int, int],
        position: str
    ) -> Optional[VideoClip]:
        """Fallback: Cria clip de texto usando PIL (sem ImageMagick)"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            from moviepy.editor import ImageClip

            # Configurações básicas
            fontsize = self.style['fontsize']
            
            # Tentar carregar fonte
            font = self._get_pil_font(fontsize)

            # Criar imagem transparente
            img_w, img_h = 1080, 200  # Tamanho fixo para o container do texto
            img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Cor e Stroke (simulado)
            fill_color = self.style['color']
            stroke_color = self.style['stroke_color']
            stroke_width = self.style.get('stroke_width', 0)

            # Desenhar stroke manualmente
            x = img_w // 2
            y = img_h // 2

            if stroke_width > 0:
                for off_x in range(-stroke_width, stroke_width + 1):
                    for off_y in range(-stroke_width, stroke_width + 1):
                        draw.text((x + off_x, y + off_y), word, font=font, fill=stroke_color, anchor="mm")

            # Desenhar texto principal
            draw.text((x, y), word, font=font, fill=fill_color, anchor="mm")

            # Converter para numpy array
            img_np = np.array(img)

            # Criar ImageClip
            txt_clip = ImageClip(img_np)
            txt_clip = txt_clip.set_start(start).set_duration(end - start)

            # Calcular posição
            video_w, video_h = video_size
            y_pct = self.POSITIONS.get(position, self.POSITIONS['bottom'])
            y_pos = video_h * y_pct

            txt_clip = txt_clip.set_position(('center', y_pos))

            return txt_clip

        except Exception as e:
            logger.error(f"   ❌ Falha fatal no fallback PIL: {e}")
            return None

    def _get_pil_font(self, size: int):
        """Obtém uma fonte PIL com fallbacks."""
        from PIL import ImageFont
        import os
        
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/impact.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        
        return ImageFont.load_default()

    def create_sentence_captions(
        self,
        video_clip: VideoClip,
        segments: List[Dict],
        position: str = 'auto',
        video_path: Path = None
    ) -> VideoClip:
        """
        Cria legendas por frase (fallback se word-level não disponível)
        """
        try:
            if not segments:
                return video_clip
            
            # Determinar posição ideal
            actual_position = self._determine_optimal_position(
                position, video_path, video_clip.size
            )
            
            text_clips = []
            for segment in segments:
                text_clip = self._create_word_clip(
                    segment.get('text', ''),
                    segment.get('start', 0),
                    segment.get('end', 1),
                    video_clip.size,
                    actual_position
                )
                if text_clip:
                    text_clips.append(text_clip)
            
            if text_clips:
                return CompositeVideoClip([video_clip] + text_clips)
            return video_clip
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip

    def get_available_positions(self) -> Dict[str, float]:
        """Retorna as posições disponíveis para legendas."""
        return self.POSITIONS.copy()

    def set_custom_position(self, name: str, y_percentage: float):
        """
        Define uma posição customizada para legendas.
        
        Args:
            name: Nome da posição
            y_percentage: Posição Y em porcentagem (0.0 = topo, 1.0 = base)
        """
        self.POSITIONS[name] = max(0.05, min(0.95, y_percentage))
        logger.info(f"   📍 Posição customizada '{name}' definida em {y_percentage:.0%}")


if __name__ == "__main__":
    # Teste rápido
    captions = DynamicCaptions(style='hormozi')
    print("Dynamic Captions inicializado com sucesso!")
    print(f"Posições disponíveis: {captions.get_available_positions()}")
