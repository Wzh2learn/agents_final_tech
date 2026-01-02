"""
主Agent：建账规则助手
对应 Dify 工作流：Master_Router

功能：
- 角色识别和路由（产品经理/技术开发/销售运营/默认工程师）
- 调用文档处理工具
- 调用QA问答工具
- 调用反馈处理工具
"""
import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 导入工具
from tools.document_processor import document_processor, validate_rules
from tools.qa_agent import qa_agent, classify_query
from tools.feedback_handler import feedback_handler, generate_summary_report
from tools.file_writer import (
    write_to_file,
    write_to_storage,
    save_rule_to_knowledge,
    save_qa_answer,
    read_from_storage,
    list_storage_files
)

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    result = add_messages(old, new)
    # 转换为列表后再切片
    return list(result)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    # 构建工具列表
    tools = [
        document_processor,      # 文档处理工具
        validate_rules,          # 规则校验工具
        qa_agent,                # QA问答工具
        classify_query,          # 查询分类工具
        feedback_handler,        # 反馈处理工具
        generate_summary_report,  # 反馈汇总工具
        write_to_file,           # 写入本地文件
        write_to_storage,        # 写入对象存储
        save_rule_to_knowledge,   # 保存规则到知识库
        save_qa_answer,          # 保存问答对到知识库
        read_from_storage,       # 从对象存储读取
        list_storage_files       # 列出对象存储文件
    ]

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
