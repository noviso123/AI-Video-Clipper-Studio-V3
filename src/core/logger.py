"""
Sistema de logging centralizado
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from .config import Config

class ColoredFormatter(logging.Formatter):
    """Formatter com cores para terminal"""

    COLORS = {
        'DEBUG': '\033[36m',    # Ciano
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarelo
        'ERROR': '\033[31m',    # Vermelho
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logger(name: str = "AI-VideoClipper") -> logging.Logger:
    """
    Configura e retorna um logger com formatação personalizada

    Args:
        name: Nome do logger

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if Config.DEBUG_MODE else logging.INFO)

    console_format = ColoredFormatter(
        '%(levelname)s | %(asctime)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Handler para arquivo (se não estiver em modo debug)
    if not Config.DEBUG_MODE:
        log_dir = Config.BASE_DIR / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"clipper_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            '%(levelname)s | %(asctime)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger

# Logger padrão
logger = setup_logger()
