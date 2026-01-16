"""
FastAPI 路由模块
统一管理所有 API 路由
"""
from fastapi import APIRouter

# 创建主路由
api_router = APIRouter()

# 导入子路由（延迟导入避免循环依赖）
def include_routers():
    from web.routers.pages import router as pages_router
    from web.routers.chat import router as chat_router
    from web.routers.knowledge import router as knowledge_router
    from web.routers.collaboration import router as collaboration_router
    from web.routers.cache import router as cache_router
    from auth.router import router as auth_router

    api_router.include_router(pages_router, tags=["页面"])
    api_router.include_router(auth_router, prefix="/api/auth", tags=["认证"])
    api_router.include_router(chat_router, prefix="/api", tags=["聊天"])
    api_router.include_router(knowledge_router, prefix="/api/knowledge", tags=["知识库"])
    api_router.include_router(collaboration_router, prefix="/api/collaboration", tags=["协作"])
    api_router.include_router(cache_router, prefix="/api/cache", tags=["缓存"])
