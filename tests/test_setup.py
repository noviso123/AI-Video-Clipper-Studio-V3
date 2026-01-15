# Testes Rápidos - Validação dos Módulos

from pathlib import Path
import sys

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Testa se todas as importações funcionam"""
    print("🧪 Testando importações...")

    try:
        from src.core.config import Config
        print("✅ Config OK")

        from src.core.logger import setup_logger
        print("✅ Logger OK")

        from src.modules.downloader import VideoDownloader
        print("✅ Downloader OK")

        from src.modules.transcriber import AudioTranscriber
        print("✅ Transcriber OK")

        print("\n✅ Todas as importações funcionaram!")
        return True
    except Exception as e:
        print(f"\n❌ Erro na importação: {e}")
        return False

def test_config():
    """Testa se a configuração está carregando"""
    print("\n🧪 Testando configuração...")

    try:
        from src.core.config import Config

        print(f"   WHISPER_MODEL: {Config.WHISPER_MODEL}")
        print(f"   VIDEO_FPS: {Config.VIDEO_FPS}")
        print(f"   TEMP_DIR: {Config.TEMP_DIR}")
        print(f"   EXPORT_DIR: {Config.EXPORT_DIR}")

        print("\n✅ Configuração OK!")
        return True
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

def test_directories():
    """Testa se os diretórios são criados"""
    print("\n🧪 Testando criação de diretórios...")

    try:
        from src.core.config import Config

        Config.ensure_directories()

        print(f"   temp/: {'✅' if Config.TEMP_DIR.exists() else '❌'}")
        print(f"   exports/: {'✅' if Config.EXPORT_DIR.exists() else '❌'}")
        print(f"   src/assets/: {'✅' if Config.ASSETS_DIR.exists() else '❌'}")
        print(f"   src/assets/fonts/: {'✅' if (Config.ASSETS_DIR / 'fonts').exists() else '❌'}")

        print("\n✅ Diretórios criados!")
        return True
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

def test_ffmpeg():
    """Testa se FFmpeg está instalado"""
    print("\n🧪 Testando FFmpeg...")

    import subprocess

    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True,
                              text=True,
                              timeout=5)

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   {version_line}")
            print("\n✅ FFmpeg OK!")
            return True
        else:
            print("\n❌ FFmpeg não encontrado!")
            return False
    except FileNotFoundError:
        print("\n❌ FFmpeg não está instalado ou não está no PATH")
        print("   Instale: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

def test_whisper():
    """Testa se Whisper está instalado"""
    print("\n🧪 Testando Whisper...")

    try:
        import whisper
        print(f"   Versão: {whisper.__version__ if hasattr(whisper, '__version__') else 'unknown'}")
        print("   Modelos disponíveis:", whisper.available_models())
        print("\n✅ Whisper OK!")
        return True
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🧪 VALIDAÇÃO DO SISTEMA")
    print("="*60)

    results = {
        "Importações": test_imports(),
        "Configuração": test_config(),
        "Diretórios": test_directories(),
        "FFmpeg": test_ffmpeg(),
        "Whisper": test_whisper()
    }

    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)

    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:20s}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema pronto para uso!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        print("   Verifique as mensagens de erro acima e corrija")
        print("   Consulte SETUP.md para mais informações")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_all_tests()
