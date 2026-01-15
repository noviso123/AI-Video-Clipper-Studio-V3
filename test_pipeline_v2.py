#!/usr/bin/env python3
"""
Teste Completo do Pipeline V2
Testa todas as correções implementadas:
- Face tracking
- Detecção de legendas
- Thumbnail com busca de rostos
- Crop inteligente
"""
import sys
import os
sys.path.insert(0, '/home/ubuntu/AI-Video-Clipper-Studio-V3')

from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)

def test_full_pipeline():
    """Executa teste completo do pipeline."""
    
    print("=" * 60)
    print("🧪 TESTE COMPLETO DO PIPELINE V2")
    print("=" * 60)
    
    # Caminho do vídeo de teste
    video_path = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/temp/teste_video.mp4")
    
    if not video_path.exists():
        # Copiar do upload
        import shutil
        src = Path("/home/ubuntu/upload/YTDown.com_YouTube_Me-de-10-minutos-e-eu-te-ensino-a-VIVER_Media_VOCi5P1PZsI_001_1080p(1).mp4")
        if src.exists():
            video_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, video_path)
            print(f"✅ Vídeo copiado para: {video_path}")
        else:
            print("❌ Vídeo de teste não encontrado!")
            return False
    
    # Criar diretório de exports
    export_dir = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/exports_v2")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # ========== TESTE 1: Detecção de Legendas ==========
    print("\n" + "=" * 60)
    print("📝 TESTE 1: Detecção de Legendas Existentes")
    print("=" * 60)
    
    try:
        from src.modules.subtitle_detector import SubtitleDetector
        detector = SubtitleDetector()
        
        subtitle_result = detector.detect_subtitle_regions(video_path, sample_count=10)
        
        print(f"   Legendas detectadas: {subtitle_result.get('has_subtitles')}")
        print(f"   Posição: {subtitle_result.get('subtitle_position')}")
        print(f"   Confiança: {subtitle_result.get('confidence', 0):.1%}")
        print(f"   Sugestão para novas legendas: {subtitle_result.get('suggested_new_position')}")
        print(f"   Scores por região: {subtitle_result.get('region_scores')}")
        
        results['subtitle_detection'] = '✅ OK'
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        results['subtitle_detection'] = f'❌ {e}'
    
    # ========== TESTE 2: Thumbnail com busca de rostos ==========
    print("\n" + "=" * 60)
    print("🖼️ TESTE 2: Geração de Thumbnail (busca rostos em todo vídeo)")
    print("=" * 60)
    
    try:
        from src.modules.thumbnail_generator import ThumbnailGenerator
        thumb_gen = ThumbnailGenerator()
        
        # Momento de teste (segundos 30-60 onde provavelmente tem pessoa)
        moment = {
            'start': 30,
            'end': 60,
            'hook': 'Como viver melhor'
        }
        
        thumb_path = export_dir / "thumbnail_v2.jpg"
        result = thumb_gen.generate_thumbnail(
            video_path,
            moment,
            thumb_path,
            vertical=True
        )
        
        if result and result.exists():
            print(f"   ✅ Thumbnail gerada: {result}")
            print(f"   Tamanho: {result.stat().st_size / 1024:.1f} KB")
            results['thumbnail'] = '✅ OK'
        else:
            print("   ❌ Falha ao gerar thumbnail")
            results['thumbnail'] = '❌ Falha'
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        results['thumbnail'] = f'❌ {e}'
    
    # ========== TESTE 3: Criação de Clipe com Face Tracking ==========
    print("\n" + "=" * 60)
    print("🎬 TESTE 3: Criação de Clipe (Face Tracking + Detecção Legendas)")
    print("=" * 60)
    
    try:
        from src.modules.editor import VideoEditor
        editor = VideoEditor()
        
        # Criar clipe de 30-50 segundos (onde provavelmente tem pessoa)
        clip_path = export_dir / "clip_v2_face_tracking.mp4"
        
        result = editor.create_clip(
            video_path,
            start_time=30,
            end_time=50,
            output_path=clip_path,
            crop_mode='face_tracking'
        )
        
        if result and result.exists():
            print(f"   ✅ Clipe gerado: {result}")
            print(f"   Tamanho: {result.stat().st_size / 1024 / 1024:.2f} MB")
            results['clip_face_tracking'] = '✅ OK'
            
            # Extrair frames para visualização
            import cv2
            cap = cv2.VideoCapture(str(result))
            frames_dir = export_dir / "frames_v2"
            frames_dir.mkdir(exist_ok=True)
            
            # Pegar 5 frames distribuídos
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            for i, frame_idx in enumerate([0, total_frames//4, total_frames//2, 3*total_frames//4, total_frames-1]):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(str(frames_dir / f"frame_{i+1:02d}.jpg"), frame)
            cap.release()
            print(f"   📸 Frames extraídos em: {frames_dir}")
        else:
            print("   ❌ Falha ao gerar clipe")
            results['clip_face_tracking'] = '❌ Falha'
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        results['clip_face_tracking'] = f'❌ {e}'
    
    # ========== TESTE 4: Clipe com Crop Otimizado (sem rostos) ==========
    print("\n" + "=" * 60)
    print("🎬 TESTE 4: Clipe com Crop Otimizado (início do vídeo - sem rostos)")
    print("=" * 60)
    
    try:
        clip_path2 = export_dir / "clip_v2_optimized.mp4"
        
        result = editor.create_clip(
            video_path,
            start_time=0,
            end_time=15,
            output_path=clip_path2,
            crop_mode='face_tracking'  # Deve usar fallback otimizado
        )
        
        if result and result.exists():
            print(f"   ✅ Clipe gerado: {result}")
            print(f"   Tamanho: {result.stat().st_size / 1024 / 1024:.2f} MB")
            results['clip_optimized'] = '✅ OK'
        else:
            print("   ❌ Falha ao gerar clipe")
            results['clip_optimized'] = '❌ Falha'
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        results['clip_optimized'] = f'❌ {e}'
    
    # ========== RESUMO ==========
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for test, status in results.items():
        print(f"   {test}: {status}")
    
    all_passed = all('✅' in str(v) for v in results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
    print("=" * 60)
    
    print(f"\n📁 Arquivos gerados em: {export_dir}")
    
    # Listar arquivos gerados
    print("\n📄 Arquivos gerados:")
    for f in export_dir.rglob("*"):
        if f.is_file():
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.2f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            print(f"   {f.relative_to(export_dir)}: {size_str}")
    
    return all_passed


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
