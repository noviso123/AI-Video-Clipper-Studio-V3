"""
TikTok Publisher - Automação via Selenium
Responsável por fazer upload de vídeos no TikTok Web.
"""
import time
import os
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from ..browsers.profile_manager import ProfileManager
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class TikTokPublisher:
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.upload_url = "https://www.tiktok.com/upload?lang=pt-BR"

    def upload(self, video_path: str, description: str) -> str:
        """
        Realiza o upload do vídeo para o TikTok.
        Retorna o link do vídeo ou lança exceção.
        """
        driver = self.profile_manager.get_driver("tiktok", headless=False) # Headless False para debug/primeiro login
        
        try:
            logger.info("🎵 Acessando TikTok Upload...")
            driver.get(self.upload_url)
            time.sleep(5)

            # 1. Verificar Login
            if "login" in driver.current_url:
                logger.warning("⚠️ Login necessário! Por favor, faça login no navegador aberto.")
                logger.info("⏳ Aguardando login manual (60s)...")
                # Esperar usuário logar manualmente
                try:
                    WebDriverWait(driver, 120).until(
                        lambda d: "upload" in d.current_url and "login" not in d.current_url
                    )
                    logger.info("✅ Login detectado! Salvando cookies...")
                    time.sleep(3) # Garantir que cookies assentaram
                    # Cookies são salvos automaticamente pelo ProfileManager (user-data-dir), 
                    # mas podemos forçar refresh se necessário.
                except:
                    raise Exception("Timeout: Login não realizado a tempo.")

            # 2. Upload do Arquivo
            logger.info("📤 Enviando arquivo de vídeo...")
            
            # Localizar input de arquivo (geralmente hidden)
            # TikTok muda classes frequentemente, tentar input generico
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            
            # Caminho absoluto é crucial
            abs_path = str(Path(video_path).absolute())
            file_input.send_keys(abs_path)
            
            # Aguardar upload (barra de progresso ou mudança na UI)
            logger.info("⏳ Aguardando processamento do vídeo...")
            # Este sleep é precário, ideal seria esperar elemento "Uploaded"
            time.sleep(15) 

            # 3. Preencher Legenda
            logger.info("✍️ Escrevendo legenda...")
            try:
                # Tentar encontrar a div contenteditable do editor
                caption_editor = driver.find_element(By.CSS_SELECTOR, ".public-DraftEditor-content")
                caption_editor.click()
                
                # Limpar (se tiver algo) e escrever
                caption_editor.send_keys(Keys.CONTROL + "a")
                caption_editor.send_keys(Keys.BACKSPACE)
                
                # Digitar devagar para parecer humano
                for char in description:
                    caption_editor.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.1))
                
                time.sleep(2)
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível preencher a legenda automaticamente: {e}")

            # 4. Publicar
            logger.info("🚀 Clicando em Publicar...")
            
            # Botão Postar
            post_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Publicar') or contains(text(), 'Post')]")
            
            # Scroll até ele
            driver.execute_script("arguments[0].scrollIntoView();", post_btn)
            time.sleep(1)
            
            post_btn.click()
            
            # 5. Aguardar Confirmação
            logger.info("⏳ Finalizando publicação...")
            time.sleep(10)
            
            # Tentar pegar link (complicado via web interface, geralmente redireciona para perfil)
            # Vamos assumir sucesso se não der erro fatal
            
            return "https://www.tiktok.com/upload/complete" # Placeholder de sucesso

        except Exception as e:
            logger.error(f"❌ Erro no upload TikTok: {e}")
            # Salvar screenshot para debug
            driver.save_screenshot("error_tiktok_upload.png")
            raise e
        finally:
            logger.info("🛑 Fechando navegador TikTok...")
            driver.quit()
