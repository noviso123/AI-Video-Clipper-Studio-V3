"""
TikTok Publisher - Automação via tiktok-uploader ou Selenium
Usa a biblioteca tiktok-uploader do GitHub quando disponível,
com fallback para Selenium customizado.
"""
import time
import os
import random
from pathlib import Path
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Tentar importar tiktok-uploader
try:
    from tiktok_uploader.upload import upload_video as tiktok_upload
    from tiktok_uploader.auth import AuthBackend
    TIKTOK_UPLOADER_AVAILABLE = True
except ImportError:
    TIKTOK_UPLOADER_AVAILABLE = False


class TikTokPublisher:
    def __init__(self):
        from ..browsers.profile_manager import ProfileManager
        self.profile_manager = ProfileManager()
        self.upload_url = "https://www.tiktok.com/upload?lang=pt-BR"
        self.cookies_dir = Path("browser_profiles") / "cookies"

    def upload(self, video_path: str, description: str, headless: bool = True) -> str:
        """
        Realiza o upload do vídeo para o TikTok.
        Tenta usar tiktok-uploader primeiro, depois Selenium.
        Retorna o link do vídeo ou lança exceção.
        """
        # Verificar arquivo
        if not Path(video_path).exists():
            raise Exception(f"Arquivo não encontrado: {video_path}")
        
        # Tentar com tiktok-uploader (mais confiável)
        if TIKTOK_UPLOADER_AVAILABLE:
            try:
                return self._upload_with_library(video_path, description)
            except Exception as e:
                logger.warning(f"⚠️ tiktok-uploader falhou: {e}")
                logger.info("   Tentando fallback com Selenium...")
        
        # Fallback: Selenium
        return self._upload_with_selenium(video_path, description, headless=headless)
    
    def _upload_with_library(self, video_path: str, description: str) -> str:
        """Upload usando a biblioteca tiktok-uploader"""
        logger.info("🎵 Usando biblioteca tiktok-uploader...")
        
        # Verificar cookies
        cookies_txt = self.cookies_dir / "tiktok_cookies.txt"
        cookies_pkl = self.cookies_dir / "tiktok_cookies.pkl"
        
        cookies_path = None
        if cookies_txt.exists():
            cookies_path = str(cookies_txt)
        elif cookies_pkl.exists():
            # Converter pkl para lista de cookies
            import pickle
            with open(cookies_pkl, 'rb') as f:
                cookies_list = pickle.load(f)
            logger.info(f"   📁 Cookies carregados: {len(cookies_list)} cookies")
            
            # Usar cookies_list diretamente
            try:
                failed = tiktok_upload(
                    video_path,
                    description=description,
                    cookies_list=cookies_list,
                    headless=True # Forçar headless para modo Cloud/Colab
                )
                
                if failed:
                    raise Exception(f"Upload retornou falha: {failed}")
                
                logger.info("✅ Upload via tiktok-uploader concluído!")
                return "https://www.tiktok.com/@me - Publicado com tiktok-uploader"
            except Exception as e:
                raise e
        
        if cookies_path:
            logger.info(f"   📁 Usando cookies: {cookies_path}")
            auth = AuthBackend(cookies=cookies_path)
            
            failed = tiktok_upload(
                video_path,
                description=description,
                auth=auth,
                headless=True # Forçar headless para modo Cloud/Colab
            )
            
            if failed:
                raise Exception(f"Upload retornou falha: {failed}")
            
            logger.info("✅ Upload via tiktok-uploader concluído!")
            return "https://www.tiktok.com/@me - Publicado com tiktok-uploader"
        else:
            raise Exception("Cookies não encontrados. Execute: python extract_cookies.py tiktok")

    def _upload_with_selenium(self, video_path: str, description: str, headless: bool = True) -> str:
        """Upload usando Selenium (fallback)"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        
        # Modo headless respeitado
        driver = self.profile_manager.get_driver("tiktok", headless=headless)
        
        try:
            logger.info("🎵 Acessando TikTok Upload (Selenium)...")
            driver.get(self.upload_url)
            
            # Tentar carregar cookies salvos
            try:
                self.profile_manager.load_cookies_from_file(driver, "tiktok")
                driver.refresh()
                time.sleep(3)
            except:
                pass
            
            # Espera inteligente pela página carregar
            logger.info("⏳ Aguardando carregamento total da página...")
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # 1. Verificar Login (Safe Login)
            is_logged = self._is_logged_in(driver)
            if not is_logged:
                logger.info("🍪 Tentando carregar cookies persistentes para o TikTok...")
                if self.profile_manager.load_cookies_from_file(driver, "tiktok"):
                    driver.refresh()
                    time.sleep(5)
                
                if not self._is_logged_in(driver):
                    if headless:
                        raise Exception("Login necessário no TikTok, mas não é possível realizar em modo HEADLESS (Colab). Realize o login uma vez em modo visível primeiro.")
                    
                    logger.warning("⚠️ Login necessário no TikTok! Navegador aberto para intervenção.")
                    logger.info("⏳ Por favor, faça o login e navegue até a tela de upload. Aguardando (180s)...")
                    try:
                        WebDriverWait(driver, 180).until(
                            lambda d: "upload" in d.current_url.lower() and "login" not in d.current_url.lower()
                        )
                        logger.info("✅ Login detectado com sucesso!")
                        time.sleep(2)
                        self.profile_manager.save_cookies(driver, "tiktok")
                    except:
                        raise Exception("Timeout: O login não foi detectado ou demorou demais.")

            # 2. Upload do Arquivo
            logger.info("📤 Localizando botão de upload...")
            self._handle_iframes(driver)

            try:
                file_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                abs_path = str(Path(video_path).absolute())
                logger.info(f"   📂 Enviando arquivo: {abs_path}")
                file_input.send_keys(abs_path)
            except Exception as e:
                logger.error(f"   ❌ Erro ao enviar arquivo: {e}")
                raise Exception("Não foi possível encontrar o campo de seleção de vídeo no TikTok.")
            
            logger.info("⏳ Vídeo enviado. Aguardando processamento...")
            time.sleep(15) 

            # 3. Preencher Legenda
            logger.info("✍️ Preparando legenda...")
            try:
                caption_selectors = ["div[role='textbox']", ".public-DraftEditor-content", "[contenteditable='true']"]
                caption_box = None
                for sel in caption_selectors:
                    try:
                        caption_box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                        if caption_box: break
                    except: continue
                
                if caption_box:
                    logger.info(f"   Digitando legenda ({len(description)} caracteres)...")
                    
                    # Limpar overlays que impedem o clique (Joyride/Tour)
                    try:
                        driver.execute_script("""
                            document.querySelectorAll('.react-joyride__overlay, .react-joyride__spotlight, [class*="Modal"], [class*="Overlay"]').forEach(el => el.remove());
                            document.body.style.overflow = 'auto';
                        """)
                        time.sleep(1)
                    except:
                        pass

                    try:
                        # Tentar via JS para suportar emojis (mais robusto que send_keys)
                        driver.execute_script("""
                            const el = arguments[0];
                            const text = arguments[1];
                            el.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('delete', false, null);
                            document.execCommand('insertText', false, text);
                        """, caption_box, description)
                        time.sleep(2)
                        logger.info("   ✅ Legenda adicionada via JS")
                    except Exception as js_err:
                        logger.warning(f"   ⚠️ Erro ao digitar via JS: {js_err}. Tentando fallback Selenium...")
                        caption_box.click()
                        time.sleep(0.5)
                        caption_box.send_keys(Keys.CONTROL + "a")
                        caption_box.send_keys(Keys.BACKSPACE)
                        
                        # Fallback seguro: remover emojis para send_keys
                        safe_caption = "".join(c for c in description if ord(c) <= 0xFFFF)
                        for char in safe_caption:
                            caption_box.send_keys(char)
                        logger.info("   ✅ Legenda (sem emojis) adicionada via fallback")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao preencher legenda: {e}")

            # 4. Publicar
            logger.info("🚀 Localizando botão de publicação...")
            time.sleep(2)
            post_selectors = ["//button[contains(., 'Publicar')]", "//button[contains(., 'Post')]", "button[data-e2e='post-publish']"]
            post_btn = None
            for selector in post_selectors:
                try:
                    if selector.startswith("//"): post_btn = driver.find_element(By.XPATH, selector)
                    else: post_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if post_btn.is_displayed() and post_btn.is_enabled(): break
                except: continue
            
            if post_btn:
                logger.info("   ✅ Botão encontrado! Clicando...")
                try:
                    # Garantir que não há overlays bloqueando o clique final
                    driver.execute_script("document.querySelectorAll('.react-joyride__overlay').forEach(el => el.remove());")
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post_btn)
                    time.sleep(1)
                    post_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", post_btn)
                
                logger.info("⏳ Aguardando confirmação de upload (15s)...")
                time.sleep(15)
                return "TikTok - Post enviado com sucesso"
            else:
                raise Exception("Botão 'Publicar' não encontrado.")

        except Exception as e:
            logger.error(f"❌ Erro no upload TikTok: {e}")
            try:
                screenshot_path = f"error_tiktok_upload_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
            except: pass
            raise e
        finally:
            logger.info("🛑 Fechando navegador TikTok...")
            try: driver.quit()
            except: pass

    def _is_logged_in(self, driver) -> bool:
        """Verifica se há sinais de login (Perfil, Avatar, etc)"""
        try:
            # Lista de seletores comuns de perfil logado
            selectors = [
                "div[data-e2e='profile-icon']",
                "img[class*='Avatar']",
                "a[href*='/@']",
                "button[aria-label*='Perfil']",
                "button[aria-label*='Profile']",
                ".avatar-container"
            ]
            for sel in selectors:
                if driver.find_elements(By.CSS_SELECTOR, sel): 
                    return True
            
            # Verificação via JS
            return driver.execute_script("""
                return !!(document.querySelector('div[data-e2e="profile-icon"]') || 
                          document.querySelector('img[class*="Avatar"]') ||
                          document.querySelector('a[href*="/@"]'));
            """)
        except: 
            return False

    def _handle_iframes(self, driver):
        """Alterna para o iframe correto"""
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                driver.switch_to.frame(iframe)
                if driver.find_elements(By.CSS_SELECTOR, "input[type='file']"): return
                driver.switch_to.default_content()
        except: driver.switch_to.default_content()
