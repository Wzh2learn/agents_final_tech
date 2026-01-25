"""
聊天 API 路由
"""
import json
import logging
import re
import asyncio
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from biz.agent_service import get_agent_service
from storage.thread_settings import get_thread_settings_service
from utils.constants import (
    is_valid_role, get_role_key, get_role_name, get_role_greeting
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 获取线程设置服务
thread_settings = get_thread_settings_service()

# 输入验证常量
MAX_MESSAGE_LENGTH = 4000  # 最大消息长度
MAX_CONVERSATION_ID_LENGTH = 100  # 最大会话ID长度

# 超时配置
CHAT_TIMEOUT_SECONDS = 120  # 聊天请求超时时间 120秒


def _sanitize_error_message(error: str) -> str:
    """脱敏错误信息，防止敏感信息泄露"""
    # 移除可能的路径信息
    sanitized = error.replace("\\", "/").replace("/", "\\")
    # 移除可能的 API key 信息
    sanitized = sanitized.replace("sk-", "***")
    sanitized = sanitized.replace("api_key", "***")
    sanitized = sanitized.replace("API_KEY", "***")
    sanitized = sanitized.replace("password", "***")
    sanitized = sanitized.replace("token", "***")
    # 限制长度
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    return sanitized


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"
    role: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("消息内容不能为空")
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"消息长度不能超过 {MAX_MESSAGE_LENGTH} 字符")
        # 移除潜在的危险字符
        if "<script" in v.lower() or "javascript:" in v.lower():
            raise ValueError("消息包含不允许的内容")
        return v.strip()

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        if len(v) > MAX_CONVERSATION_ID_LENGTH:
            raise ValueError(f"会话ID长度不能超过 {MAX_CONVERSATION_ID_LENGTH} 字符")
        # 只允许字母、数字、下划线、连字符
        if not re.match(r'^[\w\-]*$', v):
            raise ValueError("会话ID包含不允许的字符")
        return v


class RoleRequest(BaseModel):
    role: str
    conversation_id: str = "default"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if not v:
            raise ValueError("角色不能为空")
        if len(v) > 50:
            raise ValueError("角色名称过长")
        return v

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        if len(v) > MAX_CONVERSATION_ID_LENGTH:
            raise ValueError(f"会话ID长度不能超过 {MAX_CONVERSATION_ID_LENGTH} 字符")
        return v


class ResetRequest(BaseModel):
    conversation_id: str = "default"

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        if len(v) > MAX_CONVERSATION_ID_LENGTH:
            raise ValueError(f"会话ID长度不能超过 {MAX_CONVERSATION_ID_LENGTH} 字符")
        return v


@router.post("/chat")
async def chat(request: ChatRequest):
    """流式对话接口"""
    message = request.message
    conversation_id = request.conversation_id or "default"
    role = request.role

    # 尝试从 session 中获取角色
    if conversation_id.startswith('session_'):
        try:
            session_id = int(conversation_id.split('_')[1])
            from web.collaboration_service import get_collaboration_service
            service = get_collaboration_service()
            session = service.get_session(session_id)
            if session and not role:
                role = session.get('role_key')
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse session from conversation_id: {e}")
        except Exception as e:
            logger.warning(f"Failed to get session role: {e}")

    if not role:
        role = thread_settings.get_role(conversation_id) or 'default_engineer'

    # 快速检测：判断是否为通用问题（无需检索知识库）
    general_patterns = [
        r'^(你好|您好|hello|hi|你好吗)',
        r'^谢谢',
        r'^请问.*?是什么$',
        r'^.*?是什么$',
        r'^如何.*?$',
        r'^怎么.*?$',
        r'^能不能.*?$',
        r'^可以.*?吗$',
        r'^帮我.*?$',
        r'^解释.*?$',
        r'^说.*?$',
        r'^讲.*?$',
    ]
    
    is_general_question = False
    for pattern in general_patterns:
        if re.search(pattern, message.lower()):
            is_general_question = True
            break
    
    # 金融规则相关关键词（必须检索）
    financial_keywords = ['规则', '建账', '催收', '逾期', '利息', '罚息', '本金', 
                         '还款', '分期', '账单', '征信', '贷款', '授信', '额度',
                         '风控', '审核', '准入', '条件', '触发', '流程', '步骤',
                         '文档', '知识库', '文件', '规定', '政策', '制度']
    
    needs_rag = any(keyword in message for keyword in financial_keywords)
    
    logger.info(f"问题分析: message={message[:30]}..., is_general={is_general_question}, needs_rag={needs_rag}")
    
    try:
        logger.info(f"开始处理聊天请求: conversation_id={conversation_id}, role={role}")
        
        # 获取 agent_service 实例
        agent_service = get_agent_service()
        
        # 提取 session_id 用于保存消息
        session_id = None
        if conversation_id.startswith('session_'):
            try:
                session_id = int(conversation_id.split('_')[1])
            except (ValueError, IndexError):
                session_id = None
        
        # 非流式调用 - 等待完整响应 (带超时控制)
        full_content = ""
        sources = []
        
        try:
            async with asyncio.timeout(CHAT_TIMEOUT_SECONDS):
                async for chunk in agent_service.stream_chat(
                    request.message, conversation_id, role
                ):
                    if isinstance(chunk, dict) and chunk.get("type") == "content":
                        full_content += chunk.get("content", "")
                    elif isinstance(chunk, dict) and chunk.get("type") == "trace":
                        # 捕获检索结果作为引用来源
                        trace_content = chunk.get("content", [])
                        if isinstance(trace_content, list):
                            for item in trace_content:
                                if isinstance(item, dict) and 'content' in item:
                                    sources.append(item)
                    elif isinstance(chunk, str):
                        full_content += chunk
        except asyncio.TimeoutError:
            logger.warning(f"聊天请求超时: conversation_id={conversation_id}")
            return {"status": "error", "message": f"请求超时，请稍后重试", "content": f"抱歉，请求超时了，请稍后重试"}
        
        logger.info(f"聊天请求完成: full_content length = {len(full_content)}, sources count = {len(sources)}")

        # 保存消息历史到协作数据库
        if session_id:
            try:
                from storage.collaboration import get_collaboration_db
                db = get_collaboration_db()
                db.add_message(session_id, 'user', request.message)
                if full_content:
                    db.add_message(session_id, 'agent', full_content)
                logger.info(f"保存消息到会话 {session_id}: user={request.message[:20]}..., agent={full_content[:20]}...")
            except Exception as e:
                logger.error(f"保存消息到协作数据库失败: {e}")

        # 返回完整响应
        return {
            "status": "success",
            "content": full_content,
            "sources": sources
        }
    except Exception as e:
        sanitized_error = _sanitize_error_message(str(e))
        logger.error(f"Chat error: {sanitized_error}")
        return {"status": "error", "message": f"抱歉发生了错误，请稍后重试", "content": f"抱歉发生了错误，请稍后重试"}


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


