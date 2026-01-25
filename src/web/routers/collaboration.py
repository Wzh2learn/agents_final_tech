"""
协作会话 API 路由
"""
import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class SessionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    role_key: str = "default_engineer"
    type: str = "private"


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    role_key: Optional[str] = None


class ParticipantCreate(BaseModel):
    nickname: str
    avatar_color: str = "#667eea"


class CollabChatRequest(BaseModel):
    message: str
    session_id: int
    conversation_id: Optional[str] = None
    role: str = "default"


@router.get("/sessions")
async def get_sessions():
    """获取所有会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    sessions = service.get_all_sessions()
    return {"status": "success", "sessions": sessions}


@router.post("/sessions")
async def create_session(request: SessionCreate):
    """创建新会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    session = service.create_session(
        name=request.name,
        session_type=request.type,
        role_key=request.role_key
    )
    if session:
        return {"status": "success", "session": session}
    return {"error": "创建会话失败"}


@router.get("/sessions/{session_id}")
async def get_session(session_id: int):
    """获取会话详情"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    session = service.get_session(session_id)
    if session:
        return {"status": "success", "session": session}
    return {"error": "会话不存在"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    """删除会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    if service.delete_session(session_id):
        return {"status": "success", "message": "会话已删除"}
    return {"error": "删除失败"}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: int, request: SessionUpdate):
    """更新会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    if service.update_session(session_id, request.name, request.role_key):
        return {"status": "success"}
    return {"error": "更新失败"}


@router.get("/sessions/{session_id}/participants")
async def get_participants(session_id: int, online_only: bool = False):
    """获取参与者列表"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    participants = service.get_session_participants(session_id, online_only)
    return {"status": "success", "participants": participants}


@router.post("/sessions/{session_id}/participants")
async def add_participant(session_id: int, request: ParticipantCreate):
    """添加参与者"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    participant = service.add_participant(
        session_id, request.nickname, request.avatar_color
    )
    if participant:
        return {"status": "success", "participant": participant}
    return {"error": "添加失败"}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: int):
    """获取会话消息"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    messages = service.get_session_messages(session_id)
    return {"status": "success", "messages": messages}


@router.post("/chat")
async def collaboration_chat(request: CollabChatRequest):
    """协作聊天 - 仅处理 AI 响应，不处理用户消息（用户消息由 WebSocket 直接广播）"""
    from biz.agent_service import get_agent_service
    from web.websocket_server import broadcast_agent_message

    agent_service = get_agent_service()
    conv_id = request.conversation_id or f"session_{request.session_id}"

    try:
        full_content = ""
        async for chunk in agent_service.stream_chat(
            request.message, conv_id, request.role
        ):
            if isinstance(chunk, dict) and chunk.get("type") == "content":
                full_content += chunk.get("content", "")

        if full_content:
            # 仅广播 AI 响应，不处理用户消息（用户消息由 WebSocket 客户端直接广播）
            await broadcast_agent_message(
                session_id=request.session_id, content=full_content
            )
        return {"status": "success", "content": full_content}
    except Exception as e:
        logger.error(f"Collaboration chat failed: {e}")
        return {"error": str(e)}
