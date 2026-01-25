"""
RAG 业务逻辑层
统一封装检索、重排序与知识库维护逻辑。
"""
import json
import logging
import os
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from tools.vector_store import get_vector_store
from tools.reranker_tool import rerank_documents
from tools.bm25_retriever import bm25_retrieve
from tools.question_classifier import classify_question_type, get_retrieval_strategy
from tools.document_loader import load_document, get_document_info
from tools.text_splitter import split_text_recursive, split_text_by_markdown_structure, hierarchical_split
from storage.provider import get_storage_provider
from utils.config_loader import get_config

logger = logging.getLogger(__name__)

# 从配置文件加载领域关键词
def _get_domain_keywords() -> Dict[str, List[str]]:
    """从配置文件加载领域关键词"""
    try:
        config = get_config()
        return config.get("domain_keywords", {
            "催收": ["催收", "逾期", "还款", "坏账"],
            "风控": ["风控", "风险", "审核", "准入"],
            "财务": ["财务", "会计", "账务", "建账"],
            "贷款": ["贷款", "授信", "额度", "利息"],
            "通用": []
        })
    except Exception:
        # 配置加载失败时返回默认值
        return {
            "催收": ["催收", "逾期", "还款", "坏账"],
            "风控": ["风控", "风险", "审核", "准入"],
            "财务": ["财务", "会计", "账务", "建账"],
            "贷款": ["贷款", "授信", "额度", "利息"],
            "通用": []
        }

