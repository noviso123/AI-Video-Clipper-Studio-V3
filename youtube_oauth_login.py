#!/usr/bin/env python3
"""
YouTube OAuth2 Authenticator
Usa o credentials.json para gerar token de acesso ao YouTube.
"""
import os
import sys
import pickle
from pathlib import Path

# Adicionar diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.core.logger import setup_logger

logger = setup_logger("YouTubeAuth")

# Escopos necessários para upload de vídeos
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# Diretório de credenciais
COOKIES_DIR = Path("browser_profiles") / "cookies"
COOKIES_DIR.mkdir(parents=True, exist_ok=True)

def authenticate_youtube():
    """
    Autentica no YouTube usando OAuth2.
    Na primeira execução, abrirá o navegador para login.
    Depois, usará o token salvo.
    """
    credentials_file = Path("credentials.json")
    token_file = COOKIES_DIR / "youtube_token.pkl"
    
    if not credentials_file.exists():
        logger.error(f"❌ Arquivo credentials.json não encontrado!")
        return None
    
    logger.info("📺 Iniciando autenticação OAuth2 para YouTube...")
    
    creds = None
    
    # Verificar se já existe token salvo
    if token_file.exists():
        try:
            with open(token_file, 'rb') as f:
                creds = pickle.load(f)
            logger.info("   ✅ Token existente carregado")
        except Exception as e:
            logger.warning(f"   ⚠️ Erro ao carregar token: {e}")
    
    # Se não há credenciais válidas, fazer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("   🔄 Renovando token expirado...")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao renovar token: {e}")
                creds = None
        
        if not creds:
            logger.info("   🌐 Abrindo navegador para autenticação...")
            logger.info("   💡 Faça login na conta Google e autorize o aplicativo")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), 
                SCOPES
            )
            creds = flow.run_local_server(port=8080)
            logger.info("   ✅ Autenticação concluída!")
        
        # Salvar token para uso futuro
        with open(token_file, 'wb') as f:
            pickle.dump(creds, f)
        logger.info(f"   💾 Token salvo: {token_file}")
    
    # Testar conexão
    try:
        youtube = build('youtube', 'v3', credentials=creds)
        # Buscar informações do canal
        request = youtube.channels().list(part='snippet', mine=True)
        response = request.execute()
        
        if response.get('items'):
            channel = response['items'][0]['snippet']
            logger.info(f"   📺 Canal: {channel.get('title', 'N/A')}")
            logger.info("   ✅ Autenticação YouTube PRONTA!")
            return creds
        else:
            logger.warning("   ⚠️ Nenhum canal encontrado para esta conta")
            return creds
            
    except Exception as e:
        logger.error(f"   ❌ Erro ao testar conexão: {e}")
        return creds

def main():
    print("\n" + "=" * 60)
    print("🔐 YOUTUBE OAUTH2 AUTHENTICATOR")
    print("=" * 60)
    
    creds = authenticate_youtube()
    
    if creds:
        print("\n" + "=" * 60)
        print("✅ SUCESSO! YouTube autenticado via OAuth2")
        print("   Token salvo em: browser_profiles/cookies/youtube_token.pkl")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ FALHA na autenticação YouTube")
        print("=" * 60)

if __name__ == "__main__":
    main()
