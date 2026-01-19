"""
聊天 API 路由
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from biz.agent_service import get_agent_service
from storage.thread_settings import get_thread_settings_service
from utils.constants import (
    is_valid_role, get_role_key, get_role_name, get_role_greeting
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 获取线程设置服务
thread_settings = get_thread_settings_service()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"
    role: Optional[str] = None


class RoleRequest(BaseModel):
    role: str
    conversation_id: str = "default"


class ResetRequest(BaseModel):
    conversation_id: str = "default"


@router.post("/chat")
async def chat(request: ChatRequest):
    """聊天 API（流式响应）"""
    agent_service = get_agent_service()

    # 获取角色
    role = request.role
    conversation_id = request.conversation_id

    # 如果是 session_ 开头，从数据库加载角色
    if conversation_id.startswith('session_'):
        try:
            session_id = int(conversation_id.split('_')[1])
            from web.collaboration_service import get_collaboration_service
            svc = get_collaboration_service()
            session = svc.get_session(session_id)
            if session and not role:
                role = session.get('role_key')
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse session from conversation_id: {e}")
        except Exception as e:
            logger.warning(f"Failed to get session role: {e}")

    if not role:
        role = thread_settings.get_role(conversation_id) or 'default_engineer'

    async def generate():
        full_content = ""
        try:
            async for chunk in agent_service.stream_chat(
                request.message, conversation_id, role
            ):
                if isinstance(chunk, dict) and chunk.get("type") == "content":
                    text = chunk.get("content", "")
                    full_content += text
                    yield f"data: {json.dumps({'content': text, 'done': False}, ensure_ascii=False)}\n\n"
                elif isinstance(chunk, str):
                    full_content += chunk
                    yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"

            # 保存消息历史
            if conversation_id.startswith('session_'):
                try:
                    session_id = int(conversation_id.split('_')[1])
                    from storage.collaboration import get_collaboration_db
                    db = get_collaboration_db()
                    db.add_message(session_id, 'user', request.message)
                    if full_content:
                        db.add_message(session_id, 'agent', full_content)
                except Exception as e:
                    logger.error(f"Failed to save message: {e}")

            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: {json.dumps({'content': f'错误: {str(e)}', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/reset")
async def reset_conversation(request: ResetRequest):
    """重置会话"""
    thread_settings.delete(request.conversation_id)
    return {"status": "success", "message": f"会话 {request.conversation_id} 已重置"}


@router.post("/set_role")
async def set_role(request: RoleRequest):
    """设置会话角色"""
    role = request.role
    conversation_id = request.conversation_id

    if is_valid_role(role):
        thread_settings.set_role(conversation_id, get_role_key(role))
        return {
            "status": "success",
            "role": get_role_name(role),
            "role_key": get_role_key(role),
            "greeting": get_role_greeting(role, full=False)
        }
    raise HTTPException(status_code=400, detail="无效的角色选择")


@router.get("/status")
async def get_status(conversation_id: str = "default"):
    """获取会话状态"""
    role = thread_settings.get_role(conversation_id)
    return {
        "status": "success",
        "conversation_id": conversation_id,
        "role": role
    }


# ==================== 会话管理 API ====================

class CreateSessionRequest(BaseModel):
    name: str = "新对话"
    role_key: str = "default_engineer"
    type: str = "private"  # private 或 collaboration


class UpdateSessionRequest(BaseModel):
    name: Optional[str] = None
    role_key: Optional[str] = None


@router.get("/chat/sessions")
async def get_chat_sessions():
    """获取所有活跃会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    sessions = service.get_all_sessions(active_only=True)
    return {"status": "success", "sessions": sessions}


@router.post("/chat/sessions")
async def create_chat_session(request: CreateSessionRequest):
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
    raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: int):
    """获取单个会话详情"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    session = service.get_session(session_id)
    if session:
        return {"status": "success", "session": session}
    raise HTTPException(status_code=404, detail="会话不存在")


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: int):
    """删除会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    success = service.delete_session(session_id)
    if success:
        return {"status": "success", "message": "会话已删除"}
    raise HTTPException(status_code=500, detail="删除会话失败")


@router.patch("/chat/sessions/{session_id}")
async def update_chat_session(session_id: int, request: UpdateSessionRequest):
    """更新会话（如重命名或切换角色）"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    success = service.update_session(
        session_id=session_id,
        name=request.name,
        role_key=request.role_key
    )
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="更新失败")


@router.get("/chat/sessions/{session_id}/history")
async def get_chat_session_history(session_id: int):
    """获取会话历史消息"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    messages = service.get_session_messages(session_id)
    return {"status": "success", "messages": messages}
