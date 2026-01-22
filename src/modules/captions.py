"""
Módulo de Legendas Dinâmicas (Ultimate Optimized V3)
Cache de imagem e processamento otimizado para Google Colab.
"""
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip, CompositeVideoClip
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class DynamicCaptions:
    """Legendas estilo TikTok/Reels - Versão Super-Otimizada com Cache."""

    def __init__(self, style: str = 'viral'):
        self.font_size = 85
        self.color = (255, 255, 255)
        self.highlight_color = (255, 215, 0)
        self.stroke_color = (0, 0, 0)
        self.stroke_width = 8
        self.shadow_color = (0, 0, 0, 160)
        self.shadow_offset = (6, 6)
        self.pos_y_pct = 0.70
        
        # CACHE DE ALTA PERFORMANCE
        self._text_cache = {} 
        self._font_cache = {}

    def create_captions(self, video_clip: CompositeVideoClip, words: List[Dict], position: str = 'bottom') -> CompositeVideoClip:
        """Adiciona legendas ao vídeo usando o pipeline otimizado."""
        if not words:
            logger.warning("⚠️ Nenhuma palavra para legendar")
            return video_clip

        try:
            # Agrupa em frases curtas (1-2 palavras) para ritmo rápido
            groups = self._group_words(words)
            clips = []

            for group in groups:
                duration = max(0.1, group['end'] - group['start'])
                
                # Cria clip de texto (Frame + Mask em um único gerador p/ economizar CPU)
                txt_clip = VideoClip(
                    lambda t, g=group: self._make_frame(t, g, video_clip.size),
                    duration=duration
                )
                txt_clip = txt_clip.set_start(group['start']).set_position('center')

                # Máscara de transparência baseada no canal Alpha cacheado
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
        """Renderiza apenas a parte de COR (RGB) usando cache."""
        res_img = self._get_cached_render(t, group, size)
        return res_img[:, :, :3]

    def _make_mask(self, t, group, size):
        """Renderiza apenas a parte de MÁSCARA (A) usando cache."""
        res_img = self._get_cached_render(t, group, size)
        return res_img[:, :, 3] / 255.0

    def _get_cached_render(self, t, group, size):
        """O CORAÇÃO DA OTIMIZAÇÃO: Gerencia o cache e animações via OpenCV."""
        text = group['text'].upper()
        cache_key = f"{text}_{size[0]}x{size[1]}"
        
        # 1. Recuperar base (ou renderizar se for a primeira vez)
        if cache_key in self._text_cache:
            base_img = self._text_cache[cache_key]
        else:
            # Renderização Pesada (PIL) - Acontece apenas uma vez por frase
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            font = self._get_font(self.font_size)
            
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=self.stroke_width)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            ox, oy = (size[0] - tw) // 2, int(size[1] * self.pos_y_pct) - (th // 2)

            # Sombra
            draw.text((ox + self.shadow_offset[0], oy + self.shadow_offset[1]), text, font=font, 
                      fill=self.shadow_color, stroke_width=self.stroke_width, stroke_fill=self.shadow_color)
            
            # Texto Principal com Highlight
            fill_color = self.highlight_color if len(text) > 8 or hash(text) % 4 == 0 else self.color
            draw.text((ox, oy), text, font=font, fill=fill_color, 
                      stroke_width=self.stroke_width, stroke_fill=self.stroke_color)
            
            base_img = np.array(img)
            self._text_cache[cache_key] = base_img

        # 2. Animação de Escala (OpenCV - 100x mais rápido que PIL)
        scale = 1.0
        if t < 0.1: scale = 0.8 + (2.0 * t) 
        
        if scale != 1.0:
            h, w = base_img.shape[:2]
            new_w, new_h = int(w * scale), int(h * scale)
            # Garantir dimensões pares para evitar erros de render
            new_w, new_h = (new_w // 2) * 2, (new_h // 2) * 2
            
            temp_img = cv2.resize(base_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Reposicionar no centro do canvas original
            final_overlay = np.zeros_like(base_img)
            dy, dx = (h - new_h) // 2, (w - new_w) // 2
            final_overlay[dy:dy+new_h, dx:dx+new_w] = temp_img
            return final_overlay
        
        return base_img

    def _get_font(self, size: int):
        """Carrega fonte com cache interno."""
        if size in self._font_cache: return self._font_cache[size]
        
        base_path = Path(__file__).parent.parent.parent
        font_paths = [
            base_path / "assets/fonts/Oswald-Bold.ttf",
            base_path / "assets/fonts/impact.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
        ]

        for path in font_paths:
            if path.exists():
                try:
                    font = ImageFont.truetype(str(path), size)
                    self._font_cache[size] = font
                    return font
                except: continue
        
        # Fallback
        font = ImageFont.load_default()
        self._font_cache[size] = font
        return font

    def _group_words(self, words: List[Dict]) -> List[Dict]:
        """Agrupa palavras e mapeia Emojis."""
        EMOJI_MAP = {
            'DINHEIRO': '💰', 'RICO': '🤑', 'SUCESSO': '🚀', 'BRASIL': '🇧🇷',
            'AMOR': '❤️', 'CORAÇÃO': '💖', 'FOGO': '🔥', 'TRABALHO': '💼', 
            'MEDO': '😨', 'ASSUSTADOR': '👻', 'FELIZ': '😊', 'ANIMAL': '🐶',
            'PODCAST': '🎙️', 'VIDEO': '🎬', 'GANHAR': '🏆', 'INTERNET': '🌐'
        }

        groups = []
        i = 0
        while i < len(words):
            current = words[i]
            nxt = words[i+1] if i + 1 < len(words) else None

            word_clean = current.get('word', '').upper().strip(',.!?')
            emoji = EMOJI_MAP.get(word_clean, '')
            text = f"{current.get('word', '')} {emoji}".strip()

            if nxt and (nxt['start'] - current['end'] < 0.2) and len(current.get('word','')) < 7:
                nxt_clean = nxt.get('word', '').upper().strip(',.!?')
                nxt_emoji = EMOJI_MAP.get(nxt_clean, '')
                final_text = f"{current.get('word','')} {nxt.get('word','')} {emoji if emoji else nxt_emoji}".strip()
                groups.append({'text': final_text, 'start': current['start'], 'end': nxt['end']})
                i += 2
            else:
                groups.append({'text': text, 'start': current['start'], 'end': current['end']})
                i += 1
        return groups
