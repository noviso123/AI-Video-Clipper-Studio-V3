"""
Configuração centralizada do sistema
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações centralizadas do sistema"""

    # Diretórios Base
    BASE_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
    EXPORT_DIR = BASE_DIR / os.getenv("EXPORT_DIR", "exports")
    ASSETS_DIR = BASE_DIR / os.getenv("ASSETS_DIR", "src/assets")

    # Whisper (Transcrição Local)
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "pt")

    # IA Local
    USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "true").lower() == "true"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Vídeo
    CLIP_DURATION_MIN = int(os.getenv("CLIP_DURATION_MIN", 30))
    CLIP_DURATION_MAX = int(os.getenv("CLIP_DURATION_MAX", 60))
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", 30))
    VIDEO_QUALITY = os.getenv("VIDEO_QUALITY", "high")
    OUTPUT_RESOLUTION = tuple(map(int, os.getenv("OUTPUT_RESOLUTION", "1080x1920").split("x")))

    # Edição
    FACE_TRACKING_ENABLED = os.getenv("FACE_TRACKING_ENABLED", "true").lower() == "true"
    DYNAMIC_CAPTIONS_ENABLED = os.getenv("DYNAMIC_CAPTIONS_ENABLED", "true").lower() == "true"
    BROLL_ENABLED = os.getenv("BROLL_ENABLED", "true").lower() == "true"

    # Áudio
    AUDIO_EMOTION_DETECTION = os.getenv("AUDIO_EMOTION_DETECTION", "true").lower() == "true"
    VOLUME_THRESHOLD = float(os.getenv("VOLUME_THRESHOLD", 0.7))

    # Agente Crítico
    CRITIC_ENABLED = os.getenv("CRITIC_ENABLED", "true").lower() == "true"
    CRITIC_MIN_SCORE = float(os.getenv("CRITIC_MIN_SCORE", 8.0))
    MAX_REFINEMENT_LOOPS = int(os.getenv("MAX_REFINEMENT_LOOPS", 3))

    # Debug
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def ensure_directories(cls):
        """Cria os diretórios necessários se não existirem"""
        cls.TEMP_DIR.mkdir(exist_ok=True, parents=True)
        cls.EXPORT_DIR.mkdir(exist_ok=True, parents=True)
        cls.ASSETS_DIR.mkdir(exist_ok=True, parents=True)
        (cls.ASSETS_DIR / "fonts").mkdir(exist_ok=True)
        (cls.ASSETS_DIR / "overlays").mkdir(exist_ok=True)
        (cls.ASSETS_DIR / "sounds").mkdir(exist_ok=True)

    @classmethod
    def get_quality_settings(cls):
        """Retorna configurações de qualidade de vídeo"""
        quality_map = {
            "low": {"bitrate": "1000k", "audio_bitrate": "128k"},
            "medium": {"bitrate": "2500k", "audio_bitrate": "192k"},
            "high": {"bitrate": "5000k", "audio_bitrate": "256k"},
            "ultra": {"bitrate": "8000k", "audio_bitrate": "320k"}
        }
        return quality_map.get(cls.VIDEO_QUALITY, quality_map["high"])
