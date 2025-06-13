import logging
import sys
from logging.handlers import RotatingFileHandler
from cryptography.hazmat.primitives import hashes, hmac
from config.secrets import LOG_HMAC_KEY


class HMACLogFilter(logging.Filter):
    """Добавляет HMAC к лог-сообщениям с возможностью сокращения"""
    def __init__(self, short_hmac=False):
        super().__init__()
        self.short_hmac = short_hmac
    
    def filter(self, record):
        h = hmac.HMAC(LOG_HMAC_KEY, hashes.SHA256())
        h.update(record.msg.encode())
        full_hmac = h.finalize().hex()
        
        if self.short_hmac:
            # Сокращаем HMAC до первых 8 символов для консоли
            record.hmac = f"{full_hmac[:8]}..."
        else:
            # Полный HMAC для файла
            record.hmac = full_hmac
        return True


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консоли с датой и сокращенным HMAC"""
    COLORS = {
        'DEBUG': '\033[94m',     # Синий
        'INFO': '\033[92m',      # Зелёный
        'WARNING': '\033[93m',   # Жёлтый
        'ERROR': '\033[91m',     # Красный
        'CRITICAL': '\033[95m',  # Пурпурный
        'RESET': '\033[0m',      # Сброс цвета
        'DATE': '\033[93m',      # Жёлтый для времени
        'HMAC': '\033[90m'       # Серый для HMAC
    }

    def formatTime(self, record, datefmt=None):
        """Цветное форматирование времени"""
        base_time = super().formatTime(record, datefmt)
        return f"{self.COLORS['DATE']}{base_time}{self.COLORS['RESET']}"

    def format(self, record):
        level_color = self.COLORS.get(record.levelname.strip(), self.COLORS['RESET'])
        hmac_color = self.COLORS['HMAC']
        reset = self.COLORS['RESET']
        
        # Форматируем сообщение с цветами
        record.levelname = f"{level_color}{record.levelname}{reset}"
        record.hmac = f"{hmac_color}{record.hmac}{reset}"
        
        return super().format(record)


def configure_logging():
    """Настройка безопасного логгирования"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Базовый формат с датой (одинаковый для файла и консоли)
    log_format = '%(asctime)s | %(levelname)-8s | HMAC:%(hmac)s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 1. Файловый лог (полный HMAC)
    file_handler = RotatingFileHandler(
        "data/audit.log",
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.addFilter(HMACLogFilter(short_hmac=False))
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(file_handler)

    # 2. Консольный лог (сокращенный HMAC + цвета)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.addFilter(HMACLogFilter(short_hmac=True))
    console_handler.setFormatter(ColoredFormatter(log_format, datefmt=date_format))
    logger.addHandler(console_handler)

    logging.info("Инициализировано безопасное логгирование")