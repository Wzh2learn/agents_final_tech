"""
缓存 API 路由
"""
from fastapi import APIRouter
from utils.cache import get_cache

router = APIRouter()


@router.get("/stats")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return {"status": "success", "cache": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/clear")
async def clear_cache():
    """清空缓存"""
    try:
        cache = get_cache()
        cache.clear()
        return {"status": "success", "message": "缓存已清空"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
