"""
Fábrica de Conteúdo Autônomo
Orquestra Ingestão -> Pesquisa -> Agentes -> Roteiro Final
"""
import os
import asyncio
from typing import Optional, Dict
from ..modules.ingestor import get_ingestor
from ..modules.researcher import get_researcher
from ..agents.agents_crew import ContentAgents, ContentTasks, Crew, Process
from ..core.logger import setup_logger

logger = setup_logger(__name__)

class AutonomousFactory:
    """O 'Cérebro' que transforma fontes brutas em vídeos virais"""

    def __init__(self):
        self.ingestor = get_ingestor()
        self.researcher = get_researcher()
        self.agents = ContentAgents()
        self.tasks = ContentTasks()

    async def process_source(self, source: str, is_url: bool = False) -> Dict:
        """Processa uma fonte (Arquivo ou URL) e gera um roteiro viral"""
        try:
            # 1. Ingestão de Dados
            context = ""
            if is_url:
                logger.info(f"🌐 Pesquisando URL: {source}")
                context = await self.researcher.crawl_url(source)
            else:
                logger.info(f"📄 Ingerindo Arquivo: {source}")
                context = self.ingestor.convert_file(source)

            if not context or len(context) < 50:
                return {"error": "Conteúdo insuficiente na fonte fornecida."}

            # 2. Configuração da Crew (Agentes)
            logger.info("🤖 Iniciando Crew de Agentes Offline...")

            research_agent = self.agents.researcher()
            writer_agent = self.agents.scriptwriter()
            director_agent = self.agents.director()
            producer_agent = self.agents.producer()

            # 3. Definição do Pipeline de Tarefas (Fluxo Completo Passo a Passo)
            t1 = self.tasks.research_task(research_agent, context)
            t2 = self.tasks.script_task(writer_agent)
            t3 = self.tasks.visual_task(director_agent)
            t4 = self.tasks.review_task(producer_agent)

            crew = Crew(
                agents=[research_agent, writer_agent, director_agent, producer_agent],
                tasks=[t1, t2, t3, t4],
                process=Process.sequential,
                verbose=True
            )

            # 4. Execução Autônoma
            result = crew.kickoff()
            script_final = str(result)

            logger.info("✅ Roteiro gerado pelos agentes!")

            # 5. Produção do Vídeo Final (Integração Total)
            video_result = await self.produce_video(script_final, source)

            logger.info("✅ Fábrica Autônoma Concluída com Vídeo!")

            return {
                "success": True,
                "context_preview": context[:500],
                "final_script": script_final,
                "video_result": video_result,
                "source": source
            }

        except Exception as e:
            logger.error(f"❌ Erro Crítico na Fábrica: {e}")
            return {"error": str(e)}

    async def produce_video(self, script: str, source_name: str) -> Dict:
        """Transforma o roteiro em um vídeo real com Inteligência Total (Voz + Crop + Legenda)"""
        try:
            from ..modules.narrator import get_narrator
            from ..modules.broll import BRollManager
            from ..modules.captions import DynamicCaptions
            from ..modules.transcriber import AudioTranscriber
            from moviepy.editor import ColorClip, AudioFileClip, VideoFileClip, TextClip, CompositeVideoClip
            import time

            logger.info("🎬 Iniciando Produção INTELIGENTE do Vídeo...")
            narrator = get_narrator()
            broll_manager = BRollManager()
            captions_gen = DynamicCaptions(style='hormozi')

            # 1. Gerar Áudio Multi-Voz (Narração Neural Kokoro Inteligente)
            output_id = f"auto_{int(time.time())}"
            audio_path = os.path.join(os.getcwd(), 'temp', f"{output_id}.mp3")

            # Limpar marcações técnicas que NÃO devem ser faladas (ex: [B-Roll], [Corte])
            import re
            speech_script = re.sub(r'\[(B-Roll|Corte|Legenda|Visual|Transição).*?\]', '', script, flags=re.IGNORECASE)

            # Garantir que temos marcadores de voz. Se não houver nenhum, assume Michael.
            if '[VOICE:' not in speech_script.upper():
                speech_script = f"[VOICE: michael] {speech_script}"

            if not narrator.generate_multi_voice_narration(speech_script, audio_path):
                return {"error": "Falha na geração de áudio multi-voz"}

            # 2. Transcrição para obter timestamps WORD-LEVEL
            logger.info("🎙️ Transcrevendo narração para sincronia de legendas...")
            transcriber = AudioTranscriber(model_name="base")
            segments = transcriber.transcribe(audio_path)

            # Extrair palavras individuais para o efeito Hormozi
            all_words = []
            for s in segments:
                if 'words' in s:
                    all_words.extend(s['words'])
                else:
                    # Fallback: estimar timestamps se o whisper não retornou word-level
                    words = s['text'].split()
                    duration = s['end'] - s['start']
                    for i, w in enumerate(words):
                        all_words.append({
                            'word': w,
                            'start': s['start'] + (i / len(words)) * duration,
                            'end': s['start'] + ((i + 1) / len(words)) * duration
                        })

            # 3. Criar Fundo e Sincronizar Áudio
            audio = AudioFileClip(audio_path)
            duration = audio.duration

            # Fundo Cinematográfico (9:16)
            # Em um fluxo 100% inteligente, se tivermos um vídeo de fundo, usaríamos crop_mode='face'
            # Como é gerado do zero, usamos um fundo sólido + B-Rolls
            bg = ColorClip(size=(720, 1280), color=(10, 10, 25), duration=duration)
            bg = bg.set_audio(audio)

            # 4. Adicionar B-Rolls Inteligentes (Keyword based + Instruções do Agente)
            # Prioridade para o que o Diretor pediu explicitamente
            agent_brolls = broll_manager.parse_agent_instructions(script, segments)
            auto_brolls = broll_manager.detect_broll_moments(segments)

            # Mesclar (Agent brolls primeiro)
            all_broll_moments = agent_brolls + auto_brolls
            final_video = broll_manager.add_brolls_to_clip(bg, all_broll_moments)

            # 5. Adicionar Legendas Dinâmicas (Inteligência de Posicionamento)
            logger.info("📝 Aplicando Legendas Dinâmicas Inteligentes...")
            final_video = captions_gen.create_captions(final_video, all_words, position='auto')

            # 6. Renderizar Vídeo Final
            video_path = os.path.join(os.getcwd(), 'exports', f"{output_id}.mp4")
            logger.info(f"⏳ Renderizando Vídeo Totalmente Automático: {video_path}")

            final_video.write_videofile(
                video_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                logger=None,
                threads=4
            )

            # Limpeza manual de objetos MoviePy (evita memory leaks)
            audio.close()
            final_video.close()
            bg.close()

            return {
                "success": True,
                "video_url": f"/exports/{output_id}.mp4",
                "path": video_path,
                "duration": duration,
                "script_preview": script[:100] + "..."
            }

        except Exception as e:
            logger.error(f"❌ Erro na produção inteligente: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def run(self, source: str, is_url: bool = False) -> Dict:
        """Síncrono para integração rápida"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(self.process_source(source, is_url))
            loop.close()
            return res
        except Exception as e:
            return {"error": str(e)}

# Singleton
factory = None
def get_factory() -> AutonomousFactory:
    global factory
    if factory is None:
        factory = AutonomousFactory()
    return factory
