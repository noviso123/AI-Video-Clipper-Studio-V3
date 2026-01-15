"""
Módulo de Geração de Thumbnails IA (Fase 21)
Cria thumbnails virais extraindo rostos e adicionando textos/efeitos.
"""
import logging
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    def __init__(self):
        logger.info("🖼️ Thumbnail Generator: Inicializado")
        # Cores vibrantes para stroke/borda
        self.stroke_colors = ['#FF0000', '#00FF00', '#FFFF00', '#00FFFF', '#FF00FF']

    def generate_thumbnail(self, video_path: Path, moment: dict, output_path: Path) -> Path:
        """
        Gera uma thumbnail para o momento viral.
        """
        try:
            # 1. Extrair Frame do meio do clipe
            timestamp = (moment['start'] + moment['end']) / 2
            frame = self._extract_frame(video_path, timestamp)

            if frame is None:
                logger.warning("   ⚠️ Falha ao extrair frame para thumbnail")
                return None

            # 2. Processar Imagem (Pillow)
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # --- FEATURE 1: Background Removal (Se rembg estiver disponível) ---
            try:
                from rembg import remove
                # Remover fundo e colocar cor sólida ou gradiente
                subject = remove(img)

                # Criar fundo dark
                bg = Image.new('RGB', img.size, (20, 20, 20))
                # Adicionar um brilho atrás
                draw = ImageDraw.Draw(bg)
                cx, cy = bg.width // 2, bg.height // 2
                draw.ellipse((cx-300, cy-300, cx+300, cy+300), fill=(50, 50, 100), outline=None)

                # Colocar sujeito
                bg.paste(subject, (0, 0), subject)
                img = bg

            except ImportError:
                logger.info("   ℹ️ rembg não instalado, usando frame original")
            except Exception as e:
                logger.warning(f"   ⚠️ Erro no rembg: {e}. Usando original.")

            # --- FEATURE 2: Image Enhancing ---
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.3)

            # --- FEATURE 3: Text Overlay ---
            draw = ImageDraw.Draw(img)

            # Tentar carregar fonte impactante (Arial Black ou Impact)
            try:
                font = ImageFont.truetype("arialbd.ttf", 80)
            except:
                font = ImageFont.load_default()

            text = moment['hook'].upper()

            # Quebrar texto se for muito longo
            words = text.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if len(" ".join(current_line)) > 15: # Max chars per line
                    lines.append(" ".join(current_line))
                    current_line = []
            if current_line:
                lines.append(" ".join(current_line))

            # Desenhar texto com stroke
            y_text = 100
            for line in lines[:3]: # Max 3 linhas
                #bbox = draw.textbbox((0, 0), line, font=font)
                #w = bbox[2] - bbox[0]
                w = draw.textlength(line, font=font)
                x_text = (img.width - w) / 2

                # Stroke preto grosso
                stroke_width = 4
                for off_x in range(-stroke_width, stroke_width+1):
                    for off_y in range(-stroke_width, stroke_width+1):
                         draw.text((x_text+off_x, y_text+off_y), line, font=font, fill='black')

                # Texto principal (Amarelo ou Branco)
                text_color = random.choice(['#FFFF00', '#FFFFFF', '#00FF00'])
                draw.text((x_text, y_text), line, font=font, fill=text_color)

                y_text += 100

            # Salvar
            img.save(str(output_path), quality=95)
            logger.info(f"   🖼️ Thumbnail salva: {output_path.name}")

            return output_path

        except Exception as e:
            logger.error(f"❌ Erro ao gerar thumbnail: {e}")
            return None

    def _extract_frame(self, video_path: Path, timestamp: float):
        """Extrai um frame específico do vídeo"""
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        cap.release()
        if ret:
            return frame
        return None
