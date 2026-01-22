from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import Toolkit
from ..publishers.tiktok_publisher import TikTokPublisher
from ..publishers.youtube_publisher import YouTubePublisher
from ..publishers.instagram_publisher import InstagramPublisher
from ..core.config import config as app_config
from ..core.logger import setup_logger
import os

logger = setup_logger(__name__)

class SocialTools(Toolkit):
    def __init__(self):
        super().__init__(name="social_tools")
        self.tiktok = TikTokPublisher()
        self.youtube = YouTubePublisher()
        self.instagram = InstagramPublisher()
        
        # Registrar ferramentas
        self.register(self.publish_to_all_platforms)
        self.register(self.publish_to_tiktok)
        self.register(self.publish_to_youtube)
        self.register(self.publish_to_instagram)

    def publish_to_tiktok(self, video_path: str, title: str, headless: bool = True) -> str:
        """Publica um vídeo apenas no TikTok."""
        try:
            url = self.tiktok.upload(video_path, title, headless=headless)
            return f"✅ TikTok: Concluído ({url})"
        except Exception as e:
            return f"❌ TikTok: Erro ({str(e)})"

    def publish_to_youtube(self, video_path: str, title: str, description: str = "", headless: bool = True) -> str:
        """Publica um vídeo apenas no YouTube Shorts."""
        try:
            url = self.youtube.upload(video_path, title, description, headless=headless)
            return f"✅ YouTube: Concluído ({url})"
        except Exception as e:
            return f"❌ YouTube: Erro ({str(e)})"

    def publish_to_instagram(self, video_path: str, caption: str, headless: bool = True) -> str:
        """Publica um vídeo apenas no Instagram Reels."""
        try:
            url = self.instagram.upload(video_path, caption, headless=headless)
            return f"✅ Instagram: Concluído ({url})"
        except Exception as e:
            return f"❌ Instagram: Erro ({str(e)})"

    def publish_to_all_platforms(self, video_path: str, title: str, description: str = "", headless: bool = True) -> str:
        """
        Publica o mesmo vídeo em TODAS as plataformas (TikTok, YouTube Shorts, Instagram Reels).
        Usa o robô de browser em cada uma.
        """
        results = []
        logger.info(f"🚀 Iniciando postagem multi-plataforma para: {video_path}")
        
        results.append(self.publish_to_tiktok(video_path, title, headless))
        results.append(self.publish_to_youtube(video_path, title, description, headless))
        results.append(self.publish_to_instagram(video_path, title, headless)) # Usa title como caption
        
        return "\n".join(results)

class SocialAutoAgent:
    """Agente Multi-Plataforma Agno"""
    
    def __init__(self):
        self.model = app_config.GEMINI_MODEL
        self.tools = SocialTools()
        
        self.agent = Agent(
            model=Gemini(id=self.model),
            tools=[self.tools],
            description="Você é um assistente de publicação multi-plataforma especialista em TikTok, YouTube Shorts e Instagram Reels.",
            instructions=[
                "Você gerencia publicações automáticas via robô de browser (Selenium).",
                "Você pode publicar em uma plataforma específica ou em todas simultaneamente.",
                "Sempre que o usuário pedir para publicar em 'todos' ou 'YouTube e Reels', use a ferramenta `publish_to_all_platforms`.",
                "Explique que o processo roda em segundo plano (headless) por padrão e usa os perfis já logados.",
                "Se houver erro de login, peça ao usuário para rodar uma vez em modo visível para fazer o login manual."
            ],
            markdown=True
        )

    def run(self, message: str):
        return self.agent.run(message)
