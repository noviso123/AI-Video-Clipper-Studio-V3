"""
Gerenciador de Publicações
Coordena o upload para múltiplas plataformas usando Selenium.
"""
from typing import List, Dict
from ..browsers.profile_manager import ProfileManager
from ..core.logger import setup_logger

logger = setup_logger(__name__)

from ..publishers.tiktok_publisher import TikTokPublisher
from ..publishers.youtube_publisher import YouTubePublisher
from ..publishers.instagram_publisher import InstagramPublisher

class PublisherManager:
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.platforms = ["tiktok", "youtube", "instagram"]
        self.tiktok_publisher = TikTokPublisher()
        self.youtube_publisher = YouTubePublisher()
        self.instagram_publisher = InstagramPublisher()
        
    def publish_all(self, video_path: str, metadata: Dict) -> Dict[str, str]:
        """
        Publica o vídeo em todas as plataformas configuradas.
        Returns:
            Dict: { "tiktok": "http://link...", "youtube": "http://link..." }
        """
        results = {}
        
        # 1. TikTok
        try:
            # Usar título + hashtags para a descrição
            desc = f"{metadata['title']}\n\n{metadata['description']}\n\n{' '.join(metadata['hashtags'])}"
            link = self.tiktok_publisher.upload(video_path, desc)
            results['tiktok'] = link
        except Exception as e:
            logger.error(f"❌ Erro TikTok: {e}")
            results['tiktok'] = f"Erro: {str(e)}"

        # 2. YouTube Shorts
        try:
            # YouTube Title limit is 100 chars
            title = metadata['title'][:90] 
            desc = f"{metadata['description']}\n\n{' '.join(metadata['hashtags'])}"
            link = self.youtube_publisher.upload(video_path, title, desc)
            results['youtube'] = link
        except Exception as e:
            logger.error(f"❌ Erro YouTube: {e}")
            results['youtube'] = f"Erro: {str(e)}"

        # 3. Instagram Reels
        try:
            caption = f"{metadata['title']}\n\n{metadata['description']}\n.\n.\n{' '.join(metadata['hashtags'])}"
            link = self.instagram_publisher.upload(video_path, caption)
            results['instagram'] = link
        except Exception as e:
            logger.error(f"❌ Erro Instagram: {e}")
            results['instagram'] = f"Erro: {str(e)}"
            
        return results




