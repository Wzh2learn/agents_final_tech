"""
缓存工具 - 支持内存缓存和 Redis 分布式缓存
"""
import time
import threading
import json
import os
import inspect
from typing import Any, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")  # memory 或 redis


class SimpleCache:
    """简单的内存缓存实现"""

    def __init__(self):
        """初始化缓存"""
        self._cache = {}
        self._locks = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期返回None
        """
        with self._lock:
            if key in self._cache:
                value, expiry_time = self._cache[key]
                if time.time() < expiry_time:
                    logger.debug(f"缓存命中: {key}")
                    return value
                else:
                    # 缓存已过期，删除
                    del self._cache[key]
                    logger.debug(f"缓存过期: {key}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认300秒（5分钟）
        """
        expiry_time = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expiry_time)
            logger.debug(f"缓存设置: {key}, TTL: {ttl}秒")

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"缓存删除: {key}")
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.debug("缓存已清空")

    def cleanup_expired(self) -> int:
        """清理过期缓存

        Returns:
            清理的数量
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry_time) in self._cache.items()
                if expiry_time <= current_time
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"清理过期缓存: {len(expired_keys)} 个")
            return len(expired_keys)

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        with self._lock:
            return {
                "type": "memory",
                "total_keys": len(self._cache),
                "keys": list(self._cache.keys())
            }


class RedisCache:
    """Redis 分布式缓存实现"""

    def __init__(self, redis_url: str = REDIS_URL):
        self._redis = None
        self._redis_url = redis_url
        self._fallback = SimpleCache()
        self._connect()

    def _connect(self):
        """连接 Redis"""
        try:
            import redis
            self._redis = redis.from_url(self._redis_url)
            self._redis.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败，降级到内存缓存: {e}")
            self._redis = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._redis:
            return self._fallback.get(key)
        try:
            value = self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get 失败: {e}")
            return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值"""
        if not self._redis:
            return self._fallback.set(key, value, ttl)
        try:
            self._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error(f"Redis set 失败: {e}")
            self._fallback.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._redis:
            return self._fallback.delete(key)
        try:
            return bool(self._redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete 失败: {e}")
            return self._fallback.delete(key)

    def clear(self) -> None:
        """清空缓存"""
        if not self._redis:
            return self._fallback.clear()
        try:
            self._redis.flushdb()
        except Exception as e:
            logger.error(f"Redis clear 失败: {e}")
            self._fallback.clear()

    def get_stats(self) -> dict:
        """获取缓存统计"""
        if not self._redis:
            stats = self._fallback.get_stats()
            stats["type"] = "memory (fallback)"
            return stats
        try:
            info = self._redis.info()
            return {
                "type": "redis",
                "total_keys": self._redis.dbsize(),
                "used_memory": info.get("used_memory_human", "N/A")
            }
        except:
            return {"type": "redis", "status": "error"}


# 全局缓存实例
_cache_instance = None


def get_cache():
    """获取缓存实例（根据配置选择类型）"""
    global _cache_instance
    if _cache_instance is None:
        if CACHE_TYPE == "redis":
            _cache_instance = RedisCache()
        else:
            _cache_instance = SimpleCache()
    return _cache_instance


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀

    Usage:
        @cached(ttl=60, key_prefix="stats")
        def get_statistics():
            return heavy_computation()
    """
    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
                cache = get_cache()
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    return cached_value

                result = await func(*args, **kwargs)
                cache.set(cache_key, result, ttl)
                return result

            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def cache_key(*args) -> str:
    """
    生成缓存键

    Args:
        *args: 键的组成部分

    Returns:
        缓存键字符串
    """
    return ":".join(str(arg) for arg in args)
