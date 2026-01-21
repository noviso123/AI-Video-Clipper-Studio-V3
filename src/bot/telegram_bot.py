"""
Telegram Bot para AI Video Clipper (Versão 3.0 - Ultimate)
Funcionalidades:
- Upload de arquivos de vídeo diretos
- Menu de Configurações (/settings) persistente
- Controle total de parâmetros via UI
- Progresso em tempo real
"""
import os
import sys
import asyncio
import logging
import subprocess
import shutil
import signal
import json
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente explicitamente
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_output.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TelegramBot")

# Add src to path para garantir consistência
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
CONFIG_FILE = "bot_users.json"

class VideoClipperBot:
    def __init__(self, token: str):
        self.app = ApplicationBuilder().token(token).build()
        self.active_processes = {}  # chat_id -> process
        self.user_configs = self._load_config()

        # Handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("settings", self.settings_command))
        self.app.add_handler(CommandHandler("cancel", self.cancel_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("logs", self.logs_command))
        self.app.add_handler(CommandHandler("nuke", self.nuke_command))

        # Mensagens e Arquivos
        self.app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, self.handle_video))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.user_configs, f)

    def _get_user_config(self, chat_id):
        str_id = str(chat_id)
        if str_id not in self.user_configs:
            self.user_configs[str_id] = {
                'clips': 3,
                'min': 30,
                'max': 60,
                'captions': True,
                'voice': False
            }
            self._save_config()
        return self.user_configs[str_id]

    def run(self):
        logger.info("🤖 Bot Iniciado! Aguardando mensagens...")
        print("✅ Telegram Bot Online (V3 Ultimate). Pressione Ctrl+C para parar.")
        self.app.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user.first_name

        keyboard = [
            [InlineKeyboardButton("⚙️ Configurações", callback_data='settings_menu')],
            [InlineKeyboardButton("📝 Comandos", callback_data='help_info')],
            [InlineKeyboardButton("📜 Logs", callback_data='view_logs')]
        ]

        welcome_msg = (
            f"👋 **Olá, {user}!**\n\n"
            "🎬 **AI Video Clipper Studio V3 (Ultimate)**\n"
            "Eu sou seu assistente de produção de conteúdo.\n\n"
            "🚀 **Funcionalidades:**\n"
            "• Envie **Links** (YouTube/TikTok)\n"
            "• Envie **Vídeos** (Upload direto)\n"
            "• Configure preferências em `/settings`\n\n"
            "👇 **Menu Principal:**"
        )

        await update.message.reply_text(
            welcome_msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        config = self._get_user_config(chat_id)
        await self._show_settings_menu(update, context, config)

    async def _show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, config: dict, is_edit=False):
        # Emojis de status
        e_captions = "✅" if config['captions'] else "❌"
        e_voice = "✅" if config['voice'] else "❌"

        keyboard = [
            [
                InlineKeyboardButton(f"Legendas {e_captions}", callback_data='toggle_captions'),
                InlineKeyboardButton(f"Narração {e_voice}", callback_data='toggle_voice')
            ],
            [
                InlineKeyboardButton(f"Clipes: {config['clips']}", callback_data='cycle_clips'),
                InlineKeyboardButton(f"Tempo: {config['min']}-{config['max']}s", callback_data='cycle_duration')
            ],
            [InlineKeyboardButton("💾 Salvar & Fechar", callback_data='close_settings')]
        ]

        text = (
            "⚙️ **Painel de Configurações**\n\n"
            f"📝 **Legendas:** {e_captions}\n"
            f"🗣️ **Narração:** {e_voice}\n"
            f"✂️ **Qtd. Clipes:** {config['clips']}\n"
            f"⏱️ **Duração:** {config['min']}s a {config['max']}s"
        )

        if is_edit:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "ℹ️ **Guia Ultimate:**\n\n"
            "1️⃣ **Links**: Cole um link do YouTube ou TikTok.\n"
            "2️⃣ **Arquivos**: Envie um vídeo .mp4 direto para o chat.\n"
            "3️⃣ **Config**: Use `/settings` para ajustar legendas e duração.\n\n"
            "🛠️ **Comandos:**\n"
            "`/cancel` - Parar\n"
            "`/status` - Monitorar recursos\n"
            "`/logs` - Ver debug\n"
            "`/nuke` - Limpar tudo"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lida com upload de arquivos de vídeo"""
        chat_id = update.effective_chat.id
        video = update.message.video or update.message.document

        if not video:
            await update.message.reply_text("⚠️ Arquivo inválido.")
            return

        file_id = video.file_id

        status_msg = await update.message.reply_text("📥 **Baixando vídeo enviado...**")

        try:
            new_file = await context.bot.get_file(file_id)

            # Salvar em temp
            temp_dir = PROJECT_ROOT / "temp"
            temp_dir.mkdir(exist_ok=True)

            file_path = temp_dir / f"upload_{file_id}.mp4"
            await new_file.download_to_drive(file_path)

            await status_msg.edit_text("✅ Download concluído! Iniciando processamento...")

            # Iniciar processamento via arquivo local
            await self.process_clipper(update, context, file_path=str(file_path), status_msg=status_msg)

        except Exception as e:
            logger.error(f"Erro no download: {e}")
            await status_msg.edit_text(f"❌ Erro ao baixar vídeo (Limite de 20MB da API Telegram?): {e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()

        # Ignorar mensagens sem link
        if "http" not in text:
            await update.message.reply_text("⚠️ Envie um **link**, um **arquivo de vídeo** ou use `/settings`.")
            return

        url = next((w for w in text.split() if w.startswith("http")), None)
        if not url: return

        await self.process_clipper(update, context, url=url)

    async def process_clipper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url=None, file_path=None, status_msg=None):
        chat_id = update.effective_chat.id
        config = self._get_user_config(chat_id)

        if chat_id in self.active_processes:
            await update.message.reply_text("⚠️ Processo em andamento. Use /cancel.")
            return

        if not status_msg:
            status_msg = await update.message.reply_text(f"⏳ **Iniciando IA...**\nConfig: {config['clips']} clipes")

        # Construir comando
        cmd = [sys.executable, "main.py"]

        if url:
            cmd.extend(["--url", url])
        elif file_path:
            cmd.extend(["--file", file_path])

        # Aplicar Configurações do Usuário
        cmd.extend(["--clips", str(config['clips'])])
        cmd.extend(["--min", str(config['min'])])
        cmd.extend(["--max", str(config['max'])])

        if config['captions']:
            cmd.append("--captions")
        if config['voice']:
            cmd.append("--voice")

        logger.info(f"🚀 Iniciando processo {chat_id}: {' '.join(cmd)}")

        try:
            # Usar cwd para garantir que imports funcionem
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(PROJECT_ROOT),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )

            self.active_processes[chat_id] = process
            final_files = []
            last_progress_text = ""

            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break

                line = line_bytes.decode('utf-8', errors='replace').strip()
                if not line: continue

                # Logar progresso para debug
                # logger.info(f"[Main.py] {line}")

                progress, stage_name = self._parse_progress(line)

                if progress > 0:
                    bar_len = 10
                    filled = int(bar_len * progress / 100)
                    bar = "🟩" * filled + "⬜" * (bar_len - filled)

                    progress_text = (
                        f"🎬 **Clipper em Ação**\n"
                        f"{bar} **{progress}%**\n"
                        f"📌 {stage_name}\n"
                    )

                    if progress_text != last_progress_text:
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=status_msg.message_id,
                                text=progress_text,
                                parse_mode=ParseMode.MARKDOWN
                            )
                            last_progress_text = progress_text
                        except:
                            pass

                if "gerado com sucesso:" in line:
                    parts = line.split("gerado com sucesso:")
                    if len(parts) > 1:
                        final_files.append(Path(parts[1].strip()))

            return_code = await process.wait()
            if chat_id in self.active_processes:
                del self.active_processes[chat_id]

            if return_code == 0 and final_files:
                await status_msg.edit_text("✅ **Concluído!** Enviando clipes...")
                for fpath in final_files:
                    if fpath.exists():
                        caption = f"✨ **{fpath.name}**\nHashtags: #Viral #Shorts"
                        with open(fpath, 'rb') as vf:
                            await context.bot.send_video(chat_id, vf, caption=caption, supports_streaming=True)
                await context.bot.send_message(chat_id, "🚀 **Pronto!** Mande o próximo.")
            else:
                await status_msg.edit_text("❌ Algo deu errado. Use /logs.")

        except Exception as e:
            logger.error(f"Erro fatal: {e}")
            if chat_id in self.active_processes: del self.active_processes[chat_id]
            await status_msg.edit_text(f"❌ Erro Crítico: {e}")

    def _parse_progress(self, line: str):
        if "STAGE 1" in line: return 10, "Baixando/Lendo..."
        if "STAGE 2" in line: return 30, "Transcrição IA..."
        if "STAGE 3" in line: return 50, "Análise Viral..."
        if "STAGE 4" in line: return 75, "Edição Mágica..."
        if "Thumb" in line: return 85, "Thumbnails..."
        if "CONCLUÍDO" in line: return 100, "Finalizando..."
        return 0, ""

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = query.message.chat_id
        data = query.data

        await query.answer()

        if data == 'settings_menu':
            config = self._get_user_config(chat_id)
            await self._show_settings_menu(update, context, config, is_edit=False)

        elif data in ['help_info', 'system_status', 'view_logs']:
            if data == 'help_info': await self.help_command(update, context)
            if data == 'system_status': await self.status_command(update, context)
            if data == 'view_logs': await self.logs_command(update, context)

        elif data == 'close_settings':
            await query.delete_message()

        # Toggles de Config
        elif data in ['toggle_captions', 'toggle_voice', 'cycle_clips', 'cycle_duration']:
            config = self._get_user_config(chat_id)

            if data == 'toggle_captions':
                config['captions'] = not config['captions']
            elif data == 'toggle_voice':
                config['voice'] = not config['voice']
            elif data == 'cycle_clips':
                vals = [1, 3, 5, 10]
                try:
                    curr_idx = vals.index(config['clips'])
                    config['clips'] = vals[(curr_idx + 1) % len(vals)]
                except: config['clips'] = 3
            elif data == 'cycle_duration':
                # Alternar entre Short (15-30), Medium (30-60), Long (60-90)
                if config['max'] == 60:
                    config['min'], config['max'] = 60, 90
                elif config['max'] == 90:
                    config['min'], config['max'] = 15, 30
                else:
                    config['min'], config['max'] = 30, 60

            self._save_config()
            await self._show_settings_menu(update, context, config, is_edit=True)

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id in self.active_processes:
            process = self.active_processes[chat_id]
            try:
                process.terminate()
                if os.name == 'nt':
                     subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])

                await update.message.reply_text("🛑 Cancelado.")
            except: pass
            del self.active_processes[chat_id]
        else:
            await update.message.reply_text("💤 Nada rodando.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            msg = f"🖥️ **Status**\nCPU: {cpu}%\nRAM: {mem.percent}%"
            await update.message.reply_text(msg)
        except: pass

    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        log_file = PROJECT_ROOT / "logs" / f"clipper_{self._get_today()}.log"
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-10:]
            await update.message.reply_text(f"📜 Logs:\n{''.join(lines)}")
        else:
            await update.message.reply_text("❌ Sem logs hoje.")

    async def nuke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        shutil.rmtree(PROJECT_ROOT / "temp", ignore_errors=True)
        (PROJECT_ROOT / "temp").mkdir(exist_ok=True)
        await update.message.reply_text("☢️ Temp limpo.")

    def _get_today(self):
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN ausente.")
        sys.exit(1)

    VideoClipperBot(token).run()
