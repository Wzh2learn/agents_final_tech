"""
Rerank 工具
使用 BGE reranker 模型对检索结果进行重排序
"""
from typing import List, Optional, Literal
from langchain.tools import tool
from langchain_core.documents import Document


# 全局变量存储 reranker 模型
_reranker_model = None
_cross_encoder = None
_device = None


def __dynamic_import():
    """动态导入 reranker 相关库"""
    global _cross_encoder, _device

    # 尝试导入 sentence-transformers
    try:
        from sentence_transformers import CrossEncoder
        import torch

        _cross_encoder = CrossEncoder
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        return True
    except ImportError:
        return False


def _init_reranker(
    model_name: str = "BAAI/bge-reranker-large"
):
    """
    初始化 reranker 模型（惰性加载）

    Args:
        model_name: 模型名称
            - "BAAI/bge-reranker-large": 大模型，效果更好但较慢
            - "BAAI/bge-reranker-base": 基础模型，速度快
    """
    global _reranker_model

    if _reranker_model is not None:
        return _reranker_model

    if _cross_encoder is None:
        raise RuntimeError(
            "Reranker 库未安装，请运行: "
            "pip install sentence-transformers"
        )

    try:
        _reranker_model = _cross_encoder(model_name)
        return _reranker_model
    except Exception as e:
        raise RuntimeError(f"初始化 reranker 模型失败: {str(e)}")


def __parse_documents_input(documents_input: str) -> List[Document]:
    """
    解析输入的文档数据

    Args:
        documents_input: 文档输入，可以是：
            1. 字符串列表（直接使用）
            2. JSON 格式的字符串（需要解析）

    Returns:
        Document 对象列表
    """
    # 如果是列表类型，直接使用
    if isinstance(documents_input, list):
        # 假设每个元素是字符串或字典
        docs = []
        for item in documents_input:
            if isinstance(item, str):
                docs.append(Document(page_content=item))
            elif isinstance(item, dict):
                docs.append(
                    Document(
                        page_content=item.get('content', ''),
                        metadata=item.get('metadata', {})
                    )
                )
        return docs

    # 如果是字符串，尝试解析 JSON
    elif isinstance(documents_input, str):
        try:
            import json
            data = json.loads(documents_input)

            if isinstance(data, list):
                docs = []
                for item in data:
                    if isinstance(item, str):
                        docs.append(Document(page_content=item))
                    elif isinstance(item, dict):
                        docs.append(
                            Document(
                                page_content=item.get('content', ''),
                                metadata=item.get('metadata', {})
                            )
                        )
                return docs
            else:
                raise ValueError("JSON 数据应该是列表格式")
        except json.JSONDecodeError:
            # 如果不是 JSON，当作单个文档处理
            return [Document(page_content=documents_input)]

    raise ValueError(f"无法解析文档输入: {type(documents_input)}")


