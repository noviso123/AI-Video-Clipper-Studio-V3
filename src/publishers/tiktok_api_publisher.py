#!/usr/bin/env python3
"""
TikTok API Publisher - Usa API Oficial do TikTok for Developers
Este módulo implementa upload de vídeos via Content Posting API.

Documentação: https://developers.tiktok.com/doc/content-posting-api-get-started
"""
import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class TikTokAPIPublisher:
    """Publisher TikTok usando API oficial"""
    
    # Endpoints da API
    OAUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
    STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
    CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
    
    def __init__(self):
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8888/callback")
        
        # Diretório para tokens
        self.token_dir = Path("browser_profiles")
        self.token_dir.mkdir(exist_ok=True)
        self.token_file = self.token_dir / "tiktok_token.json"
        
        # Carregar token existente se houver
        self.access_token = None
        self.open_id = None
        self._load_token()
        
        if not self.client_key or not self.client_secret:
            logger.warning("⚠️ TIKTOK_CLIENT_KEY ou TIKTOK_CLIENT_SECRET não configurados no .env")
    
    def _load_token(self):
        """Carrega token salvo"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.open_id = data.get("open_id")
                    expires_at = data.get("expires_at", 0)
                    
                    if time.time() > expires_at:
                        logger.warning("⚠️ Token expirado, necessário reautorizar")
                        self.access_token = None
                    else:
                        logger.info("🔑 Token TikTok carregado")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar token: {e}")
    
    def _save_token(self, token_data: dict):
        """Salva token para uso futuro"""
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        logger.info(f"💾 Token salvo em {self.token_file}")
    
    def get_authorization_url(self) -> str:
        """Gera URL para autorização OAuth"""
        import urllib.parse
        
        params = {
            "client_key": self.client_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "video.publish,user.info.basic",
            "state": "tiktok_auth_state"
        }
        
        url = f"{self.OAUTH_URL}?{urllib.parse.urlencode(params)}"
        return url
    
    def exchange_code_for_token(self, code: str) -> dict:
        """Troca authorization code por access token"""
        logger.info("🔄 Trocando code por access_token...")
        
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(self.TOKEN_URL, data=data, headers=headers)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            self.open_id = result["open_id"]
            
            # Salvar token com tempo de expiração
            token_data = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "open_id": result["open_id"],
                "expires_in": result.get("expires_in", 86400),
                "expires_at": time.time() + result.get("expires_in", 86400)
            }
            self._save_token(token_data)
            
            logger.info("✅ Token obtido com sucesso!")
            return token_data
        else:
            error = result.get("error", {})
            raise Exception(f"Erro ao obter token: {error}")
    
    def get_creator_info(self) -> dict:
        """Obtém informações do criador (limites de publicação)"""
        if not self.access_token:
            raise Exception("Token não configurado. Execute authorize_tiktok.py primeiro.")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.CREATOR_INFO_URL, headers=headers, json={})
        return response.json()
    
    def upload(self, video_path: str, title: str, privacy: str = "SELF_ONLY") -> str:
        """
        Faz upload de vídeo via API oficial.
        
        Args:
            video_path: Caminho do vídeo
            title: Título/descrição do vídeo (pode incluir #hashtags)
            privacy: SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR, PUBLIC_TO_EVERYONE
        
        Returns:
            publish_id do vídeo
        """
        if not self.access_token:
            raise Exception("Token não configurado. Execute: python authorize_tiktok.py")
        
        video_path = Path(video_path)
        if not video_path.exists():
            raise Exception(f"Arquivo não encontrado: {video_path}")
        
        video_size = video_path.stat().st_size
        
        logger.info(f"📤 Iniciando upload via API TikTok...")
        logger.info(f"   Vídeo: {video_path.name} ({video_size / 1024 / 1024:.1f} MB)")
        
        # 1. Iniciar upload
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        # Calcular chunks (máximo 64MB por chunk recomendado)
        chunk_size = min(64 * 1024 * 1024, video_size)  # 64MB ou tamanho total
        total_chunks = (video_size + chunk_size - 1) // chunk_size
        
        init_data = {
            "post_info": {
                "title": title[:150],  # Limite de 150 caracteres
                "privacy_level": privacy,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunks
            }
        }
        
        logger.info("   1️⃣ Solicitando upload URL...")
        response = requests.post(self.INIT_URL, headers=headers, json=init_data)
        result = response.json()
        
        if result.get("error", {}).get("code") != "ok":
            error_msg = result.get("error", {}).get("message", "Erro desconhecido")
            raise Exception(f"Erro ao iniciar upload: {error_msg}")
        
        upload_url = result["data"]["upload_url"]
        publish_id = result["data"]["publish_id"]
        
        logger.info(f"   ✅ Upload URL obtida: {publish_id}")
        
        # 2. Enviar vídeo
        logger.info("   2️⃣ Enviando vídeo...")
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        upload_headers = {
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            "Content-Length": str(video_size)
        }
        
        upload_response = requests.put(upload_url, data=video_data, headers=upload_headers)
        
        if upload_response.status_code not in [200, 201]:
            raise Exception(f"Erro ao enviar vídeo: {upload_response.status_code} - {upload_response.text}")
        
        logger.info("   ✅ Vídeo enviado!")
        
        # 3. Verificar status
        logger.info("   3️⃣ Verificando status...")
        
        for attempt in range(10):
            time.sleep(5)  # Esperar 5 segundos entre verificações
            
            status_data = {"publish_id": publish_id}
            status_response = requests.post(
                self.STATUS_URL,
                headers=headers,
                json=status_data
            )
            status_result = status_response.json()
            
            status = status_result.get("data", {}).get("status", "PROCESSING")
            
            if status == "PUBLISH_COMPLETE":
                logger.info("   ✅ Publicação concluída!")
                return publish_id
            elif status in ["FAILED", "CANCELLED"]:
                fail_reason = status_result.get("data", {}).get("fail_reason", "Desconhecido")
                raise Exception(f"Upload falhou: {fail_reason}")
            else:
                logger.info(f"   ⏳ Status: {status} (tentativa {attempt + 1}/10)")
        
        logger.warning("   ⚠️ Timeout verificando status, mas upload foi enviado")
        return publish_id
    
    def is_configured(self) -> bool:
        """Verifica se a API está configurada e com token válido"""
        return bool(self.client_key and self.client_secret and self.access_token)
