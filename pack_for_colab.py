import os
import zipfile
from pathlib import Path

def zip_project(output_filename="AI_Video_Clipper_V3_Ultimate.zip"):
    """Compacta o projeto para upload no Google Drive, ignorando lixo."""

    root_dir = Path.cwd()
    output_path = root_dir / output_filename

    # O que ignorar
    excludes = {
        '.venv', 'venv', '.git', '.idea', '__pycache__',
        'temp', 'node_modules', '.DS_Store',
        output_filename # Não zipar o próprio zip
    }

    print(f"📦 Compactando projeto em: {output_filename}...")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Filtrar diretórios proibidos in-place
            dirs[:] = [d for d in dirs if d not in excludes]

            for file in files:
                if file in excludes or file.endswith('.pyc'):
                    continue

                file_path = Path(root) / file
                archive_name = file_path.relative_to(root_dir)

                print(f"  + {archive_name}")
                zipf.write(file_path, archive_name)

    print(f"\n✅ Sucesso! Arquivo criado: {output_path}")
    print("👉 Arraste este arquivo para o seu Google Drive para iniciar.")

if __name__ == "__main__":
    zip_project()
