"""
Módulo de Scraping de B-Rolls (Alternativa Gratuita sem API)
Faz scraping ético do Pexels/Coverr para obter vídeos gratuitos.
"""
import requests
import random
import json
import re
from typing import List, Optional
from pathlib import Path
from bs4 import BeautifulSoup
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class BrollScraper:
    """Scraper para baixar vídeos de stock gratuitos sem API Key"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.download_dir = Path("assets/brolls")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def search_and_download(self, query: str, duration_min: float = 2.0) -> Optional[Path]:
        """Busca e baixa um vídeo para o termo especificado"""
        try:
            # 1. Tentar Pexels Web Search
            video_url = self._search_pexels_web(query)
            
            if not video_url:
                # 2. Fallback: Coverr
                video_url = self._search_coverr(query)
            
            if not video_url:
                logger.warning(f"   ⚠️ Nenhum vídeo encontrado para '{query}' (Scraping)")
                return None
                
            # 3. Baixar Vídeo
            return self._download_file(video_url, query)

        except Exception as e:
            logger.error(f"Erro no scraping de B-Roll ({query}): {e}")
            return None

    def _search_pexels_web(self, query: str) -> Optional[str]:
        """Faz scraping da busca do Pexels"""
        try:
            url = f"https://www.pexels.com/search/videos/{query}/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"   Pexels Web status: {response.status_code}")
                return None

            # Método 1: Tentar extrair do JSON __NEXT_DATA__ (React)
            soup = BeautifulSoup(response.text, 'html.parser')
            next_data = soup.find("script", {"id": "__NEXT_DATA__"})
            
            if next_data:
                data = json.loads(next_data.string)
                # Navegar no JSON para achar media
                # Estrutura varia, mas geralmente está em props -> pageProps -> initialData -> search -> media
                try:
                    media_list = data['props']['pageProps']['serverData']['search']['media']
                    videos = [m for m in media_list if m.get('type') == 'Video']
                    
                    if videos:
                        # Pegar um aleatório
                        video = random.choice(videos[:5]) # Top 5
                        # Pegar melhor arquivo de vídeo (HD, sem ser 4k pra não pesar)
                        files = video['video_files']
                        # Preferir HD (1280x720 ou 1920x1080)
                        best_file = next((f for f in files if f['width'] == 1920), files[0])
                        return best_file['link']
                except KeyError:
                    pass

            # Método 2: Scraping bruto falhou? Tentar Playwright se disponível
            try:
                from playwright.sync_api import sync_playwright
                logger.info("   🕸️ Tentando com Playwright (Headless)...")
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(user_agent=self.headers['User-Agent'])
                    page.goto(url)
                    # Esperar carregar algo que pareça video
                    page.wait_for_selector("article, div[data-testid='photo-grid-masonry']", timeout=10000)
                    
                    # Extrair conteúdo
                    content = page.content()
                    browser.close()
                    
                    # Tentar parsear novamente
                    soup = BeautifulSoup(content, 'html.parser')
                    next_data = soup.find("script", {"id": "__NEXT_DATA__"})
                    if next_data:
                         data = json.loads(next_data.string)
                         try:
                            media_list = data['props']['pageProps']['serverData']['search']['media']
                            videos = [m for m in media_list if m.get('type') == 'Video']
                            if videos:
                                video = random.choice(videos[:5])
                                files = video['video_files']
                                best_file = next((f for f in files if f['width'] == 1920), files[0])
                                return best_file['link']
                         except: pass

            except ImportError:
                logger.debug("   Playwright não instalado ou falhou.")
            except Exception as e:
                logger.debug(f"   Erro Playwright: {e}")

            return None

        except Exception as e:
            logger.debug(f"   Erro Pexels Web: {e}")
            return None

    def _search_coverr(self, query: str) -> Optional[str]:
        # Implementação futura se necessário
        return None

    def _download_file(self, url: str, query: str) -> Optional[Path]:
        """Baixa o arquivo da URL"""
        try:
            filename = f"{query}_{random.randint(1000,9999)}.mp4"
            filepath = self.download_dir / query / filename
            filepath.parent.mkdir(exist_ok=True, parents=True) # Criar categoria
            
            # Verificar se já existe algo na pasta para não baixar duplicado à toa
            existing = list(filepath.parent.glob("*.mp4"))
            if existing:
                return random.choice(existing)

            logger.info(f"   ⬇️ Baixando B-Roll: {query}...")
            
            with requests.get(url, stream=True, headers=self.headers, timeout=15) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"   ✅ B-Roll baixado: {filepath.name}")
            return filepath
            
        except Exception as e:
            logger.error(f"   Erro download B-Roll: {e}")
            return None
