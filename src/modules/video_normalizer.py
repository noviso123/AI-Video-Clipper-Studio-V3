import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoNormalizer:
    """Normaliza vídeos para formato compatível (H.264/AAC) usando FFmpeg do sistema."""

    @staticmethod
    def normalize_video(input_path: Path) -> Path:
        """
        Converte o vídeo para H.264/MP4 para garantir compatibilidade com OpenCV/MoviePy.
        Retorna o caminho do novo arquivo.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Vídeo não encontrado: {input_path}")

        # Definir nome de saída (ex: video_normalized.mp4)
        output_path = input_path.parent / f"{input_path.stem}_normalized.mp4"

        # Se já existe um normalizado mais recente que o original, usa ele
        if output_path.exists() and output_path.stat().st_mtime > input_path.stat().st_mtime:
            logger.info(f"✅ Vídeo já normalizado encontrado: {output_path.name}")
            return output_path

        logger.info(f"🔄 Normalizando vídeo (Transcoding para H.264)...")

        # Comando ffmpeg para converter para H.264 e garantir compatibilidade
        # -y: sobrescrever saída
        # -i: entrada
        # -c:v libx264: codec de vídeo compatível
        # -preset ultrafast: conversão rápida
        # -c:a aac: codec de áudio padrão
        # -strict experimental: para compatibilidade aac em versões antigas
        command = [
            'ffmpeg', '-y',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-c:a', 'aac',
            '-strict', 'experimental',
            str(output_path)
        ]

        try:
            # Executar ffmpeg silenciosamente (apenas erros no log)
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info(f"✅ Vídeo normalizado com sucesso: {output_path.name}")
            return output_path

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8', errors='ignore')
            logger.error(f"❌ Erro ao normalizar vídeo: {error_msg}")
            # Em caso de falha, retorna o original e torce para funcionar (ou lança erro)
            # Vamos retornar o original para não travar totalmente, mas logar o erro.
            return input_path
