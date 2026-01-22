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

    def upload(self, video_path: str, caption: str, location: str = None, headless: bool = True) -> str:
        """
        Realiza o upload do Reel para o Instagram em modo robótico (Selenium).
        """
        driver = self.profile_manager.get_driver("instagram", headless=headless)
        
        try:
            logger.info("📸 Acessando Instagram...")
            driver.get(self.base_url)
            
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # 1. Verificar Login (Safe Login)
            if "accounts/login" in driver.current_url or "instagram.com/login" in driver.current_url:
                logger.info("🍪 Tentando carregar cookies persistentes...")
                if self.profile_manager.load_cookies_from_file(driver, "instagram"):
                    driver.refresh()
                    time.sleep(5)
                
                if "accounts/login" in driver.current_url or "instagram.com/login" in driver.current_url:
                    if headless:
                        raise Exception("Login necessário no Instagram, mas não é possível realizar em modo HEADLESS (Colab).")
                    
                    logger.warning("⚠️ Login necessário no Instagram! Navegador aberto para intervenção.")
                    logger.info("⏳ Por favor, faça o login no navegador. Aguardando (180s)...")
                    try:
                        WebDriverWait(driver, 180).until(
                            lambda d: "accounts/login" not in d.current_url
                        )
                        logger.info("✅ Login detectado no Instagram!")
                        time.sleep(5)
                    except:
                        raise Exception("Timeout: Login no Instagram não realizado a tempo.")

            # 2. Iniciar Fluxo de Criação
            logger.info("➕ Iniciando criação de post...")
            
            # Limpar modais de "Ativar notificações" ou "Salvar login"
            try:
                driver.execute_script("""
                    document.querySelectorAll('button:not([type="submit"]), [role="dialog"]').forEach(btn => {
                        if(btn.innerText.includes('Agora não') || btn.innerText.includes('Not Now')) btn.click();
                    });
                """)
                time.sleep(2)
            except:
                pass

            # Botão "Criar"
            create_btn = None
            selectors = [
                "svg[aria-label='Novo post'], svg[aria-label='New post'], svg[aria-label='Criar'], svg[aria-label='Create']",
                "//span[contains(text(), 'Criar') or contains(text(), 'Create')]"
            ]
            
            for sel in selectors:
                try:
                    if sel.startswith("//"):
                        elem = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, sel))
                        )
                    else:
                        elem = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                        )
                    
                    # Se for SVG, tentar clicar via JS para evitar problemas de interceptação
                    if elem.tag_name == "svg":
                        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", elem)
                    else:
                        elem.click()
                    
                    create_btn = elem
                    break
                except:
                    continue
            
            if not create_btn:
                # Tentar clique forçado no ícone Plus que costuma ser o Criar
                try:
                    logger.info("   Tentando clique forçado no ícone de criação...")
                    driver.execute_script("document.querySelector('svg[aria-label=\"Novo post\"], svg[aria-label=\"Criar\"]').parentElement.click()")
                    time.sleep(3)
                except:
                    raise Exception("Não foi possível localizar botão Criar no Instagram")

            # NOVO: O Instagram agora abre um menu. Precisamos clicar em "Postar" ou "Post"
            logger.info("   Selecionando opção 'Postar' no menu...")
            try:
                post_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Postar') or contains(text(), 'Post')]"))
                )
                post_option.click()
                time.sleep(3)
            except:
                logger.warning("   ⚠️ Opção 'Postar' não encontrada, talvez o modal já tenha aberto.")

            # 3. Upload do Arquivo
            logger.info("📤 Selecionando vídeo...")
            
            abs_path = str(Path(video_path).absolute())
            if not Path(abs_path).exists():
                raise Exception(f"Arquivo não encontrado: {abs_path}")
            
            # O modal de "Criar nova publicação" abre. Procurar input file.
            file_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            file_input.send_keys(abs_path)
            
            logger.info("⏳ Aguardando processamento...")
            time.sleep(5)

            # 4. Modais de Edição (Cortar / Filtros) - Clicar em "Avançar"
            logger.info("➡️ Avançando telas de edição...")
            
            # Função auxiliar para clicar em "Avançar"
            def click_next():
                # Tentar fechar modais informativos ("Agora os posts de vídeo são compartilhados como reels")
                try:
                    ok_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[text()='OK' or text()='Ok']"))
                    )
                    ok_btn.click()
                    time.sleep(2)
                    logger.info("   ✅ Modal informativo fechado (OK)")
                except:
                    pass

                next_selectors = [
                    "//div[text()='Avançar' or text()='Next']",
                    "//button[text()='Avançar' or text()='Next']",
                    "//button[contains(text(), 'Avançar') or contains(text(), 'Next')]"
                ]
                
                # Se encontrarmos o botão de "Compartilhar", significa que chegamos na última tela!
                share_selectors = [
                    "//div[text()='Compartilhar' or text()='Share']",
                    "//button[text()='Compartilhar' or text()='Share']"
                ]

                for sel in share_selectors:
                    try:
                        if driver.find_elements(By.XPATH, sel):
                            logger.info("   🎯 Tela de detalhes (Compartilhar) alcançada!")
                            return "STOP"
                    except:
                        pass

                for sel in next_selectors:
                    try:
                        next_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, sel))
                        )
                        # Tentar clicar via JS se o Selenium falhar (devido a overlays)
                        try:
                            next_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", next_btn)
                            
                        time.sleep(4) # Esperar animação de transição
                        return True
                    except:
                        continue
                return False

            # Tentar avançar até 3 telas (Corte, Filtros)
            for i in range(3):
                status = click_next()
                if status == "STOP":
                    break
                if not status:
                    logger.warning(f"   ⚠️ Não foi possível avançar tela {i+1}")
                    break
                logger.info(f"   ✅ Tela {i+1} avançada")

            # 5. Legenda e Compartilhar
            logger.info("✍️ Escrevendo legenda...")
            try:
                # Screenshot diagnóstico para ver o estado da tela de detalhes
                time.sleep(2)
                diag_path = f"debug_instagram_caption_{int(time.time())}.png"
                driver.save_screenshot(diag_path)
                logger.info(f"   📸 Screenshot diagnóstico salvo: {diag_path}")

                caption_selectors = [
                    (By.CSS_SELECTOR, "div[aria-label*='legenda'], div[aria-label*='caption']"),
                    (By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"),
                    (By.XPATH, "//div[@contenteditable='true' and contains(@aria-label, 'legenda')]"),
                    (By.XPATH, "//div[@contenteditable='true' and contains(@aria-label, 'caption')]"),
                    (By.CSS_SELECTOR, "textarea[aria-label*='legenda']"),
                    (By.CSS_SELECTOR, "div.notranslate.public-DraftEditor-content")
                ]
                
                caption_area = None
                for by, sel in caption_selectors:
                    try:
                        caption_area = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((by, sel))
                        )
                        break
                    except:
                        continue
                
                if caption_area:
                    logger.info(f"   Digitando legenda ({len(caption)} caracteres)...")
                    try:
                        # Tentar via JS para suportar emojis e ser mais rápido
                        driver.execute_script("""
                            const el = arguments[0];
                            const text = arguments[1];
                            el.focus();
                            document.execCommand('insertText', false, text);
                        """, caption_area, caption)
                        time.sleep(1)
                        logger.info("   ✅ Legenda adicionada via JS")
                    except Exception as js_err:
                        logger.warning(f"   ⚠️ Erro ao digitar via JS: {js_err}. Tentando fallback Selenium...")
                        caption_area.click()
                        time.sleep(0.5)
                        caption_area.send_keys(Keys.CONTROL + "a")
                        caption_area.send_keys(Keys.BACKSPACE)
                        
                        # Fallback: Filtrar apenas caracteres compatíveis com BMP para send_keys
                        safe_caption = "".join(c for c in caption if ord(c) <= 0xFFFF)
                        for char in safe_caption:
                            caption_area.send_keys(char)
                            time.sleep(random.uniform(0.01, 0.03))
                        logger.info("   ✅ Legenda (sem emojis) adicionada via fallback")
                else:
                    logger.warning("   ⚠️ Campo de legenda não encontrado")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro ao escrever legenda: {e}")

            # Adicionar localização (se fornecida)
            if location:
                try:
                    logger.info(f"📍 Adicionando localização: {location}")
                    location_input = driver.find_element(By.XPATH, "//input[@placeholder='Adicionar local' or @placeholder='Add location']")
                    location_input.click()
                    time.sleep(0.5)
                    location_input.send_keys(location)
                    time.sleep(1)
                    # Clicar no primeiro resultado
                    first_result = driver.find_element(By.XPATH, "//button[contains(@class, 'location')]")
                    first_result.click()
                    logger.info("   ✅ Localização adicionada")
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível adicionar localização: {e}")

            try:
                # Função final para clicar em Compartilhar
                def click_share():
                    share_selectors = [
                        "//div[text()='Compartilhar' or text()='Share']",
                        "//button[text()='Compartilhar' or text()='Share']"
                    ]
                    for sel in share_selectors:
                        try:
                            btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, sel)))
                            try:
                                btn.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn)
                            return True
                        except:
                            continue
                    return False

                logger.info("🚀 Compartilhando...")
                if not click_share():
                    # Tentar detecção rápida se o clique falhar
                    pass
                
                time.sleep(5)
                
                # 2. Verificar imediatamente se já foi compartilhado (sucesso rápido)
                text_content = driver.find_element(By.TAG_NAME, "body").text
                if "compartilhado" in text_content.lower() or "shared" in text_content.lower():
                    logger.info("✅ Reel publicado com sucesso (detecção rápida)!")
                    return "https://instagram.com - Reel publicado com sucesso"

                # 3. Esperar mensagem oficial se ainda não detectado
                WebDriverWait(driver, 90).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'compartilhada') or contains(text(), 'compartilhado') or contains(text(), 'shared')]"))
                )
                logger.info("✅ Reel publicado com sucesso!")
                
                # Tentar capturar link do Reel
                try:
                    time.sleep(2)
                    link_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/reel/') or contains(@href, '/p/')]")
                    reel_link = link_elem.get_attribute("href")
                    logger.info(f"✅ Link capturado: {reel_link}")
                    return reel_link
                except:
                    logger.warning("⚠️ Não foi possível capturar link direto")
                
                return "https://instagram.com - Reel publicado com sucesso"
            
            except Exception as e:
                logger.warning(f"⚠️ Timeout esperando confirmação: {e}")
                return "https://instagram.com - Upload realizado"

        except Exception as e:
            logger.error(f"❌ Erro no upload Instagram: {e}")
            try:
                screenshot_path = f"error_instagram_upload_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"   📸 Screenshot salvo: {screenshot_path}")
            except:
                pass
            raise e
        finally:
            logger.info("🛑 Fechando navegador Instagram...")
            try:
                driver.quit()
            except:
                pass

