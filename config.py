import logging
import os

from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name: str, default: str = None) -> str:
    """
    Получает переменную окружения. Если не найдена и default=None - вызывает ошибку.
    """
    value = os.getenv(name)
    if value is None:
        if default is None:
            logging.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Переменная {name} обязательна!")
            raise ValueError(f"Не найдена обязательная переменная: {name}")
        logging.warning(f"Предупреждение: {name} не найден. Используется default: {default}")
        return default
    return value


class ENVIRONMENT_VAR:
    """Класс для доступа к переменным окружения"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def DB_ENCRYPTION_KEY(self) -> bytes:
        """Ключ для шифрования БД (обязательный)"""
        key = get_env_variable("DB_ENCRYPTION_KEY")  # Без default - вызовет ошибку если нет
        return key.encode()

    @property
    def LOG_HMAC_KEY(self) -> bytes:
        """Ключ для логирования (обязательный)"""
        key = get_env_variable("LOG_HMAC_KEY")
        return key.encode()

    @property
    def PASSWORD_HMAC_KEY(self) -> bytes:
        """Ключ для паролей (обязательный)"""
        key = get_env_variable("PASSWORD_HMAC_KEY")
        return key.encode()

# Инициализация класса
env_cfg = ENVIRONMENT_VAR()
"""Класс для доступа к переменным окружения в стиле ENVIRONMENT_VAR.KEY"""


# # Генерация ключей:
# import base64
# import os

# # DB_ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32))
# # LOG_HMAC_KEY = base64.urlsafe_b64encode(os.urandom(32))
# # PASSWORD_HMAC_KEY = base64.urlsafe_b64encode(os.urandom(32))

# # print(f"DB_ENCRYPTION_KEY = {DB_ENCRYPTION_KEY!r}")
# # print(f"LOG_HMAC_KEY = {LOG_HMAC_KEY!r}")
# # print(f"PASSWORD_HMAC_KEY = {PASSWORD_HMAC_KEY!r}")
