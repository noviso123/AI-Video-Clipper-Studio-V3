"""
Script de Hotfix para MoviePy (Python 3.12+)
Corrige Warnings de Sintaxe (Invalid Escape Sequence) diretamente no source instalado.
"""
import site
import os
import glob
from pathlib import Path

def patch_moviepy():
    # Encontrar instalação do MoviePy
    site_packages = site.getsitepackages()
    moviepy_path = None

    for sp in site_packages:
        path = Path(sp) / "moviepy"
        if path.exists():
            moviepy_path = path
            break

    if not moviepy_path:
        print("❌ MoviePy não encontrado nos site-packages.")
        return

    print(f"🔧 Aplicando patch em: {moviepy_path}")

    # Arquivos conhecidos com problema
    targets = [
        "config_defaults.py",
        "video/io/ffmpeg_reader.py"
    ]

    replaced_count = 0

    for relative_path in targets:
        file_path = moviepy_path / relative_path
        if not file_path.exists():
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Apply regex fixes
            # 1. config_defaults.py: invalid escape sequence \'\P\'
            new_content = content.replace("IMAGEMAGICK_BINARY = r\"", "IMAGEMAGICK_BINARY = r\"") # No-op check

            # Corrections (escaping backslashes in non-raw strings usually, but here likely regex)
            # Python 3.12 complains about invalid escapes.
            # Fix: Convert sensitive regex strings to raw strings or escape backslashes

            # Specific fixes based on user logs:

            # ffmpeg_reader.py:294: lines_video = [l for l in lines if ' Video: ' in l and re.search('\d+x\d+', l)]
            if "re.search('\\d+x\\d+', l)" in content: # Already escaped? Mmm
               pass

            # We will use simple string replacement for the known bad lines

            # Fix 1: ffmpeg_reader.py video dimension regex
            # Original might be: re.search('\d+x\d+', l) -> re.search(r'\d+x\d+', l)
            if "re.search('\\d+x\\d+', l)" in content:
                 new_content = new_content.replace("re.search('\\d+x\\d+', l)", "re.search(r'\\d+x\\d+', l)")
            elif 're.search(\'\\d+x\\d+\', l)' in content:
                 new_content = new_content.replace('re.search(\'\\d+x\\d+\', l)', 're.search(r\'\\d+x\\d+\', l)')

            # Fix 2: rotation regex
            # match = re.search('\d+$', rotation_line)
            if "re.search('\\d+$', rotation_line)" in content:
                new_content = new_content.replace("re.search('\\d+$', rotation_line)", "re.search(r'\\d+$', rotation_line)")
            elif "re.search('\\d+$'," in content: # variation
                new_content = new_content.replace("re.search('\\d+$',", "re.search(r'\\d+$',")

            # Generic safe replace common patterns if specific fails
            new_content = new_content.replace("re.search('\\d+", "re.search(r'\\d+")
            new_content = new_content.replace('re.search("\\d+', 're.search(r"\\d+')

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Corrigido: {relative_path}")
                replaced_count += 1
            else:
                print(f"ℹ️  Nenhuma alteração necessária em: {relative_path}")

        except Exception as e:
            print(f"⚠️ Erro ao corrigir {relative_path}: {e}")

    if replaced_count > 0:
        print("✨ Hotfix aplicado com sucesso!")
    else:
        print("🔍 Nenhuma correção aplicada (talvez já corrigido ou versão diferente).")

if __name__ == "__main__":
    patch_moviepy()
