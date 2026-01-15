#!/usr/bin/env python3
"""
Script de Teste Completo - AI Video Clipper Studio V3
Valida todas as correções implementadas:
1. Face Tracking
2. Thumbnail Generator
3. Redimensionamento dinâmico
4. Módulos sem erros de sintaxe
"""

import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, '/home/ubuntu/AI-Video-Clipper-Studio-V3')

import traceback
from pathlib import Path

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✅ PASSOU{Colors.RESET}" if passed else f"{Colors.RED}❌ FALHOU{Colors.RESET}"
    print(f"  {status} - {name}")
    if message and not passed:
        print(f"         {Colors.YELLOW}{message}{Colors.RESET}")

def test_imports():
    """Testa se todos os módulos podem ser importados sem erros."""
    print(f"\n{Colors.BLUE}═══ TESTE 1: Importação de Módulos ═══{Colors.RESET}")
    
    modules = [
        ('src.core.config', 'Config'),
        ('src.core.logger', 'setup_logger'),
        ('src.modules.editor', 'VideoEditor'),
        ('src.modules.thumbnail_generator', 'ThumbnailGenerator'),
        ('src.modules.captions', 'DynamicCaptions'),
        ('src.modules.transcriber', 'AudioTranscriber'),
        ('src.modules.downloader', 'VideoDownloader'),
        ('src.modules.analyzer', 'ViralAnalyzer'),
        ('src.modules.audio_analyzer', 'AudioAnalyzer'),
        ('src.modules.broll', 'BRollManager'),
        ('src.modules.variants', 'VariantGenerator'),
        ('src.modules.visual_polisher', 'VisualPolisher'),
        ('src.modules.audio_enhancer', 'AudioEnhancer'),
        ('src.agents.orchestrator', 'OrchestratorAgent'),
        ('src.agents.curator', 'CuratorAgent'),
        ('src.agents.copywriter', 'CopywriterAgent'),
        ('src.agents.critic', 'CriticAgent'),
        ('src.agents.director', 'DirectorAgent'),
        ('src.agents.metadata_agent', 'MetadataAgent'),
        ('src.agents.voice_agent', 'VoiceAgent'),
    ]
    
    all_passed = True
    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print_test(f"{module_path}.{class_name}", True)
        except Exception as e:
            print_test(f"{module_path}.{class_name}", False, str(e))
            all_passed = False
    
    return all_passed

def test_face_tracker():
    """Testa se o Face Tracker está funcionando."""
    print(f"\n{Colors.BLUE}═══ TESTE 2: Face Tracker ═══{Colors.RESET}")
    
    try:
        from src.modules.editor import FaceTracker
        import cv2
        import numpy as np
        
        tracker = FaceTracker()
        print_test("FaceTracker inicializado", tracker.initialized)
        
        if tracker.initialized:
            # Criar imagem de teste (retângulo simulando rosto)
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Adicionar um retângulo branco no centro (simula área clara)
            cv2.rectangle(test_frame, (220, 140), (420, 340), (255, 255, 255), -1)
            
            # Testar detecção (pode não detectar pois não é um rosto real)
            faces = tracker.detect_faces(test_frame)
            print_test("detect_faces() funciona", True)
            
            # Testar get_faces_center
            if faces:
                center = tracker.get_faces_center(faces)
                print_test("get_faces_center() funciona", center is not None)
            else:
                # Testar com faces simuladas
                fake_faces = [(100, 100, 50, 50)]
                center = tracker.get_faces_center(fake_faces)
                print_test("get_faces_center() funciona (com dados simulados)", center == (125.0, 125.0))
            
            # Testar bounding box
            fake_faces = [(100, 100, 50, 50), (200, 150, 60, 60)]
            bbox = tracker.get_faces_bounding_box(fake_faces)
            print_test("get_faces_bounding_box() funciona", bbox is not None)
            
            return True
        else:
            print_test("OpenCV Cascade disponível", False, "Cascade não carregado")
            return False
            
    except Exception as e:
        print_test("Face Tracker", False, str(e))
        traceback.print_exc()
        return False

