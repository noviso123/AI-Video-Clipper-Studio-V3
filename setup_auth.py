import time
import sys
from src.browsers.profile_manager import ProfileManager

def setup_auth(platform_name: str, url: str):
    print(f"\n" + "="*50)
    print(f"🔐 CONFIGURANDO: {platform_name.upper()}")
    print("="*50)
    print("1. Vou abrir o navegador.")
    print("2. Faça seu LOGIN manualmente.")
    print("3. Resolva CAPTCHAS se aparecerem.")
    print("4. Volte aqui e pressione ENTER quando estiver logado.")
    print("-" * 50)
    
    # input("👉 Pressione ENTER para abrir o navegador...")
    
    pm = ProfileManager()
    # Force headless=False to show UI
    driver = pm.get_driver(platform_name, headless=False)
    
    try:
        driver.get(url)
        print(f"\n🌐 Navegador aberto em: {url}")
        print("⌨️  (Interaja na janela do Chrome...)")
        
        print("\n⏳ A janela ficará aberta por 10 minutos para você logar.")
        print("✅ Feche a janela manualmente quando terminar.")
        
        import time
        time.sleep(600)  # Mantém aberto por 10 minutos
        
        # Opcional: Salvar cookies explícitos de backup
        try:
             pm.save_cookies(driver, platform_name)
             print("🍪 Cookies salvos com sucesso!")
        except: pass
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        try:
            driver.quit()
        except: pass
        print(f"🔒 {platform_name.upper()} finalizado.\n")

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", help="Plataforma para abrir (tiktok, youtube, instagram)")
    args = parser.parse_args()

    platforms_map = {
        "tiktok": "https://www.tiktok.com/login",
        "youtube": "https://studio.youtube.com",
        "instagram": "https://www.instagram.com/accounts/login/"
    }

    if args.platform:
        if args.platform in platforms_map:
            setup_auth(args.platform, platforms_map[args.platform])
        else:
            print(f"Plataforma inválida. Use: {', '.join(platforms_map.keys())}")
        return

    print("\n🚀 SETUP DE AUTENTICAÇÃO DAS REDES SOCIAIS")
    print("Este script vai abrir o Chrome para você logar em cada rede.")
    print("Isso garante que o robô consiga postar depois.\n")
    
    platforms = [
        ("tiktok", "https://www.tiktok.com/login"),
        ("youtube", "https://studio.youtube.com"),
        ("instagram", "https://www.instagram.com/accounts/login/")
    ]
    
    for name, url in platforms:
        choice = input(f"Deseja configurar {name.upper()} agora? (S/n): ").strip().lower()
        if choice != 'n':
            setup_auth(name, url)
            
    print("\n✨ Tudo pronto! Agora o Telegram Bot pode publicar.")

if __name__ == "__main__":
    main()
