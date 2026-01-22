"""
YouTube Shorts Publisher - Automação via Selenium
Responsável por fazer upload de Short no YouTube Studio.
"""
import time
import os
import random
from typing import List
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

    def upload(self, video_path: str, title: str, description: str = "", tags: List[str] = None, category: str = "Entertainment", headless: bool = True) -> str:
        """
        Realiza o upload do vídeo para o YouTube Shorts em modo robótico (Selenium).
        """
        driver = self.profile_manager.get_driver("youtube", headless=headless)
        
        # Tags padrão se não fornecidas
        if tags is None:
            tags = ["shorts", "viral", "brasil", "youtube", "trending"]
        
        # Garantir que #Shorts está no título
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
        
        try:
            logger.info("📺 Acessando YouTube Studio...")
            driver.get(self.upload_url)
            
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # 1. Verificar Login (Safe Login + Account Selection)
            if "accounts.google.com" in driver.current_url or "ServiceLogin" in driver.current_url or "signin/chooser" in driver.current_url:
                logger.info("🍪 Tentando carregar cookies persistentes para o Google/YouTube...")
                if self.profile_manager.load_cookies_from_file(driver, "youtube"):
                    driver.get(self.upload_url)
                    time.sleep(5)
                
                # Se ainda estiver na tela de login após tentar cookies
                if "accounts.google.com" in driver.current_url or "ServiceLogin" in driver.current_url:
                    if headless:
                        raise Exception("Login necessário no YouTube, mas não é possível realizar em modo HEADLESS (Colab). Realize o login uma vez em modo visível primeiro.")
                    
                    logger.warning("⚠️ Login ou Seleção de Conta necessária no YouTube!")
                    # Tentar auto-selecionar se houver apenas uma conta
                    try:
                        account_elems = driver.find_elements(By.XPATH, "//div[@role='link' and @data-email]")
                        if account_elems:
                            logger.info("   Tentando selecionar conta existente...")
                            account_elems[0].click()
                            time.sleep(3)
                    except:
                        pass

                    if "studio.youtube.com" not in driver.current_url:
                        logger.info("⏳ Aguardando intervenção manual/login (180s)...")
                        try:
                            WebDriverWait(driver, 180).until(
                                lambda d: "studio.youtube.com" in d.current_url
                            )
                            logger.info("✅ Login detectado no YouTube!")
                            time.sleep(5)
                        except:
                            raise Exception("Timeout: Login no YouTube não realizado.")
            
            # Se já estiver no Studio mas não na página de upload, ir para lá
            if "videos/upload" not in driver.current_url:
                driver.get(self.upload_url)
                time.sleep(3)

            # 2. Upload do Arquivo
            logger.info("📤 Enviando arquivo de vídeo...")
            
            # Limpar Modais Obstrutivos (Tour do Studio, etc)
            try:
                driver.execute_script("""
                    document.querySelectorAll('ytcp-omnisearch, ytcp-feature-discovery-callout, #back-button, .style-scope.ytcp-video-share-dialog').forEach(el => el.remove());
                    document.querySelectorAll('ytcp-button[label="FECHAR"], ytcp-button[label="CLOSE"]').forEach(el => el.click());
                """)
                time.sleep(2)
            except:
                pass

            # Tentar localizar input de arquivo
            file_input = None
            try:
                file_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                abs_path = str(Path(video_path).absolute())
                file_input.send_keys(abs_path)
            except:
                # Método alternativo: Botão "Criar" -> "Enviar vídeo"
                logger.info("   Tentando fluxo alternativo de navegação...")
                try:
                    # Encontrar o botão 'Criar' de forma resiliente
                    create_btn = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#create-icon, ytcp-button#create-icon, [aria-label='Criar'], [aria-label='Create']"))
                    )
                    
                    # Tentar clicar via Selenium primeiro, depois JS
                    try:
                        create_btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", create_btn)
                    
                    time.sleep(2)
                    
                    upload_menu = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//ytcp-text-menu-item[.//div[contains(text(), 'Enviar') or contains(text(), 'Upload')]]"))
                    )
                    upload_menu.click()
                    time.sleep(2)
                    
                    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                    abs_path = str(Path(video_path).absolute())
                    file_input.send_keys(abs_path)
                except Exception as e:
                    raise Exception(f"Não foi possível iniciar upload no YouTube: {e}")

            logger.info("⏳ Aguardando processamento inicial...")
            time.sleep(10)

            # 3. Preencher Detalhes
            logger.info("✍️ Preenchendo Título e Descrição...")
            
            # YouTube Studio usa elementos customizados
            # Textbox 0 = Title, 1 = Description
            try:
                textboxes = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.ID, "textbox"))
                )
                
                if len(textboxes) >= 1:
                    title_box = textboxes[0]
                    logger.info(f"   Digitando título ({len(title)} caracteres)...")
                    try:
                        # Injeção via JS para suporte a emojis
                        driver.execute_script("""
                            const el = arguments[0];
                            const text = arguments[1];
                            el.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('delete', false, null);
                            document.execCommand('insertText', false, text);
                        """, title_box, title)
                        time.sleep(1)
                    except:
                        title_box.send_keys(title)
                    logger.info(f"   ✅ Título adicionado")

                if len(textboxes) >= 2:
                    desc_box = textboxes[1]
                    logger.info("   Adicionando descrição...")
                    try:
                        driver.execute_script("""
                            const el = arguments[0];
                            const text = arguments[1];
                            el.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('delete', false, null);
                            document.execCommand('insertText', false, text);
                        """, desc_box, description)
                        time.sleep(1)
                    except:
                        desc_box.send_keys(description)
                    logger.info("   ✅ Descrição adicionada")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao preencher título/descrição: {e}")

            # 4. Adicionar Tags (se disponível na interface)
            if tags:
                try:
                    logger.info(f"🏷️  Adicionando {len(tags)} tags...")
                    # Procurar campo de tags (pode variar)
                    tags_input = driver.find_element(By.XPATH, "//input[@aria-label='Tags' or @placeholder='Tags']")
                    tags_str = ", ".join(tags)
                    tags_input.send_keys(tags_str)
                    logger.info(f"   ✅ Tags: {tags_str[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ Campo de tags não encontrado: {e}")

            # 5. Configurar Audiência (Não é conteúdo para crianças)
            logger.info("➡️ Configurando audiência...")
            try:
                not_kids = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK"))
                )
                not_kids.click()
                time.sleep(1)
                logger.info("   ✅ Audiência configurada")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao configurar audiência: {e}")

            # 6. Avançar telas (Elementos do vídeo, Verificações, Visibilidade)
            logger.info("➡️ Avançando para visibilidade...")
            for i in range(3):
                try:
                    next_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "next-button"))
                    )
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(2)
                    logger.info(f"   ✅ Tela {i+1}/3")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao avançar tela {i+1}: {e}")

            # 7. Definir como Público e Publicar
            logger.info("🚀 Definindo como Público...")
            try:
                public_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "PUBLIC"))
                )
                public_radio.click()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao definir público: {e}")

            logger.info("🚀 Clicando em Publicar...")
            try:
                # Tentar clicar via Selenium explicitamente no botão que tem o ID 'done-button'
                # Em PT-BR ele diz 'PUBLICAR', em EN diz 'PUBLISH' ou 'DONE'
                done_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "done-button"))
                )
                logger.info(f"   Botão 'Publicar' localizado: {done_btn.text}")
                
                # Clicar e esperar um pouco
                driver.execute_script("arguments[0].scrollIntoView(true);", done_btn)
                time.sleep(1)
                
                try:
                    done_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", done_btn)
                
                logger.info("   ✅ Clique em Publicar realizado. Aguardando confirmação do servidor (15s)...")
                time.sleep(15) # Tempo essencial para o YouTube processar o salvamento
            except Exception as e:
                logger.warning(f"⚠️ Erro ao clicar no botão final: {e}")
                # Fallback JS agressivo
                driver.execute_script("""
                    document.querySelectorAll('ytcp-button[label="PUBLICAR"], ytcp-button[label="PUBLISH"], #done-button').forEach(el => el.click());
                """)
                time.sleep(10)
            
            # 8. Tentar capturar link do vídeo
            logger.info("🔗 Tentando capturar link...")
            try:
                # Esperar modal de compartilhamento ou link aparecer
                link_elem = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.style-scope.ytcp-video-share-dialog, a[href*='youtube.com/shorts/']"))
                )
                video_link = link_elem.get_attribute("href")
                logger.info(f"✅ Link capturado: {video_link}")
                return video_link
            except:
                logger.warning("⚠️ Não foi possível capturar link direto")
                # Fallback: verificar URL atual
                if "studio.youtube.com" in driver.current_url:
                    return "https://youtube.com/shorts - Publicado com sucesso"
                return driver.current_url

        except Exception as e:
            logger.error(f"❌ Erro no upload YouTube: {e}")
            try:
                screenshot_path = f"error_youtube_upload_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"   📸 Screenshot salvo: {screenshot_path}")
            except:
                pass
            raise e
        finally:
            logger.info("🛑 Fechando navegador YouTube...")
            try:
                driver.quit()
            except:
                pass

