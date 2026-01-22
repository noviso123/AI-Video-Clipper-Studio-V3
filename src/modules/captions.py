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
        self.font_size = 85  # Ajustado para equilíbrio
        self.color = (255, 255, 255)  # Branco padrão
        self.highlight_color = (255, 215, 0)  # Amarelo Ouro (Gold) para destaques
        self.stroke_color = (0, 0, 0)  # Preto
        self.stroke_width = 8  # Borda bem visível
        self.shadow_color = (0, 0, 0, 160)
        self.shadow_offset = (6, 6)
        self.pos_y_pct = 0.70  # Um pouco mais baixo para podcasts

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

        # 2. Desenhar Texto Principal com Stroke e Animação de Escala (Pop-In)
        # Determinar cor (Highlight)
        fill_color = self.highlight_color if len(text) > 8 or hash(text) % 4 == 0 else self.color
        
        # ANIMAÇÃO: Pop-In (Escala de 0.8 -> 1.0 no início)
        scale = 1.0
        if t < 0.1: # Primeiro décimo de segundo
            scale = 0.8 + (2.0 * t) # vai de 0.8 a 1.0 linearmente
            
        if scale != 1.0:
            original_font_size = self.font_size
            animated_font = self._get_font(int(original_font_size * scale))
            
            # Recalcular bbox para a fonte escalonada
            abbox = draw.textbbox((0, 0), text, font=animated_font, stroke_width=int(self.stroke_width * scale))
            atw, ath = abbox[2] - abbox[0], abbox[3] - abbox[1]
            ax = (size[0] - atw) // 2
            ay = int(size[1] * pos_y_pct) - (ath // 2)
            
            draw.text(
                (ax, ay), text, font=animated_font, fill=fill_color,
                stroke_width=int(self.stroke_width * scale), stroke_fill=self.stroke_color
            )
        else:
            draw.text(
                (x, y), text, font=font, fill=fill_color,
                stroke_width=self.stroke_width, stroke_fill=self.stroke_color
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
        base_path = Path(__file__).parent.parent.parent
        font_paths = [
            base_path / "assets/fonts/Oswald-Bold.ttf",
            base_path / "assets/fonts/impact.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), # Linux Default
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf") # Linux Fallback
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
        """Agrupa palavras para ritmo rápido e adiciona EMOJIS automáticos."""
        # Dicionário de Emojis Virais (Mapeamento de palavras-chave)
        EMOJI_MAP = {
            'DINHEIRO': '💰', 'RICO': '🤑', 'SUCESSO': '🚀', 'BRASIL': '🇧🇷',
            'AMOR': '❤️', 'CORAÇÃO': '💖', 'FOGO': '🔥', 'QUENTE': '🔥',
            'TRABALHO': '💼', 'NEGÓCIO': '📊', 'MEDO': '😨', 'ASSUSTADOR': '👻',
            'FELIZ': '😊', 'ALEGRIA': '🎉', 'CHORAR': '😢', 'TRISTE': '😔',
            'COMIDA': '🍔', 'FOME': '🍕', 'OLHA': '👀', 'VEJA': '👁️',
            'TEMPO': '⏱️', 'RELOGIO': '⌚', 'IDEIA': '💡', 'MENTE': '🧠',
            'ANIMAL': '🐶', 'CACHORRO': '🐕', 'GATO': '🐈', 'FORTE': '💪',
            'PODCAST': '🎙️', 'VIDEO': '🎬', 'CAMERA': '📷', 'MUSICA': '🎵',
            'GANHAR': '🏆', 'PERDER': '📉', 'MUNDO': '🌍', 'INTERNET': '🌐'
        }

        groups = []
        i = 0
        while i < len(words):
            current_word = words[i]
            next_word = words[i+1] if i + 1 < len(words) else None

            # Processar texto e adicionar emoji se houver match
            word_clean = current_word.get('word', '').upper().strip(',.!?')
            emoji = EMOJI_MAP.get(word_clean, '')
            text_with_emoji = f"{current_word.get('word', '')} {emoji}".strip()

            should_group = False
            if next_word:
                len_ok = len(current_word.get('word','')) < 7 and len(next_word.get('word','')) < 7
                gap_ok = (next_word['start'] - current_word['end']) < 0.2
                if len_ok and gap_ok:
                    should_group = True

            if should_group:
                next_word_clean = next_word.get('word', '').upper().strip(',.!?')
                next_emoji = EMOJI_MAP.get(next_word_clean, '')
                # Se a primeira palavra já tem emoji, talvez não precise na segunda do grupo
                final_text = f"{current_word.get('word','')} {next_word.get('word','')} {emoji if emoji else next_emoji}".strip()
                
                groups.append({
                    'text': final_text,
                    'start': current_word['start'],
                    'end': next_word['end']
                })
                i += 2
            else:
                groups.append({
                    'text': text_with_emoji,
                    'start': current_word['start'],
                    'end': current_word['end']
                })
                i += 1

        return groups
