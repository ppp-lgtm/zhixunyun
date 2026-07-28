import hashlib
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.config import get_settings

_settings = get_settings()

SECRET_KEY = _settings.JWT_SECRET
ALGORITHM = _settings.JWT_ALGORITHM
EXPIRE_HOURS = _settings.JWT_EXPIRE_HOURS


def hash_password(password: str) -> str:
    """使用 sha256 + 随机盐 哈希密码"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    if not hashed or "$" not in hashed:
        return False
    salt, stored = hashed.split("$", 1)
    return stored == hashlib.sha256((password + salt).encode()).hexdigest()


def create_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    payload = {"user_id": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
