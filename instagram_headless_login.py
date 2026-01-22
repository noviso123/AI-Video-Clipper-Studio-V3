#!/usr/bin/env python3
"""
Instagram Headless Login usando Instagrapi
Autenticação 100% programática sem Selenium/Chrome.
"""
import sys
import pickle
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.core.logger import setup_logger

logger = setup_logger("InstagramAuth")

# Diretório de cookies
COOKIES_DIR = Path("browser_profiles") / "cookies"
COOKIES_DIR.mkdir(parents=True, exist_ok=True)

def login_instagram_headless(username: str, password: str) -> bool:
    """
    Login headless no Instagram usando instagrapi.
    """
    try:
        from instagrapi import Client
        
        logger.info("📸 Iniciando login headless no Instagram...")
        logger.info(f"   Usuário: {username}")
        
        cl = Client()
        
        # Configurações para evitar bloqueio
        cl.delay_range = [1, 3]
        
        # Tentar carregar sessão existente
        session_file = COOKIES_DIR / "instagram_session.json"
        
        if session_file.exists():
            try:
                logger.info("   🔄 Tentando restaurar sessão existente...")
                cl.load_settings(session_file)
                cl.login(username, password)
                cl.get_timeline_feed()  # Testar se está funcionando
                logger.info("   ✅ Sessão existente restaurada!")
            except Exception as e:
                logger.warning(f"   ⚠️ Sessão expirada, fazendo novo login: {e}")
                cl = Client()
                cl.login(username, password)
        else:
            logger.info("   🔐 Fazendo login...")
            cl.login(username, password)
        
        # Salvar sessão
        cl.dump_settings(session_file)
        logger.info(f"   💾 Sessão salva: {session_file}")
        
        # Converter para formato de cookies Selenium (para compatibilidade)
        cookies_list = [
            {"name": "sessionid", "value": cl.sessionid, "domain": ".instagram.com", "path": "/"},
            {"name": "ds_user_id", "value": str(cl.user_id), "domain": ".instagram.com", "path": "/"},
            {"name": "csrftoken", "value": cl.token, "domain": ".instagram.com", "path": "/"},
        ]
        
        pkl_path = COOKIES_DIR / "instagram_cookies.pkl"
        with open(pkl_path, 'wb') as f:
            pickle.dump(cookies_list, f)
        logger.info(f"   ✅ Cookies Pickle: {pkl_path}")
        
        # Obter informações do perfil
        user_info = cl.account_info()
        logger.info(f"   👤 Perfil: @{user_info.username}")
        logger.info(f"   📊 Seguidores: {user_info.follower_count}")
        
        logger.info("✅ Login Instagram HEADLESS concluído com sucesso!")
        return True
        
    except ImportError:
        logger.error("❌ Biblioteca instagrapi não instalada!")
        logger.info("   Execute: pip install instagrapi")
        return False
    except Exception as e:
        logger.error(f"❌ Erro no login Instagram: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🔐 INSTAGRAM HEADLESS LOGIN")
    print("=" * 60)
    
    # Credenciais fornecidas pelo usuário
    username = "empreendedorismobr2026"
    password = "Jhow@07111998"
    
    success = login_instagram_headless(username, password)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ SUCESSO! Instagram autenticado via instagrapi")
        print("   Sessão salva em: browser_profiles/cookies/instagram_session.json")
        print("   Cookies salvo em: browser_profiles/cookies/instagram_cookies.pkl")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ FALHA na autenticação Instagram")
        print("   Verifique as credenciais ou tente novamente mais tarde")
        print("=" * 60)

if __name__ == "__main__":
    main()
