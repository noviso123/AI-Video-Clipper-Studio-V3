"""
Módulo de Edição de Vídeo (Stage 4) - VERSÃO 4.0
Corta, redimensiona e edita vídeos usando MoviePy

VERSÃO 4.0 - PROCESSAMENTO FRAME A FRAME:
- Análise inteligente de cada frame
- Crop dinâmico baseado no conteúdo
- Preservação automática de legendas
- Transições suaves entre estratégias
- Letterbox para conteúdo que não pode ser cortado
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

# Imports opcionais
try:
    from .subtitle_detector import SubtitleDetector
    SUBTITLE_DETECTOR_AVAILABLE = True
except ImportError:
    SUBTITLE_DETECTOR_AVAILABLE = False

try:
    from .frame_analyzer import FrameAnalyzer, FrameAnalysis, CropStrategy, FrameType
    FRAME_ANALYZER_AVAILABLE = True
except ImportError:
    FRAME_ANALYZER_AVAILABLE = False

try:
    from .dynamic_processor import DynamicVideoProcessor
    DYNAMIC_PROCESSOR_AVAILABLE = True
except ImportError:
    DYNAMIC_PROCESSOR_AVAILABLE = False

try:
    from .intelligent_cropper import IntelligentCropper, SceneContext
    INTELLIGENT_CROPPER_AVAILABLE = True
except ImportError:
    INTELLIGENT_CROPPER_AVAILABLE = False


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
        """Detecta rostos em um frame."""
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
        """Calcula o centro médio de todos os rostos detectados."""
        if not faces:
            return None

        centers_x = [x + w/2 for (x, y, w, h) in faces]
        centers_y = [y + h/2 for (x, y, w, h) in faces]

        return (np.mean(centers_x), np.mean(centers_y))

    def get_bounding_box(self, faces: List[Tuple[int, int, int, int]], padding: float = 0.2) -> Tuple[int, int, int, int]:
        """Calcula bounding box que engloba todos os rostos."""
        if not faces:
            return None

        min_x = min(x for (x, y, w, h) in faces)
        min_y = min(y for (x, y, w, h) in faces)
        max_x = max(x + w for (x, y, w, h) in faces)
        max_y = max(y + h for (x, y, w, h) in faces)

        width = max_x - min_x
        height = max_y - min_y

        pad_x = int(width * padding)
        pad_y = int(height * padding)

        return (
            max(0, min_x - pad_x),
            max(0, min_y - pad_y),
            int(width + 2 * pad_x),
            int(height + 2 * pad_y)
        )


class VideoEditor:
    """Editor de vídeo com processamento frame a frame inteligente."""

    def __init__(self):
        self.target_width, self.target_height = Config.OUTPUT_RESOLUTION
        self.fps = Config.VIDEO_FPS
        self.quality_settings = Config.get_quality_settings()
        self.face_tracker = FaceTracker()

        # Inicializar detector de legendas
        self.subtitle_detector = None
        if SUBTITLE_DETECTOR_AVAILABLE:
            self.subtitle_detector = SubtitleDetector()

        # Inicializar analisador de frames
        self.frame_analyzer = None
        if FRAME_ANALYZER_AVAILABLE:
            self.frame_analyzer = FrameAnalyzer()

        # Inicializar processador dinâmico
        self.dynamic_processor = None
        if DYNAMIC_PROCESSOR_AVAILABLE:
            self.dynamic_processor = DynamicVideoProcessor()

        # Inicializar cropper inteligente
        self.intelligent_cropper = None
        if INTELLIGENT_CROPPER_AVAILABLE:
            self.intelligent_cropper = IntelligentCropper(self.target_width, self.target_height)

        logger.info(f"🎬 Video Editor inicializado (V4.0 - Frame a Frame)")
        logger.info(f"   Resolução alvo: {self.target_width}x{self.target_height}")
        logger.info(f"   Face Tracking: {'Ativo' if self.face_tracker.initialized else 'Inativo'}")
        logger.info(f"   Detecção de Legendas: {'Ativo' if self.subtitle_detector else 'Inativo'}")
        logger.info(f"   Análise Frame a Frame: {'Ativo' if self.frame_analyzer else 'Inativo'}")
        logger.info(f"   Processamento Dinâmico: {'Ativo' if self.dynamic_processor else 'Inativo'}")
        logger.info(f"   Cropping Inteligente: {'Ativo' if self.intelligent_cropper else 'Inativo'}")

    def create_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
        crop_mode: str = 'auto',
        vibe: str = 'General',
        transcription: List[Dict] = None
    ) -> Path:
        """
        Cria um clipe vertical (9:16) do vídeo.

        Args:
            video_path: Caminho do vídeo original
            start_time: Tempo de início em segundos
            end_time: Tempo de fim em segundos
            output_path: Caminho para salvar o clipe
            crop_mode: 'auto', 'dynamic', 'face_tracking', 'letterbox', 'center'
            vibe: Vibe ou estilo detectado pelo orquestrador
            transcription: Transcrição para legendas (opcional)
        """
        logger.info(f"✂️  Cortando vídeo: {start_time:.1f}s -> {end_time:.1f}s (Modo: {crop_mode}, Vibe: {vibe})")

        try:
            # Se modo dinâmico e processador disponível, usar processamento frame a frame
            if crop_mode in ['auto', 'dynamic'] and self.dynamic_processor:
                logger.info("   🎯 Usando processamento dinâmico frame a frame")
                return self.dynamic_processor.process_with_dynamic_crop(
                    video_path, output_path, start_time, end_time, transcription
                )

            # Fallback para processamento tradicional
            return self._create_clip_traditional(
                video_path, start_time, end_time, output_path, crop_mode
            )

        except Exception as e:
            logger.error(f"❌ Erro ao criar clipe: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_clip_traditional(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
        crop_mode: str
    ) -> Path:
        """Processamento tradicional (fallback)."""

        clip_src = VideoFileClip(str(video_path))
        duration = clip_src.duration
        
        # Clamp timestamps to avoid OOB errors (precision issues)
        safe_start = max(0, start_time)
        safe_end = min(duration - 0.05, end_time) # 50ms buffer
        
        if safe_end <= safe_start:
             logger.error(f"   ⚠️ Tempo inválido após clamp: {safe_start} -> {safe_end} (Duration: {duration})")
             return None

        clip = clip_src.subclip(safe_start, safe_end)
        original_w, original_h = clip.size

        # Detectar legendas
        subtitle_data = None
        if self.subtitle_detector:
            subtitle_data = self.subtitle_detector.detect_subtitle_regions(video_path, sample_count=5)

        # Analisar rostos
        face_data = None
        if crop_mode in ['face_tracking', 'auto'] and Config.FACE_TRACKING_ENABLED:
            face_data = self._analyze_faces_in_clip(video_path, start_time, end_time)

        # Determinar estratégia
        if crop_mode == 'auto':
            crop_mode = self._determine_best_mode(subtitle_data, face_data)
            logger.info(f"   🤖 Modo automático selecionou: {crop_mode}")

        # Aplicar crop - PRIORIZAR face tracking / intelligent cropping
        if crop_mode == 'letterbox':
            final_clip = self._apply_letterbox(clip)
        elif self.intelligent_cropper or (crop_mode == 'face_tracking' and face_data):
            # Usar intelligent cropping se disponível (ignora subtitle_data para priorizar dynamic crop)
            final_clip = self._apply_face_tracking(clip, face_data, None)  # Pass None for subtitle_data to force face tracking
        else:
            # Fallback para letterbox apenas se nada mais funcionar
            final_clip = self._apply_letterbox(clip)

        # Visual Polish
        try:
            from src.modules.visual_polisher import VisualPolisher
            polisher = VisualPolisher()
            final_clip = polisher.apply_style(final_clip, 'General')
        except:
            pass

        # Exportar
        output_path.parent.mkdir(parents=True, exist_ok=True)

        final_clip.write_videofile(
            str(output_path),
            fps=self.fps or clip.fps or 30,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate=self.quality_settings.get('bitrate', '5M'),
            audio_bitrate=self.quality_settings.get('audio_bitrate', '192k'),
            logger=None
        )

        clip.close()
        final_clip.close()

        logger.info(f"✅ Clipe salvo: {output_path.name}")
        return output_path

    def _determine_best_mode(self, subtitle_data: Dict, face_data: Dict) -> str:
        """Determina o melhor modo de crop."""

        # Prioridade 1: Se tem rostos detectados, SEMPRE usar face tracking (melhor para podcasts/talking heads)
        if face_data and face_data.get('total_faces_detected', 0) > 0:
            return 'face_tracking'

        # Prioridade 2: Se tem legendas existentes, usar letterbox para preservá-las
        if subtitle_data and subtitle_data.get('has_subtitles'):
            if subtitle_data.get('confidence', 0) > 0.4:
                return 'letterbox'

        # Padrão: face_tracking (mais engajante para redes sociais)
        return 'face_tracking'

    def _apply_letterbox(self, clip: VideoFileClip) -> VideoFileClip:
        """Aplica letterbox preservando todo o conteúdo."""
        original_w, original_h = clip.size

        logger.info(f"   📦 Aplicando letterbox")

        # Calcular escala
        scale_w = self.target_width / original_w
        scale_h = self.target_height / original_h
        scale = min(scale_w, scale_h)

        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        # Redimensionar
        resized = clip.resize((new_w, new_h))

        # Criar fundo
        bg = ColorClip(
            size=(self.target_width, self.target_height),
            color=(0, 0, 0)
        ).set_duration(clip.duration)

        # Posicionar
        x_pos = (self.target_width - new_w) // 2
        y_pos = (self.target_height - new_h) // 2

        final = CompositeVideoClip([
            bg,
            resized.set_position((x_pos, y_pos))
        ])

        if clip.audio:
            final = final.set_audio(clip.audio)

        return final

    def _apply_face_tracking(
        self,
        clip: VideoFileClip,
        face_data: Dict,
        subtitle_data: Dict = None
    ) -> VideoFileClip:
        """
        Aplica crop INTELIGENTE frame-a-frame com análise de contexto.
        
        Detecta automaticamente:
        - Quem está falando (single speaker)
        - Múltiplas pessoas conversando (conversation)
        - Objetos sendo mostrados (product showcase)
        - Grupos de pessoas (group shot)
        
        Ajusta zoom e posição dinamicamente baseado no contexto.
        """

        # Se tem legendas existentes com alta confiança, usar letterbox
        if subtitle_data and subtitle_data.get('has_subtitles'):
            if subtitle_data.get('confidence', 0) > 0.6:
                return self._apply_letterbox(clip)

        original_w, original_h = clip.size

        # Usar IntelligentCropper se disponível
        if self.intelligent_cropper:
            logger.info(f"   🧠 Cropping INTELIGENTE (context-aware)")
            
            # Resetar estado do cropper para novo clip
            self.intelligent_cropper.reset()
            
            def make_frame_intelligent(get_frame, t):
                """Processa cada frame com cropping inteligente."""
                frame = get_frame(t)
                
                # Analisar frame e obter decisão de crop
                decision = self.intelligent_cropper.analyze_frame(frame)
                
                # Aplicar crop baseado na decisão
                result = self.intelligent_cropper.apply_crop(frame, decision)
                
                return result

            # Aplicar transformação frame a frame
            final_clip = clip.fl(make_frame_intelligent)
            final_clip = final_clip.set_duration(clip.duration)
            
            if clip.audio:
                final_clip = final_clip.set_audio(clip.audio)
            
            return final_clip
        
        # Fallback: face tracking simples
        logger.info(f"   🎯 Face tracking DINÂMICO (frame-a-frame)")
        
        target_ratio = self.target_height / self.target_width
        crop_width = int(original_h / target_ratio)
        if crop_width > original_w:
            return self._apply_letterbox(clip)

        crop_height = original_h

        # Posição inicial baseada na análise prévia
        initial_center_x = original_w / 2
        if face_data and face_data.get('avg_center'):
            initial_center_x = face_data['avg_center'][0]

        # Estado para suavização (smooth tracking)
        last_x = [initial_center_x]  # Mutable para closure
        deadzone = 50  # Pixels de tolerância para reduzir jitter

        def make_frame_with_face_tracking(get_frame, t):
            """Processa cada frame com face tracking dinâmico."""
            frame = get_frame(t)
            
            # Detectar rosto neste frame
            if self.face_tracker.initialized:
                try:
                    faces = self.face_tracker.detect_faces(frame)
                    if faces:
                        center = self.face_tracker.get_faces_center(faces)
                        if center:
                            target_x = center[0]
                            
                            # Aplicar deadzone para suavização
                            if abs(target_x - last_x[0]) > deadzone:
                                # Movimento suave (interpolação)
                                last_x[0] = last_x[0] + (target_x - last_x[0]) * 0.3
                except:
                    pass  # Manter posição anterior se falhar
            
            # Calcular crop centrado no rosto
            center_x = last_x[0]
            
            # Garantir limites
            center_x = max(crop_width / 2, min(center_x, original_w - crop_width / 2))
            
            # Calcular coordenadas de crop
            x1 = int(center_x - crop_width / 2)
            x2 = int(center_x + crop_width / 2)
            y1 = 0
            y2 = crop_height
            
            # Aplicar crop
            cropped_frame = frame[y1:y2, x1:x2]
            
            # Redimensionar para resolução alvo
            import cv2
            resized = cv2.resize(cropped_frame, (self.target_width, self.target_height))
            
            return resized

        # Aplicar transformação frame a frame
        final_clip = clip.fl(make_frame_with_face_tracking)
        final_clip = final_clip.set_duration(clip.duration)
        
        if clip.audio:
            final_clip = final_clip.set_audio(clip.audio)
        
        return final_clip

    def _analyze_faces_in_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float
    ) -> Dict:
        """Analisa rostos no intervalo do clipe."""
        logger.info(f"   🔍 Analisando rostos no clipe...")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {}

        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        all_faces = []
        all_centers = []
        frames_analyzed = 0

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

            avg_faces = result['avg_faces_per_frame']
            if avg_faces <= 1.5:
                result['is_single_person'] = True
            elif avg_faces > 1.5:
                result['is_multiple_people'] = True

        logger.info(f"      Rostos detectados: {result['total_faces_detected']}")
        logger.info(f"      Média por frame: {result['avg_faces_per_frame']:.1f}")

        return result

    def batch_create_clips(
        self,
        video_path: Path,
        moments: list,
        output_dir: Path
    ) -> list:
        """Cria múltiplos clipes de uma vez."""
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
                    crop_mode='auto'
                )
                output_paths.append(path)

            except Exception as e:
                logger.error(f"   Erro no clipe {i}: {e}")
                continue

        logger.info(f"✅ {len(output_paths)}/{len(moments)} clipes criados com sucesso")
        return output_paths


if __name__ == "__main__":
    editor = VideoEditor()
    print("Video Editor V4.0 inicializado com sucesso!")
