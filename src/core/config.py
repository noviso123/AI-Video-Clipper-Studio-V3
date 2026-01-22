"""
Configuração Centralizada (Otimizada e Completa)
100% Local, Zero Custos
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env se existir
load_dotenv()

class Config:
    """Configurações centralizadas do sistema"""

    # Diretórios
    BASE_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
    EXPORT_DIR = BASE_DIR / os.getenv("EXPORT_DIR", "exports")
    ASSETS_DIR = BASE_DIR / "src" / "assets"

    # Agno + Gemini (IA Local/Cloud)
    # Requer GEMINI_API_KEY no .env
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Mapear para GOOGLE_API_KEY (exigido por Agno e outras libs)
    if GEMINI_API_KEY:
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

    # Transcrição
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "pt")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

    # Vídeo
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
    OUTPUT_RESOLUTION = (1080, 1920)  # 9:16 para viral
    CLIP_DURATION_MIN = int(os.getenv("CLIP_DURATION_MIN", "60"))
    CLIP_DURATION_MAX = int(os.getenv("CLIP_DURATION_MAX", "90"))

    # Debug
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Metadados Personalizados
    MANDATORY_HASHTAGS = os.getenv("MANDATORY_HASHTAGS", "")

    @classmethod
    def ensure_directories(cls):
        """Cria diretórios necessários"""
        cls.TEMP_DIR.mkdir(exist_ok=True, parents=True)
        cls.EXPORT_DIR.mkdir(exist_ok=True, parents=True)

        # Assets subdirs
        if cls.ASSETS_DIR.exists():
            (cls.ASSETS_DIR / "fonts").mkdir(exist_ok=True)
            (cls.ASSETS_DIR / "sounds").mkdir(exist_ok=True)

# Instância global
config = Config()
