"""
Módulo de Edição de Vídeo (Stage 4) - VERSÃO 3.0
Corta, redimensiona e edita vídeos usando MoviePy

VERSÃO 3.0 - MELHORIAS:
- Detecção inteligente de tipo de conteúdo (animação, screencast, pessoa real)
- Preservação de legendas existentes
- Modo "letterbox" para conteúdo que não pode ser cortado
- Crop adaptativo baseado no tipo de conteúdo
"""
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import subprocess
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, ColorClip
from moviepy.video.fx.crop import crop
from moviepy.video.fx.resize import resize
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Import opcional do detector de legendas
try:
    from .subtitle_detector import SubtitleDetector
    SUBTITLE_DETECTOR_AVAILABLE = True
except ImportError:
    SUBTITLE_DETECTOR_AVAILABLE = False


class FaceTracker:
    """Classe para detecção e tracking de rostos em vídeos."""
    
    def __init__(self):
        """Inicializa o detector de rostos."""
        self.face_cascade = None
        self.initialized = False
        
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.warning("   ⚠️ Cascade classifier vazio")
            else:
                self.initialized = True
                logger.info("   ✅ Face Tracker inicializado com sucesso")
        except Exception as e:
            logger.warning(f"   ⚠️ Face Tracker não disponível: {e}")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta rostos em um frame.
        
        Returns:
            Lista de tuplas (x, y, width, height) para cada rosto
        """
        if not self.initialized or frame is None:
            return []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            return [(x, y, w, h) for (x, y, w, h) in faces]
        except Exception as e:
            logger.debug(f"   Erro na detecção de rostos: {e}")
            return []
    
    def get_faces_center(self, faces: List[Tuple[int, int, int, int]]) -> Tuple[float, float]:
        """
        Calcula o centro médio de todos os rostos detectados.
        
        Returns:
            Tupla (center_x, center_y) ou None se não houver rostos
        """
        if not faces:
            return None
        
        centers_x = [x + w/2 for (x, y, w, h) in faces]
        centers_y = [y + h/2 for (x, y, w, h) in faces]
        
        return (np.mean(centers_x), np.mean(centers_y))
    
    def get_bounding_box(self, faces: List[Tuple[int, int, int, int]], padding: float = 0.2) -> Tuple[int, int, int, int]:
        """
        Calcula bounding box que engloba todos os rostos.
        
        Returns:
            Tupla (x, y, width, height) ou None
        """
        if not faces:
            return None
        
        min_x = min(x for (x, y, w, h) in faces)
        min_y = min(y for (x, y, w, h) in faces)
        max_x = max(x + w for (x, y, w, h) in faces)
        max_y = max(y + h for (x, y, w, h) in faces)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Adicionar padding
        pad_x = int(width * padding)
        pad_y = int(height * padding)
        
        return (
            max(0, min_x - pad_x),
            max(0, min_y - pad_y),
            int(width + 2 * pad_x),
            int(height + 2 * pad_y)
        )


class ContentAnalyzer:
    """Analisa o tipo de conteúdo do vídeo para determinar estratégia de crop."""
    
    # Tipos de conteúdo
    CONTENT_TALKING_HEAD = "talking_head"      # Pessoa falando (pode fazer crop agressivo)
    CONTENT_ANIMATION = "animation"            # Animação/desenho (crop moderado)
    CONTENT_SCREENCAST = "screencast"          # Tela de computador/interface (não cortar)
    CONTENT_MIXED = "mixed"                    # Conteúdo misto (letterbox)
    CONTENT_TEXT_HEAVY = "text_heavy"          # Muito texto/legendas (não cortar)
    
    def __init__(self):
        self.face_tracker = FaceTracker()
    
    def analyze_content(self, video_path: Path, sample_count: int = 10) -> Dict:
        """
        Analisa o conteúdo do vídeo para determinar a melhor estratégia de crop.
        
        Returns:
            Dict com tipo de conteúdo e recomendações
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {'type': self.CONTENT_MIXED, 'can_crop': False}
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Métricas para análise
        face_detections = 0
        text_regions = 0
        edge_density_samples = []
        color_variance_samples = []
        
        for i in range(sample_count):
            timestamp = duration * (i + 1) / (sample_count + 1)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            # Detectar rostos
            faces = self.face_tracker.detect_faces(frame)
            if faces:
                face_detections += 1
            
            # Analisar densidade de bordas (interfaces têm muitas bordas retas)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (frame_height * frame_width)
            edge_density_samples.append(edge_density)
            
            # Analisar variância de cores (animações têm cores mais uniformes)
            color_variance = np.std(frame)
            color_variance_samples.append(color_variance)
            
            # Detectar regiões de texto (alto contraste local)
            text_score = self._detect_text_regions(frame)
            if text_score > 0.3:
                text_regions += 1
        
        cap.release()
        
        # Determinar tipo de conteúdo
        face_ratio = face_detections / sample_count
        text_ratio = text_regions / sample_count
        avg_edge_density = np.mean(edge_density_samples) if edge_density_samples else 0
        avg_color_variance = np.mean(color_variance_samples) if color_variance_samples else 0
        
        content_type = self._determine_content_type(
            face_ratio, text_ratio, avg_edge_density, avg_color_variance
        )
        
        # Determinar se pode fazer crop
        can_crop_aggressively = content_type == self.CONTENT_TALKING_HEAD and face_ratio > 0.5
        should_use_letterbox = content_type in [self.CONTENT_SCREENCAST, self.CONTENT_TEXT_HEAVY, self.CONTENT_MIXED]
        
        result = {
            'type': content_type,
            'face_ratio': face_ratio,
            'text_ratio': text_ratio,
            'edge_density': avg_edge_density,
            'can_crop_aggressively': can_crop_aggressively,
            'should_use_letterbox': should_use_letterbox,
            'recommended_strategy': self._get_recommended_strategy(content_type, face_ratio, text_ratio)
        }
        
        logger.info(f"   📊 Análise de conteúdo:")
        logger.info(f"      Tipo: {content_type}")
        logger.info(f"      Rostos detectados: {face_ratio:.0%}")
        logger.info(f"      Regiões de texto: {text_ratio:.0%}")
        logger.info(f"      Estratégia recomendada: {result['recommended_strategy']}")
        
        return result
    
    def _detect_text_regions(self, frame: np.ndarray) -> float:
        """Detecta quantidade de texto/legendas no frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Região inferior (onde geralmente ficam legendas)
        h, w = gray.shape
        bottom_region = gray[int(h * 0.7):, :]
        
        # Detectar alto contraste (texto branco em fundo escuro ou vice-versa)
        _, binary = cv2.threshold(bottom_region, 200, 255, cv2.THRESH_BINARY)
        white_ratio = np.sum(binary > 0) / binary.size
        
        # Detectar bordas (texto tem muitas bordas)
        edges = cv2.Canny(bottom_region, 50, 150)
        edge_ratio = np.sum(edges > 0) / edges.size
        
        return (white_ratio * 0.5 + edge_ratio * 0.5)
    
    def _determine_content_type(
        self, 
        face_ratio: float, 
        text_ratio: float, 
        edge_density: float,
        color_variance: float
    ) -> str:
        """Determina o tipo de conteúdo baseado nas métricas."""
        
        # Muito texto = não cortar
        if text_ratio > 0.5:
            return self.CONTENT_TEXT_HEAVY
        
        # Muitos rostos = talking head
        if face_ratio > 0.6:
            return self.CONTENT_TALKING_HEAD
        
        # Alta densidade de bordas + baixa variância de cor = screencast/interface
        if edge_density > 0.15 and color_variance < 50:
            return self.CONTENT_SCREENCAST
        
        # Baixa variância de cor = animação
        if color_variance < 40:
            return self.CONTENT_ANIMATION
        
        # Conteúdo misto
        return self.CONTENT_MIXED
    
    def _get_recommended_strategy(
        self, 
        content_type: str, 
        face_ratio: float,
        text_ratio: float
    ) -> str:
        """Retorna a estratégia recomendada de crop."""
        
        if content_type == self.CONTENT_TALKING_HEAD and face_ratio > 0.7:
            return "face_tracking"
        
        if content_type in [self.CONTENT_SCREENCAST, self.CONTENT_TEXT_HEAVY]:
            return "letterbox"
        
        if content_type == self.CONTENT_ANIMATION:
            return "letterbox_or_minimal_crop"
        
        if text_ratio > 0.3:
            return "letterbox"
        
        return "minimal_crop"


class VideoEditor:
    """Editor de vídeo para criar clipes 9:16 com crop inteligente."""

    def __init__(self):
        self.target_width, self.target_height = Config.OUTPUT_RESOLUTION
        self.fps = Config.VIDEO_FPS
        self.quality_settings = Config.get_quality_settings()
        self.face_tracker = FaceTracker()
        self.content_analyzer = ContentAnalyzer()
        
        # Inicializar detector de legendas
        self.subtitle_detector = None
        if SUBTITLE_DETECTOR_AVAILABLE:
            self.subtitle_detector = SubtitleDetector()
        
        logger.info(f"🎬 Video Editor inicializado (V3.0)")
        logger.info(f"   Resolução alvo: {self.target_width}x{self.target_height}")
        logger.info(f"   Face Tracking: {'Ativo' if self.face_tracker.initialized else 'Inativo'}")
        logger.info(f"   Detecção de Legendas: {'Ativo' if self.subtitle_detector else 'Inativo'}")
        logger.info(f"   Análise de Conteúdo: Ativo")

    def create_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
        crop_mode: str = 'auto'
    ) -> Path:
        """
        Cria um clipe vertical (9:16) do vídeo.
        
        Args:
            video_path: Caminho do vídeo original
            start_time: Tempo de início em segundos
            end_time: Tempo de fim em segundos
            output_path: Caminho para salvar o clipe
            crop_mode: 'auto', 'face_tracking', 'letterbox', 'center', 'smart'
        """
        logger.info(f"✂️  Cortando vídeo: {start_time:.1f}s -> {end_time:.1f}s (Modo: {crop_mode})")
        
        try:
            # Carregar vídeo
            clip = VideoFileClip(str(video_path)).subclip(start_time, end_time)
            
            # Analisar conteúdo do vídeo
            content_analysis = self.content_analyzer.analyze_content(video_path, sample_count=8)
            
            # Detectar legendas existentes
            subtitle_data = None
            if self.subtitle_detector:
                subtitle_data = self.subtitle_detector.detect_subtitle_regions(video_path, sample_count=5)
            
            # Analisar rostos se necessário
            face_data = None
            if crop_mode in ['face_tracking', 'smart', 'auto'] and Config.FACE_TRACKING_ENABLED:
                face_data = self._analyze_faces_in_clip(video_path, start_time, end_time)
            
            # Determinar modo de crop baseado na análise
            if crop_mode == 'auto':
                crop_mode = self._determine_best_crop_mode(content_analysis, face_data, subtitle_data)
                logger.info(f"   🤖 Modo automático selecionou: {crop_mode}")
            
            # Aplicar crop/resize
            final_clip = self._apply_crop_strategy(clip, crop_mode, face_data, subtitle_data, content_analysis)

            # Visual Polish (Color Grading)
            try:
                from src.modules.visual_polisher import VisualPolisher
                polisher = VisualPolisher()
                final_clip = polisher.apply_style(final_clip, 'General')
            except Exception as e:
                logger.debug(f"   Visual polish não aplicado: {e}")

            # Garantir diretório de saída
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Exportar
            final_clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                bitrate=self.quality_settings.get('video_bitrate', '5M'),
                audio_bitrate=self.quality_settings.get('audio_bitrate', '192k'),
                logger=None
            )

            # Limpar
            clip.close()
            final_clip.close()

            logger.info(f"✅ Clipe salvo: {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro ao criar clipe: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _determine_best_crop_mode(
        self, 
        content_analysis: Dict, 
        face_data: Dict,
        subtitle_data: Dict
    ) -> str:
        """Determina o melhor modo de crop baseado na análise."""
        
        # Se tem muitas legendas, usar letterbox
        if subtitle_data and subtitle_data.get('has_subtitles'):
            if subtitle_data.get('confidence', 0) > 0.5:
                logger.info(f"   📝 Legendas detectadas com alta confiança - usando letterbox")
                return 'letterbox'
        
        # Baseado no tipo de conteúdo
        content_type = content_analysis.get('type', 'mixed')
        
        if content_type == ContentAnalyzer.CONTENT_TALKING_HEAD:
            if face_data and face_data.get('total_faces_detected', 0) > 5:
                return 'face_tracking'
        
        if content_type in [ContentAnalyzer.CONTENT_SCREENCAST, ContentAnalyzer.CONTENT_TEXT_HEAVY]:
            return 'letterbox'
        
        if content_type == ContentAnalyzer.CONTENT_ANIMATION:
            return 'letterbox'
        
        if content_type == ContentAnalyzer.CONTENT_MIXED:
            return 'letterbox'
        
        return 'minimal_crop'

    def _apply_crop_strategy(
        self,
        clip: VideoFileClip,
        crop_mode: str,
        face_data: Dict,
        subtitle_data: Dict,
        content_analysis: Dict
    ) -> VideoFileClip:
        """Aplica a estratégia de crop selecionada."""
        
        if crop_mode == 'letterbox':
            return self._create_letterbox(clip, subtitle_data)
        
        elif crop_mode == 'face_tracking':
            if face_data and face_data.get('total_faces_detected', 0) > 0:
                return self._crop_with_face_tracking_safe(clip, face_data, subtitle_data)
            else:
                return self._create_letterbox(clip, subtitle_data)
        
        elif crop_mode == 'minimal_crop':
            return self._crop_minimal(clip, subtitle_data)
        
        elif crop_mode == 'smart':
            return self._crop_smart(clip, face_data, subtitle_data)
        
        elif crop_mode == 'center':
            return self._crop_center(clip, subtitle_data)
        
        else:
            return self._create_letterbox(clip, subtitle_data)

    def _create_letterbox(self, clip: VideoFileClip, subtitle_data: Dict = None) -> VideoFileClip:
        """
        Cria vídeo em letterbox (barras pretas) para preservar todo o conteúdo.
        O vídeo original é redimensionado para caber inteiro no formato 9:16.
        """
        original_w, original_h = clip.size
        
        logger.info(f"   📦 Criando letterbox para preservar conteúdo")
        logger.info(f"      Original: {original_w}x{original_h}")
        
        # Calcular escala para caber no formato vertical
        scale_w = self.target_width / original_w
        scale_h = self.target_height / original_h
        scale = min(scale_w, scale_h)  # Usar a menor escala para caber tudo
        
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        
        # Redimensionar o vídeo
        resized_clip = clip.resize((new_w, new_h))
        
        # Criar fundo preto
        bg = ColorClip(size=(self.target_width, self.target_height), color=(0, 0, 0))
        bg = bg.set_duration(clip.duration)
        
        # Posicionar o vídeo no centro (ou levemente acima para deixar espaço para legendas)
        x_pos = (self.target_width - new_w) // 2
        
        # Se tem legendas na base, posicionar vídeo mais acima
        if subtitle_data and subtitle_data.get('subtitle_position') == 'bottom':
            y_pos = int((self.target_height - new_h) * 0.3)  # 30% do espaço disponível
        else:
            y_pos = (self.target_height - new_h) // 2
        
        # Compor vídeo sobre fundo
        final = CompositeVideoClip([
            bg,
            resized_clip.set_position((x_pos, y_pos))
        ])
        
        logger.info(f"      Novo tamanho: {new_w}x{new_h}")
        logger.info(f"      Posição: ({x_pos}, {y_pos})")
        
        return final

    def _crop_minimal(self, clip: VideoFileClip, subtitle_data: Dict = None) -> VideoFileClip:
        """
        Crop mínimo - corta apenas o necessário para chegar em 9:16.
        Prioriza manter o máximo de conteúdo possível.
        """
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width  # 1920/1080 = 1.777
        original_ratio = original_h / original_w
        
        logger.info(f"   ✂️ Crop mínimo")
        
        # Se o vídeo já é mais vertical que 9:16, usar letterbox
        if original_ratio >= target_ratio:
            return self._create_letterbox(clip, subtitle_data)
        
        # Calcular crop necessário (cortar laterais)
        crop_width = int(original_h / target_ratio)
        crop_height = original_h
        
        # Centralizar o crop
        center_x = original_w / 2
        center_y = original_h / 2
        
        # Ajustar se houver legendas
        if subtitle_data and subtitle_data.get('has_subtitles'):
            # Não ajustar Y para não cortar legendas
            pass
        
        # Garantir limites
        center_x = max(crop_width / 2, min(center_x, original_w - crop_width / 2))
        
        clip_cropped = crop(
            clip,
            x_center=center_x,
            y_center=center_y,
            width=crop_width,
            height=crop_height
        )
        
        clip_resized = clip_cropped.resize((self.target_width, self.target_height))
        return clip_resized

    def _crop_with_face_tracking_safe(
        self, 
        clip: VideoFileClip, 
        face_data: Dict,
        subtitle_data: Dict = None
    ) -> VideoFileClip:
        """
        Crop com face tracking SEGURO - não corta legendas.
        Se detectar que vai cortar legendas, usa letterbox.
        """
        original_w, original_h = clip.size
        
        # Verificar se tem legendas que seriam cortadas
        if subtitle_data and subtitle_data.get('has_subtitles'):
            subtitle_pos = subtitle_data.get('subtitle_position')
            confidence = subtitle_data.get('confidence', 0)
            
            if confidence > 0.4:
                logger.info(f"   ⚠️ Legendas detectadas em '{subtitle_pos}' - usando letterbox para preservar")
                return self._create_letterbox(clip, subtitle_data)
        
        # Se poucos rostos detectados, usar letterbox
        if face_data.get('total_faces_detected', 0) < 3:
            logger.info(f"   ⚠️ Poucos rostos detectados - usando letterbox")
            return self._create_letterbox(clip, subtitle_data)
        
        target_ratio = self.target_height / self.target_width
        
        # Calcular dimensões do crop
        crop_width = int(original_h / target_ratio)
        if crop_width > original_w:
            # Vídeo muito estreito, usar letterbox
            return self._create_letterbox(clip, subtitle_data)
        
        crop_height = original_h
        
        # Determinar centro do crop baseado nos rostos
        if face_data.get('is_single_person') and face_data.get('avg_center'):
            center_x, center_y = face_data['avg_center']
            logger.info(f"   🎯 Focando em uma pessoa em ({center_x:.0f}, {center_y:.0f})")
        elif face_data.get('is_multiple_people') and face_data.get('bounding_box'):
            bbox = face_data['bounding_box']
            center_x = bbox[0] + bbox[2] / 2
            center_y = bbox[1] + bbox[3] / 2
            logger.info(f"   🎯 Enquadrando múltiplas pessoas")
        else:
            center_x = original_w / 2
            center_y = original_h / 2
        
        # Garantir que o crop não saia dos limites
        center_x = max(crop_width / 2, min(center_x, original_w - crop_width / 2))
        center_y = max(crop_height / 2, min(center_y, original_h - crop_height / 2))
        
        # Aplicar crop
        clip_cropped = crop(
            clip,
            x_center=center_x,
            y_center=center_y,
            width=crop_width,
            height=crop_height
        )
        
        clip_resized = clip_cropped.resize((self.target_width, self.target_height))
        return clip_resized

    def _crop_center(self, clip: VideoFileClip, subtitle_data: Dict = None) -> VideoFileClip:
        """Crop central simples para 9:16."""
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width

        # Calcular dimensões do crop
        crop_width = int(original_h / target_ratio)

        if crop_width > original_w:
            # Vídeo muito estreito, usar letterbox
            return self._create_letterbox(clip, subtitle_data)
        
        crop_height = original_h
        x_center = original_w / 2
        y_center = original_h / 2

        clip_cropped = crop(
            clip,
            x_center=x_center,
            y_center=y_center,
            width=crop_width,
            height=crop_height
        )

        clip_resized = clip_cropped.resize((self.target_width, self.target_height))
        return clip_resized

    def _crop_smart(self, clip: VideoFileClip, face_data: Dict, subtitle_data: Dict = None) -> VideoFileClip:
        """
        Crop inteligente que considera todos os fatores.
        """
        # Se tem legendas, usar letterbox
        if subtitle_data and subtitle_data.get('has_subtitles'):
            if subtitle_data.get('confidence', 0) > 0.4:
                return self._create_letterbox(clip, subtitle_data)
        
        # Se tem rostos, usar face tracking seguro
        if face_data and face_data.get('total_faces_detected', 0) > 3:
            return self._crop_with_face_tracking_safe(clip, face_data, subtitle_data)
        
        # Caso contrário, letterbox
        return self._create_letterbox(clip, subtitle_data)

    def _analyze_faces_in_clip(
        self, 
        video_path: Path, 
        start_time: float, 
        end_time: float
    ) -> Dict:
        """
        Analisa rostos no intervalo do clipe.
        """
        logger.info(f"   🔍 Analisando rostos no clipe...")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {}
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        all_faces = []
        all_centers = []
        frames_analyzed = 0
        
        # Amostrar frames no intervalo
        duration = end_time - start_time
        sample_count = min(20, max(5, int(duration * 2)))
        
        for i in range(sample_count):
            timestamp = start_time + (duration * i / sample_count)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            frames_analyzed += 1
            faces = self.face_tracker.detect_faces(frame)
            
            if faces:
                all_faces.extend(faces)
                center = self.face_tracker.get_faces_center(faces)
                if center:
                    all_centers.append(center)
        
        cap.release()
        
        # Compilar resultados
        result = {
            'total_faces_detected': len(all_faces),
            'frames_analyzed': frames_analyzed,
            'avg_faces_per_frame': len(all_faces) / max(frames_analyzed, 1),
            'avg_center': None,
            'bounding_box': None,
            'is_single_person': False,
            'is_multiple_people': False
        }
        
        if all_centers:
            result['avg_center'] = (
                np.mean([c[0] for c in all_centers]),
                np.mean([c[1] for c in all_centers])
            )
        
        if all_faces:
            result['bounding_box'] = self.face_tracker.get_bounding_box(all_faces)
            
            # Determinar se é uma pessoa ou múltiplas
            avg_faces = result['avg_faces_per_frame']
            if avg_faces <= 1.5:
                result['is_single_person'] = True
            elif avg_faces > 1.5:
                result['is_multiple_people'] = True
        
        logger.info(f"      Rostos detectados: {result['total_faces_detected']}")
        logger.info(f"      Média por frame: {result['avg_faces_per_frame']:.1f}")
        logger.info(f"      Tipo: {'Uma pessoa' if result['is_single_person'] else 'Múltiplas pessoas' if result['is_multiple_people'] else 'Sem rostos'}")
        
        return result

    def batch_create_clips(
        self,
        video_path: Path,
        moments: list,
        output_dir: Path
    ) -> list:
        """
        Cria múltiplos clipes de uma vez.
        """
        logger.info(f"📦 Criando {len(moments)} clipes em lote...")

        output_paths = []

        for i, moment in enumerate(moments, 1):
            output_path = output_dir / f"clip_{i:02d}_score{moment['score']}.mp4"

            try:
                path = self.create_clip(
                    video_path,
                    moment['start'],
                    moment['end'],
                    output_path,
                    crop_mode='auto'  # Usar modo automático
                )
                output_paths.append(path)

            except Exception as e:
                logger.error(f"   Erro no clipe {i}: {e}")
                continue

        logger.info(f"✅ {len(output_paths)}/{len(moments)} clipes criados com sucesso")
        return output_paths


if __name__ == "__main__":
    # Teste rápido
    editor = VideoEditor()
    print("Video Editor V3.0 inicializado com sucesso!")
    print(f"Face Tracking disponível: {editor.face_tracker.initialized}")
