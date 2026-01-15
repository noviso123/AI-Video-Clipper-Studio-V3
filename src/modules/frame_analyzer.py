"""
Módulo de Análise Frame a Frame Inteligente
Analisa cada frame individualmente e determina a melhor estratégia de processamento.

Funcionalidades:
- Detecção de rostos (quantidade e posição)
- Detecção de texto/legendas
- Detecção de conteúdo visual importante
- Detecção de silêncio/voz
- Recomendação de crop por frame
- Transições suaves entre estratégias
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import cv2
import numpy as np
from dataclasses import dataclass
from enum import Enum
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class FrameType(Enum):
    """Tipos de frame detectados."""
    SINGLE_PERSON = "single_person"          # Uma pessoa falando
    MULTIPLE_PEOPLE = "multiple_people"      # Múltiplas pessoas
    TEXT_HEAVY = "text_heavy"                # Muito texto/legendas
    VISUAL_CONTENT = "visual_content"        # Conteúdo visual importante
    TRANSITION = "transition"                # Frame de transição
    EMPTY = "empty"                          # Frame vazio/escuro
    MIXED = "mixed"                          # Conteúdo misto


class CropStrategy(Enum):
    """Estratégias de crop disponíveis."""
    FACE_FOCUS = "face_focus"                # Foca no rosto
    MULTI_FACE = "multi_face"                # Enquadra múltiplos rostos
    LETTERBOX = "letterbox"                  # Preserva tudo com barras
    CENTER_CROP = "center_crop"              # Crop central
    CONTENT_AWARE = "content_aware"          # Crop baseado no conteúdo
    NO_CROP = "no_crop"                      # Sem crop (redimensiona)


@dataclass
class FrameAnalysis:
    """Resultado da análise de um frame."""
    frame_index: int
    timestamp: float
    frame_type: FrameType
    crop_strategy: CropStrategy
    
    # Detecções
    faces: List[Tuple[int, int, int, int]]  # Lista de (x, y, w, h)
    face_centers: List[Tuple[float, float]]
    has_text: bool
    text_regions: List[Tuple[int, int, int, int]]
    has_subtitles: bool
    subtitle_position: str  # 'top', 'center', 'bottom'
    
    # Métricas
    brightness: float
    contrast: float
    edge_density: float
    motion_score: float
    
    # Crop recomendado
    crop_center: Tuple[float, float]
    crop_size: Tuple[int, int]
    confidence: float
    
    # Áudio
    has_voice: bool
    silence_duration: float


class FrameAnalyzer:
    """Analisador de frames inteligente."""
    
    def __init__(self):
        """Inicializa o analisador."""
        # Inicializar detector de rostos
        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                self.face_cascade = None
        except:
            pass
        
        # Cache de análises anteriores para transições suaves
        self.previous_analyses: List[FrameAnalysis] = []
        self.smoothing_window = 5  # Frames para suavização
        
        logger.info("🔍 Frame Analyzer: Inicializado")
        logger.info(f"   Face Detection: {'Ativo' if self.face_cascade else 'Inativo'}")
    
    def analyze_video(
        self, 
        video_path: Path, 
        start_time: float = 0,
        end_time: float = None,
        sample_rate: int = 5  # Analisar a cada N frames
    ) -> List[FrameAnalysis]:
        """
        Analisa todos os frames de um vídeo.
        
        Args:
            video_path: Caminho do vídeo
            start_time: Tempo inicial em segundos
            end_time: Tempo final em segundos
            sample_rate: Analisar a cada N frames
            
        Returns:
            Lista de FrameAnalysis para cada frame analisado
        """
        logger.info(f"🎬 Analisando vídeo frame a frame: {video_path.name}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error("   ❌ Não foi possível abrir o vídeo")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if end_time is None:
            end_time = duration
        
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        logger.info(f"   Frames: {start_frame} -> {end_frame}")
        logger.info(f"   Resolução: {frame_width}x{frame_height}")
        logger.info(f"   FPS: {fps}")
        
        analyses = []
        previous_frame = None
        
        for frame_idx in range(start_frame, end_frame, sample_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            timestamp = frame_idx / fps
            
            # Analisar frame
            analysis = self._analyze_single_frame(
                frame, 
                frame_idx, 
                timestamp,
                previous_frame,
                frame_width,
                frame_height
            )
            
            analyses.append(analysis)
            previous_frame = frame
        
        cap.release()
        
        # Aplicar suavização nas transições
        analyses = self._smooth_transitions(analyses)
        
        # Estatísticas
        frame_types = {}
        for a in analyses:
            ft = a.frame_type.value
            frame_types[ft] = frame_types.get(ft, 0) + 1
        
        logger.info(f"   ✅ {len(analyses)} frames analisados")
        logger.info(f"   Tipos detectados: {frame_types}")
        
        return analyses
    
    def _analyze_single_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
        timestamp: float,
        previous_frame: np.ndarray,
        video_width: int,
        video_height: int
    ) -> FrameAnalysis:
        """Analisa um único frame."""
        
        # Detectar rostos
        faces = self._detect_faces(frame)
        face_centers = self._get_face_centers(faces)
        
        # Detectar texto/legendas
        has_text, text_regions = self._detect_text(frame)
        has_subtitles, subtitle_position = self._detect_subtitles(frame)
        
        # Métricas visuais
        brightness = self._calculate_brightness(frame)
        contrast = self._calculate_contrast(frame)
        edge_density = self._calculate_edge_density(frame)
        
        # Movimento (comparar com frame anterior)
        motion_score = 0.0
        if previous_frame is not None:
            motion_score = self._calculate_motion(frame, previous_frame)
        
        # Determinar tipo de frame
        frame_type = self._determine_frame_type(
            faces, has_text, has_subtitles, edge_density, brightness
        )
        
        # Determinar estratégia de crop
        crop_strategy = self._determine_crop_strategy(
            frame_type, faces, has_subtitles, subtitle_position
        )
        
        # Calcular centro e tamanho do crop
        crop_center, crop_size = self._calculate_crop_params(
            frame_type, crop_strategy, faces, face_centers,
            video_width, video_height, has_subtitles, subtitle_position
        )
        
        # Confiança da análise
        confidence = self._calculate_confidence(
            frame_type, len(faces), has_subtitles, edge_density
        )
        
        return FrameAnalysis(
            frame_index=frame_index,
            timestamp=timestamp,
            frame_type=frame_type,
            crop_strategy=crop_strategy,
            faces=faces,
            face_centers=face_centers,
            has_text=has_text,
            text_regions=text_regions,
            has_subtitles=has_subtitles,
            subtitle_position=subtitle_position,
            brightness=brightness,
            contrast=contrast,
            edge_density=edge_density,
            motion_score=motion_score,
            crop_center=crop_center,
            crop_size=crop_size,
            confidence=confidence,
            has_voice=True,  # Será atualizado pela análise de áudio
            silence_duration=0.0
        )
    
    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detecta rostos no frame."""
        if self.face_cascade is None:
            return []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )
            return [(x, y, w, h) for (x, y, w, h) in faces]
        except:
            return []
    
    def _get_face_centers(self, faces: List[Tuple[int, int, int, int]]) -> List[Tuple[float, float]]:
        """Calcula centros dos rostos."""
        return [(x + w/2, y + h/2) for (x, y, w, h) in faces]
    
    def _detect_text(self, frame: np.ndarray) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """Detecta regiões de texto no frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar alto contraste (texto)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / max(h, 1)
            
            # Texto geralmente tem aspect ratio > 2
            if aspect_ratio > 2 and w > 50:
                text_regions.append((x, y, w, h))
        
        has_text = len(text_regions) > 0
        return has_text, text_regions
    
    def _detect_subtitles(self, frame: np.ndarray) -> Tuple[bool, str]:
        """Detecta legendas e sua posição."""
        h, w = frame.shape[:2]
        
        # Dividir em regiões
        regions = {
            'top': frame[:int(h*0.2), :],
            'center': frame[int(h*0.35):int(h*0.65), :],
            'bottom': frame[int(h*0.75):, :]
        }
        
        scores = {}
        for name, region in regions.items():
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Detectar texto branco em fundo escuro
            _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            white_ratio = np.sum(binary > 0) / binary.size
            
            # Detectar bordas (texto tem muitas bordas horizontais)
            edges = cv2.Canny(gray, 50, 150)
            edge_ratio = np.sum(edges > 0) / edges.size
            
            scores[name] = white_ratio * 0.5 + edge_ratio * 0.5
        
        # Determinar se tem legenda e onde
        max_region = max(scores, key=scores.get)
        max_score = scores[max_region]
        
        has_subtitles = max_score > 0.1
        subtitle_position = max_region if has_subtitles else 'none'
        
        return has_subtitles, subtitle_position
    
    def _calculate_brightness(self, frame: np.ndarray) -> float:
        """Calcula brilho médio do frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray) / 255.0
    
    def _calculate_contrast(self, frame: np.ndarray) -> float:
        """Calcula contraste do frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.std(gray) / 128.0
    
    def _calculate_edge_density(self, frame: np.ndarray) -> float:
        """Calcula densidade de bordas."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return np.sum(edges > 0) / edges.size
    
    def _calculate_motion(self, frame: np.ndarray, previous_frame: np.ndarray) -> float:
        """Calcula quantidade de movimento entre frames."""
        try:
            gray1 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(gray1, gray2)
            motion = np.mean(diff) / 255.0
            return motion
        except:
            return 0.0
    
    def _determine_frame_type(
        self,
        faces: List,
        has_text: bool,
        has_subtitles: bool,
        edge_density: float,
        brightness: float
    ) -> FrameType:
        """Determina o tipo do frame baseado nas análises."""
        
        # Frame escuro/vazio
        if brightness < 0.1:
            return FrameType.EMPTY
        
        # Muito texto
        if has_text and edge_density > 0.15:
            return FrameType.TEXT_HEAVY
        
        # Uma pessoa
        if len(faces) == 1:
            return FrameType.SINGLE_PERSON
        
        # Múltiplas pessoas
        if len(faces) > 1:
            return FrameType.MULTIPLE_PEOPLE
        
        # Conteúdo visual (alta densidade de bordas, sem rostos)
        if edge_density > 0.1 and len(faces) == 0:
            return FrameType.VISUAL_CONTENT
        
        return FrameType.MIXED
    
    def _determine_crop_strategy(
        self,
        frame_type: FrameType,
        faces: List,
        has_subtitles: bool,
        subtitle_position: str
    ) -> CropStrategy:
        """Determina a estratégia de crop para o frame."""
        
        # Se tem legendas, preservar tudo
        if has_subtitles:
            return CropStrategy.LETTERBOX
        
        # Baseado no tipo de frame
        if frame_type == FrameType.SINGLE_PERSON:
            return CropStrategy.FACE_FOCUS
        
        if frame_type == FrameType.MULTIPLE_PEOPLE:
            return CropStrategy.MULTI_FACE
        
        if frame_type == FrameType.TEXT_HEAVY:
            return CropStrategy.LETTERBOX
        
        if frame_type == FrameType.VISUAL_CONTENT:
            return CropStrategy.LETTERBOX
        
        if frame_type == FrameType.EMPTY:
            return CropStrategy.CENTER_CROP
        
        return CropStrategy.CONTENT_AWARE
    
    def _calculate_crop_params(
        self,
        frame_type: FrameType,
        crop_strategy: CropStrategy,
        faces: List,
        face_centers: List,
        video_width: int,
        video_height: int,
        has_subtitles: bool,
        subtitle_position: str
    ) -> Tuple[Tuple[float, float], Tuple[int, int]]:
        """Calcula parâmetros do crop (centro e tamanho)."""
        
        # Ratio alvo 9:16
        target_ratio = 1920 / 1080
        
        # Calcular tamanho do crop
        crop_width = int(video_height / target_ratio)
        if crop_width > video_width:
            crop_width = video_width
            crop_height = int(video_width * target_ratio)
        else:
            crop_height = video_height
        
        # Calcular centro
        if crop_strategy == CropStrategy.FACE_FOCUS and face_centers:
            # Centralizar no rosto
            center_x, center_y = face_centers[0]
        
        elif crop_strategy == CropStrategy.MULTI_FACE and face_centers:
            # Centralizar em todos os rostos
            center_x = np.mean([c[0] for c in face_centers])
            center_y = np.mean([c[1] for c in face_centers])
        
        elif crop_strategy == CropStrategy.LETTERBOX:
            # Centro do vídeo (letterbox não usa crop real)
            center_x = video_width / 2
            center_y = video_height / 2
        
        else:
            # Centro padrão
            center_x = video_width / 2
            center_y = video_height / 2
        
        # Ajustar para legendas
        if has_subtitles:
            if subtitle_position == 'bottom':
                # Mover crop para cima para incluir legendas
                center_y = min(center_y, video_height * 0.4)
            elif subtitle_position == 'top':
                center_y = max(center_y, video_height * 0.6)
        
        # Garantir limites
        center_x = max(crop_width / 2, min(center_x, video_width - crop_width / 2))
        center_y = max(crop_height / 2, min(center_y, video_height - crop_height / 2))
        
        return (center_x, center_y), (crop_width, crop_height)
    
    def _calculate_confidence(
        self,
        frame_type: FrameType,
        num_faces: int,
        has_subtitles: bool,
        edge_density: float
    ) -> float:
        """Calcula confiança da análise."""
        confidence = 0.5
        
        # Mais rostos = mais confiança
        if num_faces > 0:
            confidence += 0.2
        
        # Legendas detectadas = mais confiança
        if has_subtitles:
            confidence += 0.15
        
        # Tipo claro = mais confiança
        if frame_type in [FrameType.SINGLE_PERSON, FrameType.MULTIPLE_PEOPLE]:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _smooth_transitions(self, analyses: List[FrameAnalysis]) -> List[FrameAnalysis]:
        """Suaviza transições entre estratégias de crop."""
        if len(analyses) < 3:
            return analyses
        
        # Aplicar média móvel nos centros de crop
        for i in range(1, len(analyses) - 1):
            prev_center = analyses[i-1].crop_center
            curr_center = analyses[i].crop_center
            next_center = analyses[i+1].crop_center
            
            # Média ponderada (mais peso no atual)
            smooth_x = (prev_center[0] * 0.25 + curr_center[0] * 0.5 + next_center[0] * 0.25)
            smooth_y = (prev_center[1] * 0.25 + curr_center[1] * 0.5 + next_center[1] * 0.25)
            
            # Atualizar apenas se a estratégia permitir movimento
            if analyses[i].crop_strategy not in [CropStrategy.LETTERBOX, CropStrategy.NO_CROP]:
                analyses[i].crop_center = (smooth_x, smooth_y)
        
        return analyses


