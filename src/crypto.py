# Copyright 2025 Schrodinger71
# Licensed under the Apache License, Version 2.0 (see LICENSE file)

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, hmac

from config import env_cfg


class CryptoManager:
    def __init__(self):
        # Ключ для шифрования/дешифровки (Fernet)
        self.cipher = Fernet(env_cfg.DB_ENCRYPTION_KEY)
        
        
        # Ключ для HMAC хэширования паролей
        self.hmac_key = env_cfg.PASSWORD_HMAC_KEY

    def encrypt(self, data: str) -> str:
        """Шифрование строковых данных"""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Расшифровка данных"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()

    def hash_password(self, password: str) -> str:
        """
        Хэширует пароль с помощью HMAC + SHA256.
        Возвращает hex-строку.
        """
        h = hmac.HMAC(self.hmac_key, hashes.SHA256())
        h.update(password.encode())
        return h.finalize().hex()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Проверяет, что пароль совпадает с хэшом.
        Возвращает True или False.
        """
        h = hmac.HMAC(self.hmac_key, hashes.SHA256())
        h.update(password.encode())
        try:
            h.verify(bytes.fromhex(password_hash))
            return True
        except Exception:
            return False
