"""
Agent 业务逻辑层
封装 Agent 的构建、执行与会话管理。
"""
import logging
import json
import os
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
from agents.agent import build_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.types import RunnableConfig
from storage.memory.memory_saver import get_memory_saver

logger = logging.getLogger(__name__)

# 单例锁，确保线程安全
_agent_service_lock = asyncio.Lock()
_agent_service = None

class AgentService:
    """Agent 业务服务类，提供同步和流式对话接口"""
    MAX_REFLECTION_INDEX_SIZE = 1000  # 最大保留的 conversation_id 数量
    
    def __init__(self):
        self._agent = None
        self._system_prompt = self._load_system_prompt()
        self._reflection_index: Dict[str, str] = {}  # conversation_id -> last reflected message ID
        self._reflection_inflight: set[str] = set()
    
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

    async def _get_long_term_context(self, message: str, conversation_id: str) -> str:
        """获取长期记忆上下文 (Target Attention 召回)"""
        try:
            from storage.memory.episodic_memory import get_episodic_memory_provider
            provider = get_episodic_memory_provider()
            memories = await provider.search_memory(message, conversation_id, top_k=3)
            if not memories:
                return ""
            
            context = "\n".join([f"[相关历史记忆]: {m.page_content}" for m in memories])
            return f"\n以下是与当前问题相关的历史对话背景：\n{context}\n"
        except Exception as e:
            logger.warning(f"获取长期记忆失败: {e}")
            return ""

    async def _check_and_trigger_reflection(self, conversation_id: str, messages: List[Any]):
        """检查并触发记忆反射逻辑 (HMM 核心触发器)"""
        # The graph keeps a sliding window, so a list length is not a durable
        # cursor. Use stable message IDs within this process instead.
        if conversation_id in self._reflection_inflight:
            return
        eligible = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
        ids = [m.id for m in eligible]
        if any(not isinstance(message_id, str) or not message_id for message_id in ids) or len(set(ids)) != len(ids):
            logger.warning("Skipping reflection: message IDs are missing or duplicated")
            return
        last_id = self._reflection_index.get(conversation_id)
        if last_id is not None:
            if last_id not in ids:
                logger.warning("Skipping reflection: previous cursor is outside the current message window")
                return
            eligible = eligible[ids.index(last_id) + 1:]
        if len(eligible) < 15:
            return
        msgs_to_reflect = eligible[:10]
        # There is no await between the check and insertion; concurrent tasks on
        # this service's event loop cannot reserve the same session twice.
        self._reflection_inflight.add(conversation_id)

        try:
            logger.info(f"触发记忆反射检查: conversation_id={conversation_id}, msg_count={len(messages)}")
            from tools.memory_reflector import reflect_on_conversation
            from storage.memory.episodic_memory import get_episodic_memory_provider
            
            # 1. 只处理游标之后最早的一批对话消息。
            msgs_json = json.dumps([
                {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
                for m in msgs_to_reflect
                if isinstance(m, (HumanMessage, AIMessage))
            ], ensure_ascii=False)
            
            # 2. 调用反射工具（避免阻塞事件循环）
            if hasattr(reflect_on_conversation, "ainvoke"):
                reflection_res_str = await reflect_on_conversation.ainvoke(msgs_json)
            else:
                reflection_res_str = await asyncio.to_thread(reflect_on_conversation.invoke, msgs_json)
            try:
                reflection_res = json.loads(reflection_res_str)
            except json.JSONDecodeError:
                logger.warning(f"Reflection JSON parse failed: {reflection_res_str[:100]}...")
                return
            
            summary = reflection_res.get("summary", "")
            facts = reflection_res.get("facts", [])
            
            if not summary:
                return

            # 3. 存入长期记忆 (Episodic Memory)
            provider = get_episodic_memory_provider()
            saved = await provider.add_memory(
                session_id=conversation_id,
                content=f"[历史摘要]: {summary}\n[关键事实]: {json.dumps(facts, ensure_ascii=False)}",
                metadata={"trigger": "auto_reflection", "msg_count": len(msgs_to_reflect)}
            )
            if saved is not True:
                logger.warning("Reflection memory was not accepted by the storage adapter")
                return
            logger.info(f"记忆反射已交给 L2 存储适配器: {conversation_id}")

            # Advance only after an accepted write. This cursor is process-local.
            self._reflection_index.pop(conversation_id, None)
            self._reflection_index[conversation_id] = msgs_to_reflect[-1].id
            if len(self._reflection_index) > self.MAX_REFLECTION_INDEX_SIZE:
                keep_count = self.MAX_REFLECTION_INDEX_SIZE // 2
                for key in list(self._reflection_index.keys())[:-keep_count]:
                    del self._reflection_index[key]
                logger.info(f"Cleaned reflection_index, kept {keep_count} entries")
            
        except Exception as e:
            logger.warning(f"记忆反射触发失败: {e}")
        finally:
            self._reflection_inflight.discard(conversation_id)

    async def chat(self, message: str, conversation_id: str, role: str = "default") -> Dict[str, Any]:
        """同步对话接口，返回内容与追踪信息"""
        config = RunnableConfig(
            configurable={
                "thread_id": conversation_id,
                "role": role
            }
        )
        agent = self.get_agent()

        # 1. 获取长期记忆上下文 (HMM 创新点)
        lt_context = await self._get_long_term_context(message, conversation_id)
        full_message = f"{lt_context}\n用户当前问题：{message}" if lt_context else message

        # 2. 从历史中获取已有消息，如果第一次对话则注入 system prompt
        checkpointer = get_memory_saver()
        state = await self._get_checkpoint(checkpointer, config)

        # 只在首次对话时添加 SystemMessage
        if state is None or not state.get("values", {}).get("messages"):
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=full_message)
            ]
        else:
            messages = [HumanMessage(content=full_message)]

        result = await agent.ainvoke({"messages": messages}, config=config)

        # 3. 异步触发记忆反射检查 (HMM 创新点)
        if "messages" in result:
            asyncio.create_task(self._check_and_trigger_reflection(conversation_id, result["messages"]))

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

        # 1. 获取长期记忆上下文 (HMM 创新点)
        lt_context = await self._get_long_term_context(message, conversation_id)
        full_message = f"{lt_context}\n用户当前问题：{message}" if lt_context else message

        # 2. 从历史中获取已有消息，如果第一次对话则注入 system prompt
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
                HumanMessage(content=full_message)
            ]
            logger.info("首次对话，注入 system prompt")
        else:
            messages = [HumanMessage(content=full_message)]
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
            
            # 3. 异步触发记忆反射检查 (HMM 创新点)
            # 重新获取 state 以获取包含最新消息的完整列表
            final_state = await self._get_checkpoint(checkpointer, config)
            if final_state and final_state.get("values", {}).get("messages"):
                asyncio.create_task(self._check_and_trigger_reflection(conversation_id, final_state["values"]["messages"]))
                
        except Exception as e:
            logger.error(f"Stream chat error: {e}", exc_info=True)
            yield {"type": "content", "content": f"抱歉，发生了错误: {str(e)}"}

async def get_agent_service() -> AgentService:
    """获取 AgentService 单例（线程安全）"""
    global _agent_service
    if _agent_service is None:
        async with _agent_service_lock:
            if _agent_service is None:
                _agent_service = AgentService()
    return _agent_service

# 同步版本供非异步上下文使用
def get_agent_service_sync() -> AgentService:
    """同步获取 AgentService 单例（注意：可能非线程安全，仅在初始化阶段使用）"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
