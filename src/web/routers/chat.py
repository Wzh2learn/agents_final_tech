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


# 角色映射
ROLE_MAP = {
    'a': 'product_manager',
    'b': 'tech_developer',
    'c': 'sales_operations',
    'd': 'default_engineer'
}

ROLE_NAMES = {
    'a': '产品经理',
    'b': '技术开发',
    'c': '销售运营',
    'd': '默认工程师'
}

ROLE_GREETINGS = {
    'a': '👋 您好！我是**产品经理助手**，专注于需求分析、产品规划和用户体验设计。',
    'b': '👨‍💻 您好！我是**技术开发助手**，精通系统架构、代码实现和技术方案设计。',
    'c': '📈 您好！我是**销售运营助手**，专注于业务分析、运营策略和数据洞察。',
    'd': '🛠️ 您好！我是**默认工程师助手**，提供全方位的技术支持和问题解决方案。'
}


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
        except:
            pass

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

    if role and role in ROLE_MAP:
        thread_settings.set_role(conversation_id, ROLE_MAP[role])
        return {
            "status": "success",
            "role": ROLE_NAMES[role],
            "role_key": ROLE_MAP[role],
            "greeting": ROLE_GREETINGS[role]
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
