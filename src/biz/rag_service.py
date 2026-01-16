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

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name
        self.provider = get_storage_provider()

    async def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None, use_hierarchical: bool = False) -> Dict[str, Any]:
        """全流程入库：加载 -> 分割 -> 存储(S3) -> 向量化(DB)
        
        Args:
            file_path: 文件路径
            metadata: 元数据
            use_hierarchical: 是否使用父子分段模式（默认False）
        """
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
                if clean_c.startswith(("📝 文本分割结果", "📝 Markdown 结构分割结果", "总块数:", "块大小:", "重叠:", "分割规则:", "====")):
                    continue
                if clean_c:
                    chunks.append(clean_c)
                    chunks_metadata_list.append({})
        
        # 3. 持久化原始文件 (ACL)
        with open(file_path, "rb") as f:
            object_key = self.provider.ingest_document(f.read(), os.path.basename(file_path), metadata or {})
            
        # 4. 向量化入库
        vector_store = get_vector_store(collection_name=self.collection_name)
        docs = []
        for i, (chunk, chunk_meta) in enumerate(zip(chunks, chunks_metadata_list)):
            combined_meta = {
                **(metadata or {}),
                **chunk_meta,
                "source": os.path.basename(file_path),
                "object_key": object_key,
                "chunk_index": i
            }
            docs.append(Document(page_content=chunk, metadata=combined_meta))
        vector_store.add_documents(docs)
        
        return {"object_key": object_key, "chunks": len(chunks), "hierarchical": use_hierarchical}

    def smart_retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """智能路由检索：分类 -> 策略选择 -> 执行检索 -> Rerank"""
        # 1. 问题分类
        q_type_json = classify_question_type.invoke({"query": query})
        try:
            q_type_data = json.loads(q_type_json)
            q_type = q_type_data.get("type", "general")
        except json.JSONDecodeError:
            q_type = "general"
        
        # 2. 获取推荐策略
        strategy_res = get_retrieval_strategy.invoke({"question_type": q_type})
        strategy_data = json.loads(strategy_res)
        
        # 修正: 从嵌套的 strategy 字典中获取配置
        strategy = strategy_data.get("strategy", {})
        method = strategy.get("method", "vector")
        use_rerank = strategy.get("use_rerank", True)
        
        logger.info(f"Query: {query} | Type: {q_type} | Strategy: {method} | Rerank: {use_rerank}")
        
        # 3. 执行基础检索
        docs = []
        if method == "vector":
            vector_store = get_vector_store(collection_name=self.collection_name)
            results = vector_store.similarity_search_with_score(query, k=top_k * 3)
            for doc, score in results:
                doc.metadata["vector_score"] = float(score)
                docs.append(doc)
        elif method == "bm25":
            bm25_res = bm25_retrieve.invoke({"query": query, "top_k": top_k * 3})
            docs = self._parse_json_docs(bm25_res)
        else: # hybrid
            from tools.hybrid_retriever import hybrid_retrieve
            hybrid_res = hybrid_retrieve.invoke({
                "query": query,
                "collection_name": self.collection_name,
                "top_k": top_k * 3
            })
            docs = self._parse_json_docs(hybrid_res)

        # 4. Rerank
        if use_rerank and docs:
            rerank_input = json.dumps([
                {"content": d.page_content, "id": str(i), "metadata": d.metadata} 
                for i, d in enumerate(docs)
            ])
            reranked_res = rerank_documents.invoke({
                "query": query,
                "documents": rerank_input,
                "top_n": top_k
            })
            
            try:
                reranked_docs = json.loads(reranked_res)
                # 转换格式为一致的字典列表
                return [{"content": d.get("content", ""), "metadata": d.get("metadata", {}), "relevance_score": d.get("relevance_score", 0.0)} for d in reranked_docs]
            except json.JSONDecodeError:
                logger.error("Failed to parse rerank results, falling back to original docs")
                return [{"content": d.page_content, "metadata": d.metadata} for d in docs[:top_k]]
            
        return [{"content": d.page_content, "metadata": d.metadata} for d in docs[:top_k]]

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
                docs_data = data.get("documents", data.get("results", data.get("final_results", [])))
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
        results = self.smart_retrieve(query, top_k=5)
        trace_results = []
        for i, item in enumerate(results):
            metadata = item.get("metadata", {})
            content = item.get("content", "")
            raw_score = metadata.get("relevance_score") or metadata.get("vector_score") or metadata.get("score") or 0.0
            
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
                "score": item.get("relevance_score", item.get("vector_score", raw_score)),
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
