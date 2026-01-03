"""
BM25 全文检索工具
基于关键词的全文检索，与向量检索互补
"""
import json
import pickle
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.tools import tool
from langchain_core.documents import Document

# 动态导入rank_bm25，避免静态类型检查错误
try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False
    BM25Okapi = None

# 导入向量存储
from tools.vector_store import get_vector_store


# BM25索引缓存目录
BM25_CACHE_DIR = "/tmp/bm25_cache"


def _get_cache_path(collection_name: str) -> str:
    """获取BM25索引的缓存文件路径"""
    Path(BM25_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    return f"{BM25_CACHE_DIR}/{collection_name}.pkl"


def _compute_docs_hash(documents: List[str]) -> str:
    """计算文档内容的哈希值"""
    content = "\n".join(documents)
    return hashlib.md5(content.encode()).hexdigest()


def _tokenize(text: str, language: str = "zh") -> List[str]:
    """
    文本分词

    Args:
        text: 文本内容
        language: 语言（zh=中文，en=英文）

    Returns:
        分词结果列表
    """
    if not text:
        return []

    # 中文分词（简单实现：按字符分词+保留完整词）
    if language == "zh":
        # 先尝试保留中文词组（长度2-4）
        tokens = []
        i = 0
        while i < len(text):
            # 尝试匹配4字词
            if i + 3 < len(text):
                tokens.append(text[i:i+4])
            # 尝试匹配3字词
            if i + 2 < len(text):
                tokens.append(text[i:i+3])
            # 尝试匹配2字词
            if i + 1 < len(text):
                tokens.append(text[i:i+2])
            # 单字
            if text[i].strip():
                tokens.append(text[i])
            i += 1
        return tokens
    else:
        # 英文分词：按空格和标点分割
        import re
        tokens = re.findall(r'\w+', text.lower())
        return tokens


def _build_bm25_index(collection_name: str, force_rebuild: bool = False) -> Dict[str, Any]:
    """
    构建或加载BM25索引

    Args:
        collection_name: 集合名称
        force_rebuild: 是否强制重建索引

    Returns:
        包含BM25索引和元数据的字典
    """
    cache_path = _get_cache_path(collection_name)

    # 尝试从缓存加载
    if not force_rebuild and Path(cache_path).exists():
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"加载BM25缓存失败: {e}, 将重建索引")

    # 从向量数据库获取所有文档
    try:
        vector_store = get_vector_store(collection_name=collection_name)

        # 获取所有文档
        # 注意：这里需要根据具体的向量存储实现调整
        # 暂时使用简化的方法，实际可能需要调用底层API
        all_docs = []

        # 尝试获取文档（简化实现）
        # 实际应该通过vector_store的API获取所有文档
        # 这里先返回空索引，实际使用时需要完善
        print(f"警告: BM25索引构建需要访问向量数据库中的所有文档")
        print(f"当前集合: {collection_name}")

        # 返回空索引
        return {
            "bm25": None,
            "documents": [],
            "tokenized_docs": [],
            "doc_count": 0,
            "cache_path": cache_path
        }

    except Exception as e:
        print(f"构建BM25索引失败: {e}")
        return {
            "bm25": None,
            "documents": [],
            "tokenized_docs": [],
            "doc_count": 0,
            "error": str(e),
            "cache_path": cache_path
        }


def _build_bm25_index_from_documents(
    documents: List[Dict[str, Any]],
    cache_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    从文档列表构建BM25索引

    Args:
        documents: 文档列表，每个文档包含 text 和 metadata
        cache_path: 缓存文件路径（可选）

    Returns:
        包含BM25索引和元数据的字典
    """
    if not documents:
        return {
            "bm25": None,
            "documents": [],
            "tokenized_docs": [],
            "doc_count": 0
        }

    # 提取文本并分词
    tokenized_docs = []
    for doc in documents:
        text = doc.get("text", doc.get("page_content", ""))
        tokens = _tokenize(text, language="zh")
        tokenized_docs.append(tokens)

    # 构建BM25索引
    bm25 = BM25Okapi(tokenized_docs)

    index_data = {
        "bm25": bm25,
        "documents": documents,
        "tokenized_docs": tokenized_docs,
        "doc_count": len(documents)
    }

    # 缓存索引
    if cache_path:
        try:
            Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'wb') as f:
                pickle.dump(index_data, f)
        except Exception as e:
            print(f"缓存BM25索引失败: {e}")

    return index_data


def _bm25_retrieve_internal(
    query: str,
    documents: str = "[]",
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5,
    k1: Optional[float] = 1.5,
    b: Optional[float] = 0.75
) -> str:
    """
    BM25 全文检索（内部函数，供其他工具调用）

    Args:
        query: 查询文本
        documents: 文档列表（JSON字符串），如果为空则尝试从向量数据库加载
        collection_name: 向量集合名称（仅当documents为空时使用）
        top_k: 返回的文档数量
        k1: BM25参数k1（控制词频饱和度，默认1.5）
        b: BM25参数b（控制文档长度归一化，默认0.75）

    Returns:
        JSON 格式的检索结果
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    # 解析文档列表
    try:
        docs_list = json.loads(documents) if documents else []
    except json.JSONDecodeError:
        docs_list = []

    # 构建或加载BM25索引
    if docs_list:
        # 使用提供的文档构建索引
        index_data = _build_bm25_index_from_documents(docs_list)
    else:
        # 尝试从向量数据库加载索引
        index_data = _build_bm25_index(collection_name)

    # 检查索引是否有效
    if index_data.get("bm25") is None:
        error_msg = index_data.get("error", "BM25索引未初始化")
        return json.dumps({
            "query": query,
            "method": "bm25",
            "results": [],
            "error": error_msg,
            "count": 0
        }, ensure_ascii=False, indent=2)

    try:
        # 对查询进行分词
        tokenized_query = _tokenize(query, language="zh")

        # 执行BM25检索
        bm25 = index_data["bm25"]
        scores = bm25.get_scores(tokenized_query)

        # 获取top_k结果
        top_indices = scores.argsort()[-top_k:][::-1]

        # 构建结果
        results = []
        for idx in top_indices:
            if idx < len(index_data["documents"]):
                doc = index_data["documents"][idx]
                results.append({
                    "document": doc.get("text", doc.get("page_content", "")),
                    "metadata": doc.get("metadata", {}),
                    "bm25_score": float(scores[idx]),
                    "index": int(idx)
                })

        # 格式化输出
        output = {
            "query": query,
            "method": "bm25",
            "parameters": {
                "k1": k1,
                "b": b,
                "top_k": top_k
            },
            "results": results,
            "count": len(results)
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "query": query,
            "method": "bm25",
            "results": [],
            "error": str(e),
            "count": 0
        }, ensure_ascii=False, indent=2)


