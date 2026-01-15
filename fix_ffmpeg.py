import shutil
import os
import imageio_ffmpeg
from pathlib import Path

def apply_fix():
    try:
        source = imageio_ffmpeg.get_ffmpeg_exe()
        # Assume venv structure
        venv_scripts = Path("venv/Scripts").absolute()
        if not venv_scripts.exists():
            # Try to find python executable path and use its dir
            import sys
            venv_scripts = Path(sys.executable).parent

        dest = venv_scripts / "ffmpeg.exe"

        print(f"Source: {source}")
        print(f"Dest: {dest}")

        if not dest.exists():
            shutil.copy(source, dest)
            print("✅ Copied ffmpeg.exe to venv/Scripts")
        else:
            print("ℹ️ ffmpeg.exe already exists in venv/Scripts")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    apply_fix()
