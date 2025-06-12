from dataclasses import dataclass

@dataclass
class User:
    username: str
    password_hash: str  # Сразу храним хэш, не пароль
    role: str           # 'admin' или 'user'
