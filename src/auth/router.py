"""
认证 API 路由
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from auth.jwt_handler import create_access_token
from auth.users import authenticate_user

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    token = create_access_token(data={"sub": user["username"]})
    return TokenResponse(access_token=token)
