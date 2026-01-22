import os
import sys
import json
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from src.publishers.publisher_manager import PublisherManager
from src.core.logger import setup_logger

logger = setup_logger("ColabMultiPublish")

def publish_all_optimized(video_path: str, meta_path: str = None):
    print("🚀 INICIANDO PUBLICAÇÃO GLOBAL EM SEGUNDO PLANO (MODO CLOUD)...")
    
    # 1. Carregar Metadados
    if meta_path and Path(meta_path).exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            # Se for metadados multi-plataforma (gerado pelo MetadataGenerator)
            # Precisamos extrair o básico ou usar a estrutura completa
            if "youtube" in metadata:
                 # Se vier do meta_01.json (agrupado)
                 base_meta = {
                     "title": metadata.get("youtube", {}).get("title", "Novo Clipe"),
                     "description": metadata.get("youtube", {}).get("description", "Publicação Automática"),
                     "hashtags": metadata.get("youtube", {}).get("hashtags", ["#viral"])
                 }
                 metadata = base_meta
    else:
        # Fallback se não houver arquivo de meta
        metadata = {
            "title": "Automação Multi-Rede 100% Background 🚀",
            "description": "Publicado automaticamente via AI Video Clipper Studio V3 em modo Headless.",
            "hashtags": ["#AI", "#Automation", "#Cloud", "#Viral"]
        }

    # 2. Executar Publicação PARALELA (Parallel Uploads)
    from concurrent.futures import ThreadPoolExecutor
    manager = PublisherManager()
    
    platforms = ['youtube', 'instagram', 'tiktok']
    results = {}
    
    def single_upload(platform):
        try:
            logger.info(f"📤 Iniciando upload para {platform.upper()}...")
            if platform == 'youtube':
                return platform, manager.youtube.publish(video_path, metadata, headless=True)
            elif platform == 'instagram':
                return platform, manager.instagram.publish(video_path, metadata, headless=True)
            elif platform == 'tiktok':
                # TikTok via undetected-chrome (Cuidado com concorrência de perfis se usar o mesmo)
                return platform, manager.tiktok.publish(video_path, metadata, headless=True)
        except Exception as e:
            return platform, f"Erro: {str(e)}"

    print("⚡ Realizando uploads simultâneos (Multi-Threading)...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        upload_results = list(executor.map(single_upload, platforms))
        for platform, status in upload_results:
            results[platform] = status

    print("\n" + "="*50)
    print("📊 RELATÓRIO FINAL DE PUBLICAÇÃO (SUPER-OTIMIZADO)")
    print("="*50)
    for platform, status in results.items():
        status_icon = "✅" if "http" in status or "sucesso" in status.lower() or "ok" in status.lower() else "❌"
        print(f"{status_icon} {platform.upper()}: {status}")
    print("="*50)
        
    except Exception as e:
        print(f"❌ Erro Crítico na Publicação Global: {e}")

if __name__ == "__main__":
    # Exemplo de uso: python colab_multi_publish.py temp/test.mp4 exports/meta_01.json
    if len(sys.argv) > 1:
        v_path = sys.argv[1]
        m_path = sys.argv[2] if len(sys.argv) > 2 else None
        publish_all_optimized(v_path, m_path)
    else:
        print("💡 Uso: python colab_multi_publish.py video.mp4 [metadata.json]")
