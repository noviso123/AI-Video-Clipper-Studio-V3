"""
Gerenciador de Perfis do Navegador (Selenium)
Gerencia sessões persistentes (cookies) para evitar login repetitivo.
"""
import os
import time
import pickle
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from ..core.logger import setup_logger

logger = setup_logger(__name__)

class ProfileManager:
    """Gerencia instâncias do Selenium com perfis persistentes"""
    
    def __init__(self, profiles_dir: str = "browser_profiles"):
        self.base_dir = Path(os.getcwd()) / profiles_dir
        self.base_dir.mkdir(exist_ok=True)
        
    def get_driver(self, platform_name: str, headless: bool = False) -> webdriver.Chrome:
        """
        Retorna um driver configurado para a plataforma específica.
        Usa um diretório de perfil único para manter cookies/sessão.
        """
        profile_path = self.base_dir / platform_name
        profile_path.mkdir(exist_ok=True)
        
        logger.info(f"🌐 Iniciando navegador para: {platform_name}")
        logger.info(f"   Perfil: {profile_path}")

        options = Options()
        if headless:
            options.add_argument("--headless=new")
            
        # Configurações anti-detecção básicas
        # Check for Flatpak Wrapper
        wrapper_path = Path(os.getcwd()) / "chrome_wrapper.sh"
        if wrapper_path.exists():
            logger.info(f"🔧 Usando Chrome Flatpak Wrapper: {wrapper_path}")
            options.binary_location = str(wrapper_path)

        options.add_argument(f"user-data-dir={profile_path.absolute()}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User Agent realista
        options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            # Detectar versão do Chrome se usar wrapper
            driver_version = None
            if wrapper_path.exists():
                try:
                    import subprocess
                    import re
                    # Executar wrapper --version com timeout
                    res = subprocess.run(
                        [str(wrapper_path), "--version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if res.returncode == 0:
                        # Output ex: "Google Chrome 120.0.6099.109"
                        ver_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", res.stdout)
                        if ver_match:
                            detected_ver = ver_match.group(1)
                            # Evitar versões malucas como 144
                            if not detected_ver.startswith("144."):
                                driver_version = detected_ver
                                logger.info(f"   🎯 Versão do Chrome detectada: {driver_version}")
                except Exception as ex:
                    logger.warning(f"   ⚠️ Falha ao detectar versão do wrapper: {ex}")

            # Instalar Driver compatível
            try:
                # Tenta sintaxe nova (webdriver-manager 4.x)
                if driver_version:
                    path = ChromeDriverManager(driver_version=driver_version).install()
                else:
                    path = ChromeDriverManager().install()
            except TypeError:
                # Fallback sintaxe antiga version=
                if driver_version:
                    path = ChromeDriverManager(version=driver_version).install()
                else:
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
            logger.error(f"❌ Erro ao iniciar driver: {e}")
            raise e

    def save_cookies(self, driver: webdriver.Chrome, platform_name: str):
        """Salva cookies explicitamente (backup)"""
        cookie_path = self.base_dir / f"{platform_name}_cookies.pkl"
        pickle.dump(driver.get_cookies(), open(cookie_path, "wb"))
        logger.info(f"🍪 Cookies salvos para {platform_name}")

    def load_cookies(self, driver: webdriver.Chrome, platform_name: str):
        """Carrega cookies de backup"""
        cookie_path = self.base_dir / f"{platform_name}_cookies.pkl"
        if cookie_path.exists():
            cookies = pickle.load(open(cookie_path, "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
            logger.info(f"🍪 Cookies carregados para {platform_name}")
