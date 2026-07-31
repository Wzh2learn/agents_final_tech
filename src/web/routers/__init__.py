"""FastAPI router registry."""

from fastapi import APIRouter


api_router = APIRouter()


def include_routers() -> None:
    """Register all web and API routers."""
    from auth.router import router as auth_router
    from web.routers.cache import router as cache_router
    from web.routers.chat import router as chat_router
    from web.routers.collaboration import router as collaboration_router
    from web.routers.knowledge import router as knowledge_router
    from web.routers.m1 import router as m1_router
    from web.routers.m2 import router as m2_router
    from web.routers.pages import router as pages_router

    api_router.include_router(pages_router, tags=["pages"])
    api_router.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    api_router.include_router(chat_router, prefix="/api", tags=["chat"])
    api_router.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
    api_router.include_router(collaboration_router, prefix="/api/collaboration", tags=["collaboration"])
    api_router.include_router(cache_router, prefix="/api/cache", tags=["cache"])
    api_router.include_router(m1_router, prefix="/api/m1", tags=["m1"])
    api_router.include_router(m2_router, prefix="/api/m2", tags=["m2"])
