"""
工具模块
导出所有对 Agent 可见的高级业务工具
"""

# 核心业务工具
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

# 统一 RAG 高级工具 (通过 Biz 层实现)
from tools.rag_tools import (
    add_document_to_knowledge_base,
    delete_documents_from_knowledge_base,
    smart_retrieve,
    batch_retrieve,
    get_retrieval_statistics
)

# 对外暴露的工具列表
ALL_TOOLS = [
    document_processor,
    validate_rules,
    qa_agent,
    classify_query,
    feedback_handler,
    generate_summary_report,
    write_to_file,
    write_to_storage,
    save_rule_to_knowledge,
    save_qa_answer,
    read_from_storage,
    list_storage_files,
    add_document_to_knowledge_base,
    delete_documents_from_knowledge_base,
    smart_retrieve,
    batch_retrieve,
    get_retrieval_statistics,
]

__all__ = ['ALL_TOOLS']
