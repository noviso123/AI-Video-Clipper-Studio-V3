"""
Instagram Publisher - Automação via Selenium
Responsável por fazer upload de Reels no Instagram Web.
"""
import time
import os
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from ..browsers.profile_manager import ProfileManager
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class InstagramPublisher:
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.base_url = "https://www.instagram.com/"

    def upload(self, video_path: str, caption: str) -> str:
        """
        Realiza o upload do Reel para o Instagram.
        """
        driver = self.profile_manager.get_driver("instagram", headless=False)
        
        try:
            logger.info("📸 Acessando Instagram...")
            driver.get(self.base_url)
            time.sleep(5)

            # 1. Verificar Login
            if "accounts/login" in driver.current_url:
                logger.warning("⚠️ Login necessário! Faça login no navegador aberto.")
                logger.info("⏳ Aguardando login manual (120s)...")
                try:
                    WebDriverWait(driver, 120).until(
                        lambda d: "accounts/login" not in d.current_url
                    )
                    logger.info("✅ Login detectado!")
                    time.sleep(5)
                except:
                    raise Exception("Timeout: Login não realizado a tempo.")

            # 2. Iniciar Fluxo de Criação
            logger.info("➕ Iniciando criação de post...")
            
            # Botão "Criar" (mais/plus icon na barra lateral)
            # Geralmente é o 4º ou 5º item do menu lateral, mas muda. Tentar por SVG aria-label "Novo post" ou "New post"
            try:
                create_btn = driver.find_element(By.CSS_SELECTOR, "svg[aria-label='Novo post'], svg[aria-label='New post'], svg[aria-label='Criar']")
                parent_btn = create_btn.find_element(By.XPATH, "./../../..") # Subir para o elemento clicável (link ou button)
                parent_btn.click()
            except:
                # Fallback: Tentar clicar pelo texto "Criar" se o menu estiver expandido
                xpath = "//span[contains(text(), 'Criar') or contains(text(), 'Create')]"
                driver.find_element(By.XPATH, xpath).click()
            
            time.sleep(3)

            # 3. Upload do Arquivo
            logger.info("📤 Selecionando vídeo...")
            # O modal de "Criar nova publicação" abre. Procurar input file.
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            abs_path = str(Path(video_path).absolute())
            file_input.send_keys(abs_path)
            
            time.sleep(5)

            # 4. Modais de Edição (Cortar / Filtros) - Clicar em "Avançar"
            logger.info("➡️ Avançando telas de edição...")
            
            # Se for vídeo, as vezes ele pergunta proporção. 9:16 já deve estar ok se o vídeo estiver certo.
            # Botão "Avançar" ou "Next" (geralmente azul no topo direito do modal)
            
            # Função auxiliar para clicar em "Avançar"
            def click_next():
                next_btn = driver.find_element(By.XPATH, "//div[text()='Avançar' or text()='Next' or text()='Compartilhar' or text()='Share']")
                next_btn.click()
                time.sleep(2)

            click_next() # Tela de corte
            click_next() # Tela de capa/trim (se houver)

            # 5. Legenda e Compartilhar
            logger.info("✍️ Escrevendo legenda...")
            try:
                caption_area = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Escreva uma legenda...'], div[aria-label='Write a caption...']")
                caption_area.click()
                
                # Digitar a legenda
                actions = ActionChains(driver)
                actions.send_keys(caption)
                actions.perform()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao por legenda: {e}")

            logger.info("🚀 Compartilhando...")
            click_next() # O botão vira "Compartilhar" na última tela
            
            # 6. Aguardar Upload
            logger.info("⏳ Aguardando finalização (pode demorar)...")
            time.sleep(10)
            
            # Esperar mensagem "Sua publicação foi compartilhada"
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'compartilhada') or contains(text(), 'shared')]"))
            )
            
            return "https://instagram.com" # Sucesso genérico

        except Exception as e:
            logger.error(f"❌ Erro no upload Instagram: {e}")
            driver.save_screenshot("error_instagram_upload.png")
            raise e
        finally:
            logger.info("🛑 Fechando navegador Instagram...")
            driver.quit()
