"""
Gerenciador de Perfis do Navegador (Selenium/Undetected)
Gerencia sessões persistentes (cookies) para evitar login repetitivo.
Usa undetected-chromedriver para anti-detecção.
"""
import os
import time
import pickle
import json
import logging
from pathlib import Path

# Tentar usar undetected-chromedriver primeiro (anti-detecção)
try:
    import undetected_chromedriver as uc
    USE_UNDETECTED = True
except ImportError:
    USE_UNDETECTED = False

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from ..core.logger import setup_logger

logger = setup_logger(__name__)

class ProfileManager:
    """Gerencia instâncias do Selenium/Undetected com perfis persistentes"""
    
    def __init__(self, profiles_dir: str = "browser_profiles"):
        self.base_dir = Path(os.getcwd()) / profiles_dir
        self.base_dir.mkdir(exist_ok=True)
        self.cookies_dir = self.base_dir / "cookies"
        self.cookies_dir.mkdir(exist_ok=True)
        
    def get_driver(self, platform_name: str, headless: bool = False) -> webdriver.Chrome:
        """
        Retorna um driver configurado para a plataforma específica.
        Usa undetected-chromedriver se disponível para evitar detecção.
        """
        profile_path = self.base_dir / platform_name
        profile_path.mkdir(exist_ok=True)
        
        if USE_UNDETECTED:
            logger.info(f"🛡️  Iniciando navegador ANTI-DETECÇÃO para: {platform_name}")
            return self._get_undetected_driver(platform_name, profile_path, headless)
        else:
            logger.warning(f"⚠️  undetected-chromedriver não instalado, usando Selenium padrão")
            return self._get_selenium_driver(platform_name, profile_path, headless)
    
    def _get_undetected_driver(self, platform_name: str, profile_path: Path, headless: bool) -> webdriver.Chrome:
        """Cria driver usando undetected-chromedriver"""
        logger.info(f"   Perfil: {profile_path}")
        
        options = uc.ChromeOptions()
        
        # Modo Headless Estilo Colab / Servidor
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-notifications")
            options.add_argument("--blink-features=AutomationControlled")

        # Configurações de Path (Fix: Restaurado)
        wrapper_path = Path(os.getcwd()) / "chrome_wrapper.sh"
        if wrapper_path.exists():
            options.binary_location = str(wrapper_path.absolute())
            
        options.add_argument(f"--user-data-dir={profile_path.absolute()}")
        options.add_argument("--start-maximized")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")
        
        try:
            driver = uc.Chrome(options=options, use_subprocess=True)
            logger.info(f"   ✅ Driver anti-detecção iniciado (Headless={headless})!")
            return driver
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar undetected driver: {e}")
            logger.info("   Tentando fallback para Selenium padrão...")
            return self._get_selenium_driver(platform_name, profile_path, headless)
    
    def _get_selenium_driver(self, platform_name: str, profile_path: Path, headless: bool) -> webdriver.Chrome:
        """Cria driver usando Selenium padrão (fallback)"""
        logger.info(f"🌐 Iniciando navegador (Selenium) para: {platform_name}")
        logger.info(f"   Perfil: {profile_path}")

        options = Options()
        if headless:
            options.add_argument("--headless=new")
            
        # Configurações anti-detecção básicas
        wrapper_path = Path(os.getcwd()) / "chrome_wrapper.sh"
        if wrapper_path.exists():
            binary_str = str(wrapper_path.absolute())
            logger.info(f"🔧 Usando Chrome Flatpak Wrapper: {binary_str}")
            options.binary_location = binary_str  # Deve ser string

        options.add_argument(f"--user-data-dir={profile_path.absolute()}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User Agent realista
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9223")

        try:
            # Tentar instalar a versão que combina com o Chrome local
            path = ChromeDriverManager().install()
            service = Service(path)
            driver = webdriver.Chrome(service=service, options=options)
            
            # Script anti-webdriver detection
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
            
            return driver
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar driver Selenium: {e}")
            # Tentativa final: sem especificar driver, deixando o selenium gerenciar (recentemente ele faz download automático)
            try:
                logger.info("📡 Tentando inicialização direta (Selenium Manager)...")
                return webdriver.Chrome(options=options)
            except:
                raise e

    def load_cookies_from_file(self, driver: webdriver.Chrome, platform_name: str) -> bool:
        """Carrega cookies do arquivo para o driver"""
        # Tentar diferentes formatos
        formats = [
            (self.cookies_dir / f"{platform_name}_cookies.pkl", self._load_pickle),
            (self.cookies_dir / f"{platform_name}_cookies.json", self._load_json),
        ]
        
        for filepath, loader in formats:
            if filepath.exists():
                try:
                    cookies = loader(filepath)
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except Exception as e:
                            pass  # Alguns cookies podem falhar
                    logger.info(f"🍪 Cookies carregados: {filepath.name} ({len(cookies)} cookies)")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao carregar {filepath}: {e}")
        
        logger.warning(f"⚠️ Nenhum arquivo de cookies encontrado para {platform_name}")
        logger.info(f"   Execute: python extract_cookies.py {platform_name}")
        return False
    
    def _load_pickle(self, filepath: Path) -> list:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    def _load_json(self, filepath: Path) -> list:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_cookies(self, driver: webdriver.Chrome, platform_name: str):
        """Salva cookies explicitamente (backup)"""
        cookie_path = self.cookies_dir / f"{platform_name}_cookies.pkl"
        pickle.dump(driver.get_cookies(), open(cookie_path, "wb"))
        logger.info(f"🍪 Cookies salvos para {platform_name}")

    def load_cookies(self, driver: webdriver.Chrome, platform_name: str):
        """Carrega cookies de backup (método legado)"""
        cookie_path = self.base_dir / f"{platform_name}_cookies.pkl"
        if cookie_path.exists():
            cookies = pickle.load(open(cookie_path, "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
            logger.info(f"🍪 Cookies carregados para {platform_name}")

