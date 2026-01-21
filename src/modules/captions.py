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
    """Legendas estilo TikTok/Reels - Visual Otimizado com Drop Shadow"""

    def __init__(self, style: str = 'viral'):
        self.font_size = 90  # Aumentado para impacto
        self.color = (255, 215, 0)  # Amarelo Ouro (Gold) - Mais vibrante
        self.stroke_color = (0, 0, 0)  # Preto
        self.stroke_width = 6  # Borda grossa
        self.shadow_color = (0, 0, 0, 180) # Sombra semi-transparente
        self.shadow_offset = (5, 5) # Deslocamento da sombra
        self.pos_y_pct = 0.65  # 65% da altura (Safe zone)

    def create_captions(self, video_clip: CompositeVideoClip, words: List[Dict], position: str = 'bottom') -> CompositeVideoClip:
        """Adiciona legendas ao vídeo"""
        if not words:
            logger.warning("⚠️ Nenhuma palavra para legendar")
            return video_clip

        try:
            # Inicializar detector facial
            import cv2
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

            # Agrupa em frases curtas (1-2 palavras) para ritmo rápido
            groups = self._group_words(words)
            clips = []

            for group in groups:
                duration = max(0.1, group['end'] - group['start'])
                mid_time = group['start'] + (duration / 2)

                # --- SMART POSITIONING ---
                # Detectar rosto no frame atual para decidir posição Y
                try:
                    # Pegar frame no meio da frase
                    frame = video_clip.get_frame(mid_time)

                    # Detectar rostos
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

                    # Decidir Y baseado nos rostos
                    smart_y_pct = self.pos_y_pct # Padrão: 0.65

                    if len(faces) > 0:
                        # Encontrar limites verticais dos rostos
                        h_frame = frame.shape[0]
                        min_face_y = min([y for (x,y,w,h) in faces])
                        max_face_y_bottom = max([y+h for (x,y,w,h) in faces])

                        # Converter 0.65 para pixels
                        default_y_px = int(h_frame * 0.65)
                        caption_h_approx = 150 # Altura estimada da legenda

                        # Checar colisão na posição padrão (0.65)
                        caption_top = default_y_px - (caption_h_approx // 2)
                        caption_bottom = default_y_px + (caption_h_approx // 2)

                        collision = False
                        for (fx, fy, fw, fh) in faces:
                            # Interseção simples em Y
                            if not (caption_bottom < fy or caption_top > fy + fh):
                                collision = True
                                break

                        if collision:
                            logger.info(f"   ⚠️ Conflito Face/Legenda em {mid_time:.1f}s. Ajustando...")

                            # Tentar posições alternativas
                            # Opção 1: Topo (0.25) - Se não houver rosto lá
                            top_y_px = int(h_frame * 0.25)
                            top_collision = False
                            for (fx, fy, fw, fh) in faces:
                                if not (top_y_px + 75 < fy or top_y_px - 75 > fy + fh):
                                    top_collision = True

                            if not top_collision:
                                smart_y_pct = 0.25
                            else:
                                # Opção 2: Fundo Extremo (0.85) - Cuidado com UI
                                smart_y_pct = 0.85

                except Exception as e:
                    logger.warning(f"   ⚠️ Erro no Smart Positioning: {e}")
                    smart_y_pct = self.pos_y_pct

                # Cria clip de texto
                txt_clip = VideoClip(
                    lambda t, g=group, y_pct=smart_y_pct: self._make_frame(t, g, video_clip.size, y_pct),
                    duration=duration
                )
                txt_clip = txt_clip.set_start(group['start']).set_position('center')

                # Máscara para transparência
                mask = VideoClip(
                    lambda t, g=group, y_pct=smart_y_pct: self._make_mask(t, g, video_clip.size, y_pct),
                    duration=duration,
                    ismask=True
                )
                txt_clip = txt_clip.set_mask(mask)
                clips.append(txt_clip)

            return CompositeVideoClip([video_clip] + clips)

        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            return video_clip

    def _make_frame(self, t, group, size, pos_y_pct=None):
        """Renderiza frame com texto, borda e sombra"""
        if pos_y_pct is None:
            pos_y_pct = self.pos_y_pct

        # Fundo transparente
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._get_font(self.font_size)

        text = group['text'].upper()

        # Calcular tamanho
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=self.stroke_width)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size[0] - text_width) // 2
        y = int(size[1] * pos_y_pct) - (text_height // 2)

        # 1. Desenhar Sombra Projetada (Drop Shadow)
        shadow_x = x + self.shadow_offset[0]
        shadow_y = y + self.shadow_offset[1]

        # Desenhar sombra (texto preto deslocado)
        draw.text(
            (shadow_x, shadow_y),
            text,
            font=font,
            fill=self.shadow_color,
            stroke_width=self.stroke_width,
            stroke_fill=self.shadow_color
        )

        # 2. Desenhar Texto Principal com Stroke Nativo e Suave
        draw.text(
            (x, y),
            text,
            font=font,
            fill=self.color,
            stroke_width=self.stroke_width,
            stroke_fill=self.stroke_color
        )

        # Converter para RGB (MoviePy espera RGB)
        # Criar fundo preto para compor, depois usar máscara
        bg = Image.new('RGB', size, (0,0,0))
        bg.paste(img, mask=img.split()[3]) # Usar canal alpha como máscara

        return np.array(bg)

    def _make_mask(self, t, group, size, pos_y_pct=None):
        """Cria máscara de transparência baseada no alpha do texto renderizado"""
        if pos_y_pct is None:
            pos_y_pct = self.pos_y_pct

        # Renderizar exatamente como o frame mas focando no canal Alpha
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._get_font(self.font_size)
        text = group['text'].upper()

        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=self.stroke_width)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size[0] - text_width) // 2
        y = int(size[1] * pos_y_pct) - (text_height // 2)

        # Desenhar área da sombra e texto para a máscara cobrir tudo
        shadow_x = x + self.shadow_offset[0]
        shadow_y = y + self.shadow_offset[1]

        # Sombra na máscara
        draw.text(
            (shadow_x, shadow_y), text, font=font, fill=(255,255,255,255),
            stroke_width=self.stroke_width, stroke_fill=(255,255,255,255)
        )

        # Texto na máscara
        draw.text(
            (x, y), text, font=font, fill=(255,255,255,255),
            stroke_width=self.stroke_width, stroke_fill=(255,255,255,255)
        )

        # Retornar canal Alpha normalizado
        return np.array(img.split()[3]) / 255.0

    def _get_font(self, size: int):
        """Carrega fonte: Prioriza Assets > Windows > Linux > Download Auto (Oswald)"""

        # 1. Caminhos locais e sistema
        project_font = Path("assets/fonts/Oswald-Bold.ttf")
        font_paths = [
            project_font,
            Path("assets/fonts/impact.ttf"),
            Path("C:/Windows/Fonts/impact.ttf"),       # Windows Impact
            Path("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf"), # Linux Impact
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") # Linux Fallback
        ]

        for path in font_paths:
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except:
                    continue

        # 2. Se chegou aqui, tentar fontes locais comuns
        fallback_fonts = [
            "impact.ttf",
            "Arial.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]

        for font_name in fallback_fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except IOError:
                continue

        # 3. Fallback absoluto otimizado para Windows/Offline
        logger.warning(f"⚠️ Nenhuma fonte personalizada encontrada. Tentando Arial do Sistema.")
        try:
             # Arial geralmente está no path em Windows/Linux
             return ImageFont.truetype("arial.ttf", size)
        except:
             logger.warning("⚠️ Arial falhou. Usando bitmap padrão (feio mas funcional).")
             return ImageFont.load_default()

    def _group_words(self, words: List[Dict]) -> List[Dict]:
        """Agrupa palavras para ritmo rápido (1-2 palavras MAX)"""
        groups = []

        # Algoritmo guloso simples: agrupa até 2 palavras se forem curtas
        i = 0
        while i < len(words):
            current_word = words[i]

            # Tentar pegar próxima palavra
            next_word = words[i+1] if i + 1 < len(words) else None

            # Critério de agrupamento:
            # - Se a palavra atual for curta (<5 chars) E a próxima também
            # - Se o gap entre elas for pequeno (<0.2s)
            should_group = False
            if next_word:
                len_ok = len(current_word.get('word','')) < 7 and len(next_word.get('word','')) < 7
                gap_ok = (next_word['start'] - current_word['end']) < 0.2
                if len_ok and gap_ok:
                    should_group = True

            if should_group:
                groups.append({
                    'text': f"{current_word.get('word','')} {next_word.get('word','')}",
                    'start': current_word['start'],
                    'end': next_word['end']
                })
                i += 2
            else:
                groups.append({
                    'text': current_word.get('word',''),
                    'start': current_word['start'],
                    'end': current_word['end']
                })
                i += 1

        return groups
