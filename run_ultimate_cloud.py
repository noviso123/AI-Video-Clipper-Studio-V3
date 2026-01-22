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

# Configuração do Sistema Headless (Fix ALSA/Audio/XDG)
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-root"
os.environ["MESA_GL_VERSION_OVERRIDE"] = "3.3"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

# Garantir que o dir XDG existe
os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(PROJECT_ROOT))

class CloudMaestro:
    def __init__(self):
        self._ensure_env_exists()
        load_dotenv()
        self.processes = []
        self.ngrok_url = None
        self.running = True

    def _ensure_env_exists(self):
        """Cria o .env se não existir, usando variáveis de ambiente do SO (Colab Secrets)"""
        env_path = PROJECT_ROOT / ".env"
        if not env_path.exists():
            logger.info("📝 .env não encontrado. Gerando a partir das chaves injetadas...")
            keys = [
                "GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "NGROK_AUTHTOKEN",
                "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "PEXELS_API_KEY"
            ]
            content = "# AI Video Clipper V3 - Auto Generated\n"
            for k in keys:
                val = os.getenv(k, "")
                content += f"{k}={val}\n"
            
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("✅ .env gerado com sucesso.")

    def start_ngrok(self, port=5000):
        """Inicia o túnel Ngrok para a Web UI"""
        token = os.getenv("NGROK_AUTHTOKEN")
        if not token or len(token) < 20:
            logger.warning("⚠️ NGROK_AUTHTOKEN inválido ou ausente. Web UI será apenas local.")
            print("\n❌ ERRO NGROK: Token inválido! Obtenha um novo em https://dashboard.ngrok.com/get-started/your-authtoken\n")
            return

        try:
            from pyngrok import ngrok, conf
            # Limpar instâncias anteriores do ngrok
            ngrok.kill()
            
            ngrok.set_auth_token(token)
            public_url = ngrok.connect(port)
            self.ngrok_url = public_url.public_url
            logger.info(f"🌐 NGROK ATIVO: {self.ngrok_url}")
            print(f"\n{'='*60}\n🚀 WEB UI ACESSÍVEL EM: {self.ngrok_url}\n{'='*60}\n")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Ngrok: {e}")
            if "ERR_NGROK_105" in str(e):
                print("\n❌ ERRO NGROK (105): Seu token parece estar mal formatado. Revise-o no Dashboard do Ngrok.")

    def _cleanup_environment(self):
        """Limpa processos fantasmas antes de começar"""
        logger.info("🧹 Limpando ambiente de processos antigos...")
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                # Matar outros processos python que não sejam este
                if proc.info['pid'] != os.getpid() and 'python' in proc.info['name']:
                    cmd = " ".join(proc.info['cmdline'] or [])
                    if "app.py" in cmd or "telegram_bot.py" in cmd or "run_ultimate_cloud.py" in cmd:
                        logger.info(f"   💀 Matando processo zumbi: {proc.info['pid']} ({cmd})")
                        proc.kill()
        except:
            pass

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
        # 0. Limpar Ambiente
        self._cleanup_environment()

        # 1. Ngrok para Flask (Porta 5000 default)
        self.start_ngrok(5000)

        # 2. Flask Backend/Frontend
        self.run_sub_process("WEB_UI", ["app.py"])

        # 3. Telegram Bot (Apenas se configurado e HABILITADO)
        enable_bot = os.getenv("ENABLE_TELEGRAM_BOT", "false").lower() == "true"
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if enable_bot and token:
            self.run_sub_process("TELEGRAM_BOT", ["src/bot/telegram_bot.py"])
        else:
            reason = "Desativado via ENABLE_TELEGRAM_BOT" if not enable_bot else "Token ausente"
            logger.info(f"🤖 Bot de Telegram ignorado ({reason}).")

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
