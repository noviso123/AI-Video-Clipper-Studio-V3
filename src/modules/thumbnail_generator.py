"""
Módulo de Geração de Thumbnails IA (Fase 21) - VERSÃO 2.0
Cria thumbnails virais extraindo rostos e adicionando textos/efeitos.
MELHORIAS V2:
- Busca extensiva por frames com rostos em todo o vídeo
- Fallback inteligente para vídeos sem rostos (screencast, animações)
- Melhor seleção de frames baseado em qualidade visual
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
        logger.info("🖼️ Thumbnail Generator: Inicializado (Versão 2.0)")
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
            # 1. Encontrar o melhor frame (PRIORIZA frames com rostos)
            frame, has_face = self._find_best_frame_with_face(video_path, moment)
            
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
            
            # 6. Tentar remover fundo (apenas se tem rosto)
            if has_face:
                img = self._try_remove_background(img)
            
            # 7. Adicionar texto overlay
            img = self._add_text_overlay(img, moment.get('hook', ''), target_size)
            
            # 8. Salvar com qualidade alta
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(output_path), quality=95, optimize=True)
            
            logger.info(f"   🖼️ Thumbnail salva: {output_path.name} ({target_size[0]}x{target_size[1]})")
            logger.info(f"      Rosto detectado: {'Sim' if has_face else 'Não (usando melhor frame)'}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro ao gerar thumbnail: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _find_best_frame_with_face(self, video_path: Path, moment: dict) -> tuple:
        """
        Encontra o melhor frame no vídeo, priorizando frames com rostos.
        
        ESTRATÉGIA:
        1. Primeiro, busca frames com rostos no intervalo do momento
        2. Se não encontrar, busca em todo o vídeo
        3. Se ainda não encontrar, retorna o frame de melhor qualidade
        
        Returns:
            Tupla (frame, has_face)
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            logger.error(f"   ❌ Não foi possível abrir o vídeo: {video_path}")
            return None, False
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        start_time = moment.get('start', 0)
        end_time = moment.get('end', min(start_time + 30, duration))
        
        logger.info(f"   🔍 Buscando melhor frame para thumbnail...")
        logger.info(f"      Intervalo do momento: {start_time:.1f}s - {end_time:.1f}s")
        
        # ========== FASE 1: Buscar no intervalo do momento ==========
        best_face_frame = None
        best_face_score = -1
        best_quality_frame = None
        best_quality_score = -1
        
        # Amostrar mais frames no intervalo
        interval_duration = end_time - start_time
        num_samples = min(20, max(5, int(interval_duration)))
        
        for i in range(num_samples):
            timestamp = start_time + (interval_duration * i / num_samples)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            # Verificar se tem rosto
            face_score, has_face = self._calculate_face_score(frame)
            quality_score = self._calculate_quality_score(frame)
            
            if has_face and face_score > best_face_score:
                best_face_score = face_score
                best_face_frame = frame.copy()
            
            if quality_score > best_quality_score:
                best_quality_score = quality_score
                best_quality_frame = frame.copy()
        
        # Se encontrou frame com rosto no intervalo, usar
        if best_face_frame is not None:
            logger.info(f"      ✅ Encontrado frame com rosto no intervalo (score: {best_face_score:.1f})")
            cap.release()
            return best_face_frame, True
        
        # ========== FASE 2: Buscar em todo o vídeo ==========
        logger.info(f"      ⚠️ Sem rostos no intervalo. Buscando em todo o vídeo...")
        
        # Amostrar frames ao longo de todo o vídeo
        num_global_samples = min(50, max(10, int(duration / 2)))
        
        for i in range(num_global_samples):
            timestamp = duration * i / num_global_samples
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            face_score, has_face = self._calculate_face_score(frame)
            
            if has_face and face_score > best_face_score:
                best_face_score = face_score
                best_face_frame = frame.copy()
        
        cap.release()
        
        # Se encontrou frame com rosto em qualquer lugar do vídeo
        if best_face_frame is not None:
            logger.info(f"      ✅ Encontrado frame com rosto no vídeo (score: {best_face_score:.1f})")
            return best_face_frame, True
        
        # ========== FASE 3: Fallback - usar melhor frame de qualidade ==========
        logger.info(f"      ℹ️ Vídeo sem rostos detectáveis. Usando frame de melhor qualidade.")
        return best_quality_frame, False

    def _calculate_face_score(self, frame: np.ndarray) -> tuple:
        """
        Calcula score baseado em rostos detectados.
        
        Returns:
            Tupla (score, has_face)
        """
        if self.face_cascade is None:
            return 0.0, False
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5,
                minSize=(50, 50)
            )
            
            if len(faces) == 0:
                return 0.0, False
            
            score = 0.0
            h, w = frame.shape[:2]
            
            for (x, y, fw, fh) in faces:
                # Tamanho do rosto (rostos maiores = melhor)
                face_area = fw * fh
                frame_area = w * h
                size_score = (face_area / frame_area) * 100
                
                # Posição (rostos centralizados = melhor)
                face_center_x = x + fw/2
                face_center_y = y + fh/2
                dist_x = abs(face_center_x - w/2) / w
                dist_y = abs(face_center_y - h/2) / h
                position_score = (1 - dist_x) * 20 + (1 - dist_y) * 20
                
                score += size_score + position_score
            
            # Bonus para um único rosto bem enquadrado
            if len(faces) == 1:
                score += 30
            
            return score, True
            
        except Exception as e:
            logger.debug(f"   Erro ao calcular face score: {e}")
            return 0.0, False

    def _calculate_quality_score(self, frame: np.ndarray) -> float:
        """
        Calcula score de qualidade visual do frame.
        Considera: nitidez, iluminação, contraste.
        """
        score = 0.0
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 1. Nitidez (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            score += min(laplacian_var / 100, 30)
            
            # 2. Iluminação (evitar frames muito escuros ou claros)
            brightness = np.mean(gray)
            if 80 < brightness < 180:
                score += 30
            elif 50 < brightness < 200:
                score += 15
            
            # 3. Contraste
            contrast = gray.std()
            score += min(contrast / 10, 20)
            
            # 4. Colorfulness (evitar frames monocromáticos)
            if len(frame.shape) == 3:
                b, g, r = cv2.split(frame)
                rg = np.absolute(r.astype(float) - g.astype(float))
                yb = np.absolute(0.5 * (r.astype(float) + g.astype(float)) - b.astype(float))
                colorfulness = np.sqrt(rg.mean()**2 + yb.mean()**2) + 0.3 * np.sqrt(rg.std()**2 + yb.std()**2)
                score += min(colorfulness / 10, 20)
            
        except Exception as e:
            logger.debug(f"   Erro ao calcular quality score: {e}")
        
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
                
                # Para thumbnail vertical, posicionar rosto no terço superior
                if target_h > target_w:  # Vertical
                    # Ajustar para que o rosto fique no terço superior
                    crop_center_y = min(crop_center_y, original_h * 0.4)
        
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
            # Linux (Ubuntu/Debian)
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            # Linux (Fedora/Bazzite)
            '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf',
            '/usr/share/fonts/google-noto/NotoSans-Bold.ttf',
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
