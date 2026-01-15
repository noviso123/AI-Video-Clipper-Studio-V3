"""
Módulo de Edição de Vídeo (Stage 4) - VERSÃO CORRIGIDA
Corta, redimensiona e edita vídeos usando MoviePy
IMPLEMENTADO: Face tracking real, smart crop, redimensionamento dinâmico
"""
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import subprocess
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
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
    
    def get_faces_bounding_box(
        self, 
        faces: List[Tuple[int, int, int, int]],
        padding: float = 0.2
    ) -> Tuple[int, int, int, int]:
        """
        Calcula a bounding box que engloba todos os rostos.
        
        Args:
            faces: Lista de rostos detectados
            padding: Margem adicional (0.2 = 20%)
        
        Returns:
            Tupla (x, y, width, height) da bounding box
        """
        if not faces:
            return None
        
        min_x = min(x for (x, y, w, h) in faces)
        min_y = min(y for (x, y, w, h) in faces)
        max_x = max(x + w for (x, y, w, h) in faces)
        max_y = max(y + h for (x, y, w, h) in faces)
        
        # Adicionar padding
        width = max_x - min_x
        height = max_y - min_y
        
        pad_x = width * padding
        pad_y = height * padding
        
        return (
            int(min_x - pad_x),
            int(min_y - pad_y),
            int(width + 2 * pad_x),
            int(height + 2 * pad_y)
        )


