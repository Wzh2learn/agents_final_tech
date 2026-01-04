"""
Agent 业务逻辑层
封装 Agent 的构建、执行与会话管理。
"""
import logging
import json
import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from agents.agent import build_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.types import RunnableConfig
from storage.memory.memory_saver import get_memory_saver

logger = logging.getLogger(__name__)

class AgentService:
    """Agent 业务服务类，提供同步和流式对话接口"""
    
    def __init__(self):
        self._agent = None
        self._system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "agent_llm_config.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            return cfg.get("sp", "你是建账规则助手")
        except Exception as e:
            logger.warning(f"Failed to load system prompt: {e}")
            return "你是建账规则助手"

    def get_agent(self):
        """延迟加载 Agent 实例"""
        if self._agent is None:
            self._agent = build_agent()
        return self._agent

    async def chat(self, message: str, conversation_id: str, role: str = "default") -> Dict[str, Any]:
        """同步对话接口，返回内容与追踪信息"""
        config = RunnableConfig(
            configurable={
                "thread_id": conversation_id,
                "role": role
            }
        )
        agent = self.get_agent()
        
        # 从历史中获取已有消息，如果第一次对话则注入 system prompt
        from storage.memory.memory_saver import get_memory_saver
        checkpointer = get_memory_saver()
        state = checkpointer.get(config)
        
        # 只在首次对话时添加 SystemMessage
        if state is None or not state.get("values", {}).get("messages"):
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=message)
            ]
        else:
            messages = [HumanMessage(content=message)]
            
        result = await agent.ainvoke({"messages": messages}, config=config)
        
        # 提取最后一条 AI 消息内容
        content = ""
        trace = []
        if "messages" in result:
            messages = result["messages"]
            for msg in messages:
                if isinstance(msg, AIMessage):
                    content = msg.content
                elif hasattr(msg, 'tool_outputs'): # 假设有某种方式获取工具输出
                    pass 
            
            # 搜索所有工具消息以获取检索结果
            from langchain_core.messages import ToolMessage
            for msg in reversed(messages):
                if isinstance(msg, ToolMessage):
                    try:
                        # 尝试解析输出，如果是 JSON 且包含检索信息则记录
                        output = json.loads(msg.content)
                        if isinstance(output, list) and len(output) > 0 and 'content' in output[0]:
                            trace = output
                            break
                    except:
                        continue

        return {"content": content, "trace": trace}

    async def stream_chat(self, message: str, conversation_id: str, role: str = "default") -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话接口，返回内容块或元数据"""
        config = RunnableConfig(
            configurable={
                "thread_id": conversation_id,
                "role": role
            }
        )
        agent = self.get_agent()
        
        # 从历史中获取已有消息，如果第一次对话则注入 system prompt
        from storage.memory.memory_saver import get_memory_saver
        checkpointer = get_memory_saver()
        state = checkpointer.get(config)
        
        # 只在首次对话时添加 SystemMessage
        if state is None or not state.get("values", {}).get("messages"):
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=message)
            ]
        else:
            messages = [HumanMessage(content=message)]
        
        async for chunk in agent.astream({"messages": messages}, config=config):
            if "messages" in chunk:
                for msg in chunk["messages"]:
                    if isinstance(msg, AIMessage) and msg.content:
                        yield {"type": "content", "content": msg.content}
            elif "agent" in chunk and "messages" in chunk["agent"]:
                for msg in chunk["agent"]["messages"]:
                    if isinstance(msg, AIMessage) and msg.content:
                        yield {"type": "content", "content": msg.content}
            
            # 捕获工具输出作为 trace
            if "tools" in chunk and "messages" in chunk["tools"]:
                from langchain_core.messages import ToolMessage
                for msg in chunk["tools"]["messages"]:
                    if isinstance(msg, ToolMessage):
                        try:
                            output = json.loads(msg.content)
                            if isinstance(output, list) and len(output) > 0 and 'content' in output[0]:
                                yield {"type": "trace", "content": output}
                        except:
                            continue

_agent_service = None

def get_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
