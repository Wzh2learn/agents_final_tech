"""
记忆反射工具 (Memory Reflector)
负责提取对话中的关键事实（Profile）并对旧对话进行摘要（Episodic）。
类比推荐系统中的特征提取与兴趣画像更新。
"""
import json
import logging
import asyncio
from typing import List, Dict, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import os
from utils.openai_network import get_chat_openai_network_kwargs

logger = logging.getLogger(__name__)

def _get_llm():
    """获取用于总结的 LLM"""
    api_key = os.getenv("SILICONFLOW_API_KEY")
    base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    return ChatOpenAI(
        model="deepseek-ai/DeepSeek-V3",
        api_key=api_key,
        base_url=base_url,
        temperature=0.3,
        request_timeout=30,  # 30秒超时
        **get_chat_openai_network_kwargs()
    )

@tool
def reflect_on_conversation(messages_json: str) -> str:
    """
    分析对话历史，提取核心事实和阶段性总结。
    
    Args:
        messages_json: 消息列表的 JSON 字符串
        
    Returns:
        JSON 格式的反射结果，包含：
        - summary: 对话阶段性摘要
        - facts: 提取出的静态事实（如用户公司信息、偏好等）
    """
    llm = _get_llm()
    
    system_prompt = """你是一个记忆提取专家。分析以下对话，提取：
1. 阶段性摘要：用一句话概括这段对话讨论的核心内容。
2. 核心事实：提取出用户提到的关于其自身、公司或业务的长期有效的静态事实（如：用户在XX银行工作，负责YY业务）。

请以 JSON 格式返回：
{
    "summary": "...",
    "facts": [{"key": "...", "value": "..."}]
}
"""
    
    try:
        response = llm.invoke([
            ("system", system_prompt),
            ("human", f"对话历史：\n{messages_json}")
        ])
        return response.content
    except asyncio.TimeoutError:
        logger.error(f"Reflection timeout: LLM request exceeded 30s")
        return json.dumps({"summary": "提取超时", "facts": []})
    except Exception as e:
        logger.error(f"Reflection failed: {e}")
        return json.dumps({"summary": "提取失败", "facts": []})
