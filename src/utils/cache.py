"""
简单内存缓存工具
用于缓存频繁访问的数据，减少数据库查询
"""
import time
import threading
from typing import Any, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


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
                "total_keys": len(self._cache),
                "keys": list(self._cache.keys())
            }


# 全局缓存实例
_cache_instance = SimpleCache()


def get_cache() -> SimpleCache:
    """获取缓存实例"""
    global _cache_instance
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
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝试从缓存获取
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
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
