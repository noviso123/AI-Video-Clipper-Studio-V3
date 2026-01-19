"""
YouTube Shorts Publisher - Automação via Selenium
Responsável por fazer upload de Short no YouTube Studio.
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

class YouTubePublisher:
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.upload_url = "https://studio.youtube.com/channel/UC/videos/upload?d=ud"

    def upload(self, video_path: str, title: str, description: str) -> str:
        """
        Realiza o upload do vídeo para o YouTube Shorts.
        """
        driver = self.profile_manager.get_driver("youtube", headless=False)
        
        try:
            logger.info("📺 Acessando YouTube Studio...")
            driver.get(self.upload_url)
            time.sleep(5)

            # 1. Verificar Login
            if "accounts.google.com" in driver.current_url:
                logger.warning("⚠️ Login necessário! Faça login no navegador aberto.")
                logger.info("⏳ Aguardando login manual (120s)...")
                try:
                    WebDriverWait(driver, 120).until(
                        lambda d: "studio.youtube.com" in d.current_url
                    )
                    logger.info("✅ Login detectado!")
                    time.sleep(3)
                except:
                    raise Exception("Timeout: Login não realizado a tempo.")

            # 2. Upload do Arquivo
            logger.info("📤 Enviando arquivo de vídeo...")
            # YouTube Studio geralmente tem um input type=file escondido
            try:
                file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                abs_path = str(Path(video_path).absolute())
                file_input.send_keys(abs_path)
            except:
                # Tentar método alternativo: Botão "Criar" -> "Enviar vídeo"
                # (Se a URL direta de upload falhou)
                logger.info("   Tentando fluxo alternativo de navegação...")
                create_btn = driver.find_element(By.ID, "create-icon")
                create_btn.click()
                time.sleep(1)
                upload_menu = driver.find_element(By.XPATH, "//ytcp-text-menu-item[.//div[contains(text(), 'Enviar') or contains(text(), 'Upload')]]")
                upload_menu.click()
                time.sleep(2)
                file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                abs_path = str(Path(video_path).absolute())
                file_input.send_keys(abs_path)

            logger.info("⏳ Aguardando processamento inicial...")
            time.sleep(10)

            # 3. Preencher Detalhes
            logger.info("✍️ Preenchendo Título e Descrição...")
            
            # Título (textbox)
            # YouTube Studio usa elementos customizados (ytcp-social-suggestions-textbox)
            # Encontrar pelo ID ou placeholder é arriscado, textboxes genéricos melhor
            textboxes = driver.find_elements(By.ID, "textbox") 
            
            # Textbox 0 usually Title, 1 usually Description
            if len(textboxes) >= 1:
                title_box = textboxes[0]
                title_box.clear()
                driver.execute_script("arguments[0].innerText = '';", title_box) # Force clear
                time.sleep(1)
                title_box.send_keys(f"{title} #Shorts")
                time.sleep(1)

            if len(textboxes) >= 2:
                desc_box = textboxes[1]
                desc_box.clear()
                driver.execute_script("arguments[0].innerText = '';", desc_box)
                time.sleep(1)
                desc_box.send_keys(description)

            # 4. Avançar telas (Não é conteúdo para crianças)
            logger.info("➡️ Configurando audiência...")
            # Radio button "Não é conteúdo para crianças"
            not_kids = driver.find_element(By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK")
            not_kids.click()
            time.sleep(1)

            # Clicar em "Próximo" 3 vezes (Elementos do vídeo, Verificações, Visibilidade)
            for i in range(3):
                next_btn = driver.find_element(By.ID, "next-button")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)

            # 5. Publicar (Público)
            logger.info("🚀 Definindo como Público...")
            public_radio = driver.find_element(By.NAME, "PUBLIC")
            public_radio.click()
            time.sleep(1)

            # Botão Publicar final
            logger.info("🚀 Clicando em Publicar...")
            done_btn = driver.find_element(By.ID, "done-button")
            driver.execute_script("arguments[0].click();", done_btn)
            
            time.sleep(5)
            
            # Tentar capturar link
            try:
                link_elem = driver.find_element(By.CSS_SELECTOR, "a.style-scope.ytcp-video-share-dialog")
                video_link = link_elem.get_attribute("href")
                return video_link
            except:
                return "https://youtube.com/shorts/uploaded"

        except Exception as e:
            logger.error(f"❌ Erro no upload YouTube: {e}")
            driver.save_screenshot("error_youtube_upload.png")
            raise e
        finally:
            logger.info("🛑 Fechando navegador YouTube...")
            driver.quit()
