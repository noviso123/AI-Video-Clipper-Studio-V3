import time
import sys
import os
from pathlib import Path
from datetime import datetime

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from src.publishers.scheduler import PublishScheduler
from src.core.logger import setup_logger

logger = setup_logger("SchedulerWorker")

def run_scheduler():
    print("📅 INICIANDO MOTOR DE AGENDAMENTO (MODO BACKGROUND)...")
    print("💡 O sistema ficará monitorando a fila 'publish_queue.json'.")
    print("🛑 Pressione Ctrl+C para parar.\n")
    
    scheduler = PublishScheduler()
    
    # Iniciar o worker em background
    scheduler.start_worker()
    
    try:
        while True:
            # Mostrar status rápido a cada 10 minutos
            queue = scheduler.get_queue_status()
            scheduled = sum(1 for j in queue if j["status"] == "scheduled")
            published = sum(1 for j in queue if j["status"] == "published")
            failed = sum(1 for j in queue if j["status"] == "failed")
            
            # Limpar console (opcional) e mostrar status
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] Fila: 📅 {scheduled} agendados | ✅ {published} publicados | ❌ {failed} falhas", end="\r")
            
            time.sleep(600) 
            
    except KeyboardInterrupt:
        print("\n\n🛑 Parando agendador...")
        scheduler.stop_worker()
        print("✅ Scheduler finalizado com segurança.")

if __name__ == "__main__":
    run_scheduler()