@tool
def rerank_documents(
    query: str,
    documents: str,
    model_name: Optional[str] = "BAAI/bge-reranker-large",
    top_n: Optional[int] = 5
) -> str:
    """
    使用 BGE reranker 对检索结果进行重排序

    Args:
        query: 用户查询
        documents: 文档列表（JSON 字符串格式）
            格式示例:
            [
                {"content": "文档1内容", "metadata": {"source": "doc1"}},
                {"content": "文档2内容", "metadata": {"source": "doc2"}}
            ]
            或简单字符串列表:
            ["文档1", "文档2", "文档3"]
        model_name: reranker 模型名称
            - "BAAI/bge-reranker-large": 大模型（默认）
            - "BAAI/bge-reranker-base": 基础模型（更快）
        top_n: 返回的 top-k 结果数

    Returns:
        重排序后的文档列表（带相关性分数）

    Raises:
        ValueError: 如果参数无效
        RuntimeError: 如果模型未安装
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    if not documents:
        raise ValueError("文档列表不能为空")

    # 解析文档输入
    doc_list = __parse_documents_input(documents)

    # 初始化 reranker 模型
    model = _init_reranker(model_name)

    try:
        # 准备输入：query + document 对
        inputs = []
        for doc in doc_list:
            inputs.append([query, doc.page_content])

        # 执行 rerank
        scores = model.predict(inputs)

        # 组合分数和文档
        ranked_docs = []
        for doc, score in zip(doc_list, scores):
            ranked_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })

        # 按分数降序排序
        ranked_docs.sort(key=lambda x: x["score"], reverse=True)

        # 返回 top_n 结果
        top_docs = ranked_docs[:top_n]

        # 格式化输出
        result = f"🔄 Rerank 重排序结果\n"
        result += f"模型: {model_name}\n"
        result += f"查询: {query}\n"
        result += f"原始文档数: {len(doc_list)}\n"
        result += f"返回 top-{top_n}\n"
        result += "=" * 50 + "\n\n"

        for i, doc_info in enumerate(top_docs, 1):
            result += f"【排名 {i}】相关性分数: {doc_info['score']:.4f}\n"
            result += f"内容: {doc_info['content'][:200]}...\n"
            if doc_info.get('metadata'):
                result += f"元数据: {doc_info['metadata']}\n"
            result += "\n"

        return result

    except Exception as e:
        raise RuntimeError(f"Rerank 执行失败: {str(e)}")


@tool
def rerank_simple(
    query: str,
    text_list: str,
    top_k: Optional[int] = 3
) -> str:
    """
    简单的文本重排序（无需元数据）

    Args:
        query: 查询文本
        text_list: 文本列表（JSON 字符串格式）
            例如: '["文本1", "文本2", "文本3"]'
        top_k: 返回 top-k 结果

    Returns:
        排序后的文本（带分数）

    Raises:
        ValueError: 如果参数无效
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    # 解析文本列表
    try:
        import json
        texts = json.loads(text_list)
        if not isinstance(texts, list):
            raise ValueError("text_list 应该是 JSON 数组")
    except json.JSONDecodeError:
        raise ValueError("text_list 应该是有效的 JSON 数组格式")

    if not texts:
        raise ValueError("文本列表不能为空")

    # 初始化 reranker
    model = _init_reranker()

    try:
        # 准备输入
        inputs = [[query, text] for text in texts]

        # 执行 rerank
        scores = model.predict(inputs)

        # 组合分数和文本
        ranked_texts = []
        for text, score in zip(texts, scores):
            ranked_texts.append({
                "text": text,
                "score": float(score)
            })

        # 按分数降序排序
        ranked_texts.sort(key=lambda x: x["score"], reverse=True)

        # 返回 top-k 结果
        top_texts = ranked_texts[:top_k]

        # 格式化输出
        result = f"🔄 重排序结果 (top-{top_k})\n"
        result += "=" * 40 + "\n"
        for i, item in enumerate(top_texts, 1):
            result += f"{i}. [{item['score']:.4f}] {item['text'][:150]}\n"

        return result

    except Exception as e:
        raise RuntimeError(f"重排序失败: {str(e)}")


@tool
def get_rerank_info() -> str:
    """
    获取 reranker 模型信息

    Returns:
        模型信息和状态
    """
    info = {
        "模型状态": "已加载" if _reranker_model else "未加载",
        "设备": _device if _device else "未检测",
        "默认模型": "BAAI/bge-reranker-large",
        "可选模型": [
            "BAAI/bge-reranker-large (推荐，效果更好)",
            "BAAI/bge-reranker-base (更快，适合实时应用)"
        ],
        "安装命令": "pip install sentence-transformers"
    }

    result = "📊 Reranker 模型信息\n"
    result += "=" * 40 + "\n"
    for key, value in info.items():
        if isinstance(value, list):
            result += f"{key}:\n"
            for v in value:
                result += f"  - {v}\n"
        else:
            result += f"{key}: {value}\n"

    return result
