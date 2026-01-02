"""
Rerank 工具
使用大语言模型对检索结果进行重排序
"""
import os
import json
from typing import List, Optional
from langchain.tools import tool
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def __parse_documents_input(documents_input: str) -> List[dict]:
    """
    解析输入的文档数据

    Args:
        documents_input: 文档输入，可以是：
            1. JSON 格式的字符串（需要解析）

    Returns:
        文档字典列表
    """
    # 如果是字符串，尝试解析 JSON
    if isinstance(documents_input, str):
        try:
            data = json.loads(documents_input)

            if isinstance(data, list):
                return data
            else:
                raise ValueError("JSON 数据应该是列表格式")
        except json.JSONDecodeError:
            raise ValueError(f"无法解析 JSON 文档输入: {documents_input[:100]}...")

    raise ValueError(f"文档输入应该是 JSON 字符串，当前类型: {type(documents_input)}")


@tool
def rerank_documents(
    query: str,
    documents: str,
    top_n: Optional[int] = 5
) -> str:
    """
    使用大语言模型对检索结果进行重排序

    Args:
        query: 用户查询
        documents: 文档列表（JSON 字符串格式）
            格式示例:
            [
                {"content": "文档1内容", "id": "1"},
                {"content": "文档2内容", "id": "2"}
            ]
        top_n: 返回的 top-k 结果数（默认 5）

    Returns:
        重排序后的文档列表（带相关性分数）

    Raises:
        ValueError: 如果参数无效
        RuntimeError: 如果LLM调用失败
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    if not documents:
        raise ValueError("文档列表不能为空")

    # 解析文档输入
    doc_list = __parse_documents_input(documents)

    # 限制 top_n 不超过文档总数
    top_n = min(top_n, len(doc_list))

    try:
        # 获取环境变量
        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

        if not api_key or not base_url:
            raise RuntimeError("未找到必要的环境变量")

        # 创建 LLM
        llm = ChatOpenAI(
            model="doubao-seed-1-6-251015",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,  # 低温度以获得稳定排序
            max_tokens=1000,
        )

        # 构建提示词
        system_prompt = """你是一个专业的文档相关性评估专家。你的任务是根据查询对文档进行相关性评分和排序。

评分标准：
- 1.0: 完全相关，直接回答了查询问题
- 0.8-0.9: 高度相关，提供了查询所需的大部分信息
- 0.6-0.7: 中度相关，部分回答了查询问题
- 0.4-0.5: 低度相关，仅提供少量相关信息
- 0.0-0.3: 不相关或几乎不相关

请严格按照以下JSON格式输出，不要输出其他任何内容：
```json
{
  "ranked_docs": [
    {
      "id": "文档ID",
      "score": 0.95,
      "reason": "简短说明相关性原因"
    }
  ]
}
```"""

        # 准备文档列表
        docs_text = ""
        for i, doc in enumerate(doc_list):
            content = doc.get("content", doc.get("text", ""))[:300]
            doc_id = doc.get("id", str(i))
            docs_text += f"\n文档 {doc_id}:\n{content}\n"

        user_message = f"""查询：{query}

待排序文档：
{docs_text}

请对以上文档进行相关性评分和排序，返回 JSON 格式的结果。"""

        # 调用 LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)

        # 解析响应
        response_content = response.content

        # 如果是列表，合并成字符串
        if isinstance(response_content, list):
            response_text = "".join(str(item) for item in response_content)
        else:
            response_text = str(response_content)

        # 提取 JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text.strip()

        # 解析 JSON
        try:
            result_data = json.loads(json_text)
            ranked_docs = result_data.get("ranked_docs", [])
        except json.JSONDecodeError:
            # 如果解析失败，返回原始顺序
            ranked_docs = []
            for i, doc in enumerate(doc_list):
                ranked_docs.append({
                    "id": doc.get("id", str(i)),
                    "score": 0.5,
                    "reason": "JSON 解析失败，保持原始顺序"
                })

        # 将分数映射到原始文档
        doc_dict = {doc.get("id", str(i)): doc for i, doc in enumerate(doc_list)}

        # 按 id 匹配并重新排序
        ranked_results = []
        for ranked_item in ranked_docs:
            doc_id = ranked_item.get("id")
            if doc_id in doc_dict:
                original_doc = doc_dict[doc_id]
                original_doc["relevance_score"] = ranked_item.get("score", 0.5)
                original_doc["reason"] = ranked_item.get("reason", "")
                ranked_results.append(original_doc)

        # 如果某些文档没有在结果中，追加到末尾
        returned_ids = {item.get("id") for item in ranked_docs}
        for doc_id, doc in doc_dict.items():
            if doc_id not in returned_ids:
                doc["relevance_score"] = 0.3
                doc["reason"] = "未在LLM评分结果中找到"
                ranked_results.append(doc)

        # 按 relevance_score 降序排序
        ranked_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # 只返回 top_n
        top_results = ranked_results[:top_n]

        # 格式化输出
        output = json.dumps(top_results, ensure_ascii=False, indent=2)

        return output

    except Exception as e:
        raise RuntimeError(f"LLM Rerank 失败: {str(e)}")
