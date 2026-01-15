"""
Módulo de Geração de Thumbnails IA (Fase 21) - CORRIGIDO
Cria thumbnails virais extraindo rostos e adicionando textos/efeitos.
Corrigido: dimensionamento, detecção de rostos, fontes, corte adequado.
"""
import logging
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
import os

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    # Tamanho padrão de thumbnail para YouTube/TikTok
    THUMBNAIL_SIZE = (1280, 720)  # 16:9 para YouTube
    THUMBNAIL_SIZE_VERTICAL = (1080, 1920)  # 9:16 para TikTok/Reels
    
    def __init__(self):
        logger.info("🖼️ Thumbnail Generator: Inicializado (Versão Corrigida)")
        # Cores vibrantes para stroke/borda
        self.stroke_colors = ['#FF0000', '#00FF00', '#FFFF00', '#00FFFF', '#FF00FF']
        
        # Carregar cascade para detecção de rostos
        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            logger.info("   ✅ Face detection habilitado")
        except Exception as e:
            logger.warning(f"   ⚠️ Face detection não disponível: {e}")

    def generate_thumbnail(
        self, 
        video_path: Path, 
        moment: dict, 
        output_path: Path,
        vertical: bool = True
    ) -> Path:
        """
        Gera uma thumbnail para o momento viral.
        
        Args:
            video_path: Caminho do vídeo
            moment: Dicionário com start, end, hook
            output_path: Caminho para salvar a thumbnail
            vertical: Se True, gera thumbnail vertical (9:16), senão horizontal (16:9)
        """
        try:
            # 1. Encontrar o melhor frame (com rosto visível)
            frame = self._find_best_frame(video_path, moment)
            
            if frame is None:
                logger.warning("   ⚠️ Falha ao extrair frame para thumbnail")
                return None

            # 2. Converter para PIL
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # 3. Determinar tamanho alvo
            target_size = self.THUMBNAIL_SIZE_VERTICAL if vertical else self.THUMBNAIL_SIZE
            
            # 4. Redimensionar e cortar inteligentemente
            img = self._smart_crop_and_resize(img, target_size, frame)
            
            # 5. Aplicar melhorias visuais
            img = self._enhance_image(img)
            
            # 6. Tentar remover fundo (opcional)
            img = self._try_remove_background(img)
            
            # 7. Adicionar texto overlay
            img = self._add_text_overlay(img, moment.get('hook', ''), target_size)
            
            # 8. Salvar com qualidade alta
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_path), quality=95, optimize=True)
            
            logger.info(f"   🖼️ Thumbnail salva: {output_path.name} ({target_size[0]}x{target_size[1]})")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro ao gerar thumbnail: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _find_best_frame(self, video_path: Path, moment: dict) -> np.ndarray:
        """
        Encontra o melhor frame no intervalo do momento.
        Prioriza frames com rostos visíveis e boa iluminação.
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            logger.error(f"   ❌ Não foi possível abrir o vídeo: {video_path}")
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        start_time = moment.get('start', 0)
        end_time = moment.get('end', start_time + 10)
        
        # Amostrar frames no intervalo
        sample_times = [
            start_time + (end_time - start_time) * 0.2,  # 20%
            start_time + (end_time - start_time) * 0.4,  # 40%
            start_time + (end_time - start_time) * 0.5,  # 50% (meio)
            start_time + (end_time - start_time) * 0.6,  # 60%
            start_time + (end_time - start_time) * 0.8,  # 80%
        ]
        
        best_frame = None
        best_score = -1
        
        for timestamp in sample_times:
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            # Calcular score do frame
            score = self._calculate_frame_score(frame)
            
            if score > best_score:
                best_score = score
                best_frame = frame.copy()
        
        cap.release()
        
        # Se não encontrou nenhum frame bom, pegar do meio
        if best_frame is None:
            cap = cv2.VideoCapture(str(video_path))
            middle_time = (start_time + end_time) / 2
            cap.set(cv2.CAP_PROP_POS_MSEC, middle_time * 1000)
            ret, best_frame = cap.read()
            cap.release()
        
        return best_frame

    def _calculate_frame_score(self, frame: np.ndarray) -> float:
        """
        Calcula um score de qualidade para o frame.
        Considera: presença de rostos, nitidez, iluminação.
        """
        score = 0.0
        
        # 1. Detectar rostos (+50 pontos por rosto)
        if self.face_cascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5,
                minSize=(50, 50)
            )
            score += len(faces) * 50
            
            # Bonus se rosto está centralizado
            if len(faces) > 0:
                h, w = frame.shape[:2]
                for (x, y, fw, fh) in faces:
                    face_center_x = x + fw/2
                    face_center_y = y + fh/2
                    # Quanto mais perto do centro, melhor
                    dist_from_center = abs(face_center_x - w/2) / w + abs(face_center_y - h/2) / h
                    score += (1 - dist_from_center) * 20
        
        # 2. Calcular nitidez (Laplacian variance)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        score += min(laplacian_var / 100, 30)  # Max 30 pontos
        
        # 3. Calcular iluminação (evitar frames muito escuros ou claros)
        brightness = np.mean(gray)
        if 80 < brightness < 180:  # Faixa ideal
            score += 20
        elif 50 < brightness < 200:
            score += 10
        
        return score

    def _smart_crop_and_resize(
        self, 
        img: Image.Image, 
        target_size: tuple,
        frame: np.ndarray = None
    ) -> Image.Image:
        """
        Redimensiona e corta a imagem de forma inteligente.
        Tenta manter rostos visíveis no crop.
        """
        original_w, original_h = img.size
        target_w, target_h = target_size
        target_ratio = target_w / target_h
        original_ratio = original_w / original_h
        
        # Detectar rostos para centralizar o crop
        crop_center_x = original_w / 2
        crop_center_y = original_h / 2
        
        if frame is not None and self.face_cascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
            
            if len(faces) > 0:
                # Calcular centro médio dos rostos
                face_centers_x = [x + w/2 for (x, y, w, h) in faces]
                face_centers_y = [y + h/2 for (x, y, w, h) in faces]
                crop_center_x = np.mean(face_centers_x)
                crop_center_y = np.mean(face_centers_y)
        
        # Calcular dimensões do crop
        if original_ratio > target_ratio:
            # Imagem mais larga - cortar laterais
            new_width = int(original_h * target_ratio)
            new_height = original_h
        else:
            # Imagem mais alta - cortar topo/base
            new_width = original_w
            new_height = int(original_w / target_ratio)
        
        # Calcular posição do crop centrado no rosto
        left = max(0, min(crop_center_x - new_width/2, original_w - new_width))
        top = max(0, min(crop_center_y - new_height/2, original_h - new_height))
        right = left + new_width
        bottom = top + new_height
        
        # Aplicar crop
        img_cropped = img.crop((int(left), int(top), int(right), int(bottom)))
        
        # Redimensionar para tamanho final
        img_resized = img_cropped.resize(target_size, Image.Resampling.LANCZOS)
        
        return img_resized

    def _enhance_image(self, img: Image.Image) -> Image.Image:
        """Aplica melhorias visuais na imagem."""
        # Aumentar contraste levemente
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)
        
        # Aumentar saturação levemente
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        
        # Aumentar nitidez
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        return img

    def _try_remove_background(self, img: Image.Image) -> Image.Image:
        """Tenta remover o fundo usando rembg (se disponível)."""
        try:
            from rembg import remove
            
            # Remover fundo
            subject = remove(img)
            
            # Criar fundo gradiente escuro
            bg = Image.new('RGB', img.size, (20, 20, 30))
            draw = ImageDraw.Draw(bg)
            
            # Adicionar brilho sutil atrás do sujeito
            cx, cy = bg.width // 2, bg.height // 2
            for i in range(5):
                radius = 200 + i * 50
                alpha = 30 - i * 5
                color = (40 + i*5, 40 + i*5, 60 + i*5)
                draw.ellipse(
                    (cx-radius, cy-radius, cx+radius, cy+radius), 
                    fill=color
                )
            
            # Compor sujeito sobre fundo
            bg.paste(subject, (0, 0), subject)
            return bg
            
        except ImportError:
            logger.debug("   ℹ️ rembg não instalado, usando imagem original")
            return img
        except Exception as e:
            logger.debug(f"   ℹ️ Erro no rembg: {e}. Usando original.")
            return img

    def _add_text_overlay(
        self, 
        img: Image.Image, 
        text: str, 
        target_size: tuple
    ) -> Image.Image:
        """Adiciona texto overlay na thumbnail."""
        if not text:
            return img
        
        draw = ImageDraw.Draw(img)
        
        # Determinar tamanho da fonte baseado no tamanho da imagem
        base_fontsize = min(target_size) // 12
        
        # Tentar carregar fonte (com fallbacks)
        font = self._get_font(base_fontsize)
        
        # Preparar texto (uppercase e quebrar linhas)
        text = text.upper().strip()
        lines = self._wrap_text(text, font, img.width * 0.9, draw)
        
        # Calcular posição vertical (parte superior da imagem)
        y_start = img.height * 0.05
        line_height = base_fontsize * 1.3
        
        # Desenhar cada linha
        for i, line in enumerate(lines[:3]):  # Máximo 3 linhas
            y_pos = y_start + i * line_height
            
            # Calcular largura do texto para centralizar
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * base_fontsize * 0.6
            
            x_pos = (img.width - text_width) / 2
            
            # Desenhar stroke (borda preta)
            stroke_width = max(3, base_fontsize // 20)
            for ox in range(-stroke_width, stroke_width + 1):
                for oy in range(-stroke_width, stroke_width + 1):
                    if ox != 0 or oy != 0:
                        draw.text((x_pos + ox, y_pos + oy), line, font=font, fill='black')
            
            # Desenhar texto principal (cor vibrante)
            text_colors = ['#FFFF00', '#FFFFFF', '#00FF00', '#FF6600']
            text_color = text_colors[i % len(text_colors)]
            draw.text((x_pos, y_pos), line, font=font, fill=text_color)
        
        return img

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Obtém uma fonte adequada com fallbacks."""
        # Lista de fontes para tentar (em ordem de preferência)
        font_paths = [
            # Linux
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            '/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf',
            # Windows
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/impact.ttf',
            # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial Bold.ttf',
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        
        # Fallback para fonte padrão
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except:
            logger.warning("   ⚠️ Usando fonte padrão do sistema")
            return ImageFont.load_default()

    def _wrap_text(
        self, 
        text: str, 
        font: ImageFont.FreeTypeFont, 
        max_width: float,
        draw: ImageDraw.Draw
    ) -> list:
        """Quebra texto em múltiplas linhas."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(test_line) * 20  # Estimativa
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def _extract_frame(self, video_path: Path, timestamp: float) -> np.ndarray:
        """Extrai um frame específico do vídeo (método legado)."""
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None


if __name__ == "__main__":
    # Teste rápido
    generator = ThumbnailGenerator()
    print("Thumbnail Generator inicializado com sucesso!")