@tool
def bm25_retrieve(
    query: str,
    documents: str = "[]",
    collection_name: Optional[str] = "knowledge_base",
    top_k: Optional[int] = 5,
    k1: Optional[float] = 1.5,
    b: Optional[float] = 0.75
) -> str:
    """
    BM25 全文检索（工具函数，供Agent调用）

    Args:
        query: 查询文本
        documents: 文档列表（JSON字符串），如果为空则尝试从向量数据库加载
        collection_name: 向量集合名称（仅当documents为空时使用）
        top_k: 返回的文档数量
        k1: BM25参数k1（控制词频饱和度，默认1.5）
        b: BM25参数b（控制文档长度归一化，默认0.75）

    Returns:
        JSON 格式的检索结果
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    # 解析文档列表
    try:
        docs_list = json.loads(documents) if documents else []
    except json.JSONDecodeError:
        docs_list = []

    # 构建或加载BM25索引
    if docs_list:
        # 使用提供的文档构建索引
        index_data = _build_bm25_index_from_documents(docs_list)
    else:
        # 尝试从向量数据库加载索引
        index_data = _build_bm25_index(collection_name)

    # 检查索引是否有效
    if index_data.get("bm25") is None:
        error_msg = index_data.get("error", "BM25索引未初始化")
        return json.dumps({
            "query": query,
            "method": "bm25",
            "results": [],
            "error": error_msg,
            "count": 0
        }, ensure_ascii=False, indent=2)

    try:
        # 对查询进行分词
        tokenized_query = _tokenize(query, language="zh")

        # 执行BM25检索
        bm25 = index_data["bm25"]
        scores = bm25.get_scores(tokenized_query)

        # 获取top_k结果
        top_indices = scores.argsort()[-top_k:][::-1]

        # 构建结果
        results = []
        for idx in top_indices:
            if idx < len(index_data["documents"]):
                doc = index_data["documents"][idx]
                results.append({
                    "document": doc.get("text", doc.get("page_content", "")),
                    "metadata": doc.get("metadata", {}),
                    "bm25_score": float(scores[idx]),
                    "index": int(idx)
                })

        # 格式化输出
        output = {
            "query": query,
            "method": "bm25",
            "parameters": {
                "k1": k1,
                "b": b,
                "top_k": top_k
            },
            "count": len(results),
            "results": results
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "query": query,
            "method": "bm25",
            "results": [],
            "error": f"BM25检索失败: {str(e)}",
            "count": 0
        }, ensure_ascii=False, indent=2)


@tool
def clear_bm25_cache(collection_name: Optional[str] = None) -> str:
    """
    清除BM25索引缓存

    Args:
        collection_name: 集合名称，如果为None则清除所有缓存

    Returns:
        操作结果
    """
    try:
        cache_dir = Path(BM25_CACHE_DIR)

        if not cache_dir.exists():
            return f"缓存目录不存在: {BM25_CACHE_DIR}"

        if collection_name:
            # 清除特定集合的缓存
            cache_path = cache_dir / f"{collection_name}.pkl"
            if cache_path.exists():
                cache_path.unlink()
                return f"已清除集合 '{collection_name}' 的BM25缓存"
            else:
                return f"集合 '{collection_name}' 的BM25缓存不存在"
        else:
            # 清除所有缓存
            cache_files = list(cache_dir.glob("*.pkl"))
            for f in cache_files:
                f.unlink()
            return f"已清除 {len(cache_files)} 个BM25缓存文件"

    except Exception as e:
        return f"清除缓存失败: {str(e)}"
