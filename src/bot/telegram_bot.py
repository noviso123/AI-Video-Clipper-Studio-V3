"""
Telegram Bot para Orchestrar AI Video Clipper
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

# Setup basic logging to both file and console
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

from src.modules.metadata_generator import MetadataGenerator
from src.publishers.publisher_manager import PublisherManager

class VideoClipperBot:
    def __init__(self, token: str):
        self.app = ApplicationBuilder().token(token).build()
        self.metadata_generator = MetadataGenerator()
        self.publisher = PublisherManager()
        self.active_processes = {} # chat_id -> process
        self.pending_approvals = {} # chat_id -> {video_path, metadata}

        # Handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("clip", self.clip_command))
        self.app.add_handler(CommandHandler("autonomous", self.autonomous_command))
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
            [InlineKeyboardButton("🔄 Atualizar / Reiniciar", callback_data='system_restart')],
            [InlineKeyboardButton("📜 Ver Últimos Logs", callback_data='view_logs')],
            [InlineKeyboardButton("❔ Ajuda", callback_data='help_info')]
        ]
        
        await update.message.reply_text(
            "🎬 **AI Video Clipper Bot**\n\n"
            "Envie um link (YouTube, TikTok, Instagram, etc.) para começar!\n"
            "Comando: `/clip <url>`\n\n"
            "**Painel de Controle:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text.startswith("http"):
            await self.process_url(update, context, text)
        else:
            await update.message.reply_text("⚠️ Por favor, envie um link válido (YouTube, TikTok, etc.).")

    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            log_path = Path("bot_output.log")
            if log_path.exists():
                # Ler últimas 15 linhas
                with open(log_path, 'r') as f:
                    lines = f.readlines()[-15:]
                log_content = "".join(lines)
                if not log_content: log_content = "Log vazio."
            else:
                log_content = "Arquivo de log não encontrado."
                
            await update.message.reply_text(f"📜 **Últimos Logs do Sistema:**\n\n```\n{log_content}\n```", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Erro ao ler logs: {e}")

    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text("🔄 **Reiniciando Sistema...** ♻️\n\nAguarde...")
        await self._perform_restart()

    async def _perform_restart(self):
        # Cleanup: Terminar todos os processos filhos
        for chat_id, process in self.active_processes.items():
            try:
                process.terminate()
                await process.wait()
            except: pass
        
        logger.info("Reiniciando bot...")
        # Clear lock/state files if they exist to ensure fresh start
        for f in ["state.json", "status.json"]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass
        await asyncio.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        process = self.active_processes.get(chat_id)
        
        if process:
            try:
                # Use process group kill to ensure all children (ffmpeg, etc) are killed
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                
                # Wait with timeout to avoid hanging the bot
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Process {process.pid} did not exit in time after SIGKILL")
                
                del self.active_processes[chat_id]
                await update.message.reply_text("🛑 **Processo cancelado e encerrado com sucesso!**")
            except Exception as e:
                logger.error(f"Erro ao cancelar: {e}")
                await update.message.reply_text("⚠️ Erro ao tentar cancelar o processo.")
        else:
            await update.message.reply_text("⚠️ Nenhum processo ativo para cancelar.")

    async def clip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "⚠️ **Uso:** `/clip <url> [opções]`\n\n"
                "**Opções:**\n"
                "`--clips N` - Número de clipes (padrão 1)\n"
                "`--min-duration N` - Duração mínima segundos\n"
                "`--max-duration N` - Duração máxima segundos\n"
                "`--style STYLE` - Estilo da legenda\n"
                "`--broll` - Ativar B-rolls\n"
                "`--variants` - Gerar TikTok/Reels/Shorts\n"
                "`--no-critic` - Pular avaliação da IA\n\n"
                "**Exemplo:** `/clip <url> --clips 3 --style neon --variants`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        url = context.args[0]
        params = self._parse_clip_args(context.args[1:])
        await self.process_url(update, context, url, params)

    def _parse_clip_args(self, args_list: list) -> dict:
        """Parse opcional de flags para o comando /clip"""
        params = {
            'clips': '1',
            'min_duration': '30',
            'max_duration': '60',
            'style': 'karaoke_modern',
            'broll': True,
            'critic': True,
            'variants': False
        }
        
        try:
            for i, arg in enumerate(args_list):
                if arg == '--clips' and i + 1 < len(args_list):
                    params['clips'] = args_list[i+1]
                elif arg == '--min-duration' and i + 1 < len(args_list):
                    params['min_duration'] = args_list[i+1]
                elif arg == '--max-duration' and i + 1 < len(args_list):
                    params['max_duration'] = args_list[i+1]
                elif arg == '--style' and i + 1 < len(args_list):
                    params['style'] = args_list[i+1]
                elif arg == '--broll':
                    params['broll'] = True
                elif arg == '--no-broll':
                    params['broll'] = False
                elif arg == '--variants':
                    params['variants'] = True
                elif arg == '--no-critic':
                    params['critic'] = False
                elif arg == '--critic':
                    params['critic'] = True
        except Exception as e:
            logger.error(f"Erro ao parsear argumentos: {e}")
            
        return params

    async def autonomous_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("⚠️ Uso: `/autonomous <url>`")
            return
        url = context.args[0]
        await self.process_url(update, context, url, autonomous=True)

    async def nuke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("☢️ **NUKE INICIADO...** Limpando tudo (Exports, Temp, Logs, Estado)...")
        # Logic from app.py:nuke_everything
        # Stop processes
        for chat_id, process in list(self.active_processes.items()):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except: pass
        self.active_processes.clear()
        
        # Clear files
        temp_dir = Path("temp")
        export_dir = Path("exports")
        for d in [temp_dir, export_dir]:
            if d.exists():
                shutil.rmtree(d)
                d.mkdir()
        
        # Clear specific logs and JSONs
        for f in ["bot_output.log", "state.json", "status.json"]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass
        
        await update.message.reply_text("✅ **Sistema resetado para o estado de fábrica!**")

    async def system_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        import platform
        import psutil
        
        cpu_usage = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        info = (
            f"🖥️ **Info do Sistema:**\n\n"
            f"**Plataforma:** {platform.system()} {platform.release()}\n"
            f"**CPU:** {cpu_usage}%\n"
            f"**Memória:** {mem.percent}% ({mem.used//1024**2}MB / {mem.total//1024**2}MB)\n"
            f"**Disco:** {disk.percent}% livre\n"
            f"**Python:** {sys.executable}\n"
            f"**Exportados:** {len(list(Path('exports').glob('*.mp4'))) if Path('exports').exists() else 0} vídeos"
        )
        await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        export_dir = Path("exports")
        if not export_dir.exists():
            await update.message.reply_text("📂 Histórico vazio.")
            return
            
        videos = sorted(list(export_dir.glob("clip_*.mp4")), key=os.path.getmtime, reverse=True)[:10]
        if not videos:
            await update.message.reply_text("📂 Nenhum clipe encontrado no histórico.")
            return
            
        msg = "📜 **Últimos 10 Clipes Gerados:**\n\n"
        for i, vid in enumerate(videos, 1):
            size = vid.stat().st_size / (1024*1024)
            msg += f"{i}. `{vid.name}` ({size:.1f} MB)\n"
            
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def process_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, params: dict = None, autonomous: bool = False):
        chat_id = update.effective_chat.id
        params = params or {}
        
        # Check for existing process
        if chat_id in self.active_processes:
            await update.message.reply_text(
                "⚠️ **Você já tem um vídeo sendo processado!**\n\n"
                "Aguarde o término ou use /cancel para parar o atual antes de iniciar outro."
            )
            return

        status_prefix = "🧠 **Iniciando Cérebro Autônomo:**" if autonomous else "⏳ **Iniciando Processamento:**"
        status_msg = await update.message.reply_text(f"{status_prefix} {url}\nIsso pode levar alguns minutos...")

        # Rodar main.py como subprocesso
        cmd = [
            sys.executable, "main.py",
            "--url", url,
            "--clips", params.get('clips', '1'),
            "--caption-style", params.get('style', 'karaoke_modern'),
            "--min-duration", params.get('min_duration', '30'),
            "--max-duration", params.get('max_duration', '60')
        ]
        
        if params.get('captions', True): cmd.append("--captions")
        if params.get('broll'): cmd.append("--broll")
        if params.get('critic'): cmd.append("--critic")
        if params.get('variants'): cmd.append("--variants")
        if autonomous: cmd.append("--critic") # Autônomo sempre usa critic para qualidade
        
        logger.info(f"🚀 Executando: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT, # Merge stderr for full logs
                preexec_fn=os.setsid 
            )
            
            self.active_processes[chat_id] = process
            
            # Monitorar progresso
            final_video_path = None
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_text = line.decode('utf-8').strip()
                if line_text:
                    logger.info(f"[CLI] {line_text}")
                    # Tentar capturar caminhos de saída
                    if "gerado com sucesso:" in line_text:
                        try:
                            # Extract path after the message: "... gerado com sucesso: /path/to/video.mp4"
                            final_video_path = line_text.split("gerado com sucesso:", 1)[1].strip()
                        except:
                            pass

                    if "STAGE" in line_text:
                        progress, stage_name = self._parse_progress_from_log(line_text)
                        
                        # Build Progress Bar
                        bar_length = 10
                        filled_length = int(bar_length * progress / 100)
                        bar = "🟩" * filled_length + "⬜" * (bar_length - filled_length)
                        
                        status_text = (
                            f"⏳ **Processando Vídeo...**\n"
                            f"{bar} **{progress}%**\n\n"
                            f"📌 **Etapa Atual:** {stage_name}\n"
                            f"_Aguarde, analisando conteúdo viral..._"
                        )
                        
                        # Add Cancel and Logs Buttons during processing
                        keyboard = [
                            [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_process')],
                            [InlineKeyboardButton("📜 Ver Logs", callback_data='view_logs_minimal')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        try:
                            # Avoid editing too frequently (Telegram rate limits)
                            if status_text != getattr(self, 'last_status_text', ''):
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=status_msg.message_id,
                                    text=status_text,
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=reply_markup
                                )
                                self.last_status_text = status_text
                        except Exception as e:
                            logger.error(f"Erro ao atualizar status: {e}")


            try:
                await process.wait()
            except Exception as e:
                logger.error(f"Erro ao esperar processo: {e}")
            finally:
                if chat_id in self.active_processes:
                    del self.active_processes[chat_id]
            
            if final_video_path and os.path.exists(final_video_path):
                await status_msg.edit_text("✅ **Vídeo Gerado!** Preparando metadados...")
                
                # 1. Enviar Vídeo
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=open(final_video_path, 'rb'),
                    caption="Aqui está seu corte! ✂️"
                )
                
                # 2. Gerar Metadados
                # Simular transcrição (ou ler do arquivo se main.py salvasse)
                fake_transcript = "Conteúdo viral simulado para geração de metadados." 
                metadata = self.metadata_generator.generate_metadata(fake_transcript, 60)
                
                # Guardar estado para aprovação
                self.pending_approvals[chat_id] = {
                    "video_path": final_video_path,
                    "metadata": metadata
                }
                
                # 3. Enviar Card de Aprovação
                msg_text = (
                    f"🎬 **Sugestão de Publicação**\n\n"
                    f"**Título:** {metadata['title']}\n"
                    f"**Descrição:** {metadata['description']}\n"
                    f"**Hashtags:** {' '.join(metadata['hashtags'])}\n\n"
                    f"📊 **Score Viral:** {metadata['viral_score']}/10\n"
                    f"📝 **Motivo:** {metadata.get('explanation', '')}"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🚀 APROVAR & POSTAR (Tiktok/Yt/Ig)", callback_data='approve')],
                    [InlineKeyboardButton("🔄 Regenerar Texto", callback_data='regenerate')],
                    [InlineKeyboardButton("❌ Cancelar", callback_data='cancel')]
                ]
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=msg_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
                
            else:
                stderr = await process.stderr.read()
                err_msg = stderr.decode()
                await status_msg.edit_text(f"❌ Falha ao gerar vídeo.\nErro: {err_msg[:200]}...")

        except Exception as e:
            logger.error(f"Erro no bot: {e}")
            await status_msg.edit_text(f"❌ Erro interno: {str(e)}")

    def _parse_progress_from_log(self, log_line: str) -> tuple[int, str]:
        """Extrai porcentagem e nome da etapa do log."""
        if "STAGE 1" in log_line: return 10, "Baixando Vídeo..."
        if "STAGE 2" in log_line: return 30, "Transcrevendo Áudio (Whisper)..."
        if "STAGE 3" in log_line: return 45, "Analisando Conteúdo Viral..."
        if "STAGE 4" in log_line: return 60, "Editando Cortes (9:16)..."
        if "STAGE 5" in log_line: return 80, "Gerando Legendas Dinâmicas..."
        if "STAGE 6" in log_line: return 90, "Finalizando Variantes..."
        if "STAGE 7" in log_line: return 95, "Revisão Final..."
        return 0, "Iniciando..."

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = query.message.chat_id
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Erro ao responder query (provavelmente antiga): {e}")
            # Don't return, try to proceed anyway if possible or just exit safely
        
        # Handle System Callbacks
        if query.data == 'system_restart':
            await query.edit_message_text("🔄 **Reiniciando...**")
            await self._perform_restart()
            return
            
        if query.data in ['view_logs', 'view_logs_minimal']:
            # Centralized log viewing logic
            is_minimal = query.data == 'view_logs_minimal'
            try:
                log_path = Path("bot_output.log")
                if log_path.exists():
                    num_lines = 5 if is_minimal else 15
                    with open(log_path, 'r') as f:
                        lines = f.readlines()[-num_lines:]
                    log_content = "".join(lines) or "Log vazio."
                else:
                    log_content = "Arquivo de log não encontrado."
                
                header = "📋 **Logs Recentes:**" if is_minimal else "📜 **Logs do Sistema:**"
                await context.bot.send_message(chat_id, f"{header}\n\n```\n{log_content}\n```", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Erro ao ler logs via botão: {e}")
            return
            
        if query.data == 'help_info':
            await query.edit_message_text(
                "ℹ️ **Ajuda (Libertação Total)**\n"
                "/clip <url> [args] - Criar cortes customizados\n"
                "/autonomous <url> - clipping 100% autônomo\n"
                "/history - Ver vídeos gerados\n"
                "/system - Saúde do servidor\n"
                "/logs - Ver logs para debug\n"
                "/cancel - Parar processamento atual\n"
                "/nuke - RESET TOTAL DO SISTEMA\n"
                "/restart - Reiniciar bot",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Handle Cancel Signal from Progress Bar
        if query.data == 'cancel_process':
            # Reusing the cancel_command logic partially but with query update
            process = self.active_processes.get(chat_id)
            if process:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError: pass
                    
                    if chat_id in self.active_processes:
                        del self.active_processes[chat_id]
                    
                    await query.edit_message_text("🛑 **Processo interrompido e cancelado!**", parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    logger.error(f"Erro ao cancelar via botão: {e}")
                    await query.edit_message_text(f"⚠️ Erro ao cancelar: {e}")
            else:
                await query.edit_message_text("⚠️ O processo já terminou ou não existe.")
            return

        data = self.pending_approvals.get(chat_id)
        if not data:
            await query.edit_message_text("⚠️ Sessão expirada ou dados perdidos.")
            return

        if query.data == 'approve':
            await query.edit_message_text("🚀 **Iniciando Publicação...**\nConectando aos navegadores (Selenium)...")
            
            # Executar publicação
            results = self.publisher.publish_all(data['video_path'], data['metadata'])
            
            msg = "✅ **Relatório de Publicação:**\n\n"
            for platform, result in results.items():
                msg += f"- {platform.capitalize()}: {result}\n"
            
            await context.bot.send_message(chat_id=chat_id, text=msg)
            
        elif query.data == 'regenerate':
             new_meta = self.metadata_generator.generate_metadata("Regenerated Prompt", 60)
             self.pending_approvals[chat_id]['metadata'] = new_meta
             
             msg_text = (
                f"🎬 **Sugestão de Publicação (Regenerada)**\n\n"
                f"**Título:** {new_meta['title']}\n"
                f"**Descrição:** {new_meta['description']}\n"
                f"**Hashtags:** {' '.join(new_meta['hashtags'])}\n\n"
                f"📊 **Score Viral:** {new_meta['viral_score']}/10"
            )
             keyboard = [
                [InlineKeyboardButton("🚀 APROVAR & POSTAR", callback_data='approve')],
                [InlineKeyboardButton("🔄 Regenerar Texto", callback_data='regenerate')],
                [InlineKeyboardButton("❌ Cancelar", callback_data='cancel')]
            ]
             await query.edit_message_text(text=msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

        elif query.data == 'cancel':
            await query.edit_message_text("❌ Operação cancelada.")
            del self.pending_approvals[chat_id]

if __name__ == '__main__':
    # Ler token de arquivo ou env
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Erro: TELEGRAM_BOT_TOKEN não encontrado nas variáveis de ambiente.")
        sys.exit(1)
        
    bot = VideoClipperBot(token)
    bot.run()
