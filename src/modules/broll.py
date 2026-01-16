"""
Módulo de B-Rolls Automáticos (Fase 8)
Insere imagens/vídeos de stock baseado em keywords detectadas
"""
from typing import List, Dict, Optional
from pathlib import Path
import os
import requests
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class BRollManager:
    """Gerencia inserção de B-Rolls automáticos"""

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

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o gerenciador de B-Rolls

        Args:
            api_key: API key do Pexels (opcional, pode ser grátis)
        """
        self.api_key = api_key or os.getenv('PEXELS_API_KEY', '')
        self.cache_dir = Config.ASSETS_DIR / "broll_cache"
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def detect_broll_moments(self, segments: List[Dict]) -> List[Dict]:
        """
        Detecta momentos onde B-Rolls podem ser inseridos

        Args:
            segments: Segmentos da transcrição

        Returns:
            Lista de momentos com keywords para B-Roll
        """
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
                        'search_terms': keywords,
                        'text': segment['text']
                    })
                    break  # Uma categoria por segmento

        logger.info(f"   Encontrados {len(broll_moments)} momentos para B-Rolls")
        return broll_moments

    def get_stock_image(self, query: str) -> Optional[Path]:
        """
        Busca imagem de stock (Pexels API ou cache local)

        Args:
            query: Termo de busca

        Returns:
            Caminho da imagem ou None
        """
        # Verificar cache primeiro
        cache_file = self.cache_dir / f"{query.replace(' ', '_')}.jpg"
        if cache_file.exists():
            return cache_file

        # Se não tem API key, avisar e retornar None (Produção Real)
        if not self.api_key:
            logger.error(f"   ❌ Erro: PEXELS_API_KEY não configurada. B-Roll ignorado para: {query}")
            return None

        try:
            # Buscar no Pexels
            headers = {'Authorization': self.api_key}
            response = requests.get(
                f'https://api.pexels.com/v1/search?query={query}&per_page=1',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data['photos']:
                    image_url = data['photos'][0]['src']['medium']

                    # Download da imagem
                    img_response = requests.get(image_url, timeout=10)
                    if img_response.status_code == 200:
                        with open(cache_file, 'wb') as f:
                            f.write(img_response.content)
                        logger.info(f"   ✅ B-Roll baixado: {query}")
                        return cache_file

        except Exception as e:
            logger.warning(f"   Erro ao buscar B-Roll: {e}")

        return None

    def add_brolls_to_clip(
        self,
        video_clip: VideoFileClip,
        broll_moments: List[Dict]
    ) -> VideoFileClip:
        """
        Adiciona B-Rolls ao vídeo

        Args:
            video_clip: Clipe de vídeo original
            broll_moments: Momentos detectados para B-Rolls

        Returns:
            Vídeo com B-Rolls inseridos
        """
        if not broll_moments:
            return video_clip

        logger.info(f"🎨 Adicionando {len(broll_moments)} B-Rolls ao vídeo...")

        overlays = []

        for moment in broll_moments[:3]:  # Máximo 3 B-Rolls por clipe
            try:
                # Buscar imagem
                search_term = moment['search_terms'][0] if moment['search_terms'] else moment['category']
                image_path = self.get_stock_image(search_term)

                if image_path and image_path.exists():
                    # Criar overlay de imagem
                    img_clip = ImageClip(str(image_path))
                    img_clip = img_clip.set_start(moment['timestamp'])
                    img_clip = img_clip.set_duration(moment['duration'])
                    img_clip = img_clip.resize(height=video_clip.h * 0.3)  # 30% da altura
                    img_clip = img_clip.set_position(('right', 'top'))
                    img_clip = img_clip.set_opacity(0.7)

                    overlays.append(img_clip)

            except Exception as e:
                logger.warning(f"   Erro ao adicionar B-Roll: {e}")
                continue

        if overlays:
            final_video = CompositeVideoClip([video_clip] + overlays)
            logger.info(f"   ✅ {len(overlays)} B-Rolls adicionados")
            return final_video

        return video_clip


if __name__ == "__main__":
    # Teste rápido
    broll = BRollManager()

    # Exemplo
    test_segments = [
        {'start': 0.0, 'end': 5.0, 'text': 'Vamos falar de dinheiro'},
        {'start': 5.0, 'end': 10.0, 'text': 'E sobre sucesso nos negócios'},
    ]

    moments = broll.detect_broll_moments(test_segments)
    print(f"Momentos detectados: {len(moments)}")
