"""
Módulo de Download de Vídeos (Stage 1)
Baixa vídeos do YouTube usando yt-dlp
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
import yt_dlp
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class VideoDownloader:
    """Download de vídeos do YouTube com yt-dlp"""

    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
        self.temp_dir.mkdir(exist_ok=True, parents=True)

    def _get_ffmpeg_path(self) -> Optional[str]:
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            return None

    def download_video(self, url: str, video_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Baixa vídeo do YouTube e extrai áudio
        """
        logger.info(f"📥 Iniciando download: {url}")

        ffmpeg_path = self._get_ffmpeg_path()

        # Validar URL
        if not self._validate_url(url):
            raise ValueError(f"URL inválida: {url}")

        # Gerar ID único se não fornecido
        if not video_id:
            video_id = self._generate_id(url)

        video_path = self.temp_dir / f"video_{video_id}.mp4"
        audio_path = self.temp_dir / f"audio_{video_id}.mp3"

        # Opções do yt-dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(video_path.with_suffix('')),  # Sem extensão, yt-dlp adiciona
            'quiet': not Config.DEBUG_MODE,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
        }

        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path

        try:
            # Download do vídeo
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("⏳ Baixando vídeo...")
                info = ydl.extract_info(url, download=True)

                metadata = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', ''),
                    'url': url,
                    'video_id': video_id
                }

            # Extração de áudio separado
            logger.info("🎵 Extraindo áudio...")
            audio_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(audio_path.with_suffix('')),
                'quiet': not Config.DEBUG_MODE,
            }
            if ffmpeg_path:
                audio_opts['ffmpeg_location'] = ffmpeg_path

            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([url])

            # Verificar se os arquivos foram criados
            # yt-dlp pode adicionar extensões, então procuramos
            video_files = list(self.temp_dir.glob(f"video_{video_id}.*"))
            audio_files = list(self.temp_dir.glob(f"audio_{video_id}.*"))

            if not video_files:
                raise FileNotFoundError(f"Vídeo não encontrado após download")
            if not audio_files:
                raise FileNotFoundError(f"Áudio não encontrado após extração")

            final_video_path = video_files[0]
            final_audio_path = audio_files[0]

            logger.info(f"✅ Download concluído!")
            logger.info(f"   Vídeo: {final_video_path.name}")
            logger.info(f"   Áudio: {final_audio_path.name}")
            logger.info(f"   Duração: {metadata['duration']//60}:{metadata['duration']%60:02d}")

            return {
                'video_path': final_video_path,
                'audio_path': final_audio_path,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"❌ Erro no download: {str(e)}")
            raise

    def _validate_url(self, url: str) -> bool:
        """Valida se a URL é de um vídeo do YouTube válido"""
        valid_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
        return any(domain in url for domain in valid_domains)

    def _generate_id(self, url: str) -> str:
        """Gera ID único baseado na URL"""
        import hashlib
        from datetime import datetime

        # Extrair ID do vídeo se possível
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('id', hashlib.md5(url.encode()).hexdigest()[:8])
        except:
            # Fallback: hash da URL + timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"{url_hash}_{timestamp}"

    def cleanup(self, video_id: str):
        """Remove arquivos temporários de um vídeo específico"""
        logger.info(f"🧹 Limpando arquivos de: {video_id}")
        for file in self.temp_dir.glob(f"*{video_id}*"):
            try:
                file.unlink()
                logger.debug(f"   Removido: {file.name}")
            except Exception as e:
                logger.warning(f"   Erro ao remover {file.name}: {e}")


if __name__ == "__main__":
    # Teste rápido
    downloader = VideoDownloader()

    # Exemplo (descomente para testar)
    # result = downloader.download_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    # print(result)
