import time
from src.browsers.profile_manager import ProfileManager

def check_login(platform, test_url, success_indicators):
    print(f"\n🔍 Verificando {platform.upper()}...", flush=True)
    try:
        pm = ProfileManager()
        # Headless mode for quick check
        driver = pm.get_driver(platform, headless=False) 
        driver.set_page_load_timeout(30)
        
        driver.get(test_url)
        time.sleep(5) # Wait for redirects
        
        current_url = driver.current_url
        print(f"   URL Final: {current_url}", flush=True)
        
        is_logged_in = False
        # If we are NOT redirected to login -> Success
        if "login" not in current_url and "signin" not in current_url:
            is_logged_in = True
            
        # Specific checks
        if platform == "youtube":
            if "studio.youtube.com" in current_url: is_logged_in = True
        elif platform == "tiktok":
             if "upload" in current_url: is_logged_in = True
        
        if is_logged_in:
            print(f"✅ {platform.upper()}: LOGADO! (Acesso liberado)", flush=True)
        else:
            print(f"❌ {platform.upper()}: NÃO LOGADO (Redirecionado para login/home)", flush=True)
            
        driver.quit()
        
    except Exception as e:
        print(f"⚠️ Erro ao verificar {platform}: {e}", flush=True)

def main():
    print("🕵️‍♂️ Testando Autenticação das Contas...", flush=True)
    
    # TikTok: Try to go to upload page
    check_login("tiktok", "https://www.tiktok.com/upload", [])
    
    # YouTube: Try to go to Studio
    check_login("youtube", "https://studio.youtube.com", [])
    
    # Instagram: Try to go to home (login usually redirects to /accounts/login)
    check_login("instagram", "https://www.instagram.com/", [])

if __name__ == "__main__":
    main()
