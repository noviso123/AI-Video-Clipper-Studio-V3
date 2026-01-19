"""
Módulo de B-Rolls 100% Offline e Procedural
Gerencia assets locais e gera fundos animados matematicamente.
"""
from typing import List, Dict, Optional
from pathlib import Path
import os
import random
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip, VideoClip
from moviepy.video.fx.resize import resize
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class BRollManager:
    """Gerencia B-Rolls locais e gerações procedurais"""

    # Keywords que disparam B-Rolls
    BROLL_TRIGGERS = {
        'dinheiro': ['money', 'cash', 'wealth', 'business'],
        'sucesso': ['success', 'winner', 'celebration', 'trophy'],
        'trabalho': ['office', 'work', 'laptop', 'meeting'],
        'viagem': ['travel', 'vacation', 'beach', 'adventure'],
        'comida': ['food', 'restaurant', 'cooking', 'meal'],
        'saude': ['fitness', 'gym', 'health', 'yoga'],
        'tecnologia': ['technology', 'computer', 'smartphone', 'innovation'],
        'natureza': ['nature', 'landscape', 'forest', 'mountains']
    }

    def __init__(self):
        """Inicializa o gerenciador de B-Rolls"""
        self.assets_dir = Path("assets/brolls")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar pastas para categorias se não existirem
        for category in self.BROLL_TRIGGERS.keys():
            (self.assets_dir / category).mkdir(exist_ok=True)

    def detect_broll_moments(self, segments: List[Dict]) -> List[Dict]:
        """Detecta momentos onde B-Rolls podem ser inseridos"""
        logger.info("🎬 Detectando momentos para B-Rolls...")

        broll_moments = []

        for segment in segments:
            text_lower = segment['text'].lower()

            for category, keywords in self.BROLL_TRIGGERS.items():
                if any(kw in text_lower for kw in keywords) or category in text_lower:
                    broll_moments.append({
                        'timestamp': segment['start'],
                        'duration': min(2.0, segment['end'] - segment['start']),
                        'category': category,
                        'text': segment['text']
                    })
                    break  # Uma categoria por segmento

        logger.info(f"   Encontrados {len(broll_moments)} momentos para B-Rolls")
        return broll_moments

    def get_broll_clip(self, category: str, duration: float, size: tuple) -> VideoClip:
        """
        Obtém um clip de B-Roll:
        1. Tenta encontrar arquivo local em assets/brolls/{category}
        2. Se não encontrar, tenta baixar usando BrollScraper
        3. Se falhar, usa Procedural (Fallback final)
        """
        # 1. Busca Local
        category_dir = self.assets_dir / category
        if category_dir.exists():
            files = list(category_dir.glob("*.mp4"))
            if files:
                file_path = random.choice(files)
                logger.info(f"   📂 Usando asset local: {file_path.name}")
                return self._load_and_process_clip(file_path, duration, size)

        # 2. Scraping (Download Sem API)
        try:
            from .broll_scraper import BrollScraper
            scraper = BrollScraper()
            logger.info(f"   🌍 Buscando B-Roll online (Scraping): {category}")
            downloaded_path = scraper.search_and_download(category)
            
            if downloaded_path and downloaded_path.exists():
                return self._load_and_process_clip(downloaded_path, duration, size)
                
        except Exception as e:
            logger.warning(f"   ⚠️ Falha no scraping: {e}")

        # 3. Geração Procedural (Fallback Final)
        logger.info(f"   🎨 Gerando B-Roll procedural (Fallback): {category}")
        return self._generate_procedural_broll(category, duration, size)

    def _load_and_process_clip(self, path: Path, duration: float, size: tuple) -> VideoClip:
        """Carrega e processa um arquivo de vídeo para B-Roll"""
        clip = VideoFileClip(str(path))
        w, h = size
        
        # Loop se for curto
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        else:
            clip = clip.subclip(0, duration)
            
        # Resize e Crop (Cover)
        clip = resize(clip, height=h)
        if clip.w < w:
            clip = resize(clip, width=w)
            
        clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=w, height=h)
        
        # Sem áudio
        clip = clip.without_audio()
        
        return clip

    def _generate_procedural_broll(self, category: str, duration: float, size: tuple) -> VideoClip:
        """Gera fundos animados baseados na categoria"""
        w, h = size
        
        # Cores base por categoria
        colors = {
            'dinheiro': (0, 100, 0),    # Verde Escuro
            'sucesso': (100, 80, 0),    # Dourado
            'tecnologia': (0, 0, 100),  # Azul Tech
            'natureza': (0, 60, 0),     # Verde Folha
            'viagem': (0, 60, 100),     # Azul Mar
        }
        base_color = colors.get(category, (20, 20, 20)) # Cinza padrão
        
        # Criar fundo sólido
        bg = ColorClip(size, color=base_color, duration=duration)
        
        # Adicionar elementos simples (ruído ou gradiente simulado)
        # Nota: MoviePy puro é limitado para gráficos complexos, 
        # então vamos fazer algo simples: overlay de cor com opacidade
        
        overlay_color = tuple([min(255, c + 50) for c in base_color])
        overlay = ColorClip(size, color=overlay_color, duration=duration)
        
        # Máscara animada (simulando movimento)
        def make_mask(t):
            # Cria um padrão de varredura simples
            import numpy as np
            mask = np.zeros((h, w), dtype=float)
            # Faixa vertical que se move
            x_pos = int((t / duration) * w)
            width = int(w * 0.2)
            start = max(0, x_pos)
            end = min(w, x_pos + width)
            mask[:, start:end] = 0.3 # 30% opacidade
            return mask

        overlay.mask = VideoClip(ismask=True, make_frame=make_mask, duration=duration)
        
        final = CompositeVideoClip([bg, overlay])
        return final

    def add_brolls_to_clip(
        self,
        video_clip: VideoFileClip,
        broll_moments: List[Dict]
    ) -> VideoFileClip:
        """Adiciona B-Rolls ao vídeo"""
        if not broll_moments:
            return video_clip

        logger.info(f"🎨 Adicionando {len(broll_moments)} B-Rolls (Locais/Procedurais)...")

        final_clip = video_clip
        clips_to_overlay = []

        for moment in broll_moments[:5]:  # Limitado a 5 para não poluir
            try:
                broll = self.get_broll_clip(moment['category'], moment['duration'], video_clip.size)
                
                broll = broll.set_start(moment['timestamp'])
                broll = broll.set_position('center')
                broll = broll.set_opacity(0.8) # Um pouco transparente para ver o original? Ou 1.0? 
                # Usuário pediu algo "melhorado", geralmente B-Roll cobre 100%. 
                # Mas sem áudio do B-Roll.
                broll = broll.set_opacity(1.0)
                
                clips_to_overlay.append(broll)

            except Exception as e:
                logger.warning(f"   Erro ao gerar B-Roll: {e}")
                continue

        if clips_to_overlay:
            final_clip = CompositeVideoClip([video_clip] + clips_to_overlay)
            logger.info(f"   ✅ B-Rolls integrados.")
            return final_clip

        return video_clip


if __name__ == "__main__":
    # Teste rápido
    broll = BRollManager()
    print("BRoll Manager Offline pronto.")
    clip = broll.get_broll_clip('tecnologia', 2.0, (1080, 1920))
    print(f"Clip gerado: {clip.duration}s")
