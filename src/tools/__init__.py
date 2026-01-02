"""
工具模块
导出所有可用的工具
"""

# 原有工具
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

# 新增 RAG 相关工具
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
    rerank_documents
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

# 所有工具列表
ALL_TOOLS = [
    # 原有工具
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
    # 新增 RAG 工具
    load_document,
    load_documents_with_metadata,
    get_document_info,
    split_text_recursive,
    split_text_by_markdown_structure,
    split_document_optimized,
    split_text_with_summary,
    rerank_documents,
    check_vector_store_setup,
    add_document_to_knowledge_base,
    delete_documents_from_knowledge_base,
    search_knowledge_base,
    get_knowledge_base_stats,
    rag_retrieve_with_rerank,
]

__all__ = ['ALL_TOOLS']
