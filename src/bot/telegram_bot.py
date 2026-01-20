"""
Telegram Bot para AI Video Clipper (Corrigido & Atualizado)
"""
import os
import sys
import asyncio
import logging
import subprocess
import shutil
import signal
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_output.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class VideoClipperBot:
    def __init__(self, token: str):
        self.app = ApplicationBuilder().token(token).build()
        self.active_processes = {}  # chat_id -> process
        self.pending_approvals = {}  # chat_id -> {video_path, metadata}

        # Handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("clip", self.clip_command))
        self.app.add_handler(CommandHandler("nuke", self.nuke_command))
        self.app.add_handler(CommandHandler("system", self.system_info_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        self.app.add_handler(CommandHandler("cancel", self.cancel_command))
        self.app.add_handler(CommandHandler("restart", self.restart_command))
        self.app.add_handler(CommandHandler("logs", self.logs_command))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))

    def run(self):
        logger.info("🤖 Bot Iniciado! Aguardando mensagens...")
        self.app.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🔄 Reiniciar Sistema", callback_data='system_restart')],
            [InlineKeyboardButton("📜 Ver Logs", callback_data='view_logs')],
            [InlineKeyboardButton("❔ Ajuda", callback_data='help_info')]
        ]

        await update.message.reply_text(
            "🎬 **AI Video Clipper Bot** (100% Local)\n\n"
            "Envie um link de vídeo para começar!\n"
            "Ou use: `/clip <url>`\n\n"
            "**Painel de Controle:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text.startswith("http"):
            await self.process_url(update, context, text)
        else:
            await update.message.reply_text("⚠️ Envie um link válido (YouTube, TikTok, etc).")

    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            log_path = Path("bot_output.log")
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-15:]
                log_content = "".join(lines) or "Log vazio."
            else:
                log_content = "Arquivo de log não encontrado."

            await update.message.reply_text(
                f"📜 **Últimos Logs:**\n\n```\n{log_content[-2000:]}\n```",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ Erro ao ler logs: {e}")

    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 **Reiniciando Sistema...**\n\nAguarde...")
        await self._perform_restart()

    async def _perform_restart(self):
        # Cleanup processos
        for chat_id, process in self.active_processes.items():
            try:
                process.terminate()
                await process.wait()
            except:
                pass

        logger.info("Reiniciando bot...")
        await asyncio.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        process = self.active_processes.get(chat_id)

        if process:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass

                del self.active_processes[chat_id]
                await update.message.reply_text("🛑 **Processo cancelado!**")
            except Exception as e:
                logger.error(f"Erro ao cancelar: {e}")
                await update.message.reply_text("⚠️ Erro ao cancelar processo.")
        else:
            await update.message.reply_text("⚠️ Nenhum processo ativo.")

    async def clip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "⚠️ **Uso:** `/clip <url> [opções]`\n\n"
                "**Opções:**\n"
                "`--clips N` - Número de clipes (padrão 3)\n"
                "`--min N` - Duração mínima (s)\n"
                "`--max N` - Duração máxima (s)\n"
                "`--captions` - Adicionar legendas\n"
                "`--voice` - Adicionar narração\n\n"
                "**Exemplo:** `/clip <url> --clips 3 --captions`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        url = context.args[0]
        params = self._parse_clip_args(context.args[1:])
        await self.process_url(update, context, url, params)

    def _parse_clip_args(self, args_list: list) -> dict:
        """Parse flags do comando /clip"""
        params = {
            'clips': 3,
            'min': 30,
            'max': 60,
            'captions': False,
            'voice': False
        }

        try:
            for i, arg in enumerate(args_list):
                if arg == '--clips' and i + 1 < len(args_list):
                    params['clips'] = int(args_list[i+1])
                elif arg == '--min' and i + 1 < len(args_list):
                    params['min'] = int(args_list[i+1])
                elif arg == '--max' and i + 1 < len(args_list):
                    params['max'] = int(args_list[i+1])
                elif arg == '--captions':
                    params['captions'] = True
                elif arg == '--voice':
                    params['voice'] = True
        except Exception as e:
            logger.error(f"Erro ao parsear args: {e}")

        return params

    async def nuke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("☢️ **NUKE INICIADO...**\n\nLimpando sistema...")

        # Parar processos
        for chat_id, process in list(self.active_processes.items()):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass
        self.active_processes.clear()

        # Limpar arquivos
        for d in [Path("temp"), Path("exports")]:
            if d.exists():
                shutil.rmtree(d)
                d.mkdir()

        for f in ["bot_output.log", "state.json"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

        await update.message.reply_text("✅ **Sistema resetado!**")

    async def system_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            import platform
            import psutil

            cpu_usage = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('.')

            info = (
                f"🖥️ **Info do Sistema:**\n\n"
                f"**Plataforma:** {platform.system()} {platform.release()}\n"
                f"**CPU:** {cpu_usage}%\n"
                f"**Memória:** {mem.percent}% ({mem.used//1024**2}MB)\n"
                f"**Disco:** {disk.percent}% livre\n"
                f"**Clipes:** {len(list(Path('exports').glob('*.mp4'))) if Path('exports').exists() else 0}"
            )
            await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Erro: {e}")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        export_dir = Path("exports")
        if not export_dir.exists():
            await update.message.reply_text("📂 Histórico vazio.")
            return

        videos = sorted(list(export_dir.glob("clip_*.mp4")), key=os.path.getmtime, reverse=True)[:10]
        if not videos:
            await update.message.reply_text("📂 Nenhum clipe encontrado.")
            return

        msg = "📜 **Últimos 10 Clipes:**\n\n"
        for i, vid in enumerate(videos, 1):
            size = vid.stat().st_size / (1024*1024)
            msg += f"{i}. `{vid.name}` ({size:.1f} MB)\n"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def process_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, params: dict = None):
        chat_id = update.effective_chat.id
        params = params or {}

        if chat_id in self.active_processes:
            await update.message.reply_text(
                "⚠️ **Processamento em andamento!**\n\n"
                "Use /cancel para parar antes de iniciar outro."
            )
            return

        status_msg = await update.message.reply_text(
            f"⏳ **Processando:** {url}\n\nIsso pode levar alguns minutos..."
        )

        # Comando main.py atualizado
        cmd = [
            sys.executable, "main.py",
            "--url", url,
            "--clips", str(params.get('clips', 3)),
            "--min", str(params.get('min', 30)),
            "--max", str(params.get('max', 60))
        ]

        if params.get('captions'):
            cmd.append("--captions")
        if params.get('voice'):
            cmd.append("--voice")

        logger.info(f"🚀 Executando: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=os.setsid
            )

            self.active_processes[chat_id] = process

            # Monitorar saída
            final_video_path = None

            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                line_text = line.decode('utf-8', errors='ignore').strip()
                if line_text:
                    logger.info(f"[CLI] {line_text}")

                    # Capturar caminho do clipe
                    if "gerado com sucesso:" in line_text:
                        try:
                            final_video_path = line_text.split("gerado com sucesso:", 1)[1].strip()
                        except:
                            pass

                    # Atualizar progresso
                    if "STAGE" in line_text:
                        progress, stage = self._parse_progress(line_text)

                        bar_filled = int(10 * progress / 100)
                        bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)

                        status_text = (
                            f"⏳ **Processando...**\n"
                            f"{bar} **{progress}%**\n\n"
                            f"📌 {stage}"
                        )

                        try:
                            if status_text != getattr(self, 'last_status', ''):
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=status_msg.message_id,
                                    text=status_text,
                                    parse_mode=ParseMode.MARKDOWN
                                )
                                self.last_status = status_text
                        except:
                            pass

            await process.wait()

            if chat_id in self.active_processes:
                del self.active_processes[chat_id]

            # Buscar último clipe gerado
            if not final_video_path:
                export_dir = Path("exports")
                clips = sorted(export_dir.glob("clip_*.mp4"), key=os.path.getmtime, reverse=True)
                if clips:
                    final_video_path = str(clips[0])

            if final_video_path and os.path.exists(final_video_path):
                await status_msg.edit_text("✅ **Vídeo Gerado!** Enviando...")

                # Enviar vídeo
                with open(final_video_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=chat_id,
                        video=video_file,
                        caption="✂️ Seu corte viral está pronto!"
                    )

                # Enviar metadados se existirem
                meta_path = Path(final_video_path).with_name(
                    Path(final_video_path).stem.replace('clip', 'meta') + '.json'
                )

                if meta_path.exists():
                    try:
                        import json
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        meta_text = (
                            f"📝 **Metadados Sugeridos:**\n\n"
                            f"**Título:** {metadata.get('title', 'N/A')}\n"
                            f"**Hashtags:** {' '.join(metadata.get('hashtags', []))}\n"
                            f"**Descrição:** {metadata.get('description', 'N/A')}"
                        )

                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=meta_text,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        logger.error(f"Erro ao enviar metadados: {e}")
            else:
                await status_msg.edit_text("❌ Falha ao gerar vídeo. Use /logs para ver detalhes.")

        except Exception as e:
            logger.error(f"Erro no bot: {e}")
            await status_msg.edit_text(f"❌ Erro: {str(e)}")

    def _parse_progress(self, log_line: str) -> tuple:
        """Parse progresso do log"""
        if "STAGE 1" in log_line:
            return 20, "Download/Carregamento..."
        if "STAGE 2" in log_line:
            return 40, "Transcrição (Vosk)..."
        if "STAGE 3" in log_line:
            return 60, "Análise Viral (Ollama)..."
        if "STAGE 4" in log_line:
            return 90, "Edição 9:16..."
        if "CONCLUÍDO" in log_line:
            return 100, "Finalizado!"
        return 0, "Iniciando..."

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = query.message.chat_id

        try:
            await query.answer()
        except:
            pass

        if query.data == 'system_restart':
            await query.edit_message_text("🔄 **Reiniciando...**")
            await self._perform_restart()
            return

        if query.data == 'view_logs':
            try:
                log_path = Path("bot_output.log")
                if log_path.exists():
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-15:]
                    log_content = "".join(lines) or "Vazio"
                else:
                    log_content = "Não encontrado"

                await context.bot.send_message(
                    chat_id,
                    f"📜 **Logs:**\n\n```\n{log_content[-2000:]}\n```",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Erro logs: {e}")
            return

        if query.data == 'help_info':
            await query.edit_message_text(
                "ℹ️ **Ajuda**\n\n"
                "/clip <url> - Criar cortes\n"
                "/history - Ver histórico\n"
                "/system - Info do sistema\n"
                "/logs - Ver logs\n"
                "/cancel - Parar processo\n"
                "/nuke - Reset total\n"
                "/restart - Reiniciar bot",
                parse_mode=ParseMode.MARKDOWN
            )
            return

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN não encontrado!")
        sys.exit(1)

    bot = VideoClipperBot(token)
    bot.run()
