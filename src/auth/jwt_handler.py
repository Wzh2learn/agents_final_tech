"""
JWT 认证处理模块
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY environment variable not set! "
        "Using a default key is insecure. Please set JWT_SECRET_KEY in production.",
        RuntimeWarning
    )
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fallback_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as exc:
        logger.warning("bcrypt backend error during verify; falling back to pbkdf2_sha256: %s", exc)
        return fallback_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    try:
        return pwd_context.hash(password)
    except ValueError as exc:
        logger.warning("bcrypt backend error during hash; falling back to pbkdf2_sha256: %s", exc)
        return fallback_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