class AudioAnalyzerForFrames:
    """Analisa áudio para detectar silêncio e voz por frame."""
    
    def __init__(self):
        logger.info("🔊 Audio Analyzer for Frames: Inicializado")
    
    def analyze_audio(
        self, 
        video_path: Path,
        frame_analyses: List[FrameAnalysis]
    ) -> List[FrameAnalysis]:
        """
        Analisa áudio e atualiza as análises de frame com informações de voz/silêncio.
        """
        try:
            from moviepy.editor import VideoFileClip
            
            clip = VideoFileClip(str(video_path))
            if clip.audio is None:
                return frame_analyses
            
            # Extrair áudio
            audio = clip.audio
            fps = clip.fps or 30
            
            for analysis in frame_analyses:
                timestamp = analysis.timestamp
                
                # Verificar se há voz neste momento
                try:
                    # Pegar 0.5 segundos de áudio
                    start = max(0, timestamp - 0.25)
                    end = min(clip.duration, timestamp + 0.25)
                    
                    audio_segment = audio.subclip(start, end)
                    audio_array = audio_segment.to_soundarray()
                    
                    # Calcular volume
                    volume = np.abs(audio_array).mean()
                    
                    # Threshold para considerar silêncio
                    analysis.has_voice = volume > 0.01
                    analysis.silence_duration = 0.0 if analysis.has_voice else 0.5
                    
                except:
                    pass
            
            clip.close()
            
        except Exception as e:
            logger.warning(f"   ⚠️ Erro na análise de áudio: {e}")
        
        return frame_analyses


if __name__ == "__main__":
    # Teste rápido
    analyzer = FrameAnalyzer()
    print("Frame Analyzer inicializado com sucesso!")