class RAGService:
    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name
        self.provider = get_storage_provider()

    def get_collection_names(self) -> List[str]:
        """获取所有集合名称"""
        from storage.database.db import get_session
        from storage.database.shared.model import LangchainPgCollection
        db = get_session()
        try:
            collections = db.query(LangchainPgCollection).all()
            return [c.name for c in collections]
        finally:
            db.close()

    async def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None, use_hierarchical: bool = False, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """全流程入库：加载 -> 分割 -> 存储(S3) -> 向量化(DB)
        
        Args:
            file_path: 文件路径
            metadata: 元数据
            use_hierarchical: 是否使用父子分段模式（默认False）
            collection_name: 目标集合名称，如果不指定则使用 self.collection_name
        """
        target_collection = collection_name or self.collection_name
        # 1. 加载
        content = load_document.invoke({"file_path": file_path})
        
        # 2. 分割
        if use_hierarchical:
            # 使用父子分段模式
            chunks_docs = hierarchical_split(content, parent_chunk_size=2000, child_chunk_size=500)
            chunks = [doc.page_content for doc in chunks_docs]
            chunks_metadata_list = [doc.metadata for doc in chunks_docs]
        else:
            # 传统分割方式
            if file_path.endswith(('.md', '.markdown')):
                chunks_str = split_text_by_markdown_structure.invoke({"text": content})
            else:
                chunks_str = split_text_recursive.invoke({"text": content})
            
            # 解析块
            import re
            raw_chunks = chunks_str.split("---")
            chunks = []
            chunks_metadata_list = []
            for c in raw_chunks:
                c = c.strip()
                if not c: continue
                clean_c = re.sub(r'^块 \d+ \(.*?\)\s*---', '', c).strip()
                if clean_c.startswith(("文本分割结果", "Markdown 结构分割结果", "总块数:", "块大小:", "重叠:", "分割规则:", "====")):
                    continue
                if clean_c:
                    chunks.append(clean_c)
                    chunks_metadata_list.append({})
        
        # 2.5 过滤空块，避免 embedding API 报参数错误
        filtered_chunks = []
        filtered_metadata = []
        max_embed_chars = int(os.getenv("EMBED_MAX_CHARS", "4000"))
        for chunk, meta in zip(chunks, chunks_metadata_list):
            if chunk is None:
                continue
            text = str(chunk).replace("\x00", "").strip()
            if not text:
                continue
            if max_embed_chars > 0 and len(text) > max_embed_chars:
                text = text[:max_embed_chars]
            filtered_chunks.append(text)
            filtered_metadata.append(meta)
        chunks = filtered_chunks
        chunks_metadata_list = filtered_metadata

        if not chunks:
            raise ValueError("文档解析后没有有效文本块，请检查文件内容")

        # 3. 持久化原始文件 (ACL)
        display_name = (metadata or {}).get("original_name", os.path.basename(file_path))
        with open(file_path, "rb") as f:
            object_key = self.provider.ingest_document(f.read(), display_name, metadata or {})
            
        # 4. 向量化入库
        vector_store = get_vector_store(collection_name=target_collection)
        docs = []
        for i, (chunk, chunk_meta) in enumerate(zip(chunks, chunks_metadata_list)):
            combined_meta = {
                **(metadata or {}),
                **chunk_meta,
                "source": display_name,
                "object_key": object_key,
                "chunk_index": i
            }
            docs.append(Document(page_content=chunk, metadata=combined_meta))
        vector_store.add_documents(docs)
        
        return {"object_key": object_key, "chunks": len(chunks), "hierarchical": use_hierarchical, "collection": target_collection}

    def smart_retrieve(
        self, 
        query: str, 
        top_k: int = 5, 
        collection_names: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        固定检索：总是检索知识库，支持多知识库智能选择
        
        Args:
            query: 查询内容
            top_k: 每个知识库返回结果数量
            collection_names: 指定要检索的知识库列表，None则智能选择
            max_results: 最大总返回结果数量（默认10）
        """
        # 限制 max_results 范围
        max_results = max(1, min(max_results, 50))
        top_k = max(1, min(top_k, 20))
        
        # 1. 智能选择知识库（如果不指定）
        if not collection_names:
            collection_names = self._select_collections(query)
        
        logger.info(f"Query: {query} | Collections: {collection_names} | TopK: {top_k} | MaxResults: {max_results}")
        
        # 2. 固定使用混合检索策略（向量 + BM25）
        all_docs = []
        
        for collection_name in collection_names:
            try:
                # 向量检索
                vector_store = get_vector_store(collection_name=collection_name)
                results = vector_store.similarity_search_with_score(query, k=top_k)
                for doc, score in results:
                    doc.metadata["vector_score"] = float(score)
                    doc.metadata["collection"] = collection_name
                    all_docs.append(doc)
                    
                # BM25 检索
                bm25_res = bm25_retrieve.invoke({
                    "query": query, 
                    "top_k": top_k,
                    "collection_name": collection_name
                })
                bm25_docs = self._parse_json_docs(bm25_res)
                for doc in bm25_docs:
                    doc.metadata["collection"] = collection_name
                    all_docs.append(doc)
            except Exception as e:
                logger.error(f"检索知识库 {collection_name} 失败: {e}")
                continue
        
        # 3. 去重并合并结果
        unique_docs = self._deduplicate_docs(all_docs)
        
        # 4. 按相关性排序（综合向量分数和 BM25 分数）
        sorted_docs = sorted(unique_docs, key=lambda x: x.metadata.get("vector_score", 0), reverse=True)
        
        # 5. 返回带引用信息的结果（限制总数量）
        final_results = sorted_docs[:max_results]
        logger.info(f"检索完成: 总候选={len(all_docs)}, 去重后={len(unique_docs)}, 最终返回={len(final_results)}")
        
        return [{
            "content": d.page_content,
            "metadata": d.metadata,
            "relevance_score": d.metadata.get("vector_score", 0.0),
            "source": d.metadata.get("source", "未知"),
            "chunk_index": d.metadata.get("chunk_index", 0),
            "collection": d.metadata.get("collection", self.collection_name)
        } for d in final_results]
    
    def _select_collections(self, query: str) -> List[str]:
        """
        智能选择相关知识库
        基于查询关键词与知识库名称的语义匹配选择
        """
        try:
            all_collections = self.get_collection_names()
            if not all_collections:
                return [self.collection_name]
            
            # 如果只有一个知识库，直接返回
            if len(all_collections) == 1:
                return all_collections
            
            query_lower = query.lower()
            
            # 从配置文件加载领域关键词
            domain_keywords = _get_domain_keywords()
            
            # 检查查询涉及的领域
            involved_domains = set()
            for domain, keywords in domain_keywords.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        involved_domains.add(domain)
                        break
            
            # 基于领域匹配选择知识库
            selected = []
            for collection in all_collections:
                collection_lower = collection.lower()
                # 1. 如果查询涉及某领域，优先选择包含该领域关键词的知识库
                matched = False
                for domain in involved_domains:
                    domain_kw = domain.lower()
                    if domain_kw in collection_lower or any(kw in collection_lower for kw in domain_keywords.get(domain, [])):
                        selected.append(collection)
                        matched = True
                        break
                # 2. 如果没有领域匹配，选择默认知识库
                if not matched:
                    if collection == self.collection_name or "default" in collection_lower or "base" in collection_lower:
                        if collection not in selected:
                            selected.append(collection)
            
            # 如果没有匹配到任何知识库，返回默认
            if not selected:
                selected = [self.collection_name]
            
            # 限制最多选择3个知识库以平衡性能和相关性
            if len(selected) > 3:
                selected = selected[:3]
            
            logger.info(f"智能选择知识库: {selected} (涉及领域: {list(involved_domains)})")
            return selected
            
        except Exception as e:
            logger.error(f"智能选择知识库失败: {e}")
            return [self.collection_name]
    
    def _deduplicate_docs(self, docs: List[Document]) -> List[Document]:
        """去重文档（基于内容相似度）"""
        if not docs:
            return []
        
        unique = []
        seen_contents = set()
        
        for doc in docs:
            content = doc.page_content[:100]  # 使用前100字符作为去重依据
            if content not in seen_contents:
                seen_contents.add(content)
                unique.append(doc)
        
        return unique

    def get_heatmap(self, topic_level: int = 3, min_frequency: int = 1) -> Dict[str, Any]:
        """获取知识热力图数据"""
        from tools.knowledge_heatmap import generate_knowledge_heatmap
        res = generate_knowledge_heatmap.invoke({
            "collection_name": self.collection_name,
            "topic_level": topic_level,
            "min_frequency": min_frequency
        })
        return json.loads(res)

    def get_hierarchy(self, doc_id: str) -> Dict[str, Any]:
        """获取文档分层结构"""
        from tools.document_hierarchy import build_document_hierarchy
        res = build_document_hierarchy.invoke({
            "document_id": doc_id,
            "collection_name": self.collection_name
        })
        return json.loads(res)

    def _parse_json_docs(self, json_str: str) -> List[Document]:
        """解析工具返回的 JSON 字符串为 Document 列表"""
        try:
            if not json_str: return []
            data = json.loads(json_str)
            
            if isinstance(data, list):
                docs_data = data
            elif isinstance(data, dict):
                if data.get("final_results"):
                    docs_data = data.get("final_results", [])
                else:
                    docs_data = data.get("results", data.get("documents", []))
            else:
                return []

            docs = []
            for d in docs_data:
                content = d.get("content") or d.get("page_content") or d.get("document") or ""
                metadata = d.get("metadata") or {}
                if content:
                    docs.append(Document(page_content=content, metadata=metadata))
            return docs
        except Exception as e:
            logger.error(f"Error parsing JSON docs: {e}")
            return []

    def batch_retrieve(self, queries: List[str], top_k: int = 5) -> Dict[str, Any]:
        """批量检索"""
        results = []
        for query in queries:
            try:
                res = self.smart_retrieve(query, top_k)
                results.append({"query": query, "results": res, "count": len(res)})
            except Exception as e:
                results.append({"query": query, "error": str(e)})
        return {"total": len(queries), "results": results}

    def get_statistics(self, queries: List[str]) -> Dict[str, Any]:
        """检索统计"""
        # 简化版统计
        batch_res = self.batch_retrieve(queries)
        stats = {
            "total": batch_res["total"],
            "success": sum(1 for r in batch_res["results"] if "error" not in r),
            "failed": sum(1 for r in batch_res["results"] if "error" in r)
        }
        return stats

    def get_traceability(self, query: str) -> List[Dict[str, Any]]:
        """获取答案溯源信息（增强版：包含精确位置和引用片段）"""
        from tools.vector_store import get_vector_store
        vector_store = get_vector_store(collection_name=self.collection_name)
        vector_results = vector_store.similarity_search_with_score(query, k=5)
        trace_results = []
        for i, (doc, score) in enumerate(vector_results):
            metadata = doc.metadata or {}
            content = doc.page_content or ""
            raw_score = float(score)
            
            # 提取位置信息
            location = self._extract_location(metadata, content)
            
            # 提取引用片段（前100个字符作为引用）
            quote = content[:100] + "..." if len(content) > 100 else content
            
            # 提取上下文（完整内容作为上下文）
            context = content
            
            trace_results.append({
                "document_name": metadata.get("source") or metadata.get("original_name") or f"文档_{i+1}",
                "content": content,
                "location": location,
                "quote": quote,
                "context": context,
                "score": raw_score,
                "raw_score": raw_score,
                "chunk_index": i,
                "metadata": metadata
            })
        return trace_results
    
    def _extract_location(self, metadata: Dict[str, Any], content: str) -> str:
        """从metadata中提取位置信息"""
        location_parts = []
        
        # 尝试提取章节信息
        if "section" in metadata:
            location_parts.append(f"章节: {metadata['section']}")
        elif "header" in metadata:
            location_parts.append(f"标题: {metadata['header']}")
        
        # 尝试提取页码
        if "page" in metadata:
            location_parts.append(f"第{metadata['page']}页")
        
        # 尝试提取行号范围
        if "start_line" in metadata and "end_line" in metadata:
            location_parts.append(f"行{metadata['start_line']}-{metadata['end_line']}")
        elif "chunk_index" in metadata:
            location_parts.append(f"段落{metadata['chunk_index']}")
        
        # 如果没有任何位置信息，尝试从内容推断
        if not location_parts:
            # 检查内容是否以Markdown标题开头
            lines = content.split('\n')
            for line in lines[:3]:  # 检查前3行
                if line.strip().startswith('#'):
                    location_parts.append(f"章节: {line.strip('#').strip()}")
                    break
        
        return " | ".join(location_parts) if location_parts else "未知位置"

    def compare_methods(self, query: str, methods: Dict[str, bool]) -> Dict[str, Any]:
        """对比不同检索方法的结果"""
        comparison = {}
        top_k = 5
        
        if methods.get('vector'):
            vector_store = get_vector_store(collection_name=self.collection_name)
            results = vector_store.similarity_search_with_score(query, k=top_k)
            scores = [float(s) for d, s in results] if results else []
            avg = sum(scores) / len(scores) if scores else 0.0
            comparison['vector'] = {
                "results": [{"content": d.page_content, "score": float(s), "metadata": d.metadata} for d, s in results],
                "avg_score": avg,
                "time": 0 # 简化处理
            }
            
        if methods.get('bm25'):
            bm25_res = bm25_retrieve.invoke({"query": query, "top_k": top_k})
            docs = self._parse_json_docs(bm25_res)
            scores = []
            normalized = []
            for d in docs:
                sc = d.metadata.get("score") if hasattr(d, "metadata") and d.metadata else 0.0
                if sc is None:
                    sc = 0.0
                scores.append(sc)
                normalized.append({"content": d.page_content, "metadata": d.metadata, "score": sc})
            avg = sum(scores) / len(scores) if scores else 0.0
            comparison['bm25'] = {
                "results": normalized,
                "avg_score": avg,
                "time": 0
            }
            
        if methods.get('hybrid'):
            from tools.hybrid_retriever import hybrid_retrieve
            hybrid_res = hybrid_retrieve.invoke({"query": query, "collection_name": self.collection_name, "top_k": top_k})
            docs = self._parse_json_docs(hybrid_res)
            scores = []
            normalized = []
            for d in docs:
                sc = d.metadata.get("score") if hasattr(d, "metadata") and d.metadata else 0.0
                if sc is None:
                    sc = 0.0
                scores.append(sc)
                normalized.append({"content": d.page_content, "metadata": d.metadata, "score": sc})
            avg = sum(scores) / len(scores) if scores else 0.0
            comparison['hybrid'] = {
                "results": normalized,
                "avg_score": avg,
                "time": 0
            }
            
        return comparison

_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
