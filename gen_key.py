# Генерация ключей:
import base64
import os

DB_ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32))
LOG_HMAC_KEY = base64.urlsafe_b64encode(os.urandom(32))
PASSWORD_HMAC_KEY = base64.urlsafe_b64encode(os.urandom(32))

print(f"DB_ENCRYPTION_KEY = {DB_ENCRYPTION_KEY!r}")
print(f"LOG_HMAC_KEY = {LOG_HMAC_KEY!r}")
print(f"PASSWORD_HMAC_KEY = {PASSWORD_HMAC_KEY!r}")
