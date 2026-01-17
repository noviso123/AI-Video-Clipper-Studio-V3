import shutil
import os
import imageio_ffmpeg
from pathlib import Path

def apply_fix():
    try:
        import sys
        source = imageio_ffmpeg.get_ffmpeg_exe()
        
        # Detectar plataforma
        is_windows = sys.platform == "win32"
        
        # Localizar diretório de binários do venv
        if is_windows:
            venv_bin = Path("venv/Scripts").absolute()
            if not venv_bin.exists():
                venv_bin = Path(sys.executable).parent
            dest_name = "ffmpeg.exe"
        else:
            venv_bin = Path("venv/bin").absolute()
            if not venv_bin.exists():
                venv_bin = Path(sys.executable).parent
            dest_name = "ffmpeg"

        dest = venv_bin / dest_name

        print(f"Plataforma: {sys.platform}")
        print(f"Source: {source}")
        print(f"Dest: {dest}")

        if not dest.exists():
            shutil.copy(source, dest)
            # No Linux, garantir permissão de execução
            if not is_windows:
                os.chmod(dest, 0o755)
            print(f"✅ Copied ffmpeg to {venv_bin}")
        else:
            print(f"ℹ️ ffmpeg already exists in {venv_bin}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    apply_fix()
