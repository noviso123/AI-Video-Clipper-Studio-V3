"""
Módulo de Narração usando Microsoft Edge TTS (Online & Gratuito)
- Qualidade Neural (Azure Voices)
- Python API com Bypass de SSL
- Compatível com Colab/Linux/Windows
"""
import logging
import os
import asyncio
import ssl
import certifi
from pathlib import Path
try:
    import edge_tts
except ImportError:
    edge_tts = None
    logger.warning("⚠️ Módulo edge-tts não encontrado. Falback offline será usado.")
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# --- MONKEY PATCH SSL (CRITICAL FOR CORPORATE PROXY) ---
# Força o Python a aceitar certificados auto-assinados ou inseguros
def create_unverified_context(*args, **kwargs):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

# Aplicar o patch globalmente no módulo SSL
ssl._create_default_https_context = create_unverified_context
ssl.create_default_context = create_unverified_context
# -------------------------------------------------------

class VoiceNarrator:
    """Narrador usando Edge-TTS (Python API)."""

    def __init__(self):
        # pt-BR-FranciscaNeural (Feminina)
        # pt-BR-AntonioNeural (Masculina)
        self.voice = "pt-BR-FranciscaNeural"

    def generate_narration(self, text: str, output_path: Path) -> bool:
        """
        Gera áudio usando a API Python do edge-tts.
        Executa o loop asyncio de forma síncrona para compatibilidade.
        """
            if not edge_tts:
                logger.warning("⚠️ edge-tts não disponível. Usando fallback offline.")
                return self._generate_offline_fallback(text, output_path)

            # Executar async rodando em loop sincrono
            asyncio.run(self._generate_async(text, output_path))

            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"✅ Narração salva: {output_path.name}")
                return True
            return False

        except Exception as e:
            logger.warning(f"⚠️ Falha na narração Online (Edge-TTS): {e}")
            return self._generate_offline_fallback(text, output_path)

    async def _generate_async(self, text, output_path):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))

    def _generate_offline_fallback(self, text: str, output_path: Path) -> bool:
        """Fallback para engine offline do sistema (pyttsx3)"""
        try:
            import pyttsx3
            logger.info("⚠️ Sem conexao? Usando fallback OFFLINE (pyttsx3)...")
            engine = pyttsx3.init()
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            return True
        except ImportError:
            logger.error("❌ pyttsx3 não instalado. Instale: pip install pyttsx3")
            return False
        except Exception as e:
            logger.error(f"❌ Erro no fallback offline: {e}")
            return False

def get_narrator():
    return VoiceNarrator()
