"""
Intelligent Context-Aware Cropping Module V2.0
Sistema avançado de enquadramento dinâmico com:
- Optical Flow para detecção de movimento precisa
- Predição de velocidade para antecipar movimentos
- Easing functions para transições suaves
- Detecção de múltiplos contextos
- Tracking de regiões de interesse
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import cv2
import math
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class SceneContext(Enum):
    """Tipos de contexto de cena."""
    SINGLE_SPEAKER = "single_speaker"      # Uma pessoa falando
    CONVERSATION = "conversation"           # Múltiplas pessoas conversando
    PRODUCT_SHOWCASE = "product_showcase"   # Objeto sendo mostrado
    GROUP_SHOT = "group_shot"              # Grupo de pessoas
    ACTION = "action"                       # Movimento rápido/ação
    STATIC = "static"                       # Cena estática
    TRANSITION = "transition"               # Transição entre contextos
    UNKNOWN = "unknown"                     # Não identificado


@dataclass
class TrackingState:
    """Estado de tracking para suavização."""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0  # Velocidade X
    vy: float = 0.0  # Velocidade Y
    zoom: float = 1.0
    target_x: float = 0.0
    target_y: float = 0.0
    target_zoom: float = 1.0


@dataclass
class CropDecision:
    """Decisão de crop para um frame."""
    center_x: float          # Centro X do crop
    center_y: float          # Centro Y do crop  
    zoom_level: float        # Nível de zoom (1.0 = normal, <1 = zoom out, >1 = zoom in)
    context: SceneContext    # Contexto detectado
    confidence: float        # Confiança na decisão (0-1)
    active_regions: List[Tuple[int, int, int, int]] = field(default_factory=list)
    motion_intensity: float = 0.0  # Intensidade de movimento (0-1)


class IntelligentCropper:
    """
    Sistema de corte inteligente V2.0 com:
    - Optical Flow para detecção de movimento
    - Predição de velocidade para movimentos suaves
    - Easing functions para transições naturais
    - Tracking temporal contínuo
    """
    
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height
        self.target_ratio = target_height / target_width
        
        # Estado de tracking
        self.tracking_state = TrackingState()
        self.initialized = False
        
        # Parâmetros de suavização (mais suave = valores menores)
        # Parâmetros de suavização (mais suave = valores menores)
        self.position_smoothing = 0.05   # Interpolação padrão (se não for cut)
        self.zoom_smoothing = 0.05       
        self.velocity_damping = 0.90     
        self.velocity_influence = 0.0    # Desativado para estilo "Cuts"
        
        # Parâmetros "Virtual Camera"
        self.deadzone = 50.0             # "Tripod Mode": Nada muda se mover menos que isso
        self.cut_threshold = 250.0       # Se mudar mais que isso = CUT instantâneo
        self.last_cut_time = 0           # Para evitar cortes frenéticos
        self.min_cut_interval = 60       # Mínimo quadros entre cortes

        
        # Parâmetros de detecção
        self.face_cascade = None
        self.motion_threshold = 20
        self.prev_frame_gray = None
        self.prev_points = None
        
        # Optical Flow params
        self.lk_params = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        )
        
        # Feature detection params
        self.feature_params = dict(
            maxCorners=100,
            qualityLevel=0.2,
            minDistance=10,
            blockSize=7
        )
        
        # Histórico para análise
        self.motion_history = []
        self.context_history = []
        self.max_history = 30  # ~1 segundo a 30fps
        self.context_buffer = [] # Buffer para histerese de contexto
        self.current_context = SceneContext.UNKNOWN

        
        # Inicializar detectores
        self._init_detectors()
        
        logger.info("🧠 Intelligent Cropper V2.0 inicializado")
        logger.info("   Optical Flow: Ativo")
        logger.info("   Velocity Prediction: Ativo")
        logger.info("   Smooth Transitions: Ativo")
        
    def _init_detectors(self):
        """Inicializa detectores de face."""
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                self.face_cascade = None
                logger.warning("   Face detector não carregado")
            else:
                logger.info("   Face detector: Ativo")
        except Exception as e:
            logger.warning(f"   Face detector não disponível: {e}")
    
    def _ease_out_expo(self, t: float) -> float:
        """Easing exponencial para transições naturais."""
        return 1 - math.pow(2, -10 * t) if t < 1 else 1
    
    def _ease_out_cubic(self, t: float) -> float:
        """Easing cúbico para transições suaves."""
        return 1 - math.pow(1 - t, 3)
    
    def _calculate_optical_flow(self, frame: np.ndarray) -> Tuple[float, float, float]:
        """
        Calcula optical flow para detectar direção e intensidade de movimento.
        Retorna: (motion_intensity, avg_flow_x, avg_flow_y)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_frame_gray is None or self.prev_points is None:
            self.prev_frame_gray = gray
            # Detectar pontos para tracking
            self.prev_points = cv2.goodFeaturesToTrack(
                gray, mask=None, **self.feature_params
            )
            return 0.0, 0.0, 0.0
        
        if self.prev_points is None or len(self.prev_points) < 5:
            # Redetectar pontos
            self.prev_points = cv2.goodFeaturesToTrack(
                gray, mask=None, **self.feature_params
            )
            self.prev_frame_gray = gray
            return 0.0, 0.0, 0.0
        
        try:
            # Calcular optical flow
            next_points, status, _ = cv2.calcOpticalFlowPyrLK(
                self.prev_frame_gray, gray, 
                self.prev_points, None, 
                **self.lk_params
            )
            
            if next_points is None:
                self.prev_frame_gray = gray
                self.prev_points = cv2.goodFeaturesToTrack(
                    gray, mask=None, **self.feature_params
                )
                return 0.0, 0.0, 0.0
            
            # Filtrar bons pontos
            good_old = self.prev_points[status == 1]
            good_new = next_points[status == 1]
            
            if len(good_old) < 3:
                self.prev_frame_gray = gray
                self.prev_points = cv2.goodFeaturesToTrack(
                    gray, mask=None, **self.feature_params
                )
                return 0.0, 0.0, 0.0
            
            # Calcular fluxo médio
            flow = good_new - good_old
            avg_flow_x = float(np.mean(flow[:, 0]))
            avg_flow_y = float(np.mean(flow[:, 1]))
            
            # Intensidade do movimento
            magnitudes = np.sqrt(np.sum(flow ** 2, axis=1))
            motion_intensity = float(np.mean(magnitudes)) / 50.0  # Normalizar
            motion_intensity = min(1.0, motion_intensity)
            
            # Atualizar estado
            self.prev_frame_gray = gray
            self.prev_points = good_new.reshape(-1, 1, 2)
            
            # Redetectar pontos periodicamente
            if len(self.prev_points) < 30:
                new_points = cv2.goodFeaturesToTrack(
                    gray, mask=None, **self.feature_params
                )
                if new_points is not None:
                    self.prev_points = np.vstack([self.prev_points, new_points])
            
            return motion_intensity, avg_flow_x, avg_flow_y
            
        except Exception as e:
            self.prev_frame_gray = gray
            self.prev_points = cv2.goodFeaturesToTrack(
                gray, mask=None, **self.feature_params
            )
            return 0.0, 0.0, 0.0
    
    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detecta rostos no frame."""
        if self.face_cascade is None:
            return []
            
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.15, 
                minNeighbors=4,
                minSize=(40, 40),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            return [tuple(f) for f in faces]
        except:
            return []
    
    def _detect_motion_regions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detecta regiões com movimento usando diferença de frames."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if not hasattr(self, 'motion_prev_gray') or self.motion_prev_gray is None:
            self.motion_prev_gray = gray
            return []
        
        # Diferença absoluta
        frame_diff = cv2.absdiff(self.motion_prev_gray, gray)
        thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=3)
        
        self.motion_prev_gray = gray
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Área mínima
                (x, y, w, h) = cv2.boundingRect(contour)
                motion_regions.append((x, y, w, h))
        
        return motion_regions
    
    def _determine_context(
        self,
        faces: List,
        motion_intensity: float,
        motion_regions: List,
        is_showing_object: bool
    ) -> SceneContext:
        """Determina o contexto com base em múltiplos fatores."""
        num_faces = len(faces)
        
        # Ação rápida
        if motion_intensity > 0.5:
            return SceneContext.ACTION
        
        # Mostrando objeto
        if is_showing_object:
            return SceneContext.PRODUCT_SHOWCASE
        
        # HISTERESE DE CONTEXTO
        # Evita mudar de contexto por "piscadas" na detecção
        
        raw_context = SceneContext.UNKNOWN
        
        # Baseado em faces
        if num_faces == 0:
            if motion_intensity < 0.1:
                raw_context = SceneContext.STATIC
            else:
                raw_context = SceneContext.UNKNOWN
        elif num_faces == 1:
            raw_context = SceneContext.SINGLE_SPEAKER
        elif num_faces == 2:
            raw_context = SceneContext.CONVERSATION
        else:
            raw_context = SceneContext.GROUP_SHOT

        # Overrides fortes
        if motion_intensity > 0.6: # Só se for MUITO movimento
            raw_context = SceneContext.ACTION
        if is_showing_object:
            raw_context = SceneContext.PRODUCT_SHOWCASE
            
        # Adicionar ao buffer
        self.context_buffer.append(raw_context)
        if len(self.context_buffer) > 15: # 0.5s buffer
             self.context_buffer.pop(0)
             
        # Decidir contexto estável (moda do buffer)
        from collections import Counter
        if not self.context_buffer:
             return raw_context
             
        counts = Counter(self.context_buffer).most_common(1)
        most_common = counts[0][0] if counts else raw_context
        
        return most_common
    
    def _detect_object_showcase(
        self, 
        frame: np.ndarray, 
        faces: List,
        motion_regions: List
    ) -> bool:
        """Detecta se um objeto está sendo mostrado."""
        height, width = frame.shape[:2]
        
        for (mx, my, mw, mh) in motion_regions:
            motion_center_y = my + mh // 2
            
            # Movimento na parte inferior (área de mãos/objetos)
            if motion_center_y > height * 0.5:
                # Verificar se não é um rosto
                motion_center_x = mx + mw // 2
                is_face = False
                for (fx, fy, fw, fh) in faces:
                    if (fx <= motion_center_x <= fx + fw and 
                        fy <= motion_center_y <= fy + fh):
                        is_face = True
                        break
                
                if not is_face:
                    motion_area = mw * mh
                    frame_area = width * height
                    if motion_area > frame_area * 0.008:
                        return True
        
        return False
    
    def _get_zoom_for_context(self, context: SceneContext, motion_intensity: float) -> float:
        """Retorna zoom ideal baseado no contexto."""
        base_zoom = {
            SceneContext.SINGLE_SPEAKER: 1.15,
            SceneContext.CONVERSATION: 0.85,
            SceneContext.PRODUCT_SHOWCASE: 0.75,
            SceneContext.GROUP_SHOT: 0.65,
            SceneContext.ACTION: 0.8,
            SceneContext.STATIC: 1.0,
            SceneContext.UNKNOWN: 1.0,
            SceneContext.TRANSITION: 1.0
        }
        
        zoom = base_zoom.get(context, 1.0)
        
        # Ajustar zoom baseado na intensidade de movimento
        if motion_intensity > 0.3:
            # Zoom out um pouco para capturar movimento
            zoom *= (1 - motion_intensity * 0.2)
        
        return zoom
    
    def _calculate_target_position(
        self,
        faces: List,
        motion_regions: List,
        context: SceneContext,
        width: int,
        height: int,
        is_showing_object: bool
    ) -> Tuple[float, float]:
        """Calcula posição alvo baseada no contexto."""
        
        if not faces:
            # Sem rostos, usar centro ou região de movimento
            if motion_regions:
                # Centro das regiões de movimento
                centers = [(x + w/2, y + h/2) for (x, y, w, h) in motion_regions]
                return np.mean([c[0] for c in centers]), np.mean([c[1] for c in centers])
            return width / 2, height / 2
        
        if context == SceneContext.SINGLE_SPEAKER:
            # Focar no rosto, com margem para movimentos
            x, y, w, h = faces[0]
            # Centro do rosto, levemente acima para headroom
            center_x = x + w / 2
            center_y = y + h / 2 - h * 0.1  # Um pouco acima
            return center_x, center_y
        
        elif context == SceneContext.CONVERSATION:
            # Centro entre os rostos
            centers = [(x + w/2, y + h/2) for (x, y, w, h) in faces]
            return np.mean([c[0] for c in centers]), np.mean([c[1] for c in centers])
        
        elif context == SceneContext.PRODUCT_SHOWCASE:
            # Centro entre rostos e área inferior
            face_centers = [(x + w/2, y + h/2) for (x, y, w, h) in faces]
            face_center_x = np.mean([c[0] for c in face_centers])
            face_center_y = np.mean([c[1] for c in face_centers])
            
            # Incluir área de objeto (mais baixa)
            target_y = (face_center_y + height * 0.65) / 2
            return face_center_x, target_y
        
        elif context == SceneContext.GROUP_SHOT:
            # Centro de todos os rostos com margem
            centers = [(x + w/2, y + h/2) for (x, y, w, h) in faces]
            center_x = np.mean([c[0] for c in centers])
            center_y = np.mean([c[1] for c in centers])
            return center_x, center_y
        
        else:
            # Default: centro
            if faces:
                x, y, w, h = faces[0]
                return x + w/2, y + h/2
            return width / 2, height / 2
    
    def _update_tracking_state(
        self,
        target_x: float,
        target_y: float,
        target_zoom: float,
        motion_intensity: float
    ):
        """Atualiza estado de tracking com lógica de VIRTUAL CAMERA (Cuts & Tripod)."""
        state = self.tracking_state
        
        # Calcular distância para o alvo
        dist = math.sqrt((target_x - state.target_x)**2 + (target_y - state.target_y)**2)
        
        # Lógica 1: CUT INSTÂNTANEO (Se mudou muito de foco)
        # Ex: Mudou de orador A para B (distante)
        frame_count = getattr(self, 'frame_count', 0)
        self.frame_count = frame_count + 1
        
        time_since_cut = self.frame_count - self.last_cut_time
        
        if dist > self.cut_threshold and time_since_cut > self.min_cut_interval:
            # CUT! Atualiza instantaneamente sem suavização
            state.x = target_x
            state.y = target_y
            state.zoom = target_zoom
            
            state.vx = 0
            state.vy = 0
            
            self.last_cut_time = self.frame_count
            
            # Atualizar targets
            state.target_x = target_x
            state.target_y = target_y
            state.target_zoom = target_zoom
            return

        # Lógica 2: TRIPOD MODE (Deadzone)
        # Se moveu pouco, IGNORAR (mantém a câmera estática no tripé)
        if dist < self.deadzone:
             # Mantém o target antigo
             target_x = state.target_x
             target_y = state.target_y
             if abs(target_zoom - state.target_zoom) < 0.2:
                 target_zoom = state.target_zoom
        
        # Lógica 3: SMOOTH ADJUSTMENT (Se for necessário mover pouco)
        # Usamos uma suavização lenta, tipo pan de câmera
        
        # Calcular erro
        error_x = target_x - state.x
        error_y = target_y - state.y
        error_zoom = target_zoom - state.zoom
        
        # Atualizar velocidade (simples exponential moving average)
        state.x += error_x * self.position_smoothing
        state.y += error_y * self.position_smoothing
        state.zoom += error_zoom * self.zoom_smoothing
        
        # Zerar velocidade inercial (não usada no modo Virtual Cam)
        state.vx = 0
        state.vy = 0
        
        # Atualizar targets
        state.target_x = target_x
        state.target_y = target_y
        state.target_zoom = target_zoom
    
    def analyze_frame(
        self, 
        frame: np.ndarray,
        audio_energy: float = 0.0,
        has_speech: bool = False
    ) -> CropDecision:
        """
        Analisa um frame e retorna decisão de crop suavizada.
        """
        height, width = frame.shape[:2]
        
        # Inicializar estado se necessário
        if not self.initialized:
            self.tracking_state.x = width / 2
            self.tracking_state.y = height / 2
            self.tracking_state.zoom = 1.0
            self.initialized = True
        
        # Detectar rostos
        faces = self._detect_faces(frame)
        
        # Calcular optical flow
        motion_intensity, flow_x, flow_y = self._calculate_optical_flow(frame)
        
        # Detectar regiões de movimento
        motion_regions = self._detect_motion_regions(frame)
        
        # Detectar objeto showcase
        is_showing_object = self._detect_object_showcase(frame, faces, motion_regions)
        
        # Determinar contexto
        context = self._determine_context(faces, motion_intensity, motion_regions, is_showing_object)
        
        # Adicionar ao histórico
        self.context_history.append(context)
        self.motion_history.append(motion_intensity)
        if len(self.context_history) > self.max_history:
            self.context_history.pop(0)
            self.motion_history.pop(0)
        
        # Calcular posição alvo
        target_x, target_y = self._calculate_target_position(
            faces, motion_regions, context, width, height, is_showing_object
        )
        
        # Calcular zoom alvo
        target_zoom = self._get_zoom_for_context(context, motion_intensity)
        
        # Atualizar tracking state com física suave
        self._update_tracking_state(target_x, target_y, target_zoom, motion_intensity)
        
        # Garantir limites
        state = self.tracking_state
        crop_width = height / self.target_ratio / state.zoom
        
        final_x = max(crop_width/2, min(state.x, width - crop_width/2))
        final_y = max(0, min(state.y, height))
        
        return CropDecision(
            center_x=final_x,
            center_y=final_y,
            zoom_level=state.zoom,
            context=context,
            confidence=0.9 if faces else 0.6,
            active_regions=list(faces) + motion_regions,
            motion_intensity=motion_intensity
        )
    
    def apply_crop(
        self, 
        frame: np.ndarray, 
        decision: CropDecision
    ) -> np.ndarray:
        """Aplica o crop ao frame com segurança máxima."""
        try:
            if frame is None or frame.size == 0:
                # Retornar frame preto se entrada inválida
                return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
            
            height, width = frame.shape[:2]
            
            # Validar zoom
            zoom = max(0.4, min(2.5, decision.zoom_level))
            
            # 1. Calcular dimensões do crop (RIGOROSAMENTE PROPORCIONAIS)
            # Crop Vertical 9:16 -> Width = Height * (9/16)
            # self.target_ratio é normalmente H/W ou W/H? 
            # Assumindo standard vertical target (1080x1920): ratio = 1920/1080 = 1.77 (H/W) ?
            # O código original usava: crop_width = int(height / self.target_ratio / zoom)
            # Se self.target_ratio for 16/9 (1.77), então crop_width = H / 1.77. Correto para vertical strip.
            
            crop_height = height # Sempre altura total inicialmente
            crop_width = int(crop_height / self.target_ratio / zoom)
            
            # 2. Centralizar crop
            center_x = decision.center_x
            
            # 3. Calcular coordenadas x1, x2
            x1 = int(center_x - crop_width / 2)
            x2 = x1 + crop_width
            
            # 4. ANTI-DISTORTION & LETTERBOXING SAFETY
            # Garantir ZERO distorção. Se o crop sair, usamos Letterbox.
            
            # Calcular limites teóricos
            x1 = int(center_x - crop_width / 2)
            y1 = 0 # Sempre altura total primeiro
            
            # Ajustar dimensões finais desejadas
            final_crop_width = crop_width
            final_crop_height = crop_height
            
            # Verificar se cabe na imagem original
            # Se x1 < 0 ou x1 + w > width, temos um problema de borda
            
            # Tentar fazer clamp (shift) primeiro
            if x1 < 0:
                x1 = 0 # Encosta na esquerda
            elif x1 + final_crop_width > width:
                x1 = width - final_crop_width # Encosta na direita
                
            # Agora verificar se AINDA está fora (caso onde crop é maior que video)
            # ou se y1+h > height
            
            valid_x1 = max(0, x1)
            valid_y1 = max(0, y1)
            valid_x2 = min(width, x1 + final_crop_width)
            valid_y2 = min(height, y1 + final_crop_height)
            
            # Extrair região válida
            crop_valid = frame[valid_y1:valid_y2, valid_x1:valid_x2]
            
            if crop_valid.size == 0:
                 return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

            # Agora precisamos colocar essa região válida dentro do frame final 9:16
            # SEM ESTICAR.
            
            # Criar canvas preto final
            canvas = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
            
            # Redimensionar crop_valid mantendo aspect ratio para caber no canvas
            h_valid, w_valid = crop_valid.shape[:2]
            
            # Calcular escala para caber (fit)
            # Queremos preencher, mas se não der, fit.
            # Normalmente o usuário quer FILL (sem bordas), mas pediu ZERO DISTORÇÃO.
            # Se não der pra preencher sem cortar ou distorcer, cortamos (pan/scan style) acima.
            # A lógica acima (clamp) já tentou manter o frame cheio.
            
            # Mas vamos garantir o resize final correto.
            # Escalar crop_valid para target_width, mantendo prop.
            
            # Scale para cobrir largura (fill width)
            scale = self.target_width / w_valid
            new_h = int(h_valid * scale)
            
            resized_crop = cv2.resize(crop_valid, (self.target_width, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Colocar no canvas
            # Centralizar verticalmente
            y_offset = (self.target_height - new_h) // 2
            
            if y_offset >= 0:
                # Letterbox (barras em cima/baixo) - Raro para 9:16 vindo de landscape
                y_end = y_offset + new_h
                canvas[y_offset:y_end, :] = resized_crop
            else:
                # Crop vertical (excesso de altura)
                # O resize gerou algo mais alto que o target. Pegar centro.
                y_start_crop = -y_offset
                y_end_crop = y_start_crop + self.target_height
                if y_end_crop > new_h: y_end_crop = new_h # Safety
                
                # Pegar fatia
                final_slice = resized_crop[y_start_crop:y_end_crop, :]
                
                # Se fatia menor (erros de arredondamento), colar no topo
                h_slice = final_slice.shape[0]
                canvas[0:h_slice, :] = final_slice

            return canvas
            
        except Exception as e:
            # Em caso de QUALQUER erro, retornar frame redimensionado
            try:
                return cv2.resize(frame, (self.target_width, self.target_height))
            except:
                return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
    
    def reset(self):
        """Reseta o estado do cropper."""
        self.tracking_state = TrackingState()
        self.initialized = False
        self.prev_frame_gray = None
        self.prev_points = None
        self.motion_prev_gray = None
        self.motion_history = []
        self.context_history = []
