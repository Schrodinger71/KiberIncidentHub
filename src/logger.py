import logging
import sys
from logging.handlers import RotatingFileHandler

from cryptography.hazmat.primitives import hashes, hmac

from config.secrets import LOG_HMAC_KEY


class HMACLogFilter(logging.Filter):
    """Добавляет HMAC к лог-сообщениям"""
    def filter(self, record):
        h = hmac.HMAC(LOG_HMAC_KEY, hashes.SHA256())
        h.update(record.msg.encode())
        record.hmac = h.finalize().hex()
        return True

class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консоли"""

    COLORS = {
        'DEBUG': '\033[94m',     # Синий
        'INFO': '\033[92m',      # Зелёный
        'WARNING': '\033[93m',   # Жёлтый
        'ERROR': '\033[91m',     # Красный
        'CRITICAL': '\033[95m',  # Пурпурный
        'RESET': '\033[0m',      # Сброс цвета
        'DATE': '\033[93m'       # Жёлтый для времени
    }

    def formatTime(self, record, datefmt=None):
        """Переопределённый метод для добавления цвета к дате"""
        base_time = super().formatTime(record, datefmt)
        return f"{self.COLORS['DATE']}{base_time}{self.COLORS['RESET']}"

    def format(self, record):
        level_color = self.COLORS.get(record.levelname.strip(), self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{level_color}{record.levelname}{reset}"
        return super().format(record)

def configure_logging():
    """Настройка безопасного логгирования"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-20s | HMAC:%(hmac)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый лог
    file_handler = RotatingFileHandler(
        "data/audit.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.addFilter(HMACLogFilter())
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Цветной консольный лог
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.addFilter(HMACLogFilter())
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-20s | HMAC:%(hmac)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logging.info("Инициализировано безопасное логгирование")
