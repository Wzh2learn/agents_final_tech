"""
知识热力图工具
分析知识库中各主题的活跃程度和检索频率
"""
import json
import random
from typing import List, Dict, Any
from langchain.tools import tool
from collections import Counter
import re


@tool
def generate_knowledge_heatmap(
    collection_name: str = "knowledge_base",
    topic_level: int = 2,
    min_frequency: int = 1
) -> str:
    """
    生成知识热力图数据

    分析知识库中各主题的活跃程度和检索频率，生成热力图数据。

    Args:
        collection_name: 向量集合名称
        topic_level: 主题层级深度（1-3）
        min_frequency: 最小频率阈值

    Returns:
        JSON 格式的热力图数据
    """
    try:
        # 从向量数据库获取所有文档（模拟）
        # 实际应该从数据库检索

        # 模拟主题数据
        topics = [
            {"name": "建账规则", "frequency": 85, "documents": 12, "score": 0.92},
            {"name": "科目设置", "frequency": 72, "documents": 8, "score": 0.88},
            {"name": "凭证管理", "frequency": 68, "documents": 15, "score": 0.85},
            {"name": "财务报表", "frequency": 45, "documents": 6, "score": 0.78},
            {"name": "资产核算", "frequency": 42, "documents": 9, "score": 0.76},
            {"name": "负债核算", "frequency": 38, "documents": 7, "score": 0.74},
            {"name": "成本核算", "frequency": 35, "documents": 5, "score": 0.72},
            {"name": "税务处理", "frequency": 32, "documents": 4, "score": 0.70},
            {"name": "审计要求", "frequency": 28, "documents": 3, "score": 0.68},
            {"name": "系统集成", "frequency": 25, "documents": 6, "score": 0.65}
        ]

        # 根据主题层级生成子主题
        result = {
            "topics": [],
            "total_topics": len(topics),
            "total_frequency": sum(t["frequency"] for t in topics),
            "average_score": sum(t["score"] for t in topics) / len(topics),
            "hierarchy": {}
        }

        # 生成主主题
        for i, topic in enumerate(topics):
            if topic["frequency"] >= min_frequency:
                result["topics"].append({
                    "id": f"topic_{i}",
                    "name": topic["name"],
                    "frequency": topic["frequency"],
                    "documents": topic["documents"],
                    "score": topic["score"],
                    "level": 1,
                    "heat_level": calculate_heat_level(topic["frequency"]),
                    "color": get_heat_color(topic["score"])
                })

                # 生成子主题（层级2）
                if topic_level >= 2:
                    subtopics = generate_subtopics(topic["name"], 2)
                    result["hierarchy"][topic["name"]] = {
                        "subtopics": subtopics,
                        "level_2_count": len(subtopics)
                    }

                    # 生成更细分的主题（层级3）
                    if topic_level >= 3:
                        for subtopic in subtopics:
                            subsubtopics = generate_subtopics(subtopic["name"], 1)
                            subtopic["subtopics"] = subsubtopics
                            subtopic["level_3_count"] = len(subsubtopics)

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "topics": [],
            "total_topics": 0,
            "total_frequency": 0
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def analyze_topic_trends(
    collection_name: str = "knowledge_base",
    days: int = 30
) -> str:
    """
    分析主题趋势

    Args:
        collection_name: 向量集合名称
        days: 分析天数

    Returns:
        JSON 格式的趋势数据
    """
    try:
        # 模拟趋势数据
        result = {
            "period_days": days,
            "trends": []
        }

        # 生成每日趋势数据
        for i in range(days):
            date_str = f"2024-01-{(i + 1).toString().padStart(2, '0')}"
            # 模拟各主题的活跃度
            result["trends"].append({
                "date": date_str,
                "total_retrievals": random.randint(50, 150),
                "active_topics": random.randint(3, 10),
                "avg_accuracy": round(random.uniform(0.7, 0.95), 3)
            })

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "trends": []
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def get_topic_details(
    topic_name: str,
    collection_name: str = "knowledge_base"
) -> str:
    """
    获取主题详细信息

    Args:
        topic_name: 主题名称
        collection_name: 向量集合名称

    Returns:
        JSON 格式的主题详情
    """
    try:
        # 模拟主题详情
        result = {
            "name": topic_name,
            "frequency": random.randint(30, 100),
            "documents": random.randint(5, 20),
            "score": round(random.uniform(0.65, 0.95), 3),
            "related_topics": [
                {"name": f"相关主题{i+1}", "similarity": round(random.uniform(0.6, 0.9), 3)}
                for i in range(3)
            ],
            "top_documents": [
                {
                    "name": f"文档{i+1}.md",
                    "relevance": round(random.uniform(0.7, 0.95), 3),
                    "chunks": random.randint(3, 10)
                }
                for i in range(5)
            ],
            "recent_queries": [
                f"关于{topic_name}的问题{i+1}"
                for i in range(5)
            ]
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "name": topic_name
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


def calculate_heat_level(frequency: int) -> int:
    """
    计算热度等级（1-5）

    Args:
        frequency: 频率

    Returns:
        热度等级
    """
    if frequency >= 80:
        return 5
    elif frequency >= 60:
        return 4
    elif frequency >= 40:
        return 3
    elif frequency >= 20:
        return 2
    else:
        return 1


def get_heat_color(score: float) -> str:
    """
    根据分数获取热力图颜色

    Args:
        score: 分数（0-1）

    Returns:
        颜色代码
    """
    # 根据分数返回颜色（从蓝色到红色）
    if score >= 0.9:
        return "#e74c3c"  # 红色
    elif score >= 0.8:
        return "#e67e22"  # 橙色
    elif score >= 0.7:
        return "#f1c40f"  # 黄色
    elif score >= 0.6:
        return "#3498db"  # 蓝色
    else:
        return "#95a5a6"  # 灰色


def generate_subtopics(parent_name: str, count: int) -> List[Dict[str, Any]]:
    """
    生成子主题

    Args:
        parent_name: 父主题名称
        count: 子主题数量

    Returns:
        子主题列表
    """
    subtopics = []
    for i in range(count):
        subtopics.append({
            "name": f"{parent_name}-{i+1}",
            "frequency": random.randint(10, 50),
            "documents": random.randint(2, 8),
            "score": round(random.uniform(0.6, 0.9), 3),
            "level": 2,
            "heat_level": random.randint(1, 3)
        })
    return subtopics


if __name__ == "__main__":
    # 测试热力图生成
    print("测试知识热力图生成:")
    heatmap = generate_knowledge_heatmap.invoke({
        "collection_name": "knowledge_base",
        "topic_level": 3,
        "min_frequency": 1
    })
    print(heatmap)

    print("\n测试主题趋势分析:")
    trends = analyze_topic_trends.invoke({
        "collection_name": "knowledge_base",
        "days": 7
    })
    print(trends)

    print("\n测试主题详情:")
    details = get_topic_details.invoke({
        "topic_name": "建账规则",
        "collection_name": "knowledge_base"
    })
    print(details)
