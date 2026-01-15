#!/usr/bin/env python3
"""
Teste Completo de Ponta a Ponta - AI Video Clipper Studio V3
Processa um vídeo real e identifica bugs no pipeline.
"""

import sys
import os
import time
import traceback

sys.path.insert(0, '/home/ubuntu/AI-Video-Clipper-Studio-V3')

from pathlib import Path

# Configurar variáveis de ambiente
os.environ['PYTHONPATH'] = '/home/ubuntu/AI-Video-Clipper-Studio-V3'

def test_full_pipeline():
    """Executa o pipeline completo em um vídeo de teste."""
    
    video_path = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/temp/video_teste.mp4")
    export_dir = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/exports")
    
    print("=" * 60)
    print("  TESTE COMPLETO DE PONTA A PONTA")
    print("=" * 60)
    print(f"\nVídeo: {video_path.name}")
    print(f"Duração: ~5 min 42s (342s)")
    print(f"Resolução: 1920x1080")
    print()
    
    errors = []
    warnings = []
    
    # ========== ETAPA 1: Extrair Áudio ==========
    print("\n[1/7] 🎵 Extraindo áudio...")
    audio_path = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/temp/audio_teste.mp3")
    try:
        import subprocess
        result = subprocess.run([
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
            str(audio_path)
        ], capture_output=True, text=True, timeout=120)
        
        if audio_path.exists():
            print(f"      ✅ Áudio extraído: {audio_path.name}")
        else:
            errors.append("Falha ao extrair áudio")
            print(f"      ❌ Falha ao extrair áudio")
    except Exception as e:
        errors.append(f"Extração de áudio: {e}")
        print(f"      ❌ Erro: {e}")
    
    # ========== ETAPA 2: Transcrição (apenas 30s para teste rápido) ==========
    print("\n[2/7] 🎤 Transcrevendo áudio (primeiros 60s)...")
    segments = []
    try:
        from src.modules.transcriber import AudioTranscriber
        
        # Extrair apenas 60s de áudio para teste rápido
        audio_short = Path("/home/ubuntu/AI-Video-Clipper-Studio-V3/temp/audio_short.mp3")
        subprocess.run([
            'ffmpeg', '-y', '-i', str(audio_path),
            '-t', '60', '-acodec', 'libmp3lame',
            str(audio_short)
        ], capture_output=True, timeout=30)
        
        transcriber = AudioTranscriber(model_name='tiny')  # Modelo rápido para teste
        segments = transcriber.transcribe(audio_short)
        
        print(f"      ✅ Transcrição concluída: {len(segments)} segmentos")
        if segments:
            print(f"      Exemplo: \"{segments[0]['text'][:50]}...\"")
    except Exception as e:
        errors.append(f"Transcrição: {e}")
        print(f"      ❌ Erro: {e}")
        traceback.print_exc()
    
    # ========== ETAPA 3: Análise de Emoção ==========
    print("\n[3/7] 🎭 Analisando emoções do áudio...")
    emotion_peaks = []
    try:
        from src.modules.audio_analyzer import AudioEmotionAnalyzer
        
        analyzer = AudioEmotionAnalyzer()
        emotion_peaks = analyzer.detect_emotion_peaks(audio_short if audio_short.exists() else audio_path)
        
        print(f"      ✅ Picos emocionais: {len(emotion_peaks)}")
    except Exception as e:
        warnings.append(f"Análise de emoção: {e}")
        print(f"      ⚠️ Aviso: {e}")
    
    # ========== ETAPA 4: Análise Viral ==========
    print("\n[4/7] 📊 Analisando momentos virais...")
    viral_moments = []
    try:
        from src.modules.analyzer import ViralAnalyzer
        
        analyzer = ViralAnalyzer()
        viral_moments = analyzer.find_viral_moments(segments, emotion_peaks)
        
        print(f"      ✅ Momentos virais: {len(viral_moments)}")
        for i, moment in enumerate(viral_moments[:3], 1):
            print(f"         {i}. Score: {moment.get('score', 0):.1f} | {moment.get('start', 0):.1f}s-{moment.get('end', 0):.1f}s")
    except Exception as e:
        errors.append(f"Análise viral: {e}")
        print(f"      ❌ Erro: {e}")
        traceback.print_exc()
    
    # ========== ETAPA 5: Criar Clipe com Face Tracking ==========
    print("\n[5/7] ✂️ Criando clipe com face tracking...")
    clip_path = None
    try:
        from src.modules.editor import VideoEditor
        
        editor = VideoEditor()
        
        # Usar primeiro momento viral ou criar um padrão
        if viral_moments:
            moment = viral_moments[0]
            start = moment.get('start', 0)
            end = min(moment.get('end', 30), start + 30)  # Máximo 30s
        else:
            start = 10
            end = 40
        
        clip_path = export_dir / "clip_teste_face_tracking.mp4"
        
        result = editor.create_clip(
            video_path=video_path,
            start_time=start,
            end_time=end,
            output_path=clip_path,
            crop_mode='face_tracking'
        )
        
        if clip_path.exists():
            # Verificar tamanho do arquivo
            size_mb = clip_path.stat().st_size / (1024 * 1024)
            print(f"      ✅ Clipe criado: {clip_path.name} ({size_mb:.1f} MB)")
            
            # Verificar resolução
            probe = subprocess.run([
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(clip_path)
            ], capture_output=True, text=True)
            
            resolution = probe.stdout.strip()
            print(f"      Resolução: {resolution}")
            
            if resolution != "1080,1920":
                warnings.append(f"Resolução incorreta: {resolution} (esperado: 1080,1920)")
        else:
            errors.append("Clipe não foi criado")
            print(f"      ❌ Clipe não foi criado")
            
    except Exception as e:
        errors.append(f"Criação de clipe: {e}")
        print(f"      ❌ Erro: {e}")
        traceback.print_exc()
    
    # ========== ETAPA 6: Gerar Thumbnail ==========
    print("\n[6/7] 🖼️ Gerando thumbnail...")
    thumb_path = None
    try:
        from src.modules.thumbnail_generator import ThumbnailGenerator
        
        generator = ThumbnailGenerator()
        
        moment = {
            'start': start if 'start' in dir() else 10,
            'end': end if 'end' in dir() else 40,
            'hook': 'COMO VIVER DE VERDADE'
        }
        
        thumb_path = export_dir / "thumbnail_teste.jpg"
        
        result = generator.generate_thumbnail(
            video_path=video_path,
            moment=moment,
            output_path=thumb_path,
            vertical=True
        )
        
        if thumb_path.exists():
            # Verificar dimensões da thumbnail
            from PIL import Image
            img = Image.open(thumb_path)
            width, height = img.size
            
            print(f"      ✅ Thumbnail criada: {thumb_path.name}")
            print(f"      Dimensões: {width}x{height}")
            
            if (width, height) != (1080, 1920):
                warnings.append(f"Dimensões da thumbnail incorretas: {width}x{height}")
        else:
            errors.append("Thumbnail não foi criada")
            print(f"      ❌ Thumbnail não foi criada")
            
    except Exception as e:
        errors.append(f"Geração de thumbnail: {e}")
        print(f"      ❌ Erro: {e}")
        traceback.print_exc()
    
    # ========== ETAPA 7: Gerar Hooks ==========
    print("\n[7/7] ✍️ Gerando hooks virais...")
    try:
        from src.agents.copywriter import CopywriterAgent
        
        agent = CopywriterAgent()
        
        text = segments[0]['text'] if segments else "Como viver de verdade em 10 minutos"
        hooks = agent.generate_hooks(text, num_variations=3)
        
        print(f"      ✅ Hooks gerados: {len(hooks)}")
        for hook in hooks[:3]:
            print(f"         - {hook.get('hook', '')[:50]}...")
            
    except Exception as e:
        warnings.append(f"Geração de hooks: {e}")
        print(f"      ⚠️ Aviso: {e}")
    
    # ========== RESUMO ==========
    print("\n" + "=" * 60)
    print("  RESUMO DO TESTE")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERROS ({len(errors)}):")
        for err in errors:
            print(f"   - {err}")
    
    if warnings:
        print(f"\n⚠️ AVISOS ({len(warnings)}):")
        for warn in warnings:
            print(f"   - {warn}")
    
    if not errors and not warnings:
        print("\n✅ TODOS OS TESTES PASSARAM SEM PROBLEMAS!")
    elif not errors:
        print("\n✅ Pipeline executado com sucesso (com avisos)")
    else:
        print("\n❌ Pipeline com erros - correções necessárias")
    
    # Listar arquivos gerados
    print("\n📁 Arquivos gerados:")
    for f in export_dir.glob("*"):
        size = f.stat().st_size / 1024
        print(f"   - {f.name} ({size:.1f} KB)")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
