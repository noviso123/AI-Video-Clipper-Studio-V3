"""
Sistema de Agendamento de Publicações
Gerencia fila de publicações, retry automático e horários ideais.
"""
import os
import json
import uuid
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class PublishScheduler:
    """Gerencia agendamento e fila de publicações automáticas"""
    
    def __init__(self, queue_file: str = "publish_queue.json"):
        self.queue_file = Path(queue_file)
        self.queue_lock = threading.Lock()
        self.worker_thread = None
        self.running = False
        
        # Configurações
        self.check_interval = int(os.getenv("PUBLISH_QUEUE_CHECK_INTERVAL", "60"))
        self.max_retries = int(os.getenv("PUBLISH_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("PUBLISH_RETRY_DELAY", "300"))  # 5 min
        
        # Horários ideais por plataforma (lista de HH:MM)
        self.best_times = {
            "tiktok": self._parse_times(
                os.getenv("TIKTOK_BEST_TIMES", "06:00,07:30,12:00,19:00,21:30")
            ),
            "youtube": self._parse_times(
                os.getenv("YOUTUBE_BEST_TIMES", "18:00,20:00")
            ),
            "instagram": self._parse_times(
                os.getenv("INSTAGRAM_BEST_TIMES", "11:00,19:00,21:00")
            )
        }
        
        # Carregar ou criar fila
        self.queue = self._load_queue()
    
    def _parse_times(self, times_str: str) -> List[tuple]:
        """Converte string 'HH:MM,HH:MM' em lista de tuplas (hora, minuto)"""
        times = []
        for t in times_str.split(','):
            try:
                h, m = t.strip().split(':')
                times.append((int(h), int(m)))
            except:
                pass
        return times
    
    def _load_queue(self) -> dict:
        """Carrega fila do arquivo JSON"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Erro ao carregar fila: {e}")
        
        # Fila vazia padrão
        return {"queue": []}
    
    def _save_queue(self):
        """Salva fila no arquivo JSON"""
        with self.queue_lock:
            try:
                with open(self.queue_file, 'w', encoding='utf-8') as f:
                    json.dump(self.queue, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"❌ Erro ao salvar fila: {e}")
    
    def add_to_queue(
        self,
        video_path: str,
        metadata: dict,
        platforms: List[str],
        schedule_time: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Adiciona vídeo à fila de publicação.
        
        Args:
            video_path: Caminho do vídeo
            metadata: Metadados completos (com dados por plataforma)
            platforms: Lista de plataformas ["tiktok", "youtube", "instagram"]
            schedule_time: Quando publicar (None = próximo horário ideal)
            user_id: ID do usuário (para bot Telegram)
        
        Returns:
            ID do job na fila
        """
        job_id = str(uuid.uuid4())[:8]
        
        # Se não especificado, agendar para próximo horário ideal
        if schedule_time is None:
            schedule_time = self._get_next_best_time(platforms[0])
        
        job = {
            "id": job_id,
            "video_path": str(video_path),
            "metadata": metadata,
            "platforms": platforms,
            "scheduled_time": schedule_time.isoformat(),
            "status": "scheduled",
            "attempts": 0,
            "created_at": datetime.now().isoformat(),
            "user_id": user_id,
            "published_links": {},
            "errors": []
        }
        
        with self.queue_lock:
            self.queue["queue"].append(job)
            self._save_queue()
        
        logger.info(f"📅 Agendado [{job_id}]: {len(platforms)} plataformas às {schedule_time.strftime('%d/%m %H:%M')}")
        return job_id
    
    def _get_next_best_time(self, platform: str) -> datetime:
        """Retorna próximo horário ideal para a plataforma"""
        now = datetime.now()
        best_times = self.best_times.get(platform, [(19, 0)])
        
        # Tentar hoje
        for hour, minute in sorted(best_times):
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target > now + timedelta(minutes=5):  # Pelo menos 5 min no futuro
                return target
        
        # Se passou todos os horários de hoje, primeiro horário de amanhã
        tomorrow = now + timedelta(days=1)
        hour, minute = best_times[0]
        return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def get_queue_status(self) -> List[dict]:
        """Retorna lista de jobs na fila"""
        with self.queue_lock:
            return self.queue["queue"].copy()
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Retorna status de um job específico"""
        with self.queue_lock:
            for job in self.queue["queue"]:
                if job["id"] == job_id:
                    return job.copy()
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancela um job agendado"""
        with self.queue_lock:
            for i, job in enumerate(self.queue["queue"]):
                if job["id"] == job_id and job["status"] in ["scheduled", "failed"]:
                    self.queue["queue"].pop(i)
                    self._save_queue()
                    logger.info(f"🚫 Job {job_id} cancelado")
                    return True
        return False
    
    def start_worker(self):
        """Inicia worker em background para processar a fila"""
        if self.running:
            logger.warning("⚠️ Worker já está rodando")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"🚀 Scheduler iniciado (verificação a cada {self.check_interval}s)")
    
    def stop_worker(self):
        """Para o worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("🛑 Scheduler parado")
    
    def _worker_loop(self):
        """Loop principal do worker"""
        while self.running:
            try:
                self._process_queue()
            except Exception as e:
                logger.error(f"❌ Erro no worker: {e}")
            
            # Esperar próximo ciclo
            time.sleep(self.check_interval)
    
    def _process_queue(self):
        """Processa jobs prontos para publicação"""
        now = datetime.now()
        jobs_to_process = []
        
        with self.queue_lock:
            for job in self.queue["queue"]:
                if job["status"] == "scheduled":
                    scheduled = datetime.fromisoformat(job["scheduled_time"])
                    if scheduled <= now:
                        jobs_to_process.append(job)
        
        # Processar fora do lock para não bloquear
        for job in jobs_to_process:
            self._publish_job(job)
    
    def _publish_job(self, job: dict):
        """Publica um job"""
        job_id = job["id"]
        logger.info(f"📤 Publicando [{job_id}]...")
        
        # Atualizar status
        self._update_job_status(job_id, "publishing")
        
        try:
            # Importar aqui para evitar circular import
            from ..publishers.publisher_manager import PublisherManager
            
            publisher = PublisherManager()
            video_path = job["video_path"]
            metadata = job["metadata"]
            
            # Publicar em cada plataforma
            results = {}
            for platform in job["platforms"]:
                try:
                    # Pegar metadados específicos da plataforma
                    platform_meta = metadata.get(platform, metadata)
                    
                    if platform == "tiktok":
                        # Usar título + hashtags para a descrição
                        desc = f"{platform_meta.get('title', '')}\n\n{platform_meta.get('description', '')}"
                        link = publisher.tiktok_publisher.upload(video_path, desc, headless=True)
                        results[platform] = link
                    
                    elif platform == "youtube":
                        title = platform_meta.get('title', 'Novo Clipe')
                        desc = platform_meta.get('description', '')
                        link = publisher.youtube_publisher.upload(video_path, title, desc, headless=True)
                        results[platform] = link
                    
                    elif platform == "instagram":
                        caption = f"{platform_meta.get('title', '')}\n\n{platform_meta.get('description', '')}"
                        link = publisher.instagram_publisher.upload(video_path, caption, headless=True)
                        results[platform] = link
                    
                    logger.info(f"   ✅ {platform}: {link}")
                
                except Exception as e:
                    error_msg = f"{platform}: {str(e)}"
                    results[platform] = f"Erro: {error_msg}"
                    logger.error(f"   ❌ {error_msg}")
            
            # Sucesso se pelo menos uma plataforma funcionou
            success_count = sum(1 for r in results.values() if not r.startswith("Erro"))
            
            if success_count > 0:
                self._update_job_status(
                    job_id, 
                    "published", 
                    published_links=results
                )
                logger.info(f"✅ [{job_id}] Publicado em {success_count}/{len(job['platforms'])} plataformas")
            else:
                raise Exception("Falhou em todas as plataformas")
        
        except Exception as e:
            # Incrementar tentativas
            attempts = job.get("attempts", 0) + 1
            error_msg = str(e)
            
            if attempts < self.max_retries:
                # Reagendar
                retry_time = datetime.now() + timedelta(seconds=self.retry_delay)
                self._update_job_status(
                    job_id,
                    "scheduled",
                    attempts=attempts,
                    scheduled_time=retry_time.isoformat(),
                    error=error_msg
                )
                logger.warning(f"⚠️ [{job_id}] Tentativa {attempts}/{self.max_retries} falhou. Retry em {retry_time.strftime('%H:%M')}")
            else:
                # Desistir
                self._update_job_status(job_id, "failed", error=error_msg)
                logger.error(f"❌ [{job_id}] Falhou após {self.max_retries} tentativas")
    
    def _update_job_status(
        self, 
        job_id: str, 
        status: str, 
        published_links: Optional[dict] = None,
        attempts: Optional[int] = None,
        scheduled_time: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Atualiza status de um job"""
        with self.queue_lock:
            for job in self.queue["queue"]:
                if job["id"] == job_id:
                    job["status"] = status
                    
                    if published_links is not None:
                        job["published_links"] = published_links
                    
                    if attempts is not None:
                        job["attempts"] = attempts
                    
                    if scheduled_time is not None:
                        job["scheduled_time"] = scheduled_time
                    
                    if error is not None:
                        job["errors"].append({
                            "timestamp": datetime.now().isoformat(),
                            "message": error
                        })
                    
                    job["updated_at"] = datetime.now().isoformat()
                    break
            
            self._save_queue()
    
    def cleanup_old_jobs(self, days: int = 7):
        """Remove jobs antigos da fila"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.queue_lock:
            original_count = len(self.queue["queue"])
            self.queue["queue"] = [
                job for job in self.queue["queue"]
                if (
                    job["status"] in ["scheduled", "publishing"] or
                    datetime.fromisoformat(job.get("updated_at", job["created_at"])) > cutoff
                )
            ]
            removed = original_count - len(self.queue["queue"])
            
            if removed > 0:
                self._save_queue()
                logger.info(f"🧹 Removidos {removed} jobs antigos da fila")
