"""
Agent 业务逻辑层
封装 Agent 的构建、执行与会话管理。
"""
import logging
import json
import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from agents.agent import build_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
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

    async def _get_checkpoint(self, checkpointer, config):
        """获取 checkpoint 状态，支持同步和异步 checkpointer"""
        try:
            if hasattr(checkpointer, "aget"):
                return await checkpointer.aget(config)
            return checkpointer.get(config)
        except Exception as e:
            logger.warning(f"Failed to get checkpoint: {e}")
            return None

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
        checkpointer = get_memory_saver()
        state = await self._get_checkpoint(checkpointer, config)

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

            # 搜索所有工具消息以获取检索结果
            for msg in reversed(messages):
                if isinstance(msg, ToolMessage):
                    try:
                        # 尝试解析输出，如果是 JSON 且包含检索信息则记录
                        output = json.loads(msg.content)
                        if isinstance(output, list) and len(output) > 0 and 'content' in output[0]:
                            trace = output
                            break
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.debug(f"Failed to parse tool output: {e}")
                        continue

        return {"content": content, "trace": trace}

    async def stream_chat(self, message: str, conversation_id: str, role: str = "default") -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话接口，返回内容块或元数据"""
        logger.info(f"开始流式聊天: conversation_id={conversation_id}, role={role}")
        config = RunnableConfig(
            configurable={
                "thread_id": conversation_id,
                "role": role
            }
        )
        agent = self.get_agent()

        # 从历史中获取已有消息，如果第一次对话则注入 system prompt
        checkpointer = get_memory_saver()
        state = None
        try:
            state = await self._get_checkpoint(checkpointer, config)
            logger.info(f"获取到 checkpoint: {state is not None}")
        except Exception as e:
            logger.warning(f"Failed to get checkpoint: {e}")
            state = None

        # 只在首次对话时添加 SystemMessage
        if state is None or not state.get("values", {}).get("messages"):
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=message)
            ]
            logger.info("首次对话，注入 system prompt")
        else:
            messages = [HumanMessage(content=message)]
            logger.info("非首次对话，使用已有历史")

        content_buffer = ""
        
        try:
            logger.info("开始调用 agent.astream")
            async for chunk in agent.astream({"messages": messages}, config=config):
                # 优先处理 AI 消息内容
                if "messages" in chunk:
                    for msg in chunk["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            content_buffer += msg.content
                            yield {"type": "content", "content": msg.content}
                elif "agent" in chunk and "messages" in chunk["agent"]:
                    for msg in chunk["agent"]["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            content_buffer += msg.content
                            yield {"type": "content", "content": msg.content}

                # 捕获工具输出作为 trace
                if "tools" in chunk and "messages" in chunk["tools"]:
                    for msg in chunk["tools"]["messages"]:
                        if isinstance(msg, ToolMessage):
                            try:
                                output = json.loads(msg.content)
                                if isinstance(output, list) and len(output) > 0 and 'content' in output[0]:
                                    yield {"type": "trace", "content": output}
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.debug(f"Failed to parse tool output in stream: {e}")
                                continue
            logger.info(f"流式聊天完成: content_buffer length = {len(content_buffer)}")
        except Exception as e:
            logger.error(f"Stream chat error: {e}", exc_info=True)
            yield {"type": "content", "content": f"抱歉，发生了错误: {str(e)}"}

_agent_service = None

def get_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
