"""
问题类型分类器
将用户查询分类为不同类型，以便选择合适的检索策略
"""
import json
from langchain.tools import tool
from langchain_openai import ChatOpenAI
import os


def _get_llm():
    """获取 LLM 实例"""
    from utils.config_loader import get_config
    app_cfg = get_config()
    llm_cfg = app_cfg.get_llm_config()

    api_key = os.getenv(llm_cfg.get("api_key_env", "SILICONFLOW_API_KEY"))
    base_url = os.getenv(llm_cfg.get("base_url_env", "SILICONFLOW_BASE_URL"))

    llm = ChatOpenAI(
        model=llm_cfg.get("model", "deepseek-ai/DeepSeek-V3.2"),
        api_key=api_key,
        base_url=base_url,
        temperature=0.1,  # 低温度确保分类稳定
        timeout=60,
        streaming=True,  # 必须为True
        extra_body={
            "thinking": {
                "type": "disabled"  # 关闭思考模式
            }
        }
    )
    return llm


@tool
def classify_question_type(query: str) -> str:
    """
    分类用户查询的问题类型

    支持的问题类型：
    1. concept - 概念型：什么是XXX、XXX的含义
    2. process - 流程型：如何做XXX、XXX的步骤
    3. compare - 对比型：XXX和YYY的区别、对比
    4. factual - 事实型：XXX的数据、日期、数量
    5. rule - 规则型：XXX的规则、规定、要求
    6. troubleshooting - 故障排查：XXX出现错误、无法XXX
    7. general - 通用型：其他问题

    Args:
        query: 用户查询文本

    Returns:
        JSON 格式的分类结果，包含：
        - type: 问题类型
        - confidence: 置信度 (0-1)
        - reason: 分类原因
    """
    if not query or not query.strip():
        raise ValueError("查询不能为空")

    llm = _get_llm()

    # 分类提示词
    system_prompt = """你是一个问题分类专家。分析用户查询，将其分类为以下类型之一：

1. concept（概念型）：询问定义、含义、解释
   示例：什么是建账？会计科目的含义是什么？

2. process（流程型）：询问操作步骤、流程、方法
   示例：如何进行建账？建账的步骤有哪些？

3. compare（对比型）：询问差异、区别、对比
   示例：现金日记账和银行存款日记账的区别是什么？

4. factual（事实型）：询问具体数据、日期、数量、信息
   示例：固定资产折旧率是多少？截止到现在的总资产是多少？

5. rule（规则型）：询问规定、要求、限制、政策
   示例：建账有哪些规定？会计核算的基本要求是什么？

6. troubleshooting（故障排查）：询问错误、问题、异常
   示例：建账时出现余额不平衡怎么办？凭证审核失败怎么处理？

7. general（通用型）：其他问题
   示例：你好、谢谢、无法明确分类的问题

请以JSON格式返回结果，格式如下：
{
    "type": "问题类型",
    "confidence": 置信度(0-1之间的小数),
    "reason": "分类原因"
}
"""

    user_prompt = f"用户查询：{query}\n\n请对上述查询进行分类，返回JSON格式结果。"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # 使用stream方式调用（集成要求）
        content = ""
        llm = _get_llm()
        for chunk in llm.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                content += str(chunk.content)

        # 尝试解析JSON
        try:
            # 提取JSON部分（如果包含在代码块中）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            # 验证返回结果
            if "type" not in result:
                result["type"] = "general"
            if "confidence" not in result:
                result["confidence"] = 0.5
            if "reason" not in result:
                result["reason"] = "默认分类"

            # 确保type是有效值
            valid_types = ["concept", "process", "compare", "factual", "rule", "troubleshooting", "general"]
            if result["type"] not in valid_types:
                result["type"] = "general"

            return json.dumps(result, ensure_ascii=False, indent=2)

        except json.JSONDecodeError:
            # 如果JSON解析失败，使用规则分类
            query_lower = query.lower()
            result = {"type": "general", "confidence": 0.3, "reason": "JSON解析失败，使用规则分类"}

            # 简单的关键词规则分类
            if any(keyword in query for keyword in ["什么是", "定义", "含义", "是什么意思"]):
                result = {"type": "concept", "confidence": 0.6, "reason": "匹配概念型关键词"}
            elif any(keyword in query for keyword in ["如何", "步骤", "流程", "怎么"]):
                result = {"type": "process", "confidence": 0.6, "reason": "匹配流程型关键词"}
            elif any(keyword in query for keyword in ["区别", "差异", "对比", "不同"]):
                result = {"type": "compare", "confidence": 0.6, "reason": "匹配对比型关键词"}
            elif any(keyword in query for keyword in ["多少", "数量", "日期", "时间", "数据"]):
                result = {"type": "factual", "confidence": 0.6, "reason": "匹配事实型关键词"}
            elif any(keyword in query for keyword in ["规则", "规定", "要求", "限制", "政策"]):
                result = {"type": "rule", "confidence": 0.6, "reason": "匹配规则型关键词"}
            elif any(keyword in query for keyword in ["错误", "失败", "问题", "无法", "异常"]):
                result = {"type": "troubleshooting", "confidence": 0.6, "reason": "匹配故障排查型关键词"}

            return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        # 发生异常时返回通用类型
        error_result = {
            "type": "general",
            "confidence": 0.0,
            "reason": f"分类失败: {str(e)}"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def get_retrieval_strategy(question_type: str) -> str:
    """
    根据问题类型推荐检索策略

    不同问题类型适合的检索策略：
    1. concept - 向量检索（语义匹配）
    2. process - 混合检索（向量 + BM25关键词匹配）
    3. compare - 混合检索（需要精确对比）
    4. factual - BM25检索（精确匹配）
    5. rule - 向量检索 + Rerank（需要深度理解）
    6. troubleshooting - 混合检索 + Rerank（需要全面匹配）
    7. general - 向量检索（通用语义匹配）

    Args:
        question_type: 问题类型（来自 classify_question_type）

    Returns:
        JSON 格式的检索策略配置
    """
    strategies = {
        "concept": {
            "method": "vector",
            "use_rerank": False,
            "top_k": 5,
            "reason": "概念型问题适合语义匹配"
        },
        "process": {
            "method": "hybrid",
            "use_rerank": False,
            "top_k": 7,
            "bm25_weight": 0.4,
            "vector_weight": 0.6,
            "reason": "流程型问题需要语义和关键词混合匹配"
        },
        "compare": {
            "method": "hybrid",
            "use_rerank": True,
            "top_k": 5,
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "reason": "对比型问题需要精确匹配，建议使用Rerank"
        },
        "factual": {
            "method": "bm25",
            "use_rerank": False,
            "top_k": 3,
            "reason": "事实型问题需要精确匹配关键词"
        },
        "rule": {
            "method": "vector",
            "use_rerank": True,
            "top_k": 5,
            "reason": "规则型问题需要深度理解，建议使用Rerank"
        },
        "troubleshooting": {
            "method": "hybrid",
            "use_rerank": True,
            "top_k": 8,
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "reason": "故障排查需要全面匹配，建议使用Rerank"
        },
        "general": {
            "method": "vector",
            "use_rerank": False,
            "top_k": 5,
            "reason": "通用问题使用语义匹配"
        }
    }

    strategy = strategies.get(question_type, strategies["general"])

    return json.dumps({
        "question_type": question_type,
        "strategy": strategy
    }, ensure_ascii=False, indent=2)
