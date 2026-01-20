"""
AI Video Clipper - Script Principal (Corrigido & Otimizado)
Fluxo Linear: Download -> Transcrição -> Análise (Ollama) -> Edição -> Legendas -> Thumbnail
"""
import argparse
import sys
import os
import json
from pathlib import Path
from moviepy.editor import VideoFileClip

# Fix PATH para FFmpeg
os.environ["PATH"] += os.pathsep + os.path.dirname(sys.executable)

# UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Caminhos
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import Config
from src.core.logger import setup_logger
from src.modules.downloader import VideoDownloader
from src.modules.transcriber import AudioTranscriber
from src.modules.editor import VideoEditor
from src.modules.analyzer import ViralAnalyzer
from src.modules.captions import DynamicCaptions
from src.modules.thumbnail_generator import ThumbnailGenerator
from src.modules.narrator import get_narrator
from src.agents.orchestrator import OrchestratorAgent

logger = setup_logger("Main")

def main():
    parser = argparse.ArgumentParser(description="🎬 AI Video Clipper - 100% Local & Open Source")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="URL do vídeo (YouTube, TikTok, etc)")
    source_group.add_argument("--file", help="Caminho para vídeo local")

    parser.add_argument("--clips", type=int, default=3, help="Número de clipes")
    parser.add_argument("--min", type=int, default=30, help="Duração mínima (segundos)")
    parser.add_argument("--max", type=int, default=60, help="Duração máxima (segundos)")
    parser.add_argument("--captions", action="store_true", help="Adicionar legendas")
    parser.add_argument("--voice", action="store_true", help="Adicionar narração intro (PT-BR)")

    args = parser.parse_args()
    Config.ensure_directories()

    try:
        # --- STAGE 1: AQUISIÇÃO ---
        logger.info("=" * 50)
        logger.info("STAGE 1: AQUISIÇÃO DE VÍDEO")
        logger.info("=" * 50)

        if args.url:
            downloader = VideoDownloader()
            video_data = downloader.download_video(args.url)
        else:
            local_path = Path(args.file).resolve()
            if not local_path.exists():
                raise FileNotFoundError(f"Vídeo não encontrado: {local_path}")

            # Estrutura de video_data consistente
            audio_path = Config.TEMP_DIR / f"{local_path.stem}.mp3"
            video_data = {
                'video_path': local_path,
                'audio_path': audio_path,
                'metadata': {
                    'video_id': local_path.stem,
                    'title': local_path.stem.replace('_', ' ').title(),
                    'duration': 0
                }
            }

            # Extrair duração e audio
            try:
                v_clip = VideoFileClip(str(local_path))
                video_data['metadata']['duration'] = int(v_clip.duration)

                if not audio_path.exists():
                    logger.info("🎵 Extraindo áudio do vídeo local...")
                    v_clip.audio.write_audiofile(str(audio_path), logger=None)
                    logger.info(f"✅ Áudio salvo: {audio_path.name}")

                v_clip.close()
            except Exception as e:
                logger.error(f"❌ Erro ao processar vídeo: {e}")
                raise

        logger.info(f"📹 Vídeo: {video_data['metadata']['title']}")
        logger.info(f"⏱️  Duração: {video_data['metadata']['duration']}s")

        # --- STAGE 2: TRANSCRIÇÃO (LOCAL) ---
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 2: TRANSCRIÇÃO (VOSK)")
        logger.info("=" * 50)

        transcriber = AudioTranscriber()
        segments = transcriber.transcribe(video_data['audio_path'])

        if not segments or len(segments) == 0:
            raise ValueError("❌ Nenhum texto foi transcrito. Verifique o áudio.")

        logger.info(f"✅ Transcrição concluída: {len(segments)} segmentos")

        # --- STAGE 3: PLANEJAMENTO & ANÁLISE (OLLAMA) ---
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 3: ANÁLISE VIRAL (OLLAMA)")
        logger.info("=" * 50)

        orchestrator = OrchestratorAgent()
        full_text = " ".join([s.get('text', '') for s in segments])
        editing_plan = orchestrator.plan_video(full_text, video_data['metadata']['duration'])

        logger.info(f"🎨 Vibe: {editing_plan.get('video_vibe', 'N/A')}")

        analyzer = ViralAnalyzer()
        viral_moments = analyzer.analyze_transcript(segments, min_duration=args.min, max_duration=args.max)

        if not viral_moments:
            raise ValueError("❌ Nenhum momento viral detectado. Tente com outro vídeo.")

        viral_moments = viral_moments[:args.clips]
        logger.info(f"🔥 {len(viral_moments)} momentos virais identificados")

        # --- STAGE 4: EDIÇÃO & PROCESSAMENTO ---
        logger.info("")
        logger.info("=" * 50)
        logger.info("STAGE 4: EDIÇÃO 9:16")
        logger.info("=" * 50)

        editor = VideoEditor()
        thumb_gen = ThumbnailGenerator()
        capt_gen = DynamicCaptions() if args.captions else None
        narrator = get_narrator() if args.voice else None

        output_dir = Config.EXPORT_DIR
        generated_clips = []

        for i, moment in enumerate(viral_moments, 1):
            try:
                logger.info(f"\n🎥 Clipe {i}/{len(viral_moments)}: {moment.get('hook', 'Sem hook')}")

                clip_path = output_dir / f"clip_{i:02d}.mp4"
                thumb_path = output_dir / f"thumb_{i:02d}.jpg"
                meta_path = output_dir / f"meta_{i:02d}.json"

                # 1. Thumbnail (Gerar ANTES da edição para usar na intro)
                thumb_gen.generate_thumbnail(
                    video_data['video_path'],  # Vídeo original
                    moment,  # Momento completo com 'start'
                    thumb_path
                )
                logger.info(f"   🖼️  Thumbnail: {thumb_path.name}")

                # 2. Edição (Crop 9:16 + Intro com Thumb e Summary + Legendas)
                result = editor.create_clip(
                    video_data['video_path'],
                    moment['start'],
                    moment['end'],
                    clip_path,
                    thumbnail_path=thumb_path,
                    segments=segments,  # Passar transcrição para legendas
                    add_captions=True
                )

                # 5. Metadados
                metadata = moment.get('metadata', {
                    'title': f"Clipe {i}",
                    'hashtags': ['#viral'],
                    'description': moment.get('hook', '')
                })

                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

                logger.info(f"   ✅ Clipe gerado com sucesso: {clip_path}")
                generated_clips.append(clip_path)

            except Exception as e:
                logger.error(f"   ❌ Erro no clipe {i}: {e}")
                continue

        logger.info("")
        logger.info("=" * 50)
        logger.info(f"✅ CONCLUÍDO! {len(generated_clips)}/{len(viral_moments)} clipes em {output_dir}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ Erro Fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
