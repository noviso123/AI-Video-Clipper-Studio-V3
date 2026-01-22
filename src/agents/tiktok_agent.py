from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import Toolkit
from ..publishers.tiktok_publisher import TikTokPublisher
from ..core.config import config as app_config
from ..core.logger import setup_logger
import os

logger = setup_logger(__name__)

class TikTokTools(Toolkit):
    def __init__(self):
        super().__init__(name="tiktok_tools")
        self.publisher = TikTokPublisher()
        # Registrar as funções como ferramentas
        self.register(self.publish_to_tiktok_with_robot)

    def publish_to_tiktok_with_robot(self, video_path: str, title: str) -> str:
        """
        Abre o navegador e publica um vídeo no TikTok usando um robô (Selenium).
        O usuário deve estar logado no navegador que será aberto.
        
        Args:
            video_path: Caminho completo para o arquivo .mp4
            title: Legenda do vídeo (máx 150 caracteres)
        """
        try:
            logger.info(f"🤖 Robô iniciando publicação: {video_path}")
            # O TikTokPublisher já gerencia o Selenium e aguarda login se necessário
            video_url = self.publisher.upload(video_path, title)
            return f"✅ Publicação robótica iniciada com sucesso! Link/Status: {video_url}"
        except Exception as e:
            logger.error(f"❌ Falha no robô TikTok: {str(e)}")
            return f"❌ Erro operacional no robô: {str(e)}"

class TikTokAutoAgent:
    """Agente Agno que gerencia a automação do TikTok via Browser (Robô)"""
    
    def __init__(self):
        self.model = app_config.GEMINI_MODEL
        self.tools = TikTokTools()
        
        self.agent = Agent(
            model=Gemini(id=self.model),
            tools=[self.tools],
            description="Você é um assistente de automação que controla um robô de browser para o TikTok.",
            instructions=[
                "Você é capaz de abrir o navegador e publicar vídeos diretamente no site do TikTok.",
                "Não dependemos mais de chaves de API oficiais para isso, usamos automação de interface.",
                "Sempre peça ao usuário o caminho do vídeo e a legenda desejada.",
                "Explique que o navegador será aberto e, se ele não estiver logado, precisará fazer o login manualmente uma vez.",
                "Use a ferramenta `publish_to_tiktok_with_robot` para iniciar o processo."
            ],
            markdown=True
        )

    def run(self, message: str):
        """Executa um comando no agente"""
        return self.agent.run(message)
