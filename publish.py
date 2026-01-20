"""
Script de Publicação Automática
Publica o mesmo vídeo em YouTube Shorts, TikTok e Instagram Reels
"""
import argparse
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.logger import setup_logger
from src.publishers.publisher_manager import PublisherManager

logger = setup_logger("Publisher")

def main():
    parser = argparse.ArgumentParser(description="📤 Publicador Multi-Plataforma")
    parser.add_argument("--video", required=True, help="Caminho do vídeo")
    parser.add_argument("--metadata", help="Caminho do arquivo JSON com metadados")
    parser.add_argument("--title", help="Título do vídeo")
    parser.add_argument("--description", help="Descrição")
    parser.add_argument("--hashtags", nargs="+", help="Hashtags (ex: #viral #shorts)")

    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        logger.error(f"❌ Vídeo não encontrado: {video_path}")
        sys.exit(1)

    # Carregar ou criar metadados
    if args.metadata and Path(args.metadata).exists():
        with open(args.metadata, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        # Criar metadados básicos
        metadata = {
            'title': args.title or video_path.stem,
            'description': args.description or "Vídeo automatizado",
            'hashtags': args.hashtags or ['#viral', '#shorts']
        }

    logger.info("=" * 50)
    logger.info("📤 PUBLICAÇÃO MULTI-PLATAFORMA")
    logger.info("=" * 50)
    logger.info(f"Vídeo: {video_path.name}")
    logger.info(f"Título: {metadata['title']}")
    logger.info(f"Hashtags: {' '.join(metadata['hashtags'])}")
    logger.info("")

    # Publicar
    publisher = PublisherManager()

    logger.info("🚀 Iniciando publicação em 3 plataformas...")
    logger.info("")

    results = publisher.publish_all(str(video_path), metadata)

    # Exibir resultados
    logger.info("=" * 50)
    logger.info("✅ RESULTADOS DA PUBLICAÇÃO")
    logger.info("=" * 50)

    for platform, result in results.items():
        icon = "✅" if "Erro" not in result else "❌"
        logger.info(f"{icon} {platform.upper()}: {result}")

    logger.info("")
    logger.info("🎉 Publicação concluída!")

if __name__ == "__main__":
    main()
