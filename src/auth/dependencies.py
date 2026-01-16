"""
FastAPI 认证依赖
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.jwt_handler import decode_token
from auth.users import get_user

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """获取当前用户（可选认证）"""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload:
        return None

    username = payload.get("sub")
    if not username:
        return None

    return get_user(username)
