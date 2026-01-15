"""
Módulo de Legendas Dinâmicas (Fase 7)
Cria legendas word-level animadas estilo Hormozi
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


class DynamicCaptions:
    """Cria legendas dinâmicas word-level"""

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
        }
    }

    def __init__(self, style: str = 'hormozi'):
        """
        Inicializa o criador de legendas

        Args:
            style: Estilo de legenda ('hormozi', 'mr_beast', 'minimal')
        """
        self.style_name = style
        self.style = self.STYLES.get(style, self.STYLES['hormozi'])

    def create_captions(
        self,
        video_clip: VideoClip,
        words: List[Dict],
        position: str = 'bottom'
    ) -> VideoClip:
        """
        Adiciona legendas dinâmicas ao vídeo

        Args:
            video_clip: Clip de vídeo original
            words: Lista de palavras com timestamps
            position: Posição das legendas ('top', 'center', 'bottom')

        Returns:
            Vídeo com legendas
        """
        logger.info(f"📝 Criando legendas dinâmicas (estilo: {self.style_name})")
        logger.info(f"   Total de palavras: {len(words)}")

        if not words:
            logger.warning("   Nenhuma palavra fornecida, retornando vídeo sem legendas")
            return video_clip

        try:
            # Criar clips de texto para cada palavra
            text_clips = []

            for word_data in words:
                text_clip = self._create_word_clip(
                    word_data['word'],
                    word_data['start'],
                    word_data['end'],
                    video_clip.size,
                    position
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

            if position == 'top':
                y_pos = video_h * 0.15
            elif position == 'center':
                y_pos = video_h * 0.5
            else:  # bottom
                y_pos = video_h * 0.75

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
            # Tentar fonte padrão simplificada
            font_path = "arial.ttf"

            try:
                font = ImageFont.truetype(font_path, fontsize)
            except:
                font = ImageFont.load_default()

            # Criar imagem transparente
            img_w, img_h = 1080, 200 # Tamanho fixo para o container do texto
            img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Desenhar texto centralizado
            # bbox = draw.textbbox((0, 0), word, font=font)
            # text_w = bbox[2] - bbox[0]
            # text_h = bbox[3] - bbox[1]

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
            if position == 'top':
                y_pos = video_h * 0.15
            elif position == 'center':
                y_pos = video_h * 0.5
            else:  # bottom
                y_pos = video_h * 0.75

            txt_clip = txt_clip.set_position(('center', y_pos))

            return txt_clip

        except Exception as e:
            logger.error(f"   ❌ Falha fatal no fallback PIL: {e}")
            return None

    def create_sentence_captions(
        self,
        video_clip: VideoClip,
        segments: List[Dict],
        position: str = 'bottom'
    ) -> VideoClip:
        """
        Cria legendas por frase (fallback se word-level não disponível)
        """
        return video_clip # Desabilitado temporariamente para não causar erros

        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip


if __name__ == "__main__":
    # Teste rápido
    captions = DynamicCaptions(style='hormozi')

    # Exemplo (descomente para testar)
    # from moviepy.editor import VideoFileClip
    # video = VideoFileClip("temp/video_test.mp4")
    # words = [
    #     {'word': 'Olá', 'start': 0.0, 'end': 0.5},
    #     {'word': 'mundo', 'start': 0.6, 'end': 1.2}
    # ]
    # video_with_captions = captions.create_captions(video, words)
    # video_with_captions.write_videofile("exports/test_captions.mp4")