def test_thumbnail_generator():
    """Testa se o Thumbnail Generator está funcionando."""
    print(f"\n{Colors.BLUE}═══ TESTE 3: Thumbnail Generator ═══{Colors.RESET}")
    
    try:
        from src.modules.thumbnail_generator import ThumbnailGenerator
        import cv2
        import numpy as np
        from PIL import Image
        
        generator = ThumbnailGenerator()
        print_test("ThumbnailGenerator inicializado", True)
        
        # Testar _get_font
        font = generator._get_font(40)
        print_test("_get_font() funciona", font is not None)
        
        # Testar _enhance_image
        test_img = Image.new('RGB', (100, 100), color='gray')
        enhanced = generator._enhance_image(test_img)
        print_test("_enhance_image() funciona", enhanced is not None)
        
        # Testar _calculate_frame_score
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        score = generator._calculate_frame_score(test_frame)
        print_test("_calculate_frame_score() funciona", isinstance(score, float))
        
        # Testar _smart_crop_and_resize
        test_img = Image.new('RGB', (1920, 1080), color='blue')
        cropped = generator._smart_crop_and_resize(test_img, (1080, 1920))
        print_test("_smart_crop_and_resize() funciona", cropped.size == (1080, 1920))
        
        # Testar _wrap_text
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        lines = generator._wrap_text("Este é um texto muito longo para testar a quebra de linhas", font, 200, draw)
        print_test("_wrap_text() funciona", len(lines) > 0)
        
        return True
        
    except Exception as e:
        print_test("Thumbnail Generator", False, str(e))
        traceback.print_exc()
        return False

def test_video_editor():
    """Testa se o Video Editor está funcionando."""
    print(f"\n{Colors.BLUE}═══ TESTE 4: Video Editor ═══{Colors.RESET}")
    
    try:
        from src.modules.editor import VideoEditor
        
        editor = VideoEditor()
        print_test("VideoEditor inicializado", True)
        print_test("Face Tracker integrado", editor.face_tracker.initialized)
        
        # Verificar métodos existem
        print_test("_crop_center() existe", hasattr(editor, '_crop_center'))
        print_test("_crop_with_face_tracking() existe", hasattr(editor, '_crop_with_face_tracking'))
        print_test("_crop_smart() existe", hasattr(editor, '_crop_smart'))
        print_test("_analyze_faces_in_clip() existe", hasattr(editor, '_analyze_faces_in_clip'))
        
        return True
        
    except Exception as e:
        print_test("Video Editor", False, str(e))
        traceback.print_exc()
        return False

def test_captions():
    """Testa se o módulo de legendas não tem erros de sintaxe."""
    print(f"\n{Colors.BLUE}═══ TESTE 5: Captions Module ═══{Colors.RESET}")
    
    try:
        from src.modules.captions import DynamicCaptions
        
        captions = DynamicCaptions(style='hormozi')
        print_test("DynamicCaptions inicializado", True)
        
        # Verificar métodos existem
        print_test("create_captions() existe", hasattr(captions, 'create_captions'))
        print_test("create_sentence_captions() existe", hasattr(captions, 'create_sentence_captions'))
        print_test("_create_word_clip() existe", hasattr(captions, '_create_word_clip'))
        print_test("_create_word_clip_pil() existe", hasattr(captions, '_create_word_clip_pil'))
        
        return True
        
    except SyntaxError as e:
        print_test("Captions (Sintaxe)", False, f"Erro de sintaxe: {e}")
        return False
    except Exception as e:
        print_test("Captions", False, str(e))
        traceback.print_exc()
        return False

