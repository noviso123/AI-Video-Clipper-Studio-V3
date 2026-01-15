#!/usr/bin/env python3
"""
Teste Completo do Pipeline V3
Testa o novo sistema de crop inteligente com letterbox
"""
import sys
import os
sys.path.insert(0, '/home/ubuntu/AI-Video-Clipper-Studio-V3')

from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')

def test_v3():
    print("=" * 60)
    print("🧪 TESTE V3 - CROP INTELIGENTE COM LETTERBOX")
    print("=" * 60)
    
    video_path = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/temp/teste_video.mp4")
    export_dir = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/exports_v3")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    from src.modules.editor import VideoEditor
    editor = VideoEditor()
    
    # Teste 1: Modo AUTO (deve escolher letterbox para este vídeo)
    print("\n" + "=" * 60)
    print("🎬 TESTE 1: Modo AUTO (30-50s)")
    print("=" * 60)
    
    clip1 = editor.create_clip(
        video_path,
        start_time=30,
        end_time=50,
        output_path=export_dir / "clip_v3_auto.mp4",
        crop_mode='auto'
    )
    
    # Teste 2: Modo LETTERBOX explícito (0-15s - intro)
    print("\n" + "=" * 60)
    print("🎬 TESTE 2: Modo LETTERBOX (0-15s)")
    print("=" * 60)
    
    clip2 = editor.create_clip(
        video_path,
        start_time=0,
        end_time=15,
        output_path=export_dir / "clip_v3_letterbox.mp4",
        crop_mode='letterbox'
    )
    
    # Extrair frames para visualização
    print("\n📸 Extraindo frames...")
    import cv2
    
    frames_dir = export_dir / "frames_v3"
    frames_dir.mkdir(exist_ok=True)
    
    for clip_name in ["clip_v3_auto.mp4", "clip_v3_letterbox.mp4"]:
        clip_path = export_dir / clip_name
        if clip_path.exists():
            cap = cv2.VideoCapture(str(clip_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Frame do meio
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            ret, frame = cap.read()
            if ret:
                output_name = clip_name.replace('.mp4', '_mid.jpg')
                cv2.imwrite(str(frames_dir / output_name), frame)
                print(f"   ✅ {output_name}")
            cap.release()
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 ARQUIVOS GERADOS:")
    print("=" * 60)
    
    for f in export_dir.rglob("*"):
        if f.is_file():
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.2f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            print(f"   {f.name}: {size_str}")
    
    print("\n✅ Teste V3 concluído!")
    return True


if __name__ == "__main__":
    test_v3()
