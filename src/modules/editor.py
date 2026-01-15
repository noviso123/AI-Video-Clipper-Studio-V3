"""
Módulo de Edição de Vídeo (Stage 4)
Corta, redimensiona e edita vídeos usando MoviePy
"""
from typing import Dict, Tuple, Optional
from pathlib import Path
import subprocess
from moviepy.editor import VideoFileClip, CompositeVideoClip
from moviepy.video.fx.crop import crop
from moviepy.video.fx.resize import resize
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class VideoEditor:
    """Editor de vídeo para criar clipes 9:16"""

    def __init__(self):
        self.target_width, self.target_height = Config.OUTPUT_RESOLUTION
        self.fps = Config.VIDEO_FPS
        self.quality_settings = Config.get_quality_settings()

    def create_clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path,
        crop_mode: str = 'center',
        vibe: str = 'General'
    ) -> Path:
        """
        Cria um clipe vertical (9:16) a partir do vídeo original

        Args:
            video_path: Caminho do vídeo original
            start_time: Início do clipe (segundos)
            end_time: Fim do clipe (segundos)
            output_path: Caminho para salvar o clipe
            crop_mode: 'center', 'smart' ou 'face_tracking'
            vibe: Estilo do vídeo para Color Grading ('Motivational', 'Sad', etc)

        Returns:
            Caminho do arquivo gerado
        """
        logger.info(f"✂️  Cortando vídeo: {start_time:.1f}s -> {end_time:.1f}s (Modo: {crop_mode})")

        try:
            # Carregar vídeo (apenas o trecho necessário para economizar memória)
            # subclip=True no VideoFileClip pode ser lento, melhor carregar full e cortar
            # Mas para vídeos longos, subclip é melhor.
            clip = VideoFileClip(str(video_path)).subclip(start_time, end_time)

            # 1. Resize e Crop (9:16)
            final_clip = self._resize_to_vertical(clip, crop_mode)

            # 2. Visual Polish (Color Grading)
            from src.modules.visual_polisher import VisualPolisher
            polisher = VisualPolisher()
            final_clip = polisher.apply_look(final_clip, vibe)

            # Exportar (sem áudio por enquanto, será mixado no final)
            # Mas aqui já salvamos o mp4 final sem legendas
            output_path.parent.mkdir(exist_ok=True, parents=True)
            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=Config.VIDEO_FPS,
                preset='fast',
                ffmpeg_params=["-crf", "23"],
                logger=None
            )

            clip.close()
            final_clip.close()

            logger.info(f"✅ Clipe criado: {output_path.name}")

            return output_path

        except Exception as e:
            logger.error(f"❌ Erro ao criar clipe: {e}")
            raise


    def _resize_to_vertical(self, clip: VideoFileClip, crop_mode: str) -> VideoFileClip:
        """
        Redimensiona vídeo para formato vertical 9:16

        Args:
            clip: Clip original
            crop_mode: Modo de crop

        Returns:
            Clip redimensionado
        """
        original_w, original_h = clip.size
        target_ratio = self.target_height / self.target_width  # 16/9
        original_ratio = original_h / original_w

        logger.info(f"   Resolução original: {original_w}x{original_h}")
        logger.info(f"   Resolução alvo: {self.target_width}x{self.target_height}")

        if crop_mode == 'center':
            # Crop central simples
            return self._crop_center(clip)

        elif crop_mode == 'smart':
            # Detectar área de interesse (placeholder por enquanto)
            logger.info("   Modo smart crop (usando center por enquanto)")
            return self._crop_center(clip)

        elif crop_mode == 'face_tracking':
            # Face tracking (placeholder por enquanto)
            if Config.FACE_TRACKING_ENABLED:
                logger.info("   Face tracking (usando center por enquanto)")
            return self._crop_center(clip)

        else:
            return self._crop_center(clip)

    def _crop_center(self, clip: VideoFileClip) -> VideoFileClip:
        """Crop central para 9:16"""
        original_w, original_h = clip.size

        # Calcular dimensões do crop
        target_ratio = self.target_height / self.target_width  # Ex: 1920/1080 = 1.77...

        # Largura do crop baseada na altura do vídeo
        crop_width = int(original_h / target_ratio)

        if crop_width > original_w:
            # Vídeo é muito largo, crop pela altura
            crop_height = int(original_w * target_ratio)
            x_center = original_w / 2
            y_center = original_h / 2

            clip_cropped = crop(
                clip,
                x_center=x_center,
                y_center=y_center,
                width=original_w,
                height=crop_height
            )
        else:
            # Vídeo é muito alto ou quadrado, crop pela largura
            x_center = original_w / 2
            y_center = original_h / 2

            clip_cropped = crop(
                clip,
                x_center=x_center,
                y_center=y_center,
                width=crop_width,
                height=original_h
            )

        # Redimensionar para resolução alvo
        clip_resized = clip_cropped.resize((self.target_width, self.target_height))

        return clip_resized

    def batch_create_clips(
        self,
        video_path: Path,
        moments: list,
        output_dir: Path
    ) -> list:
        """
        Cria múltiplos clipes de uma vez

        Args:
            video_path: Vídeo original
            moments: Lista de momentos virais
            output_dir: Diretório de saída

        Returns:
            Lista de caminhos dos clipes criados
        """
        logger.info(f"📦 Criando {len(moments)} clipes em lote...")

        output_paths = []

        for i, moment in enumerate(moments, 1):
            output_path = output_dir / f"clip_{i:02d}_score{moment['score']}.mp4"

            try:
                path = self.create_clip(
                    video_path,
                    moment['start'],
                    moment['end'],
                    output_path
                )
                output_paths.append(path)

            except Exception as e:
                logger.error(f"   Erro no clipe {i}: {e}")
                continue

        logger.info(f"✅ {len(output_paths)}/{len(moments)} clipes criados com sucesso")

        return output_paths


if __name__ == "__main__":
    # Teste rápido
    editor = VideoEditor()

    # Exemplo (descomente para testar)
    # clip_path = editor.create_clip(
    #     Path("temp/video_test.mp4"),
    #     10.0,
    #     40.0,
    #     Path("exports/test_clip.mp4")
    # )
    # print(f"Clipe criado: {clip_path}")
