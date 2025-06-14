from dotenv import load_dotenv
import os
import logging

load_dotenv()

def get_env_variable(name: str, default: str = "NULL") -> str:
    """
    Функция для безопасного получения переменных окружения.
    Если переменная не найдена, возвращает значение по умолчанию.
    """
    value = os.getenv(name)
    if not value:
        logging.warning(f"Предупреждение: {name} не найден в файле .env. "
              f"Используется значение по умолчанию: {default}"
        )
        return default
    return value


class ENVIRONMENT_VAR:
    """Класс для доступа к переменным окружения в стиле ENVIRONMENT_VAR.KEY"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # Загрузка переменных при инициализации класса
    @property
    def DB_ENCRYPTION_KEY(self) -> bytes:
        """
            Ключ для шифрования Базы Данных приложения
        """
        return get_env_variable("DB_ENCRYPTION_KEY").encode()

    @property
    def LOG_HMAC_KEY(self) -> bytes:
        """
            Ключ для генерации HMAC записей в логирровании
        """
        return get_env_variable("LOG_HMAC_KEY").encode()

    @property
    def PASSWORD_HMAC_KEY(self) -> bytes:
        """
            Ключ для хранения хэшей паролей пользователей в БД
        """
        return get_env_variable("PASSWORD_HMAC_KEY").encode()

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
