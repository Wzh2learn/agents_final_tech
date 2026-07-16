"""
RAG 业务逻辑层
统一封装检索、重排序与知识库维护逻辑。
"""
import json
import logging
import os
import asyncio
import re
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document
from tools.vector_store import get_vector_store
from tools.reranker_tool import rerank_documents
from tools.bm25_retriever import bm25_retrieve
from tools.question_classifier import classify_question_type, get_retrieval_strategy
from tools.document_loader import load_document, get_document_info
from tools.text_splitter import split_text_recursive, split_text_by_markdown_structure, hierarchical_split
from storage.provider import get_storage_provider
from utils.cache import get_cache
from utils.config_loader import get_config

logger = logging.getLogger(__name__)

# 单例锁，确保线程安全
_rag_service_lock = asyncio.Lock()
_rag_service = None

_RUNTIME_RAG_SETTINGS_CACHE_KEY = "runtime_rag_settings"


def _get_runtime_rag_settings() -> Dict[str, Any]:
    try:
        value = get_cache().get(_RUNTIME_RAG_SETTINGS_CACHE_KEY)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def get_runtime_rag_settings() -> Dict[str, Any]:
    return _get_runtime_rag_settings()


def set_runtime_rag_settings(settings: Dict[str, Any], ttl_seconds: int = 86400) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key in ("top_k", "max_results", "use_rerank", "rerank_top_n"):
        if key in settings and settings.get(key) is not None:
            safe[key] = settings.get(key)

    get_cache().set(_RUNTIME_RAG_SETTINGS_CACHE_KEY, safe, ttl=ttl_seconds)
    return safe

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
        doc = load_document.invoke({"file_path": file_path})
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        
        # 2. 分割
        if use_hierarchical:
            # 使用父子分段模式
            chunks_docs = hierarchical_split(doc, parent_chunk_size=2000, child_chunk_size=500)
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
        top_k: Optional[int] = None,
        collection_names: Optional[List[str]] = None,
        max_results: Optional[int] = None,
        use_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        固定检索：总是检索知识库，支持多知识库智能选择
        
        Args:
            query: 查询内容
            top_k: 每个知识库返回结果数量
            collection_names: 指定要检索的知识库列表，None则智能选择
            max_results: 最大总返回结果数量（默认10）
        """
        runtime_settings = _get_runtime_rag_settings()
        config = get_config()

        if top_k is None:
            top_k = runtime_settings.get("top_k")
            if top_k is None:
                top_k = config.get("rag.default_top_k", 5)

        if max_results is None:
            max_results = runtime_settings.get("max_results")
            if max_results is None:
                max_results = 10

        if use_rerank is None and "use_rerank" in runtime_settings:
            use_rerank = bool(runtime_settings.get("use_rerank"))

        if rerank_top_n is None:
            runtime_top_n = runtime_settings.get("rerank_top_n")
            if runtime_top_n is not None:
                rerank_top_n = runtime_top_n

        max_results = max(1, min(int(max_results), 50))
        top_k = max(1, min(int(top_k), 20))
        
        # 1. 智能选择知识库（如果不指定）
        if not collection_names:
            collection_names = self._select_collections(query)

        # 1.1 归一化并校验集合名，避免无效集合导致检索全空
        collection_names = [name for name in (collection_names or []) if name]
        try:
            available_collections = self.get_collection_names()
        except Exception as e:
            logger.warning(f"Get collection names failed during retrieval: {e}")
            available_collections = []

        if available_collections:
            valid_names = [name for name in collection_names if name in available_collections]
            if not valid_names:
                valid_names = available_collections[:3]
                logger.warning(
                    "No valid target collection in %s, fallback to available collections: %s",
                    collection_names,
                    valid_names
                )
            collection_names = valid_names

        if not collection_names:
            collection_names = [self.collection_name]
        
        logger.info(f"Query: {query} | Collections: {collection_names} | TopK: {top_k} | MaxResults: {max_results}")
        
        # 2. 固定使用混合检索策略（向量 + BM25）
        all_docs = []
        vector_total = 0
        bm25_total = 0
        fallback_total = 0
        
        for collection_name in collection_names:
            vector_count = 0
            bm25_count = 0
            fallback_count = 0

            try:
                vector_store = get_vector_store(collection_name=collection_name)
                results = vector_store.similarity_search_with_score(query, k=top_k)
                for doc, score in results:
                    doc.metadata["vector_score"] = float(score)
                    doc.metadata["collection"] = collection_name
                    all_docs.append(doc)
                    vector_count += 1
            except Exception as e:
                logger.warning(f"Vector retrieve failed on {collection_name}: {e}")

            try:
                bm25_res = bm25_retrieve.invoke({
                    "query": query,
                    "top_k": top_k,
                    "collection_name": collection_name
                })
                bm25_docs = self._parse_json_docs(bm25_res)
                for doc in bm25_docs:
                    doc.metadata["collection"] = collection_name
                    all_docs.append(doc)
                    bm25_count += 1
            except Exception as e:
                logger.warning(f"BM25 retrieve failed on {collection_name}: {e}")

            if vector_count == 0 and bm25_count == 0:
                fallback_docs = self._local_fallback_docs(
                    query=query,
                    collection_name=collection_name,
                    limit=top_k
                )
                for doc in fallback_docs:
                    doc.metadata["collection"] = collection_name
                    doc.metadata["fallback"] = True
                    all_docs.append(doc)
                    fallback_count += 1

            vector_total += vector_count
            bm25_total += bm25_count
            fallback_total += fallback_count
            logger.info(
                f"Retrieve path on {collection_name}: vector={vector_count}, bm25={bm25_count}, fallback={fallback_count}"
            )
        
        # 3. 去重并合并结果（合并向量/BM25分数）
        unique_docs = self._deduplicate_docs(all_docs)

        # 4. 计算综合分数（向量相似度 + BM25）
        vector_weight, bm25_weight = self._get_score_weights()
        max_bm25 = self._get_max_bm25_score(unique_docs)
        for doc in unique_docs:
            vector_sim = self._to_similarity(doc.metadata.get("vector_score"))
            bm25_score = doc.metadata.get("bm25_score")
            bm25_sim = 0.0
            if bm25_score is not None and max_bm25 > 0:
                bm25_sim = float(bm25_score) / max_bm25
            combined = (vector_weight * (vector_sim or 0.0)) + (bm25_weight * (bm25_sim or 0.0))
            doc.metadata["combined_score"] = combined

        # 5. 先按综合分数排序
        sorted_docs = sorted(unique_docs, key=lambda x: x.metadata.get("combined_score", 0), reverse=True)

        # 6. 可选：Rerank 重排序
        sorted_docs = self._maybe_rerank(query, sorted_docs, use_rerank=use_rerank, rerank_top_n=rerank_top_n)

        # 7. 返回带引用信息的结果（限制总数量）
        final_results = sorted_docs[:max_results]
        logger.info(
            "Retrieve finished: candidates=%s, unique=%s, returned=%s, vector=%s, bm25=%s, fallback=%s",
            len(all_docs),
            len(unique_docs),
            len(final_results),
            vector_total,
            bm25_total,
            fallback_total
        )

        return [{
            "content": d.page_content,
            "metadata": d.metadata,
            "relevance_score": d.metadata.get("rerank_score") or d.metadata.get("combined_score", 0.0),
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
        """去重文档（基于内容相似度），并合并分数字段"""
        if not docs:
            return []

        unique: List[Document] = []
        seen_contents: Dict[str, Document] = {}

        for doc in docs:
            content_key = doc.page_content[:100]  # 使用前100字符作为去重依据
            if content_key not in seen_contents:
                seen_contents[content_key] = doc
                unique.append(doc)
            else:
                existing = seen_contents[content_key]
                self._merge_doc_metadata(existing, doc)

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

    def get_hierarchy(self, doc_id: str, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """获取文档分层结构"""
        from tools.document_hierarchy import build_document_hierarchy
        res = build_document_hierarchy.invoke({
            "document_id": doc_id,
            "collection_name": collection_name or self.collection_name
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
                bm25_score = d.get("bm25_score") or d.get("score")
                if bm25_score is not None:
                    try:
                        metadata["bm25_score"] = float(bm25_score)
                    except (TypeError, ValueError):
                        pass
                if content:
                    docs.append(Document(page_content=content, metadata=metadata))
            return docs
        except Exception as e:
            logger.error(f"Error parsing JSON docs: {e}")
            return []

    @staticmethod
    def _query_terms(query: str) -> List[str]:
        normalized = (query or "").strip().lower()
        if not normalized:
            return []
        latin_terms = [term for term in re.findall(r"[a-z0-9_]+", normalized) if len(term) > 1]
        cjk_terms = re.findall(r"[\u4e00-\u9fff]", normalized)
        merged = latin_terms + cjk_terms
        unique_terms: List[str] = []
        seen = set()
        for term in merged:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        return unique_terms

    def _local_fallback_docs(self, query: str, collection_name: str, limit: int = 5) -> List[Document]:
        """本地兜底：向量/BM25均失败时，直接从数据库提取相关片段。"""
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        db = get_session()
        try:
            manager = DocumentManager()
            candidate_docs = manager.get_documents(
                db=db,
                skip=0,
                limit=max(limit * 3, 15),
                collection_name=collection_name
            )
            if not candidate_docs:
                return []

            query_terms = self._query_terms(query)
            lowered_query = (query or "").strip().lower()
            scored_docs: List[Tuple[float, Document]] = []

            for doc_info in candidate_docs:
                source_name = doc_info.get("original_name") or doc_info.get("id") or doc_info.get("name")
                if not source_name:
                    continue
                chunks = manager.get_document_chunks(
                    db=db,
                    document_name=source_name,
                    collection_name=collection_name,
                    skip=0,
                    limit=5
                )
                for chunk in chunks:
                    content = (chunk.get("content") or "").strip()
                    if not content:
                        continue
                    lowered = content.lower()
                    score_value = float(sum(1 for term in query_terms if term and term in lowered))
                    if lowered_query and lowered_query in lowered:
                        score_value += 1.0

                    metadata = chunk.get("metadata") or {}
                    metadata["source"] = metadata.get("source") or doc_info.get("name") or str(source_name)
                    metadata["bm25_score"] = score_value
                    metadata["retrieval_path"] = "local_fallback"
                    metadata["collection"] = collection_name
                    scored_docs.append((score_value, Document(page_content=content, metadata=metadata)))

            if not scored_docs:
                return []

            scored_docs.sort(key=lambda item: item[0], reverse=True)
            positive_docs = [doc for score_value, doc in scored_docs if score_value > 0]
            if positive_docs:
                return positive_docs[:limit]
            return [doc for _score_value, doc in scored_docs[:limit]]
        except Exception as e:
            logger.warning(f"Local fallback retrieval failed on {collection_name}: {e}")
            return []
        finally:
            db.close()

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

    def get_traceability(self, query: str, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取答案溯源信息（增强版：包含精确位置和引用片段）"""
        from tools.vector_store import get_vector_store
        vector_store = get_vector_store(collection_name=collection_name or self.collection_name)
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

    def compare_methods(self, query: str, methods: Dict[str, bool], collection_name: Optional[str] = None) -> Dict[str, Any]:
        """对比不同检索方法的结果"""
        comparison = {}
        top_k = 5
        target_collection = collection_name or self.collection_name
        
        if methods.get('vector'):
            vector_store = get_vector_store(collection_name=target_collection)
            results = vector_store.similarity_search_with_score(query, k=top_k)
            scores = [float(s) for d, s in results] if results else []
            avg = sum(scores) / len(scores) if scores else 0.0
            comparison['vector'] = {
                "results": [{"content": d.page_content, "score": float(s), "metadata": d.metadata} for d, s in results],
                "avg_score": avg,
                "time": 0 # 简化处理
            }
            
        if methods.get('bm25'):
            bm25_res = bm25_retrieve.invoke({"query": query, "top_k": top_k, "collection_name": target_collection})
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
            hybrid_res = hybrid_retrieve.invoke({"query": query, "collection_name": target_collection, "top_k": top_k})
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

    @staticmethod
    def _to_similarity(score: Optional[float]) -> Optional[float]:
        """将向量距离/分数转换为相似度（高分更好）"""
        if score is None:
            return None
        try:
            value = float(score)
        except (TypeError, ValueError):
            return None
        if value < 0:
            return -value
        # 兼容距离分数：越小越相似
        return 1.0 / (1.0 + value)

    @staticmethod
    def _get_max_bm25_score(docs: List[Document]) -> float:
        max_score = 0.0
        for doc in docs:
            try:
                score = float(doc.metadata.get("bm25_score") or 0.0)
                if score > max_score:
                    max_score = score
            except (TypeError, ValueError):
                continue
        return max_score

    @staticmethod
    def _get_score_weights() -> Tuple[float, float]:
        """获取向量与BM25权重"""
        try:
            config = get_config()
            vector_weight = float(config.get("rag.vector_weight", 0.6))
            bm25_weight = float(config.get("rag.bm25_weight", 0.4))
        except Exception:
            vector_weight, bm25_weight = 0.6, 0.4
        total = vector_weight + bm25_weight
        if total <= 0:
            return 0.6, 0.4
        return vector_weight / total, bm25_weight / total

    def _merge_doc_metadata(self, target: Document, incoming: Document) -> None:
        """合并去重时的分数字段与关键信息"""
        if not target.metadata:
            target.metadata = {}
        if not incoming.metadata:
            return

        # 合并 collection/source 等信息
        for key in ("collection", "source", "object_key", "chunk_index"):
            if key not in target.metadata and key in incoming.metadata:
                target.metadata[key] = incoming.metadata[key]

        # 合并向量分数（选择更优的相似度）
        incoming_vector = incoming.metadata.get("vector_score")
        target_vector = target.metadata.get("vector_score")
        if incoming_vector is not None:
            if target_vector is None:
                target.metadata["vector_score"] = incoming_vector
            else:
                if (self._to_similarity(incoming_vector) or 0.0) > (self._to_similarity(target_vector) or 0.0):
                    target.metadata["vector_score"] = incoming_vector

        # 合并 BM25 分数（取更大）
        incoming_bm25 = incoming.metadata.get("bm25_score")
        target_bm25 = target.metadata.get("bm25_score")
        if incoming_bm25 is not None:
            if target_bm25 is None or float(incoming_bm25) > float(target_bm25):
                target.metadata["bm25_score"] = incoming_bm25

    def _maybe_rerank(
        self,
        query: str,
        docs: List[Document],
        use_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
    ) -> List[Document]:
        """可选 Rerank（失败时回退原排序）"""
        if not docs:
            return docs

        try:
            config = get_config()
            rerank_enabled = bool(config.get("rerank.enabled", False))
            force_rerank = bool(config.get("rag.force_rerank", False))
            default_rerank = bool(config.get("rag.use_rerank_by_default", False))
            if not rerank_enabled:
                return docs

            # 显式覆盖：允许 UI/调用方强制开启/关闭 rerank（优先级最高）
            if use_rerank is not None:
                if not use_rerank:
                    return docs
            else:
                if not (force_rerank or default_rerank):
                    return docs
        except Exception:
            return docs

        try:
            payload = []
            for i, doc in enumerate(docs):
                payload.append({
                    "id": str(i),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })

            if rerank_top_n is None:
                runtime_settings = _get_runtime_rag_settings()
                if "rerank_top_n" in runtime_settings and runtime_settings.get("rerank_top_n") is not None:
                    rerank_top_n = int(runtime_settings.get("rerank_top_n"))
                else:
                    rerank_top_n = int(get_config().get("rag.default_top_n", 5))

            reranked_str = rerank_documents.invoke({
                "query": query,
                "documents": json.dumps(payload, ensure_ascii=False),
                "top_n": rerank_top_n
            })

            reranked_data = json.loads(reranked_str) if reranked_str else []
            if isinstance(reranked_data, dict) and "ranked_docs" in reranked_data:
                reranked_data = reranked_data["ranked_docs"]

            if not isinstance(reranked_data, list) or not reranked_data:
                return docs

            ordered = []
            used = set()
            for item in reranked_data:
                doc_id = item.get("id")
                if doc_id is None:
                    continue
                try:
                    idx = int(doc_id)
                except (TypeError, ValueError):
                    continue
                if idx < 0 or idx >= len(docs) or idx in used:
                    continue
                doc = docs[idx]
                rerank_score = item.get("relevance_score") or item.get("score")
                if rerank_score is not None:
                    doc.metadata["rerank_score"] = rerank_score
                reason = item.get("reason")
                if reason:
                    doc.metadata["rerank_reason"] = reason
                ordered.append(doc)
                used.add(idx)

            # 追加未出现的文档
            for i, doc in enumerate(docs):
                if i not in used:
                    ordered.append(doc)

            return ordered
        except Exception as e:
            logger.warning(f"Rerank failed, fallback to combined score: {e}")
            return docs

async def get_rag_service() -> RAGService:
    """获取 RAGService 单例（线程安全）"""
    global _rag_service
    if _rag_service is None:
        async with _rag_service_lock:
            if _rag_service is None:
                _rag_service = RAGService()
    return _rag_service

# 同步版本供非异步上下文使用
def get_rag_service_sync() -> RAGService:
    """同步获取 RAGService 单例（注意：可能非线程安全，仅在初始化阶段使用）"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
