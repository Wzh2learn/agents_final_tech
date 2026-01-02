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
# 导入 RAG 相关工具
from tools.document_loader import (
    load_document,
    load_documents_with_metadata,
    get_document_info
)
from tools.text_splitter import (
    split_text_recursive,
    split_text_by_markdown_structure,
    split_document_optimized,
    split_text_with_summary
)
from tools.reranker_tool import (
    rerank_documents,
    rerank_simple,
    get_rerank_info
)
from tools.vector_store import (
    check_vector_store_setup
)
from tools.knowledge_base import (
    add_document_to_knowledge_base,
    delete_documents_from_knowledge_base,
    search_knowledge_base,
    get_knowledge_base_stats
)
from tools.rag_retriever import (
    rag_retrieve_with_rerank,
    hybrid_search,
    format_docs_for_rag
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
        # 原有工具
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
        list_storage_files,       # 列出对象存储文件
        # 新增 RAG 工具
        load_document,           # 加载文档（Markdown/Word）
        load_documents_with_metadata,  # 加载文档带元数据
        get_document_info,       # 获取文档信息
        split_text_recursive,   # 递归文本分割
        split_text_by_markdown_structure,  # Markdown 结构分割
        split_document_optimized, # 优化文档分割
        split_text_with_summary,  # 文本分割并统计
        rerank_documents,        # 文档重排序
        rerank_simple,          # 简单文本重排序
        get_rerank_info,        # 获取 Rerank 信息
        check_vector_store_setup,  # 检查向量存储设置
        add_document_to_knowledge_base,  # 添加文档到知识库
        delete_documents_from_knowledge_base,  # 从知识库删除文档
        search_knowledge_base,   # 搜索知识库
        get_knowledge_base_stats, # 获取知识库统计
        rag_retrieve_with_rerank,  # RAG 检索（向量+Rerank）
        hybrid_search,          # 混合搜索
        format_docs_for_rag,    # 格式化文档用于 RAG
    ]

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