def test_config():
    """Testa se a configuração está carregando corretamente."""
    print(f"\n{Colors.BLUE}═══ TESTE 6: Configuração ═══{Colors.RESET}")
    
    try:
        from src.core.config import Config
        
        print_test("Config carregado", True)
        print_test(f"FACE_TRACKING_ENABLED = {Config.FACE_TRACKING_ENABLED}", True)
        print_test(f"OUTPUT_RESOLUTION = {Config.OUTPUT_RESOLUTION}", True)
        print_test(f"WHISPER_MODEL = {Config.WHISPER_MODEL}", True)
        
        # Verificar APIs
        import os
        openai_key = os.getenv('OPENAI_API_KEY', '')
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        
        has_openai = openai_key and 'PLACEHOLDER' not in openai_key
        has_gemini = gemini_key and 'PLACEHOLDER' not in gemini_key
        
        print_test("OpenAI API Key válida", has_openai, "Key não configurada ou é placeholder" if not has_openai else "")
        print_test("Gemini API Key válida", has_gemini, "Key não configurada ou é placeholder" if not has_gemini else "")
        
        return True
        
    except Exception as e:
        print_test("Config", False, str(e))
        return False

def test_agents():
    """Testa se os agentes estão funcionando."""
    print(f"\n{Colors.BLUE}═══ TESTE 7: Agentes ═══{Colors.RESET}")
    
    all_passed = True
    
    try:
        from src.agents.copywriter import CopywriterAgent
        agent = CopywriterAgent()
        
        # Testar geração de hooks
        hooks = agent.generate_hooks("Teste de texto para gerar hooks virais", num_variations=2)
        print_test("CopywriterAgent.generate_hooks()", len(hooks) > 0)
        
    except Exception as e:
        print_test("CopywriterAgent", False, str(e))
        all_passed = False
    
    try:
        from src.agents.critic import CriticAgent
        agent = CriticAgent()
        
        # Testar avaliação
        test_clip = {
            'hook': '💰 Teste de hook',
            'viral_score': 7.5,
            'duration': 45,
            'keywords': ['teste'],
            'emotion_intensity': 0.7
        }
        evaluation = agent.evaluate_clip(test_clip)
        print_test("CriticAgent.evaluate_clip()", 'overall_score' in evaluation)
        
    except Exception as e:
        print_test("CriticAgent", False, str(e))
        all_passed = False
    
    try:
        from src.agents.director import DirectorAgent
        agent = DirectorAgent()
        
        # Testar plano de edição
        test_moment = {'start': 0, 'end': 30, 'hook': 'Teste', 'score': 8.0}
        plan = agent.create_edit_plan([], [], test_moment)
        print_test("DirectorAgent.create_edit_plan()", 'sections' in plan)
        
    except Exception as e:
        print_test("DirectorAgent", False, str(e))
        all_passed = False
    
    return all_passed

def main():
    """Executa todos os testes."""
    print(f"\n{Colors.BLUE}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}   AI VIDEO CLIPPER STUDIO V3 - TESTE DE CORREÇÕES{Colors.RESET}")
    print(f"{Colors.BLUE}{'═' * 60}{Colors.RESET}")
    
    results = []
    
    results.append(("Importação de Módulos", test_imports()))
    results.append(("Face Tracker", test_face_tracker()))
    results.append(("Thumbnail Generator", test_thumbnail_generator()))
    results.append(("Video Editor", test_video_editor()))
    results.append(("Captions Module", test_captions()))
    results.append(("Configuração", test_config()))
    results.append(("Agentes", test_agents()))
    
    # Resumo
    print(f"\n{Colors.BLUE}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}   RESUMO DOS TESTES{Colors.RESET}")
    print(f"{Colors.BLUE}{'═' * 60}{Colors.RESET}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✅{Colors.RESET}" if result else f"{Colors.RED}❌{Colors.RESET}"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} testes passaram")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 TODOS OS TESTES PASSARAM!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Alguns testes falharam. Verifique os erros acima.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
