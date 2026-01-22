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
    """Gerador de thumbnails para vídeos verticais."""

    def __init__(self):
        self.target_size = (1080, 1920)  # 9:16 Vertical
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def generate_thumbnail(self, video_path: Path, moment: dict, output_path: Path, hook_text: str = None) -> Path:
        """
        Extrai frame do clipe e adiciona texto chamativo.
        Foca no rosto se disponível.
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

            # Detectar rostos para smart crop
            faces = self._detect_faces(frame)
            center_x, center_y = None, None

            if faces:
                # Focar no maior rosto
                largest_face = max(faces, key=lambda f: f['w'] * f['h'])
                center_x = largest_face['x'] + largest_face['w'] // 2
                center_y = largest_face['y'] + largest_face['h'] // 2
                # Ajuste vertical: subir bastante (60%) para garantir rosto completo visível
                center_y = max(0, center_y - int(largest_face['h'] * 0.6))

            # Converter para PIL
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Crop 9:16 Inteligente (Focado no rosto ou centro)
            img = self._smart_crop_9_16(img, center_x, center_y)

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

    def _detect_faces(self, frame):
        """Detecta rostos rapidamente usando Haar Cascade."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # OTIMIZAÇÃO: scaleFactor 1.3 é mais rápido que 1.1 (menos preciso, mas ok para thumbnail)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50)
        )
        return [{'x': x, 'y': y, 'w': w, 'h': h} for (x, y, w, h) in faces]

    def _smart_crop_9_16(self, img: Image.Image, center_x=None, center_y=None) -> Image.Image:
        """Crop 9:16 focado no ponto de interesse (rosto) ou centro."""
        w, h = img.size
        target_ratio = 9/16

        new_h = h
        new_w = int(h * target_ratio)

        if new_w > w:
            new_w = w
            new_h = int(w / target_ratio)

        # Se não tiver ponto de interesse, usa o centro
        if center_x is None:
            center_x = w // 2
        if center_y is None:
            center_y = h // 2

        left = max(0, center_x - new_w // 2)
        top = max(0, center_y - new_h // 2)

        # Ajustar limites
        if left + new_w > w:
            left = w - new_w
        if top + new_h > h:
            top = h - new_h

        right = left + new_w
        bottom = top + new_h

        return img.crop((left, top, right, bottom)).resize(self.target_size)

    def _add_viral_text(self, img: Image.Image, text: str) -> Image.Image:
        """Adiciona texto chamativo estilo viral"""
        draw = ImageDraw.Draw(img)

        # Tamanho da fonte baseado na largura da imagem (Aumentado para mobile)
        font_size = int(img.size[0] * 0.11)  # 11% da largura (era 8%)
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
        """Carrega fonte do sistema ou baixa automaticamente"""
        font_paths = [
            "src/assets/fonts/Anton-Regular.ttf",
            "assets/fonts/Anton-Regular.ttf",
            "src/assets/fonts/Oswald-Bold.ttf",
            "assets/fonts/Oswald-Bold.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

        # 1. Tentar encontrar localmente
        for path in font_paths:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, size)
                except: continue

        # 2. Se não encontrar, tentar BAIXAR automaticamente (Colab Friendly)
        try:
            logger.info("⬇️ Fonte não encontrada. Tentando baixar Anton-Regular...")
            font_url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
            assets_dir = Path("src/assets/fonts")
            assets_dir.mkdir(parents=True, exist_ok=True)
            font_path = assets_dir / "Anton-Regular.ttf"

            import requests
            response = requests.get(font_url)
            if response.status_code == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                logger.info("✅ Fonte baixada com sucesso!")
                return ImageFont.truetype(str(font_path), size)
        except Exception as e:
            logger.warning(f"⚠️ Falha no download da fonte: {e}")

        logger.warning("⚠️ Usando fonte padrão (Pode não ficar bom)")
        return ImageFont.load_default()
