"""
Módulo de Legendas Dinâmicas (Market Standard) - CORRIGIDO
Usando API moderna do PIL e renderização otimizada.
"""
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip, CompositeVideoClip
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class DynamicCaptions:
    """Legendas bold, amarelas e centralizadas (Padrão Viral)"""

    def __init__(self, style: str = 'viral'):
        self.font_size = 75
        self.color = (255, 255, 0)  # Amarelo
        self.stroke_color = (0, 0, 0)  # Preto
        self.stroke_width = 4
        self.pos_y_pct = 0.70  # 70% da altura (área segura)

    def create_captions(self, video_clip: CompositeVideoClip, words: List[Dict], position: str = 'bottom') -> CompositeVideoClip:
        """Adiciona legendas ao vídeo"""
        if not words:
            logger.warning("⚠️ Nenhuma palavra para legendar")
            return video_clip

        try:
            # Agrupa em frases curtas (1-3 palavras)
            groups = self._group_words(words)
            clips = []

            for group in groups:
                duration = max(0.1, group['end'] - group['start'])

                # Cria clip de texto
                txt_clip = VideoClip(
                    lambda t, g=group: self._make_frame(t, g, video_clip.size),
                    duration=duration
                )
                txt_clip = txt_clip.set_start(group['start']).set_position('center')

                # Máscara para transparência
                mask = VideoClip(
                    lambda t, g=group: self._make_mask(t, g, video_clip.size),
                    duration=duration,
                    ismask=True
                )
                txt_clip = txt_clip.set_mask(mask)
                clips.append(txt_clip)

            return CompositeVideoClip([video_clip] + clips)

        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip

    def _make_frame(self, t, group, size):
        """Renderiza frame com texto"""
        img = Image.new('RGB', size, (0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._get_font(self.font_size)

        text = group['text'].upper()

        # Usar textbbox (API moderna do PIL)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size[0] - text_width) // 2
        y = int(size[1] * self.pos_y_pct) - (text_height // 2)

        # Desenhar stroke (borda)
        s = self.stroke_width
        for dx, dy in [(-s,-s), (-s,s), (s,-s), (s,s), (0,s), (0,-s), (s,0), (-s,0)]:
            draw.text((x+dx, y+dy), text, font=font, fill=self.stroke_color)

        # Texto principal
        draw.text((x, y), text, font=font, fill=self.color)

        return np.array(img)

    def _make_mask(self, t, group, size):
        """Cria máscara de transparência"""
        img = Image.new('L', size, 0)
        draw = ImageDraw.Draw(img)
        font = self._get_font(self.font_size)

        text = group['text'].upper()

        # Usar textbbox
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size[0] - text_width) // 2
        y = int(size[1] * self.pos_y_pct) - (text_height // 2)

        # Desenhar área visível (branco = visível)
        s = self.stroke_width
        for dx, dy in [(-s,-s), (-s,s), (s,-s), (s,s), (0,s), (0,-s), (s,0), (-s,0), (0,0)]:
            draw.text((x+dx, y+dy), text, font=font, fill=255)

        return np.array(img) / 255.0

    def _get_font(self, size: int):
        """Carrega fonte do sistema"""
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]

        for path in font_paths:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue

        # Fallback para fonte padrão
        logger.warning("⚠️ Usando fonte padrão (pode ter qualidade reduzida)")
        return ImageFont.load_default()

    def _group_words(self, words: List[Dict]) -> List[Dict]:
        """Agrupa palavras em frases curtas (2 palavras por vez)"""
        groups = []

        for i in range(0, len(words), 2):
            chunk = words[i:i+2]
            if chunk:
                groups.append({
                    'text': " ".join([w.get('word', '') for w in chunk]),
                    'start': chunk[0].get('start', 0),
                    'end': chunk[-1].get('end', 0)
                })

        return groups
