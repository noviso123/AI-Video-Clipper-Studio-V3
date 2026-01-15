"""
Módulo de Polimento Visual (Fase 22)
Aplica Color Grading e efeitos visuais baseados na Vibe do vídeo.
"""
import logging
from moviepy.editor import VideoClip, vfx
import moviepy.video.fx.all as vfx_all

logger = logging.getLogger(__name__)

class VisualPolisher:
    def __init__(self):
        logger.info("🎨 Visual Polisher: Inicializado")

    def apply_look(self, clip: VideoClip, vibe: str) -> VideoClip:
        """
        Aplica color grading baseado na Vibe detectada pelo Orquestrador.
        """
        try:
            logger.info(f"   🎨 Aplicando estilo visual: {vibe}")

            # Normalizar vibe
            vibe = vibe.lower()

            if "motivational" in vibe or "energetic" in vibe:
                # Look "Vibrant": +Saturação, +Contraste
                clip = clip.fx(vfx_all.colorx, 1.3) # 30% mais cor
                clip = clip.fx(vfx_all.lum_contrast, 0, 1.2, 128) # +Contraste

            elif "sad" in vibe or "serious" in vibe or "emotional" in vibe:
                # Look "Cinematic/Moody": -Saturação, +Contraste
                clip = clip.fx(vfx_all.colorx, 0.8) # -20% cor
                clip = clip.fx(vfx_all.lum_contrast, 0, 1.3, 128) # +Contraste forte

            elif "educational" in vibe:
                # Look "Clean": Leve contraste, cores naturais
                clip = clip.fx(vfx_all.lum_contrast, 0, 1.1, 128)

            else:
                # Look Padrão (Leve melhoria)
                clip = clip.fx(vfx_all.colorx, 1.1)

            return clip

        except Exception as e:
            logger.error(f"❌ Erro ao aplicar visual: {e}")
            return clip
