import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from src.publishers.scheduler import PublishScheduler
from src.core.logger import setup_logger

logger = setup_logger("MassPublisher")

def mass_publish(exports_dir: str = "exports", platforms: list = None, interval_minutes: int = 60):
    """
    Varre a pasta de exportações e agenda todos os vídeos encontrados.
    """
    if platforms is None:
        platforms = ["tiktok", "instagram", "youtube"]
    
    exports_path = Path(exports_dir)
    if not exports_path.exists():
        logger.error(f"❌ Pasta de exportação não encontrada: {exports_dir}")
        return

    # 1. Localizar pares de Vídeo + Metadados
    video_files = list(exports_path.glob("clip_*.mp4"))
    if not video_files:
        logger.warning(f"⚠️ Nenhum clipe encontrado em {exports_dir}")
        return

    logger.info(f"🚀 Iniciando agendamento em massa para {len(video_files)} vídeos...")
    scheduler = PublishScheduler()
    
    # 2. Agendar com intervalos
    start_time = datetime.now() + timedelta(minutes=10) # Começar em 10 min
    
    scheduled_count = 0
    for i, video_path in enumerate(sorted(video_files)):
        # Procurar metadados correspondentes (meta_XX.json)
        clip_id = video_path.stem.split('_')[-1]
        meta_file = exports_path / f"meta_{clip_id}.json"
        
        metadata = {}
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao ler metadados {meta_file}: {e}")
        
        # Se não houver meta, usar genérico
        if not metadata:
            metadata = {
                "title": f"Clipe Viral {clip_id} 📽️",
                "description": "Conteúdo gerado automaticamente pelo AI Video Clipper Studio V3.",
                "hashtags": ["#viral", "#short", "#ia"]
            }

        # Calcular horário (intervalo entre vídeos)
        job_time = start_time + timedelta(minutes=i * interval_minutes)
        
        try:
            job_id = scheduler.add_to_queue(
                video_path=str(video_path.absolute()),
                metadata=metadata,
                platforms=platforms,
                schedule_time=job_time
            )
            logger.info(f"✅ [{job_id}] Agendado: {video_path.name} para {job_time.strftime('%H:%M')}")
            scheduled_count += 1
        except Exception as e:
            logger.error(f"❌ Erro ao agendar {video_path.name}: {e}")

    print("\n" + "="*50)
    print(f"📊 RESUMO DO AGENDAMENTO EM MASSA")
    print(f"✅ Vídeos Agendados: {scheduled_count}")
    print(f"📅 Início: {start_time.strftime('%d/%m %H:%M')}")
    print(f"🕒 Intervalo: {interval_minutes} minutos")
    print(f"📁 Fila salva em: publish_queue.json")
    print("="*50)
    print("\n💡 Dica: Agora execute 'python start_scheduler.py' para processar a fila em segundo plano.")

if __name__ == "__main__":
    # Uso: python mass_publisher.py [pasta_exports] [intervalo_min]
    e_dir = sys.argv[1] if len(sys.argv) > 1 else "exports"
    i_min = int(sys.argv[2]) if len(sys.argv) > 2 else 120 # Padrão: 2 horas entre vídeos
    
    mass_publish(exports_dir=e_dir, interval_minutes=i_min)