class SuggestionsRequest(BaseModel):
    conversation_id: str = "default"
    last_message: str = ""
    context: Optional[list] = None


@router.post("/chat/suggestions")
async def get_suggestions(request: SuggestionsRequest):
    """根据对话上下文生成下一步建议问题"""
    last_message = request.last_message.strip()
    if not last_message:
        return {"status": "success", "suggestions": []}
    
    # 尝试使用 LLM 生成动态建议
    try:
        from langchain_openai import ChatOpenAI
        import os
        
        api_key = os.getenv("SILICONFLOW_API_KEY")
        base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        
        llm = ChatOpenAI(
            model="deepseek-ai/DeepSeek-V3", # 使用更轻量/通用的模型生成建议
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            max_tokens=200
        )
        
        context_str = ""
        if request.context:
            context_str = "\n".join([f"- {msg}" for msg in request.context[-3:]])
            
        prompt = f"""基于以下对话上下文和最后一条用户消息，生成3个用户可能感兴趣的后续问题。
要求：
1. 简洁明了，每个问题不超过20字。
2. 与建账规则、财务会计或当前话题紧密相关。
3. 仅返回 JSON 数组格式，例如：["问题1", "问题2", "问题3"]

上下文：
{context_str}

最后一条消息：
{last_message}

后续问题："""
        
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        
        # 解析 JSON 数组
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            suggestions = json.loads(match.group())
            if isinstance(suggestions, list) and len(suggestions) > 0:
                return {"status": "success", "suggestions": suggestions[:3]}
    except Exception as e:
        logger.warning(f"LLM 生成建议失败，使用备选逻辑: {e}")

    # 备选逻辑：基于关键词的静态规则
    suggestions = []
    msg_lower = last_message.lower()
    
    if any(keyword in msg_lower for keyword in ['规则', '条件', '触发', '要求']):
        suggestions = ["能否举一个具体的例子来说明？", "这条规则有什么例外情况吗？", "违反这条规则会有什么后果？"]
    elif any(keyword in msg_lower for keyword in ['如何', '怎么', '怎样', '操作']):
        suggestions = ["需要准备哪些材料或数据？", "完成这个操作需要多长时间？", "有没有更简单的方法？"]
    elif any(keyword in msg_lower for keyword in ['是什么', '定义', '概念']):
        suggestions = ["这个概念和类似概念有什么区别？", "在实际工作中如何应用？", "相关的法规依据是什么？"]
    else:
        suggestions = ["能详细解释一下吗？", "有没有相关的参考资料？", "这个在实际场景中如何应用？"]
    
    return {"status": "success", "suggestions": suggestions[:3]}


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
