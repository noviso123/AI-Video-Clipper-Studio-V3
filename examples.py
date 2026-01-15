"""
Script de Exemplo - AI Video Clipper
Demonstração de uso básico do sistema
"""
import sys
from pathlib import Path

# Exemplo de URLs para testar (vídeos curtos e dinâmicos)
EXAMPLE_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up (3:32)
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (0:19) - primeiro vídeo do YouTube
]

def print_banner():
    """Exibe banner de boas-vindas"""
    print("\n" + "=" * 70)
    print("  🎬 AI VIDEO CLIPPER - Script de Exemplo")
    print("=" * 70)
    print()
    print("Este script demonstra como usar o sistema de forma programática.")
    print("Você pode adaptar este código para seus próprios casos de uso.")
    print()

def example_basic_usage():
    """Exemplo 1: Uso básico"""
    print("📌 EXEMPLO 1: Uso Básico")
    print("-" * 70)
    print()
    print("Para processar um vídeo do YouTube, use:")
    print()
    print('  python main.py --url "URL_DO_VIDEO" --clips 3')
    print()
    print("Isso irá:")
    print("  1. Baixar o vídeo")
    print("  2. Transcrever com Whisper")
    print("  3. Identificar 3 momentos virais")
    print("  4. Gerar 3 clipes em formato 9:16")
    print()
    input("Pressione ENTER para continuar...")

def example_quality_settings():
    """Exemplo 2: Ajustar qualidade"""
    print("\n📌 EXEMPLO 2: Ajustar Qualidade")
    print("-" * 70)
    print()
    print("Para vídeos de alta qualidade (PC forte):")
    print()
    print('  python main.py --url "URL" --whisper-model small --clips 5')
    print()
    print("Para processamento rápido (PC fraco):")
    print()
    print('  python main.py --url "URL" --whisper-model tiny --clips 3')
    print()
    input("Pressione ENTER para continuar...")

def example_custom_output():
    """Exemplo 3: Diretório customizado"""
    print("\n📌 EXEMPLO 3: Diretório de Saída Customizado")
    print("-" * 70)
    print()
    print("Para organizar projetos por pasta:")
    print()
    print('  python main.py --url "URL" --output ./projeto1 --keep-temp')
    print()
    print("Isso salvará os clipes em './projeto1/' e manterá arquivos temporários")
    print()
    input("Pressione ENTER para continuar...")

def example_batch_processing():
    """Exemplo 4: Processamento em lote"""
    print("\n📌 EXEMPLO 4: Processar Múltiplos Vídeos")
    print("-" * 70)
    print()
    print("Crie um arquivo 'urls.txt' com uma URL por linha:")
    print()
    print("  https://youtube.com/watch?v=VIDEO1")
    print("  https://youtube.com/watch?v=VIDEO2")
    print("  https://youtube.com/watch?v=VIDEO3")
    print()
    print("Depois execute:")
    print()
    print("  Windows PowerShell:")
    print('    Get-Content urls.txt | ForEach-Object { python main.py --url $_ }')
    print()
    print("  Linux/Mac:")
    print('    while read url; do python main.py --url "$url"; done < urls.txt')
    print()
    input("Pressione ENTER para continuar...")

def example_programmatic():
    """Exemplo 5: Uso programático"""
    print("\n📌 EXEMPLO 5: Uso Programático em Python")
    print("-" * 70)
    print()
    print("Você pode importar os módulos diretamente:")
    print()
    code = '''
# Adicionar src ao path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Importar módulos
from src.modules.downloader import VideoDownloader
from src.modules.transcriber import AudioTranscriber
from src.agents.curator import CuratorAgent

# Usar os módulos
downloader = VideoDownloader()
video_data = downloader.download_video("URL_DO_VIDEO")

transcriber = AudioTranscriber(model_name='base')
segments = transcriber.transcribe(video_data['audio_path'])

curator = CuratorAgent()
moments = curator.curate_moments(
    video_data['audio_path'],
    segments,
    num_clips=3
)

print(f"Encontrados {len(moments)} momentos virais!")
for i, moment in enumerate(moments, 1):
    print(f"{i}. {moment['hook']} (Score: {moment['score']}/10)")
'''
    print(code)
    input("Pressione ENTER para continuar...")

def run_demo():
    """Demonstração interativa"""
    print("\n📌 DEMONSTRAÇÃO INTERATIVA")
    print("-" * 70)
    print()
    print("Quer processar um vídeo de exemplo AGORA?")
    print()
    print("Vídeo de teste: Rick Astley - Never Gonna Give You Up (3:32)")
    print("URL:", EXAMPLE_URLS[0])
    print()

    response = input("Processar este vídeo? (s/n): ").lower()

    if response == 's':
        print()
        print("Processando vídeo de exemplo...")
        print()

        import subprocess

        cmd = [
            'python', 'main.py',
            '--url', EXAMPLE_URLS[0],
            '--clips', '2',
            '--whisper-model', 'tiny',
        ]

        print("Comando:", ' '.join(cmd))
        print()

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar: {e}")
        except FileNotFoundError:
            print("Certifique-se de que está no diretório correto e que o ambiente virtual está ativado")
    else:
        print()
        print("OK! Você pode executar manualmente:")
        print(f'  python main.py --url "{EXAMPLE_URLS[0]}" --clips 2')

def show_menu():
    """Menu principal"""
    print_banner()

    while True:
        print("\n📋 MENU DE EXEMPLOS")
        print("-" * 70)
        print("1. Uso Básico")
        print("2. Ajustar Qualidade")
        print("3. Diretório Customizado")
        print("4. Processamento em Lote")
        print("5. Uso Programático")
        print("6. Demonstração Interativa")
        print("0. Sair")
        print()

        choice = input("Escolha uma opção: ")

        if choice == '1':
            example_basic_usage()
        elif choice == '2':
            example_quality_settings()
        elif choice == '3':
            example_custom_output()
        elif choice == '4':
            example_batch_processing()
        elif choice == '5':
            example_programmatic()
        elif choice == '6':
            run_demo()
        elif choice == '0':
            print()
            print("👋 Até logo! Divirta-se criando clipes virais!")
            print()
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
        sys.exit(0)
