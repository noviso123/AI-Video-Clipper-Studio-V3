"""
Módulo de Detecção de Legendas Existentes (Novo)
Detecta legendas hardcoded em vídeos para evitar sobreposição e crop inadequado.

FUNCIONALIDADES:
- Detecta áreas com texto/legendas no vídeo
- Identifica posição das legendas (topo, centro, base)
- Retorna informações para crop inteligente
- Sugere posição ideal para novas legendas
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class SubtitleDetector:
    """Detecta legendas existentes em vídeos."""
    
    def __init__(self):
        logger.info("🔍 Subtitle Detector: Inicializado")
        
        # Regiões típicas de legendas (em % da altura)
        self.SUBTITLE_REGIONS = {
            'top': (0.0, 0.20),      # 0-20% do topo
            'center': (0.35, 0.65),  # 35-65% (centro)
            'bottom': (0.75, 1.0),   # 75-100% (base)
        }
    
    def detect_subtitle_regions(
        self, 
        video_path: Path,
        sample_count: int = 10
    ) -> Dict:
        """
        Detecta regiões com legendas no vídeo.
        
        Args:
            video_path: Caminho do vídeo
            sample_count: Número de frames para amostrar
            
        Returns:
            Dicionário com informações sobre legendas detectadas:
            {
                'has_subtitles': bool,
                'subtitle_position': 'top' | 'center' | 'bottom' | None,
                'subtitle_region': (y_start, y_end) em pixels,
                'confidence': float (0-1),
                'suggested_new_position': 'top' | 'center' | 'bottom',
                'safe_crop_region': (y_start, y_end) região segura para crop
            }
        """
        logger.info(f"   🔍 Analisando legendas existentes em: {video_path.name}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"   ❌ Não foi possível abrir o vídeo")
            return self._default_result()
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        # Amostrar frames ao longo do vídeo
        text_detections = {
            'top': [],
            'center': [],
            'bottom': []
        }
        
        for i in range(sample_count):
            timestamp = duration * (i + 1) / (sample_count + 1)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                continue
            
            # Detectar texto em cada região
            for region_name, (y_start_pct, y_end_pct) in self.SUBTITLE_REGIONS.items():
                y_start = int(frame_height * y_start_pct)
                y_end = int(frame_height * y_end_pct)
                
                region = frame[y_start:y_end, :]
                has_text, confidence = self._detect_text_in_region(region)
                
                if has_text:
                    text_detections[region_name].append(confidence)
        
        cap.release()
        
        # Analisar resultados
        result = self._analyze_detections(text_detections, frame_height, frame_width)
        
        logger.info(f"      Legendas detectadas: {'Sim' if result['has_subtitles'] else 'Não'}")
        if result['has_subtitles']:
            logger.info(f"      Posição: {result['subtitle_position']}")
            logger.info(f"      Confiança: {result['confidence']:.1%}")
            logger.info(f"      Sugestão para novas legendas: {result['suggested_new_position']}")
        
        return result
    
    def _detect_text_in_region(self, region: np.ndarray) -> Tuple[bool, float]:
        """
        Detecta se há texto em uma região da imagem.
        
        Usa múltiplas técnicas:
        1. Detecção de bordas (texto tem muitas bordas)
        2. Análise de contraste (legendas têm alto contraste)
        3. Detecção de áreas uniformes (fundo de legenda)
        
        Returns:
            Tupla (has_text, confidence)
        """
        if region is None or region.size == 0:
            return False, 0.0
        
        try:
            # Converter para grayscale
            if len(region.shape) == 3:
                gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            else:
                gray = region
            
            h, w = gray.shape
            
            # 1. Detecção de bordas (texto tem muitas bordas horizontais)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)
            
            # 2. Análise de contraste local
            # Legendas geralmente têm alto contraste local
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            contrast = np.std(gray - blur)
            
            # 3. Detectar áreas com cores uniformes (fundo de legenda)
            # Legendas frequentemente têm fundo preto/escuro ou caixa colorida
            dark_pixels = np.sum(gray < 50) / (h * w)
            bright_pixels = np.sum(gray > 200) / (h * w)
            
            # 4. Verificar padrão de texto (linhas horizontais de alto contraste)
            horizontal_projection = np.sum(edges, axis=1)
            text_lines = np.sum(horizontal_projection > w * 0.1)
            
            # Calcular score de confiança
            confidence = 0.0
            
            # Bordas moderadas indicam texto
            if 0.05 < edge_density < 0.3:
                confidence += 0.3
            
            # Alto contraste indica texto
            if contrast > 30:
                confidence += 0.3
            
            # Combinação de pixels escuros e claros (texto branco em fundo escuro)
            if dark_pixels > 0.3 and bright_pixels > 0.05:
                confidence += 0.2
            
            # Linhas de texto detectadas
            if text_lines > 1:
                confidence += 0.2
            
            has_text = confidence > 0.4
            
            return has_text, min(confidence, 1.0)
            
        except Exception as e:
            logger.debug(f"   Erro na detecção de texto: {e}")
            return False, 0.0
    
    def _analyze_detections(
        self, 
        detections: Dict[str, List[float]],
        frame_height: int,
        frame_width: int
    ) -> Dict:
        """Analisa as detecções e retorna resultado consolidado."""
        
        # Calcular confiança média para cada região
        region_scores = {}
        for region, confidences in detections.items():
            if confidences:
                region_scores[region] = np.mean(confidences)
            else:
                region_scores[region] = 0.0
        
        # Encontrar região com maior score
        max_region = max(region_scores, key=region_scores.get)
        max_score = region_scores[max_region]
        
        # Determinar se há legendas
        has_subtitles = max_score > 0.5
        
        # Calcular região de legenda em pixels
        subtitle_region = None
        if has_subtitles:
            y_start_pct, y_end_pct = self.SUBTITLE_REGIONS[max_region]
            subtitle_region = (
                int(frame_height * y_start_pct),
                int(frame_height * y_end_pct)
            )
        
        # Sugerir posição para novas legendas (evitar sobreposição)
        suggested_position = self._suggest_new_position(max_region if has_subtitles else None)
        
        # Calcular região segura para crop (evitar cortar legendas)
        safe_crop_region = self._calculate_safe_crop_region(
            has_subtitles, max_region, frame_height
        )
        
        return {
            'has_subtitles': has_subtitles,
            'subtitle_position': max_region if has_subtitles else None,
            'subtitle_region': subtitle_region,
            'confidence': max_score,
            'suggested_new_position': suggested_position,
            'safe_crop_region': safe_crop_region,
            'region_scores': region_scores,
            'frame_size': (frame_width, frame_height)
        }
    
    def _suggest_new_position(self, existing_position: Optional[str]) -> str:
        """Sugere posição para novas legendas evitando sobreposição."""
        if existing_position is None:
            return 'bottom'  # Padrão
        
        # Se já tem legenda embaixo, colocar no centro
        if existing_position == 'bottom':
            return 'center'
        
        # Se já tem no centro, colocar embaixo
        if existing_position == 'center':
            return 'bottom'
        
        # Se já tem no topo, colocar embaixo
        if existing_position == 'top':
            return 'bottom'
        
        return 'bottom'
    
    def _calculate_safe_crop_region(
        self, 
        has_subtitles: bool,
        subtitle_position: Optional[str],
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Calcula região segura para crop que não corta legendas.
        
        Returns:
            Tupla (y_start, y_end) da região segura
        """
        if not has_subtitles:
            # Sem legendas, toda a altura é segura
            return (0, frame_height)
        
        # Com legendas, evitar a região onde estão
        if subtitle_position == 'bottom':
            # Legendas embaixo: região segura é do topo até 75%
            return (0, int(frame_height * 0.75))
        
        elif subtitle_position == 'top':
            # Legendas no topo: região segura é de 20% até embaixo
            return (int(frame_height * 0.20), frame_height)
        
        elif subtitle_position == 'center':
            # Legendas no centro: mais complicado, priorizar base
            return (0, int(frame_height * 0.35))
        
        return (0, frame_height)
    
    def _default_result(self) -> Dict:
        """Retorna resultado padrão quando não consegue analisar."""
        return {
            'has_subtitles': False,
            'subtitle_position': None,
            'subtitle_region': None,
            'confidence': 0.0,
            'suggested_new_position': 'bottom',
            'safe_crop_region': None,
            'region_scores': {},
            'frame_size': None
        }
    
    def get_optimal_caption_position(
        self, 
        video_path: Path,
        target_position: str = 'auto'
    ) -> Tuple[str, float]:
        """
        Determina a posição ideal para adicionar legendas.
        
        Args:
            video_path: Caminho do vídeo
            target_position: 'auto', 'top', 'center', 'bottom'
            
        Returns:
            Tupla (posição, y_percentage)
        """
        if target_position != 'auto':
            positions = {
                'top': 0.15,
                'center': 0.50,
                'bottom': 0.80
            }
            return target_position, positions.get(target_position, 0.80)
        
        # Detectar legendas existentes
        result = self.detect_subtitle_regions(video_path)
        
        suggested = result['suggested_new_position']
        
        positions = {
            'top': 0.15,
            'center': 0.50,
            'bottom': 0.80
        }
        
        return suggested, positions.get(suggested, 0.80)


if __name__ == "__main__":
    # Teste rápido
    detector = SubtitleDetector()
    print("Subtitle Detector inicializado com sucesso!")
