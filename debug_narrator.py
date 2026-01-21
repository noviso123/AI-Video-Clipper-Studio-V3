import sys
import os
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, os.getcwd())

from src.core.logger import setup_logger
from src.modules.narrator import VoiceNarrator

logger = setup_logger("DebugNarrator")

def debug():
    logger.info("🔍 Iniciando debug do Narrator...")

    models_dir = Path("models/kokoro")
    logger.info(f"📂 Diretório models: {models_dir.absolute()}")

    if models_dir.exists():
        logger.info("✅ Diretório existe")
        for f in models_dir.glob("*"):
            logger.info(f"   - {f.name} ({f.stat().st_size} bytes)")
    else:
        logger.error("❌ Diretório models/kokoro NÃO existe!")

    logger.info("🧠 Tentando inicializar VoiceNarrator...")
    try:
        narrator = VoiceNarrator()
        if narrator.kokoro:
            logger.info("✅ Sucesso!")
        else:
            logger.error("❌ Falha na inicialização (kokoro is None)")
    except Exception as e:
        logger.error(f"❌ Exceção na inicialização: {e}")

if __name__ == "__main__":
    debug()
