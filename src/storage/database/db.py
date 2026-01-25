import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import logging
logger = logging.getLogger(__name__)

MAX_RETRY_TIME = 20  # 连接最大重试时间（秒）
# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def get_db_url() -> str:
    """Build database URL from environment."""
    url = os.getenv("PGDATABASE_URL") or ""
    if url is not None and url != "":
        # Ensure it uses psycopg (v3) driver if it starts with postgresql://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    if not url:
        logger.error("PGDATABASE_URL is not set")
    return url
_engine = None
_SessionLocal = None

def _create_engine_with_retry():
    url = get_db_url()
    if url is None or url == "":
        logger.error("PGDATABASE_URL is not set")
        raise ValueError("PGDATABASE_URL is not set")
    
    # 从环境变量读取连接池配置，默认使用合理值
    import os
    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    recycle = 1800
    timeout = 30
    
    # 限制最小值，防止配置过小
    pool_size = max(1, min(pool_size, 20))
    max_overflow = max(0, min(max_overflow, 20))
    
    logger.info(f"Database pool config: pool_size={pool_size}, max_overflow={max_overflow}")
    
    engine = create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=recycle,
        pool_timeout=timeout,
    )
    # 验证连接，带重试
    start_time = time.time()
    last_error = None
    while time.time() - start_time < MAX_RETRY_TIME:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except OperationalError as e:
            last_error = e
            elapsed = time.time() - start_time
            logger.warning(f"Database connection failed, retrying... (elapsed: {elapsed:.1f}s)")
            time.sleep(min(1, MAX_RETRY_TIME - elapsed))
    logger.error(f"Database connection failed after {MAX_RETRY_TIME}s: {last_error}")
    raise last_error

def get_engine():
    global _engine
    if _engine is None:
        _engine = _create_engine_with_retry()
    return _engine

def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_session():
    return get_sessionmaker()()

__all__ = [
    "get_db_url",
    "get_engine",
    "get_sessionmaker",
    "get_session",
]
