"""
AI Video Clipper V3 - CLOUD ORCHESTRATOR (MAESTRO)
Gerencia simultaneamente: Ngrok + Flask Backend + Telegram Bot
"""
import os
import sys
import time
import subprocess
import threading
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Maestro")

PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

class CloudMaestro:
    def __init__(self):
        load_dotenv()
        self.processes = []
        self.ngrok_url = None
        self.running = True

    def start_ngrok(self, port=5000):
        """Inicia o túnel Ngrok para a Web UI"""
        token = os.getenv("NGROK_AUTHTOKEN")
        if not token:
            logger.warning("⚠️ NGROK_AUTHTOKEN não encontrado. Web UI será apenas local.")
            return

        try:
            from pyngrok import ngrok
            ngrok.set_auth_token(token)
            public_url = ngrok.connect(port)
            self.ngrok_url = public_url.public_url
            logger.info(f"🌐 NGROK ATIVO: {self.ngrok_url}")
            print(f"\n{'='*60}\n🚀 WEB UI ACESSÍVEL EM: {self.ngrok_url}\n{'='*60}\n")
        except ImportError:
            logger.error("❌ pyngrok não instalado. execute: pip install pyngrok")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Ngrok: {e}")

    def run_sub_process(self, name, command):
        """Roda um script python em background"""
        logger.info(f"🎬 Iniciando {name}: {' '.join(command)}")
        
        # Usar o executável atual do python para garantir o venv/ambiente
        full_command = [sys.executable] + command
        
        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT)
        )
        
        self.processes.append((name, process))
        
        # Thread para ler logs em tempo real
        def log_reader():
            for line in iter(process.stdout.readline, ''):
                if not self.running: break
                clean_line = line.strip()
                if clean_line:
                    print(f"[{name}] {clean_line}")
            process.stdout.close()

        threading.Thread(target=log_reader, daemon=True).start()

    def stop_all(self):
        """Encerra todos os processos graciosamente"""
        self.running = False
        logger.info("🛑 Encerrando todos os serviços...")
        for name, proc in self.processes:
            logger.info(f"   Terminando {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except:
                proc.kill()
        
        from pyngrok import ngrok
        ngrok.disconnect(self.ngrok_url)
        logger.info("✅ Todos os serviços parados.")

    def start_everything(self):
        # 1. Ngrok para Flask (Porta 5000 default)
        self.start_ngrok(5000)

        # 2. Flask Backend/Frontend
        self.run_sub_process("WEB_UI", ["app.py"])

        # 3. Telegram Bot
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.run_sub_process("TELEGRAM_BOT", ["src/bot/telegram_bot.py"])
        else:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN ausente. Bot não será iniciado.")

        # Manter vivo
        try:
            while self.running:
                # Verificar se processos ainda estão vivos
                for name, proc in self.processes:
                    if proc.poll() is not None:
                        logger.error(f"❌ {name} morreu inesperadamente!")
                        # Opcional: reiniciar aqui
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop_all()

if __name__ == "__main__":
    # Signal handling
    maestro = CloudMaestro()
    
    def signal_handler(sig, frame):
        maestro.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    maestro.start_everything()
