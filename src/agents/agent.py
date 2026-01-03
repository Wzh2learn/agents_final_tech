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
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from utils.runtime_ctx import default_headers
from storage.memory.memory_saver import get_memory_saver

# 导入核心业务工具
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
from tools.rag_tools import (
    smart_retrieve,
    batch_retrieve,
    get_retrieval_statistics
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
    # 动态获取项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    workspace_path = os.getenv("WORKSPACE_PATH", base_dir)
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("SILICONFLOW_API_KEY")
    base_url = os.getenv("SILICONFLOW_BASE_URL")

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

    # 构建工具列表 (精简后的核心工具集)
    tools = [
        document_processor,      # 文档规则提取
        validate_rules,          # 规则校验
        qa_agent,                # 知识库问答 (内置检索)
        classify_query,          # 查询分类
        feedback_handler,        # 反馈处理
        generate_summary_report, # 报告生成
        write_to_file,           # 本地写入
        write_to_storage,        # 存储写入 (ACL)
        save_rule_to_knowledge,  # 规则持久化
        save_qa_answer,          # QA持久化
        read_from_storage,       # 存储读取
        list_storage_files,      # 文件列表
        smart_retrieve,          # 智能 RAG 检索 (Biz 驱动)
        batch_retrieve,          # 批量检索 (Biz 驱动)
        get_retrieval_statistics,# 检索统计 (Biz 驱动)
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
