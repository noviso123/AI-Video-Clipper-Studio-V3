"""
AI Video Clipper - Script Principal
Ponto de entrada para o sistema de clipping automático
"""
import argparse
import sys
import os
import json
from pathlib import Path

# Fix: Injetar venv/Scripts no PATH para Whisper encontrar ffmpeg.exe
try:
    # Adiciona diretório do python (venv/Scripts) ao PATH
    os.environ["PATH"] += os.pathsep + os.path.dirname(sys.executable)
except Exception:
    pass

# Fix Windows Unicode Error (Print Emojis)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import Config
from src.core.logger import setup_logger
from src.modules.downloader import VideoDownloader
from src.modules.transcriber import AudioTranscriber
from src.modules.editor import VideoEditor

logger = setup_logger("Main")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="🎬 AI Video Clipper - Sistema de Clipping Automático",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --url "https://youtube.com/watch?v=..." --clips 3
  python main.py --url "https://youtube.com/watch?v=..." --whisper-model small
  python main.py --url "https://youtube.com/watch?v=..." --clips 5 --no-critic
        """
    )

    # Argumentos
    parser = argparse.ArgumentParser(description="AI Video Clipper - Crie clipes virais automaticamente")

    # Grupo exclusivo: Ou URL ou Arquivo Local
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="URL do vídeo do YouTube")
    source_group.add_argument("--file", help="Caminho para arquivo de vídeo local")

    # Opções Gerais
    parser.add_argument("--clips", type=int, default=3, help="Número de clipes para gerar")
    parser.add_argument("--whisper-model", default=Config.WHISPER_MODEL, help="Modelo do Whisper (tiny, base, small, medium, large)")
    parser.add_argument("--output", help="Diretório de saída customizado")
    parser.add_argument("--keep-temp", action="store_true", help="Manter arquivos temporários")

    # Opções de Processamento
    parser.add_argument("--captions", action="store_true", help="Adicionar legendas dinâmicas")
    parser.add_argument("--caption-style", choices=['hormozi', 'mr_beast', 'minimal'], default='hormozi', help="Estilo da legenda")
    parser.add_argument("--broll", action="store_true", help="Adicionar B-Rolls automáticos")
    parser.add_argument("--variants", action="store_true", help="Gerar variantes para TikTok/Reels/Shorts")
    parser.add_argument("--critic", action="store_true", help="Avaliar qualidade com Agente Crítico")
    parser.add_argument("--no-face-tracking", action="store_true", help="Desativar rastreamento de rosto (crop central fixo)")

    args = parser.parse_args()

    # Banner
    print("\n" + "="*60)
    print("🎬 AI VIDEO CLIPPER - Sistema de Clipping Automático")
    print("="*60 + "\n")

    # Configurar diretórios
    Config.ensure_directories()

    try:
        # =========================================================================
        # STAGE 1: AQUISIÇÃO DO VÍDEO (Download ou Local)
        # =========================================================================
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 1: AQUISIÇÃO DO VÍDEO")
        logger.info("=" * 50)

        video_data = {}

        if args.url:
            # Modo YouTube
            downloader = VideoDownloader()
            try:
                video_data = downloader.download_video(args.url)
                logger.info("")
                logger.info("📊 Informações do Vídeo:")
                logger.info(f"   Título: {video_data['metadata']['title']}")
                logger.info(f"   Canal: {video_data['metadata']['uploader']}")
                logger.info(f"   Duração: {video_data['metadata']['duration']//60}:{video_data['metadata']['duration']%60:02d}")
            except Exception as e:
                logger.error(f"❌ Erro no download: {e}")
                sys.exit(1)

        elif args.file:
            # Modo Arquivo Local
            # Usar resolve() para garantir caminho absoluto correto no Windows
            local_path = Path(args.file).resolve()
            if not local_path.exists():
                logger.error(f"❌ Arquivo não encontrado: {local_path}")
                sys.exit(1)

            logger.info(f"📂 Processando arquivo local: {local_path}")

            # Preparar diretório temporário para extrair audio
            Config.ensure_directories()

            # Verificar se áudio já foi extraído (CHECKPOINT)
            audio_path = Config.TEMP_DIR / f"{local_path.stem}.mp3"

            # Obter duração do vídeo
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(str(local_path))
            video_duration = int(clip.duration)
            clip.close()

            # Simulando video_data
            video_data = {
                'video_id': local_path.stem,
                'metadata': {
                    'video_id': local_path.stem,
                    'title': local_path.stem.replace('_', ' ').title(),
                    'uploader': "Local File",
                    'duration': video_duration
                },
                'video_path': local_path,
                'audio_path': audio_path
            }

            # CHECKPOINT: Verificar se áudio já existe
            if audio_path.exists():
                logger.info("✅ [CHECKPOINT] Áudio já extraído anteriormente!")
                logger.info(f"   Usando: {audio_path.name}")
            else:
                # Extrair áudio para transcrição
                logger.info("🔊 Extraindo áudio do arquivo local...")
                try:
                    clip = VideoFileClip(str(local_path))
                    clip.audio.write_audiofile(str(audio_path), logger=None)
                    clip.close()
                    logger.info("✅ Áudio extraído com sucesso")
                except Exception as e:
                    logger.error(f"❌ Erro ao extrair áudio: {e}")
                    logger.info("   Certifique-se de ter FFmpeg instalado.")
                    sys.exit(1)

            logger.info("")
            logger.info("📊 Informações do Vídeo:")
            logger.info(f"   Título: {video_data['metadata']['title']}")
            logger.info(f"   Canal: {video_data['metadata']['uploader']}")
            logger.info(f"   Duração: {video_duration//60}:{video_duration%60:02d}")

        if not video_data:
            logger.error("❌ Falha no download")
            sys.exit(1)

        # NOTA: Audio Enhancement agora é feito POR CLIP no Stage 4.5 (mais inteligente!)

        # =========================================================================
        # STAGE 2: TRANSCRIÇÃO E ANÁLISE DE AUDIO
        # =========================================================================
        logger.info("")
        logger.info("=" * 50)
        logger.info(f"STAGE 2: TRANSCRIÇÃO (Whisper {args.whisper_model})")
        logger.info("=" * 50)

        video_id = video_data['metadata']['video_id']
        srt_path = Config.TEMP_DIR / f"transcript_{video_id}.srt"
        json_path = Config.TEMP_DIR / f"transcript_{video_id}.json"

        # CHECKPOINT: Verificar se transcrição já existe
        if json_path.exists():
            logger.info("✅ [CHECKPOINT] Transcrição já existe!")
            logger.info(f"   Carregando: {json_path.name}")

            # Carregar transcrição existente
            with open(json_path, 'r', encoding='utf-8') as f:
                segments = json.load(f)

            logger.info(f"   Segmentos carregados: {len(segments)}")

            # Criar transcriber para uso posterior (get_words_in_range)
            whisper_model = args.whisper_model or Config.WHISPER_MODEL
            transcriber = AudioTranscriber(model_name=whisper_model)
            transcriber._segments = segments  # Cache interno
        else:
            # Transcrever do zero
            whisper_model = args.whisper_model or Config.WHISPER_MODEL
            transcriber = AudioTranscriber(model_name=whisper_model)
            segments = transcriber.transcribe(video_data['audio_path'])

            # Exportar transcrição
            transcriber.export_srt(segments, srt_path)
            transcriber.export_json(segments, json_path)

        logger.info(f"   Transcrição salva em: {srt_path.name}")


        # STAGE 2.5: Orquestração (The Brain)
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 2.5: ORQUESTRAÇÃO (AI PLANNING)")
        logger.info("=" * 50)

        from src.agents.orchestrator import OrchestratorAgent

        # Juntar texto completo para análise
        full_transcript = " ".join([s['text'] for s in segments])
        video_duration = video_data['metadata']['duration']

        orchestrator = OrchestratorAgent()
        editing_plan = orchestrator.plan_video(full_transcript, video_duration)

        # Salvar plano para referência
        plan_path = Config.TEMP_DIR / f"plan_{video_id}.json"
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(editing_plan, f, indent=2, ensure_ascii=False)

        logger.info(f"   🧠 Vibe Detectada: {editing_plan.get('video_vibe', 'N/A')}")
        logger.info(f"   🎨 Estilo de Edição: {editing_plan.get('editing_style', 'N/A')}")

        # STAGE 2.6: Narração IA (Se necessário)
        if editing_plan.get('narration_needed') and editing_plan.get('narration_script'):
            logger.info("🎙️ Gerando Narração IA...")
            try:
                from src.agents.voice_agent import VoiceAgent
                voice_agent = VoiceAgent()

                narration_script = editing_plan['narration_script']
                narration_path = Config.TEMP_DIR / f"narration_{video_id}.mp3"

                narration_audio_path = voice_agent.generate_narration(
                    narration_script,
                    narration_path
                )

                if narration_audio_path:
                    # Adicionar ao video_data para uso futuro no editor
                    video_data['narration_path'] = narration_audio_path
                    logger.info(f"   ✅ Narração salva: {narration_audio_path.name}")
            except Exception as e:
                logger.error(f"   ❌ Erro ao gerar narração: {e}")

        # STAGE 3: Análise Viral
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 3: ANÁLISE VIRAL")
        logger.info("=" * 50)

        from src.agents.curator import CuratorAgent

        curator = CuratorAgent()
        viral_moments = curator.curate_moments(
            video_data['audio_path'],
            segments,
            num_clips=args.clips
        )

        if not viral_moments:
            logger.warning("⚠️  Nenhum momento viral identificado")
            logger.info("   Tente com um vídeo diferente ou ajuste VOLUME_THRESHOLD no .env")
            sys.exit(0)

        # Otimização de Hooks com Copywriter (Fase 9)
        from src.agents.copywriter import CopywriterAgent
        copywriter = CopywriterAgent()

        logger.info("\n✍️  Otimizando títulos com Agente Copywriter...")
        for moment in viral_moments:
            original_hook = moment['hook']
            hooks = copywriter.generate_hooks(original_hook, num_variations=1)
            if hooks:
                best_hook = hooks[0]['hook']
                moment['hook'] = best_hook
                logger.info(f"   Original: {original_hook}")
                logger.info(f"   Otimizado: {best_hook}")

        # STAGE 4: Edição de Vídeo
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 4: EDIÇÃO DE VÍDEO")
        logger.info("=" * 50)

        editor = VideoEditor()
        output_dir = Path(args.output) if args.output else Config.EXPORT_DIR
        output_dir.mkdir(exist_ok=True, parents=True)

        logger.info(f"📦 Gerando {len(viral_moments)} clipes verticais 9:16...")
        logger.info(f"   Diretório de saída: {output_dir}")

        generated_clips = []

        for i, moment in enumerate(viral_moments, 1):
            try:
                # Nome do arquivo baseado no score
                clip_filename = f"clip_{i:02d}_score{moment['score']:.1f}.mp4"
                output_path = output_dir / clip_filename

                logger.info(f"\n🎬 Clipe {i}/{len(viral_moments)}: {moment['hook']}")
                logger.info(f"   Tempo: {moment['start']:.1f}s → {moment['end']:.1f}s")

                # Criar clipe
                vibe = editing_plan.get('video_vibe', 'General')
                clip_path = editor.create_clip(
                    video_data['video_path'],
                    moment['start'],
                    moment['end'],
                    output_path,
                    crop_mode='center',
                    vibe=vibe
                )

                # STAGE 4.5: Audio Enhancement (NO CLIP - Não no vídeo inteiro!)
                try:
                    from src.modules.audio_enhancer import AudioEnhancer
                    from moviepy.editor import VideoFileClip, AudioFileClip

                    logger.info(f"   🎚️ Aprimorando áudio do clipe...")

                    # Extrair áudio do clipe
                    temp_audio = Config.TEMP_DIR / f"clip_audio_{i}.mp3"
                    clip_video = VideoFileClip(str(clip_path))
                    clip_video.audio.write_audiofile(str(temp_audio), logger=None)

                    # Aprimorar
                    enhancer = AudioEnhancer()
                    enhanced_audio = temp_audio.with_suffix('.enhanced.mp3')
                    result = enhancer.enhance_audio(temp_audio, enhanced_audio, reduce_noise=True)

                    if result:
                        # Substituir áudio no vídeo
                        new_audio = AudioFileClip(str(enhanced_audio))
                        final_video = clip_video.set_audio(new_audio)

                        # Salvar com áudio melhorado
                        temp_output = clip_path.with_suffix('.enhanced.mp4')
                        final_video.write_videofile(
                            str(temp_output),
                            codec='libx264',
                            audio_codec='aac',
                            fps=Config.VIDEO_FPS,
                            logger=None
                        )

                        clip_video.close()
                        new_audio.close()
                        final_video.close()

                        # Substituir original
                        clip_path.unlink()
                        temp_output.rename(clip_path)

                        logger.info(f"   ✅ Áudio do clipe aprimorado!")
                    else:
                        clip_video.close()

                except Exception as e:
                    logger.warning(f"   ⚠️ Audio Enhancement pulado: {e}")

                generated_clips.append({
                    'path': clip_path,
                    'moment': moment
                })


                # STAGE 5: Gerar Thumbnail (Fase 21)
                try:
                    from src.modules.thumbnail_generator import ThumbnailGenerator
                    thumb_gen = ThumbnailGenerator()
                    thumb_path = output_dir / f"thumb_{i:02d}.jpg"

                    thumb_gen.generate_thumbnail(
                        video_data['video_path'],
                        moment,
                        thumb_path
                    )
                except Exception as e:
                    logger.error(f"   ⚠️ Erro na thumbnail: {e}")

                # STAGE 6: Gerar Metadados Virais (Fase 20)
                try:
                    from src.agents.metadata_agent import MetadataAgent
                    meta_agent = MetadataAgent()

                    # Usar texto do clipe apenas
                    # clip_text = " ".join([s['text'] for s in segments if s['start'] >= moment['start'] and s['end'] <= moment['end']])
                    # Por simplicidade, usando o hook e o transcript geral

                    meta_path = output_dir / f"metadata_{i:02d}.json"
                    metadata = meta_agent.generate_metadata(moment['text'], vibe)

                    if metadata:
                        meta_agent.save_metadata(metadata, meta_path)
                        logger.info(f"   📝 Metadados salvos: {meta_path.with_suffix('.txt').name}")

                except Exception as e:
                     logger.error(f"   ⚠️ Erro nos metadados: {e}")

            except Exception as e:
                logger.error(f"   Erro ao criar clipe {i}: {e}")
                continue

        if not generated_clips:
            logger.error("❌ Nenhum clipe foi gerado com sucesso")
            sys.exit(1)

        # B-Rolls Automáticos (se habilitado)
        if args.broll:
            logger.info("")
            logger.info("=" * 50)
            logger.info("STAGE 4.5: ADICIONANDO B-ROLLS")
            logger.info("=" * 50)

            from src.modules.broll import BRollManager
            from moviepy.editor import VideoFileClip

            broll_manager = BRollManager()

            for clip_data in generated_clips:
                try:
                    clip_path = clip_data['path']
                    moment = clip_data['moment']

                    logger.info(f"\n🎨 B-Rolls para: {clip_path.name}")

                    # Carregar clipe
                    video_clip = VideoFileClip(str(clip_path))

                    # Detectar momentos (extraindo palavras do trecho)
                    clip_words = transcriber.get_words_in_range(
                        segments, moment['start'], moment['end']
                    )

                    # Ajustar timestamps para relativo
                    adjusted_segments = []
                    for w in clip_words:
                        adjusted_segments.append({
                            'text': w['word'],
                            'start': w['start'] - moment['start'],
                            'end': w['end'] - moment['start']
                        })

                    broll_moments = broll_manager.detect_broll_moments(adjusted_segments)

                    if broll_moments:
                        final_clip = broll_manager.add_brolls_to_clip(video_clip, broll_moments)

                        # Salvar temporário e substituir
                        temp_output = clip_path.with_suffix('.broll.mp4')
                        final_clip.write_videofile(
                            str(temp_output),
                            codec='libx264',
                            audio_codec='aac',
                            fps=Config.VIDEO_FPS,
                            logger=None
                        )

                        video_clip.close()
                        final_clip.close()
                        clip_path.unlink()
                        temp_output.rename(clip_path)
                    else:
                        logger.info("   Nenhum momento B-Roll detectado")
                        video_clip.close()

                except Exception as e:
                    logger.error(f"   Erro ao adicionar B-Rolls: {e}")
                    continue

        # STAGE 5: Legendas Dinâmicas (se habilitado)
        if args.captions:
            logger.info("")
            logger.info("=" * 50)
            logger.info("STAGE 5: LEGENDAS DINÂMICAS")
            logger.info("=" * 50)

            from src.modules.captions import DynamicCaptions
            from moviepy.editor import VideoFileClip

            captions_generator = DynamicCaptions(style=args.caption_style)

            for clip_data in generated_clips:
                try:
                    clip_path = clip_data['path']
                    moment = clip_data['moment']

                    logger.info(f"\n📝 Adicionando legendas: {clip_path.name}")

                    # Extrair palavras para o intervalo do clipe
                    words_in_clip = transcriber.get_words_in_range(
                        segments,
                        moment['start'],
                        moment['end']
                    )

                    if words_in_clip:
                        # Ajustar timestamps das palavras (relativo ao início do clipe)
                        adjusted_words = []
                        for word in words_in_clip:
                            adjusted_words.append({
                                'word': word['word'],
                                'start': word['start'] - moment['start'],
                                'end': word['end'] - moment['start']
                            })

                        # Carregar clipe e adicionar legendas
                        video_clip = VideoFileClip(str(clip_path))
                        video_with_captions = captions_generator.create_captions(
                            video_clip,
                            adjusted_words,
                            position='bottom'
                        )

                        # Salvar com legendas (sobrescrever)
                        temp_output = clip_path.with_suffix('.temp.mp4')
                        logger.info(f"   ⏳ Renderizando vídeo final com legendas (Isso pode demorar dependendo do tamanho)...")
                        video_with_captions.write_videofile(
                            str(temp_output),
                            codec='libx264',
                            audio_codec='aac',
                            fps=Config.VIDEO_FPS,
                            logger=None
                        )

                        # Substituir original
                        video_clip.close()
                        video_with_captions.close()
                        clip_path.unlink()
                        temp_output.rename(clip_path)

                        logger.info(f"   ✅ Legendas adicionadas!")
                    else:
                        logger.warning(f"   ⚠️  Nenhuma palavra encontrada no intervalo")

                except Exception as e:
                    logger.error(f"   Erro ao adicionar legendas: {e}")
                    continue

        logger.info("")
        logger.info("=" * 50)
        logger.info("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        logger.info("=" * 50)
        logger.info("")
        logger.info("📊 Estatísticas:")
        logger.info(f"   Vídeo original: {video_data['metadata']['title']}")
        logger.info(f"   Duração: {video_data['metadata']['duration']//60}:{video_data['metadata']['duration']%60:02d}")
        logger.info(f"   Clipes gerados: {len(generated_clips)}/{len(viral_moments)}")
        logger.info("")
        logger.info("📁 Arquivos intermediários:")
        logger.info(f"   Vídeo: {video_data['video_path'].name}")
        logger.info(f"   Áudio: {video_data['audio_path'].name}")
        logger.info(f"   Transcrição: {srt_path.name}")
        logger.info("")
        logger.info("🎬 Clipes finais (prontos para publicar):")
        for i, clip_data in enumerate(generated_clips, 1):
            clip_path = clip_data['path']
            moment = clip_data['moment']
            file_size_mb = clip_path.stat().st_size / (1024 * 1024)
            logger.info(f"   {i}. {clip_path.name} ({file_size_mb:.1f} MB)")
            logger.info(f"      {moment['hook']}")
            logger.info(f"      Score: {moment['score']}/10")
        logger.info("")
        logger.info("💡 Dicas:")
        logger.info("   - Assista os clipes para validar a qualidade")
        logger.info("   - Os clipes já estão em formato 9:16 para TikTok/Reels/Shorts")
        logger.info("   - Use os hooks sugeridos como títulos/descrições")
        logger.info("")

        # Limpeza (se --keep-temp não estiver ativo)
        if not args.keep_temp:
            logger.info("🧹 Para limpar arquivos temporários, delete a pasta 'temp/'")

        # STAGE 6: Gerar Variantes para Plataformas (se habilitado)
        if args.variants:
            logger.info("")
            logger.info("=" * 50)
            logger.info("STAGE 6: GERANDO VARIANTES")
            logger.info("=" * 50)

            from src.modules.variants import VariantGenerator

            variant_gen = VariantGenerator()
            variants_dir = output_dir / "variants"

            for clip_data in generated_clips:
                try:
                    variants = variant_gen.generate_variants(
                        clip_data['path'],
                        variants_dir
                    )
                    logger.info(f"   ✅ {len(variants)} variantes criadas para {clip_data['path'].name}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Erro ao gerar variantes: {e}")

        # STAGE 7: Avaliação pelo Agente Crítico (se habilitado)
        if args.critic:
            logger.info("")
            logger.info("=" * 50)
            logger.info("STAGE 7: AVALIAÇÃO DO AGENTE CRÍTICO")
            logger.info("=" * 50)

            from src.agents.critic import CriticAgent

            critic = CriticAgent()

            for clip_data in generated_clips:
                moment = clip_data['moment']
                evaluation = critic.evaluate_clip({
                    'hook': moment['hook'],
                    'viral_score': moment['score'],
                    'duration': moment['end'] - moment['start'],
                    'keywords': moment.get('keywords', []),
                    'emotion_intensity': moment.get('emotion_intensity', 0.5)
                })

                status = "✅ APROVADO" if evaluation['approved'] else "❌ REJEITADO"
                logger.info(f"   {clip_data['path'].name}: {evaluation['overall_score']}/10 - {status}")

        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 SISTEMA 100% COMPLETO!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("✅ Funcionalidades ativas:")
        logger.info("   • Download YouTube + Transcrição Whisper")
        logger.info("   • Análise viral (emoção + keywords)")
        logger.info("   • Edição automática 9:16")
        if args.captions:
            logger.info("   • Legendas dinâmicas word-level")
        if args.variants:
            logger.info("   • Variantes para TikTok/Reels/Shorts")
        if args.critic:
            logger.info("   • Avaliação do agente crítico")
        logger.info("")
        logger.info("=" * 60)
        logger.info("")

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Erro fatal: {e}")
        if Config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
