"""
Gerador de Thumbnails com Texto Viral
Extrai frame do vídeo e adiciona texto chamativo.
"""
import cv2
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class ThumbnailGenerator:
    def __init__(self):
        self.target_size = (1080, 1920)  # 9:16 Vertical

    def generate_thumbnail(self, video_path: Path, moment: dict, output_path: Path, hook_text: str = None) -> Path:
        """
        Extrai frame do clipe e adiciona texto chamativo.
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            # Vai para o início do clipe
            cap.set(cv2.CAP_PROP_POS_MSEC, moment.get('start', 0) * 1000)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                logger.error("❌ Não foi possível extrair frame")
                return None

            # Converter para PIL
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Crop 9:16 Central
            img = self._center_crop_9_16(img)

            # Adicionar texto chamativo
            text = hook_text or moment.get('hook', 'Assista até o final!')
            img = self._add_viral_text(img, text)

            # Salvar
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, quality=95)

            logger.info(f"✅ Thumbnail gerada: {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro na thumbnail: {e}")
            return None

    def _center_crop_9_16(self, img: Image.Image) -> Image.Image:
        """Crop central para 9:16"""
        w, h = img.size
        target_ratio = 9/16

        new_h = h
        new_w = int(h * target_ratio)

        if new_w > w:
            new_w = w
            new_h = int(w / target_ratio)

        left = (w - new_w) // 2
        top = (h - new_h) // 2
        right = left + new_w
        bottom = top + new_h

        return img.crop((left, top, right, bottom)).resize(self.target_size)

    def _add_viral_text(self, img: Image.Image, text: str) -> Image.Image:
        """Adiciona texto chamativo estilo viral"""
        draw = ImageDraw.Draw(img)

        # Tamanho da fonte baseado na largura da imagem
        font_size = int(img.size[0] * 0.08)  # 8% da largura
        font = self._get_font(font_size)

        # Quebrar texto em linhas
        words = text.upper().split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width < img.size[0] * 0.9:  # 90% da largura
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Limitar a 3 linhas
        lines = lines[:3]

        # Calcular posição (centralizado, parte superior)
        line_height = font_size * 1.3
        total_height = len(lines) * line_height
        start_y = img.size[1] * 0.15  # 15% do topo

        # Desenhar cada linha
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img.size[0] - text_width) // 2
            y = start_y + i * line_height

            # Stroke (borda preta)
            stroke_width = int(font_size * 0.08)
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))

            # Texto principal (amarelo)
            draw.text((x, y), line, font=font, fill=(255, 255, 0))

        return img

    def _get_font(self, size: int):
        """Carrega fonte do sistema"""
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

        for path in font_paths:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue

        logger.warning("⚠️ Usando fonte padrão")
        return ImageFont.load_default()
