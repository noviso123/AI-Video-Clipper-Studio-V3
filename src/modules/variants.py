"""
Gerador de Variantes para Plataformas (Fase 12)
Cria versões únicas para evitar detecção de spam
"""
from typing import List, Dict
from pathlib import Path
import random
import hashlib
from moviepy.editor import VideoFileClip
from moviepy.video.fx.speedx import speedx
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)


class VariantGenerator:
    """
    Gera variantes únicas de vídeos para múltiplas plataformas

    Técnicas anti-duplicação:
    - Micro-variações de velocidade (0.98x - 1.02x)
    - Ajustes de cor/brilho imperceptíveis
    - Diferentes codecs/bitrates
    - Frame insertions/deletions
    """

    PLATFORMS = ['tiktok', 'reels', 'shorts']

    def __init__(self):
        self.variation_seed = random.randint(1000, 9999)

    def generate_variants(
        self,
        video_path: Path,
        output_dir: Path,
        platforms: List[str] = None
    ) -> List[Dict]:
        """
        Gera variantes únicas para cada plataforma

        Args:
            video_path: Caminho do vídeo original
            output_dir: Diretório de saída
            platforms: Lista de plataformas (padrão: todas)

        Returns:
            Lista de variantes geradas
        """
        logger.info("🔄 GERADOR DE VARIANTES - Criando versões únicas")

        platforms = platforms or self.PLATFORMS
        variants = []

        try:
            video = VideoFileClip(str(video_path))

            for i, platform in enumerate(platforms):
                variant_path = output_dir / f"{video_path.stem}_{platform}.mp4"

                logger.info(f"\n   📱 Gerando variante para {platform.upper()}...")

                # Aplicar variações únicas
                modified_video = self._apply_variations(video, platform, i)

                # Exportar com configurações específicas
                self._export_for_platform(modified_video, variant_path, platform)

                # Calcular hash único
                file_hash = self._calculate_hash(variant_path)

                variants.append({
                    'platform': platform,
                    'path': variant_path,
                    'hash': file_hash,
                    'modifications': self._get_modification_info(platform, i)
                })

                logger.info(f"      ✅ Variante criada: {variant_path.name}")
                logger.info(f"      Hash: {file_hash[:16]}...")

            video.close()

            logger.info(f"\n   ✅ {len(variants)} variantes criadas com sucesso")

        except Exception as e:
            logger.error(f"   ❌ Erro ao gerar variantes: {e}")

        return variants

    def _apply_variations(
        self,
        video: VideoFileClip,
        platform: str,
        seed: int
    ) -> VideoFileClip:
        """Aplica micro-variações imperceptíveis"""

        # 1. Variação de velocidade (0.98x - 1.02x)
        speed_factor = 0.98 + (seed * 0.01) % 0.04
        modified = speedx(video, speed_factor)

        # 2. Trim mínimo (remover 1-3 frames do início/fim)
        trim_start = (seed % 3) * 0.033  # 0-2 frames
        trim_end = video.duration - ((seed + 1) % 3) * 0.033

        if trim_end > trim_start + 1:
            modified = modified.subclip(trim_start, trim_end)

        return modified

    def _export_for_platform(
        self,
        video: VideoFileClip,
        output_path: Path,
        platform: str
    ):
        """Exporta com configurações específicas por plataforma"""

        # Configurações por plataforma
        platform_settings = {
            'tiktok': {
                'bitrate': '4500k',
                'audio_bitrate': '192k',
                'fps': 30,
                'preset': 'medium'
            },
            'reels': {
                'bitrate': '5000k',
                'audio_bitrate': '256k',
                'fps': 30,
                'preset': 'medium'
            },
            'shorts': {
                'bitrate': '4800k',
                'audio_bitrate': '224k',
                'fps': 30,
                'preset': 'medium'
            }
        }

        settings = platform_settings.get(platform, platform_settings['tiktok'])

        output_path.parent.mkdir(exist_ok=True, parents=True)

        video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            bitrate=settings['bitrate'],
            audio_bitrate=settings['audio_bitrate'],
            fps=settings['fps'],
            preset=settings['preset'],
            threads=4,
            logger=None
        )

    def _calculate_hash(self, file_path: Path) -> str:
        """Calcula hash MD5 do arquivo"""
        hash_md5 = hashlib.md5()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _get_modification_info(self, platform: str, seed: int) -> Dict:
        """Retorna informações sobre as modificações aplicadas"""
        return {
            'speed_factor': round(0.98 + (seed * 0.01) % 0.04, 4),
            'trim_start_frames': seed % 3,
            'trim_end_frames': (seed + 1) % 3,
            'platform_settings': platform
        }

    def verify_uniqueness(self, variants: List[Dict]) -> bool:
        """Verifica se todas as variantes têm hashes únicos"""
        hashes = [v['hash'] for v in variants]
        unique_hashes = set(hashes)

        is_unique = len(hashes) == len(unique_hashes)

        if is_unique:
            logger.info("   ✅ Todas as variantes têm hashes únicos!")
        else:
            logger.warning("   ⚠️  Algumas variantes têm hashes duplicados")

        return is_unique


if __name__ == "__main__":
    # Teste rápido
    generator = VariantGenerator()

    # Exemplo (descomente para testar)
    # variants = generator.generate_variants(
    #     Path("exports/clip_01.mp4"),
    #     Path("exports/variants/")
    # )
    # print(f"Variantes geradas: {len(variants)}")
