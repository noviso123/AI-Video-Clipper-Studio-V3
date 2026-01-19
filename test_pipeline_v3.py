#!/usr/bin/env python3
"""
Teste Completo do Pipeline V3 (Windows + Download)
Testa o novo sistema de crop inteligente com letterbox
"""
import sys
import os
from pathlib import Path
import logging

# Adicionar raiz do projeto ao path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from src.core.config import Config
from src.core.logger import setup_logger
from src.modules.downloader import VideoDownloader
from src.modules.editor import VideoEditor

# Configurar logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')
logger = logging.getLogger("TestV3")

def test_v3():
    print("=" * 60)
    print("🧪 TESTE V3 - CROP INTELIGENTE COM LETTERBOX")
    print("=" * 60)

    # 1. Preparar Diretórios
    Config.ensure_directories()
    temp_dir = Config.TEMP_DIR
    export_dir = BASE_DIR / "exports_v3"
    export_dir.mkdir(parents=True, exist_ok=True)

    # 2. Obter Vídeo de Teste
    video_path = temp_dir / "test_video.mp4"

    if not video_path.exists():
        print("\n🎨 Gerando vídeo sintético para teste...")
        try:
            from moviepy.editor import ColorClip

            # Criar um vídeo de 60 segundos
            duration = 60
            width, height = 1920, 1080

            # Fundo colorido (Azul Escuro)
            clip = ColorClip(size=(width, height), color=(0, 0, 100), duration=duration)
            clip.fps = 30

            # Salvar
            clip.write_videofile(
                str(video_path),
                fps=30,
                codec='libx264',
                audio=False
            )
            print(f"✅ Vídeo sintético gerado: {video_path}")

        except Exception as e:
            print(f"❌ Erro ao gerar vídeo sintético: {e}")
            return False
    else:
        print(f"✅ Vídeo de teste já existe: {video_path}")

    # 3. Inicializar Editor
    print("\n🎬 Inicializando VideoEditor...")
    try:
        editor = VideoEditor()
    except Exception as e:
        print(f"❌ Falha ao inicializar VideoEditor: {e}")
        return False

    # Teste 1: Modo AUTO (0-5s)
    print("\n" + "=" * 60)
    print("🎬 TESTE 1: Modo AUTO (0-5s)")
    print("=" * 60)

    try:
        # Mock Transcription
        mock_transcription = [
            {'start': 0.5, 'end': 1.5, 'text': "Olá mundo"},
            {'start': 1.5, 'end': 2.5, 'text': "Isso é um teste"},
            {'start': 3.0, 'end': 4.0, 'text': "De legendas"}
        ]
        
        clip1 = editor.create_clip(
            video_path,
            start_time=0,
            end_time=5,
            output_path=export_dir / "clip_v3_auto.mp4",
            crop_mode='auto',
            transcription=mock_transcription
        )
        if clip1 and clip1.exists():
             print(f"✅ Clip 1 gerado com sucesso: {clip1}")
        else:
             print("❌ Falha ao gerar Clip 1")
    except Exception as e:
        print(f"❌ Erro Crítico no Clip 1: {e}")
        import traceback
        traceback.print_exc()

    # Teste 2: Modo LETTERBOX explícito (5-10s)
    print("\n" + "=" * 60)
    print("🎬 TESTE 2: Modo LETTERBOX (5-10s)")
    print("=" * 60)

    try:
        clip2 = editor.create_clip(
            video_path,
            start_time=5,
            end_time=10,
            output_path=export_dir / "clip_v3_letterbox.mp4",
            crop_mode='letterbox'
        )
        if clip2 and clip2.exists():
             print(f"✅ Clip 2 gerado com sucesso: {clip2}")
        else:
             print("❌ Falha ao gerar Clip 2")
    except Exception as e:
        print(f"❌ Erro Crítico no Clip 2: {e}")

    # Teste 3: Modo CENTER (10-15s)
    print("\n" + "=" * 60)
    print("🎬 TESTE 3: Modo CENTER (10-15s)")
    print("=" * 60)

    try:
        clip3 = editor.create_clip(
            video_path,
            start_time=10,
            end_time=15,
            output_path=export_dir / "clip_v3_center.mp4",
            crop_mode='center'
        )
        if clip3 and clip3.exists():
             print(f"✅ Clip 3 gerado com sucesso: {clip3}")
        else:
             print("❌ Falha ao gerar Clip 3")

    except Exception as e:
         print(f"❌ Erro Crítico no Clip 3: {e}")


    # Resumo
    print("\n" + "=" * 60)
    print("📊 ARQUIVOS GERADOS:")
    print("=" * 60)

    success_count = 0
    for f in export_dir.glob("*.mp4"):
        if f.is_file():
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.2f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            print(f"   {f.name}: {size_str}")
            success_count += 1

    if success_count >= 1:
        print("\n✅ Teste V3 concluído com SUCESSO! (Pelo menos 1 clipe gerado)")
        return True
    else:
        print("\n❌ Teste V3 falhou: Nenhum clipe gerado.")
        return False


if __name__ == "__main__":
    if test_v3():
        sys.exit(0)
    else:
        sys.exit(1)
