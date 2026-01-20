"""
Script de Upload Automático para Google Drive
Sincroniza projeto completo com o Drive
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

try:
    from google.colab import drive
    IS_COLAB = True
except ImportError:
    IS_COLAB = False

def upload_to_drive():
    """Faz upload do projeto para o Google Drive"""

    if not IS_COLAB:
        print("❌ Este script deve ser executado no Google Colab!")
        print("   Use o notebook AI_Video_Clipper_Colab.ipynb")
        sys.exit(1)

    # Montar Drive
    print("📁 Montando Google Drive...")
    drive.mount('/content/drive', force_remount=True)

    # Caminhos
    project_dir = Path.cwd()
    drive_dir = Path('/content/drive/MyDrive/AI-Video-Clipper-Backup')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = drive_dir / f"backup_{timestamp}"

    # Criar diretóriode backup
    backup_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Fazendo backup do projeto...")
    print(f"   De: {project_dir}")
    print(f"   Para: {backup_dir}")

    # Lista de pastas/arquivos para excluir
    exclude = [
        '__pycache__',
        '.git',
        '.venv',
        'venv',
        'temp',
        '*.pyc',
        '*.pyo',
        '.DS_Store'
    ]

    # Copiar projeto
    total_files = 0
    total_size = 0

    for root, dirs, files in os.walk(project_dir):
        # Filtrar diretórios excluídos
        dirs[:] = [d for d in dirs if d not in exclude]

        for file in files:
            # Pular arquivos excluídos
            if any(file.endswith(ext) for ext in exclude if '*' in ext):
                continue

            src_path = Path(root) / file
            rel_path = src_path.relative_to(project_dir)
            dst_path = backup_dir / rel_path

            # Criar diretório se necessário
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # Copiar arquivo
            shutil.copy2(src_path, dst_path)

            total_files += 1
            total_size += src_path.stat().st_size

            if total_files % 50 == 0:
                print(f"   Copiados: {total_files} arquivos...")

    print("")
    print("=" * 50)
    print("✅ BACKUP CONCLUÍDO!")
    print("=" * 50)
    print(f"📊 Arquivos: {total_files}")
    print(f"💾 Tamanho: {total_size / (1024*1024):.1f} MB")
    print(f"📁 Localização: {backup_dir}")
    print("")

    # Criar link simbólico para o último backup
    latest_link = drive_dir / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(backup_dir)

    print(f"🔗 Link direto: {latest_link}")

if __name__ == "__main__":
    upload_to_drive()