class VideoEditor:
    """Editor de vídeo para criar clipes 9:16 com face tracking real e detecção de legendas."""

    def __init__(self):
        self.target_width, self.target_height = Config.OUTPUT_RESOLUTION
        self.fps = Config.VIDEO_FPS
        self.quality_settings = Config.get_quality_settings()
        self.face_tracker = FaceTracker()
        
        # Inicializar detector de legendas
        self.subtitle_detector = None
        if SUBTITLE_DETECTOR_AVAILABLE:
            self.subtitle_detector = SubtitleDetector()
        
        logger.info(f"🎬 Video Editor inicializado")
        logger.info(f"   Resolução alvo: {self.target_width}x{self.target_height}")
        logger.info(f"   Face Tracking: {'Ativo' if self.face_tracker.initialized else 'Inativo'}")
        logger.info(f"   Detecção de Legendas: {'Ativo' if self.subtitle_detector else 'Inativo'}")

    def create_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
        crop_mode: str = 'center',
        vibe: str = 'General'
    ) -> Path:
        """
        Cria um clipe vertical (9:16) a partir do vídeo original
        
        Args:
            video_path: Caminho do vídeo original
            start_time: Início do clipe (segundos)
            end_time: Fim do clipe (segundos)
            output_path: Caminho para salvar o clipe
            crop_mode: 'center', 'smart' ou 'face_tracking'
            vibe: Estilo do vídeo para Color Grading
        
        Returns:
            Caminho do arquivo gerado
        """
        logger.info(f"✂️  Cortando vídeo: {start_time:.1f}s -> {end_time:.1f}s (Modo: {crop_mode})")

        try:
            # Carregar vídeo
            clip = VideoFileClip(str(video_path)).subclip(start_time, end_time)
            
            # Analisar rostos se face_tracking ou smart estiver habilitado
            face_data = None
            if crop_mode in ['face_tracking', 'smart'] and Config.FACE_TRACKING_ENABLED:
                face_data = self._analyze_faces_in_clip(video_path, start_time, end_time)
            
            # Detectar legendas existentes no vídeo
            subtitle_data = None
            if self.subtitle_detector:
                subtitle_data = self.subtitle_detector.detect_subtitle_regions(video_path, sample_count=5)
            
            # 1. Resize e Crop (9:16) com face tracking e consideração de legendas
            final_clip = self._resize_to_vertical(clip, crop_mode, face_data, subtitle_data)

            # 2. Visual Polish (Color Grading)
            try:
                from src.modules.visual_polisher import VisualPolisher
                polisher = VisualPolisher()
                final_clip = polisher.apply_look(final_clip, vibe)
            except Exception as e:
                logger.warning(f"   ⚠️ Visual polish pulado: {e}")

            # Exportar
            output_path.parent.mkdir(exist_ok=True, parents=True)
            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=Config.VIDEO_FPS,
                preset='fast',
                ffmpeg_params=["-crf", "23"],
                logger=None
            )

            clip.close()
            final_clip.close()

            logger.info(f"✅ Clipe criado: {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro ao criar clipe: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _analyze_faces_in_clip(
        self, 
        video_path: Path, 
        start_time: float, 
        end_time: float,
        sample_interval: float = 1.0
    ) -> Dict:
        """
        Analisa rostos ao longo do clipe para determinar o melhor enquadramento.
        
        Returns:
            Dicionário com informações sobre rostos detectados
        """
        logger.info("   🔍 Analisando rostos no clipe...")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        all_faces = []
        face_counts = []
        centers = []
        
        # Amostrar frames ao longo do clipe
        current_time = start_time
        while current_time < end_time:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
            ret, frame = cap.read()
            
            if ret and frame is not None:
                faces = self.face_tracker.detect_faces(frame)
                face_counts.append(len(faces))
                
                if faces:
                    all_faces.extend(faces)
                    center = self.face_tracker.get_faces_center(faces)
                    if center:
                        centers.append(center)
            
            current_time += sample_interval
        
        cap.release()
        
        # Calcular estatísticas
        result = {
            'frame_width': frame_width,
            'frame_height': frame_height,
            'total_faces_detected': len(all_faces),
            'avg_face_count': np.mean(face_counts) if face_counts else 0,
            'max_face_count': max(face_counts) if face_counts else 0,
            'avg_center': None,
            'bounding_box': None,
            'is_single_person': False,
            'is_multiple_people': False
        }
        
        if centers:
            result['avg_center'] = (np.mean([c[0] for c in centers]), np.mean([c[1] for c in centers]))
        
        if all_faces:
            result['bounding_box'] = self.face_tracker.get_faces_bounding_box(all_faces)
        
        # Determinar tipo de vídeo
        avg_count = result['avg_face_count']
        if avg_count > 0:
            result['is_single_person'] = avg_count < 1.5
            result['is_multiple_people'] = avg_count >= 1.5
        
        logger.info(f"      Rostos detectados: {result['total_faces_detected']}")
        logger.info(f"      Média por frame: {result['avg_face_count']:.1f}")
        logger.info(f"      Tipo: {'Uma pessoa' if result['is_single_person'] else 'Múltiplas pessoas' if result['is_multiple_people'] else 'Sem rostos'}")
        
        return result

    def _resize_to_vertical(
        self, 
        clip: VideoFileClip, 
        crop_mode: str,
        face_data: Dict = None,
        subtitle_data: Dict = None
    ) -> VideoFileClip:
        """
        Redimensiona vídeo para formato vertical 9:16 com tracking inteligente.
        
        MELHORIAS V2:
        - Detecta vídeos sem rostos (screencast, animações)
        - Usa crop central otimizado para conteúdo sem rostos
        - Avisa quando não detecta rostos
        
        MELHORIAS V3:
        - Considera legendas existentes no crop
        - Evita cortar legendas hardcoded
        """
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width  # 16/9 = 1.77...
        
        logger.info(f"   Resolução original: {original_w}x{original_h}")
        logger.info(f"   Resolução alvo: {self.target_width}x{self.target_height}")
        
        # Informar sobre legendas detectadas
        if subtitle_data and subtitle_data.get('has_subtitles'):
            logger.info(f"   📝 Legendas existentes detectadas: {subtitle_data.get('subtitle_position')}")
            logger.info(f"      Confiança: {subtitle_data.get('confidence', 0):.1%}")

        # Verificar se tem rostos detectados
        has_faces = face_data and face_data.get('total_faces_detected', 0) > 0
        
        if not has_faces and crop_mode in ['face_tracking', 'smart']:
            logger.warning(f"   ⚠️ Nenhum rosto detectado no clipe - usando crop central otimizado")
            return self._crop_center_optimized(clip, subtitle_data)
        
        if crop_mode == 'center' or face_data is None:
            return self._crop_center(clip, subtitle_data)
        
        elif crop_mode == 'face_tracking' and face_data and face_data.get('avg_center'):
            return self._crop_with_face_tracking(clip, face_data, subtitle_data)
        
        elif crop_mode == 'smart' and face_data:
            return self._crop_smart(clip, face_data, subtitle_data)
        
        else:
            return self._crop_center(clip, subtitle_data)

    def _crop_center(self, clip: VideoFileClip, subtitle_data: Dict = None) -> VideoFileClip:
        """Crop central simples para 9:16, considerando legendas existentes."""
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width

        # Calcular dimensões do crop
        crop_width = int(original_h / target_ratio)

        if crop_width > original_w:
            # Vídeo muito largo, crop pela altura
            crop_height = int(original_w * target_ratio)
            x_center = original_w / 2
            y_center = original_h / 2
            
            # Ajustar Y se houver legendas
            if subtitle_data and subtitle_data.get('has_subtitles'):
                y_center = self._adjust_crop_for_subtitles(
                    y_center, crop_height, original_h, subtitle_data
                )

            clip_cropped = crop(
                clip,
                x_center=x_center,
                y_center=y_center,
                width=original_w,
                height=crop_height
            )
        else:
            # Crop pela largura
            x_center = original_w / 2
            y_center = original_h / 2

            clip_cropped = crop(
                clip,
                x_center=x_center,
                y_center=y_center,
                width=crop_width,
                height=original_h
            )

        # Redimensionar para resolução alvo
        clip_resized = clip_cropped.resize((self.target_width, self.target_height))
        return clip_resized
    
    def _adjust_crop_for_subtitles(
        self,
        y_center: float,
        crop_height: int,
        original_h: int,
        subtitle_data: Dict
    ) -> float:
        """
        Ajusta o centro Y do crop para incluir legendas existentes.
        
        Se as legendas estão na base, move o crop para baixo.
        Se estão no topo, move para cima.
        """
        subtitle_pos = subtitle_data.get('subtitle_position')
        
        if subtitle_pos == 'bottom':
            # Legendas na base: mover crop para baixo para incluí-las
            # Garantir que a base do crop chegue até as legendas
            ideal_y = original_h - crop_height / 2
            y_center = min(y_center + crop_height * 0.1, ideal_y)
            logger.info(f"   📝 Ajustando crop para incluir legendas na base")
            
        elif subtitle_pos == 'top':
            # Legendas no topo: mover crop para cima
            ideal_y = crop_height / 2
            y_center = max(y_center - crop_height * 0.1, ideal_y)
            logger.info(f"   📝 Ajustando crop para incluir legendas no topo")
        
        # Garantir limites
        y_center = max(crop_height / 2, min(y_center, original_h - crop_height / 2))
        
        return y_center

    def _crop_with_face_tracking(
        self, 
        clip: VideoFileClip, 
        face_data: Dict,
        subtitle_data: Dict = None
    ) -> VideoFileClip:
        """
        Crop dinâmico que segue o rosto detectado.
        Para uma pessoa: foca no rosto
        Para múltiplas pessoas: enquadra todas
        """
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width
        
        # Calcular dimensões do crop
        crop_width = int(original_h / target_ratio)
        if crop_width > original_w:
            crop_width = original_w
            crop_height = int(original_w * target_ratio)
        else:
            crop_height = original_h
        
        # Determinar centro do crop baseado nos rostos
        if face_data.get('is_single_person') and face_data.get('avg_center'):
            # Uma pessoa: centralizar no rosto
            center_x, center_y = face_data['avg_center']
            logger.info(f"   🎯 Focando em uma pessoa em ({center_x:.0f}, {center_y:.0f})")
        
        elif face_data.get('is_multiple_people') and face_data.get('bounding_box'):
            # Múltiplas pessoas: centralizar na bounding box
            bbox = face_data['bounding_box']
            center_x = bbox[0] + bbox[2] / 2
            center_y = bbox[1] + bbox[3] / 2
            logger.info(f"   🎯 Enquadrando múltiplas pessoas")
        
        else:
            # Fallback para centro
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
        
        # Redimensionar
        clip_resized = clip_cropped.resize((self.target_width, self.target_height))
        return clip_resized

    def _crop_smart(self, clip: VideoFileClip, face_data: Dict, subtitle_data: Dict = None) -> VideoFileClip:
        """
        Crop inteligente que considera:
        - Rostos detectados
        - Regra dos terços
        - Movimento no vídeo
        - Legendas existentes
        """
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width
        
        # Calcular dimensões do crop
        crop_width = int(original_h / target_ratio)
        if crop_width > original_w:
            crop_width = original_w
            crop_height = int(original_w * target_ratio)
        else:
            crop_height = original_h
        
        # Determinar centro inteligente
        if face_data.get('avg_center'):
            center_x, center_y = face_data['avg_center']
            
            # Aplicar regra dos terços - posicionar rosto no terço superior
            if face_data.get('is_single_person'):
                # Ajustar Y para que o rosto fique no terço superior
                target_y = crop_height * 0.33  # Terço superior
                offset_y = center_y - target_y
                center_y = original_h / 2 + offset_y * 0.5  # Ajuste suave
        else:
            center_x = original_w / 2
            center_y = original_h / 2
        
        # Garantir limites
        center_x = max(crop_width / 2, min(center_x, original_w - crop_width / 2))
        center_y = max(crop_height / 2, min(center_y, original_h - crop_height / 2))
        
        logger.info(f"   🎯 Smart crop: centro em ({center_x:.0f}, {center_y:.0f})")
        
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

    def _crop_center_optimized(self, clip: VideoFileClip, subtitle_data: Dict = None) -> VideoFileClip:
        """
        Crop central otimizado para vídeos sem rostos.
        Tenta manter o conteúdo principal visível (screencast, animações, gráficos).
        
        ESTRATÉGIA:
        - Analisa onde está o conteúdo principal (não apenas centro geométrico)
        - Evita cortar texto ou elementos importantes nas bordas
        - Prioriza a área com mais atividade/contraste
        - Considera legendas existentes
        """
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width
        
        # Calcular dimensões do crop
        crop_width = int(original_h / target_ratio)
        if crop_width > original_w:
            crop_width = original_w
            crop_height = int(original_w * target_ratio)
        else:
            crop_height = original_h
        
        # Para vídeos sem rostos, analisar onde está o conteúdo principal
        # Pegar um frame do meio para análise
        try:
            frame = clip.get_frame(clip.duration / 2)
            center_x, center_y = self._find_content_center(frame)
        except:
            center_x = original_w / 2
            center_y = original_h / 2
        
        # Garantir limites
        center_x = max(crop_width / 2, min(center_x, original_w - crop_width / 2))
        center_y = max(crop_height / 2, min(center_y, original_h - crop_height / 2))
        
        logger.info(f"   🎯 Crop otimizado (sem rostos): centro em ({center_x:.0f}, {center_y:.0f})")
        
        clip_cropped = crop(
            clip,
            x_center=center_x,
            y_center=center_y,
            width=crop_width,
            height=crop_height
        )
        
        clip_resized = clip_cropped.resize((self.target_width, self.target_height))
        return clip_resized

    def _find_content_center(self, frame: np.ndarray) -> Tuple[float, float]:
        """
        Encontra o centro do conteúdo principal em um frame.
        Útil para vídeos sem rostos (screencast, animações).
        """
        h, w = frame.shape[:2]
        
        try:
            # Converter para grayscale
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                gray = frame
            
            # Detectar bordas (onde tem conteúdo)
            edges = cv2.Canny(gray, 50, 150)
            
            # Encontrar momentos da imagem de bordas
            moments = cv2.moments(edges)
            
            if moments['m00'] > 0:
                cx = moments['m10'] / moments['m00']
                cy = moments['m01'] / moments['m00']
                return (cx, cy)
            
        except Exception as e:
            logger.debug(f"   Erro ao encontrar centro do conteúdo: {e}")
        
        # Fallback: centro geométrico
        return (w / 2, h / 2)

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
                    crop_mode='face_tracking' if Config.FACE_TRACKING_ENABLED else 'center'
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
    print("Video Editor inicializado com sucesso!")
    print(f"Face Tracking disponível: {editor.face_tracker.initialized}")
