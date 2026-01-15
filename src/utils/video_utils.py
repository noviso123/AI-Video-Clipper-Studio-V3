"""
Utilitários para processamento de vídeo
"""
from typing import Tuple
from pathlib import Path


def format_time(seconds: float) -> str:
    """
    Formata segundos como HH:MM:SS

    Args:
        seconds: Tempo em segundos

    Returns:
        String formatada
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """
    Formata tamanho de arquivo em formato legível

    Args:
        bytes_size: Tamanho em bytes

    Returns:
        String formatada (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def calculate_video_aspect_ratio(width: int, height: int) -> Tuple[int, int]:
    """
    Calcula a proporção de aspecto de um vídeo

    Args:
        width: Largura do vídeo
        height: Altura do vídeo

    Returns:
        Tupla (numerador, denominador) da proporção
    """
    from math import gcd

    divisor = gcd(width, height)
    return (width // divisor, height // divisor)


def is_vertical_video(width: int, height: int) -> bool:
    """
    Verifica se o vídeo é vertical

    Args:
        width: Largura do vídeo
        height: Altura do vídeo

    Returns:
        True se vertical (altura > largura)
    """
    return height > width


def ensure_dir(path: Path) -> Path:
    """
    Garante que um diretório existe, criando se necessário

    Args:
        path: Caminho do diretório

    Returns:
        Path do diretório
    """
    path.mkdir(exist_ok=True, parents=True)
    return path
