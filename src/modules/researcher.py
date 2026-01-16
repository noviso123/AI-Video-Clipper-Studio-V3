"""
Módulo de Pesquisa e Extração Web (Cérebro)
Usa Crawl4AI para capturar conteúdo de URLs e transformar em Markdown pronto para LLM.
"""
import os
import asyncio
from typing import Optional
from crawl4ai import AsyncWebCrawler
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class ContentResearcher:
    """Extrai conteúdo de URLs de forma inteligente"""

    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), 'temp', 'research')
        os.makedirs(self.temp_dir, exist_ok=True)

    async def crawl_url(self, url: str) -> str:
        """Processa uma URL e retorna o conteúdo em Markdown"""
        try:
            logger.info(f"🌐 Iniciando Crawl: {url}")

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)

                if result.success:
                    logger.info(f"✅ Crawl concluído: {len(result.markdown)} caracteres extraídos.")
                    return result.markdown
                else:
                    logger.error(f"❌ Erro no Crawl: {result.error_message}")
                    return f"Erro no Crawl: {result.error_message}"

        except Exception as e:
            logger.error(f"❌ Erro crítico no pesquisador: {e}")
            return f"Erro na pesquisa: {str(e)}"

    def run_crawl(self, url: str) -> str:
        """Wrapper síncrono para facilitar a integração com Flask se necessário"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            content = loop.run_until_complete(self.crawl_url(url))
            loop.close()
            return content
        except Exception as e:
            logger.error(f"Erro no loop de crawl: {e}")
            return str(e)

# Singleton
researcher = None
def get_researcher() -> ContentResearcher:
    global researcher
    if researcher is None:
        researcher = ContentResearcher()
    return researcher
