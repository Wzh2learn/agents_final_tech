"""
文档分层结构工具
构建和展示文档的分层结构，便于知识库导航和检索
"""
import json
import re
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from langchain_core.documents import Document


@tool
def build_document_hierarchy(
    document_id: str,
    collection_name: str = "knowledge_base"
) -> str:
    """
    构建文档分层结构

    从知识库中检索文档的所有文本块，并根据文档结构构建分层视图。

    Args:
        document_id: 文档ID
        collection_name: 向量集合名称

    Returns:
        JSON 格式的分层结构
    """
    try:
        from storage.database.db import get_session
        from storage.database.document_manager import DocumentManager

        manager = DocumentManager()
        db = get_session()
        try:
            chunks = manager.get_document_chunks(db, document_id, collection_name=collection_name, skip=0, limit=10000)
        finally:
            db.close()

        parent_nodes: Dict[str, Dict[str, Any]] = {}
        root_children: List[Dict[str, Any]] = []

        def prettify_text(text: str) -> str:
            """清理和格式化文本内容"""
            if not text:
                return ""
            clean = text.replace("\u3000", " ")
            clean = re.sub(r"[ \t]+", " ", clean)
            clean = re.sub(r"(\d+)\s*\.\s*", r"\1. ", clean)
            clean = re.sub(r"\s*\n\s*", "\n", clean)
            clean = clean.replace(" · ", " | ")
            clean = re.sub(r"(?<!\n)(\d+\.)", r"\n\1", clean)
            clean = re.sub(r"(?<!\n)(Phase\s*\d+)", r"\n\1", clean, flags=re.IGNORECASE)
            clean = re.sub(r"\n{2,}", "\n", clean)
            return clean.strip()

        def parse_parent_order(parent_value: Any) -> int:
            """解析父块顺序号"""
            if isinstance(parent_value, int):
                return parent_value
            if isinstance(parent_value, str) and parent_value.startswith("parent_"):
                try:
                    return int(parent_value.split("_", 1)[1])
                except (ValueError, IndexError):
                    return 0
            return 0

        def parse_child_order(child_value: Any, chunk_value: Any) -> int:
            """解析子块顺序号"""
            if isinstance(child_value, int):
                return child_value
            if isinstance(chunk_value, str) and "_" in chunk_value:
                try:
                    return int(chunk_value.split("_", 1)[1])
                except (ValueError, IndexError):
                    return 0
            return 0

        def build_display_title(prefix: str, major: int, minor: Optional[int]) -> str:
            """构建显示标题"""
            if minor is None:
                return f"{prefix} {major + 1}"
            return f"{prefix} {major + 1}.{minor + 1}"

        for chunk in chunks:
            content = prettify_text(chunk.get("content") or "")
            meta = chunk.get("metadata") or {}
            is_parent = bool(meta.get("is_parent"))
            parent_id = meta.get("parent_id")
            child_index = meta.get("child_index")
            chunk_index = meta.get("chunk_index")
            parent_order = parse_parent_order(parent_id or chunk_index)
            child_order = parse_child_order(child_index, chunk_index)

            display_title = build_display_title(
                "父块" if is_parent else "子块",
                parent_order,
                None if is_parent else child_order
            )

            summary_lines = content.split("\n")[:4]
            summary_text = "\n".join(summary_lines)
            if len(summary_text) > 220:
                summary_text = summary_text[:220] + "..."

            node = {
                "title": display_title,
                "display_title": display_title,
                "content": content,
                "summary": summary_text,
                "metadata": meta,
                "children": [],
                "order_key": (parent_order, child_order if not is_parent else -1)
            }

            if is_parent or not parent_id:
                node_id = parent_id or f"parent_{chunk_index}"
                parent_nodes[node_id] = node
                root_children.append(node)
            else:
                parent_node = parent_nodes.get(parent_id)
                if not parent_node:
                    parent_node = {
                        "title": f"父块 {parent_id}",
                        "content": "",
                        "summary": "",
                        "metadata": {"parent_id": parent_id, "is_parent": True},
                        "children": []
                    }
                    parent_nodes[parent_id] = parent_node
                    root_children.append(parent_node)
                parent_node["children"].append(node)

        for parent in root_children:
            parent["children"].sort(key=lambda c: c.get("order_key", (0, 0)))
        root_children.sort(key=lambda n: n.get("order_key", (0, 0)))

        first_meta = chunks[0].get("metadata") if chunks else {}
        result = {
            "document_id": document_id,
            "title": document_id,
            "children": root_children,
            "metadata": {
                "total_chunks": len(chunks),
                "collection_name": collection_name,
                "content_type": first_meta.get("content_type"),
                "object_key": first_meta.get("object_key"),
                "original_name": first_meta.get("original_name"),
                "source": first_meta.get("source")
            }
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "document_id": document_id
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def get_hierarchy_level(
    document_id: str,
    level: int,
    collection_name: str = "knowledge_base"
) -> str:
    """
    获取文档指定层级的内容

    Args:
        document_id: 文档ID
        level: 层级（1, 2, 3...）
        collection_name: 向量集合名称

    Returns:
        JSON 格式的层级内容
    """
    try:
        result = {
            "document_id": document_id,
            "level": level,
            "sections": []
        }

        # 模拟层级内容
        if level == 1:
            result["sections"] = [
                {
                    "title": "概述",
                    "chunks": [0, 1, 2, 3, 4, 5, 6]
                },
                {
                    "title": "核心规则",
                    "chunks": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
                }
            ]
        elif level == 2:
            result["sections"] = [
                {
                    "title": "什么是建账规则",
                    "chunks": [0, 1, 2, 3]
                },
                {
                    "title": "应用场景",
                    "chunks": [4, 5, 6]
                },
                {
                    "title": "科目设置规则",
                    "chunks": [7, 8, 9, 10, 11]
                },
                {
                    "title": "凭证处理规则",
                    "chunks": [12, 13, 14, 15, 16]
                }
            ]
        elif level == 3:
            result["sections"] = [
                {"title": "定义", "chunks": [0, 1]},
                {"title": "重要性", "chunks": [2, 3]},
                {"title": "科目分类", "chunks": [7, 8]},
                {"title": "科目编码", "chunks": [9, 10, 11]},
                {"title": "凭证类型", "chunks": [12, 13]},
                {"title": "凭证审批", "chunks": [14, 15, 16]}
            ]
        else:
            result["sections"] = []

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "document_id": document_id,
            "level": level
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def get_hierarchy_path(
    document_id: str,
    chunk_index: int,
    collection_name: str = "knowledge_base"
) -> str:
    """
    获取文本块在文档结构中的路径

    Args:
        document_id: 文档ID
        chunk_index: 文本块索引
        collection_name: 向量集合名称

    Returns:
        JSON 格式的路径信息
    """
    try:
        result = {
            "document_id": document_id,
            "chunk_index": chunk_index,
            "path": []
        }

        # 模拟路径
        if chunk_index == 0:
            result["path"] = [
                {"level": 1, "title": "概述"},
                {"level": 2, "title": "什么是建账规则"},
                {"level": 3, "title": "定义"}
            ]
        elif chunk_index == 7:
            result["path"] = [
                {"level": 1, "title": "核心规则"},
                {"level": 2, "title": "科目设置规则"},
                {"level": 3, "title": "科目分类"}
            ]
        else:
            result["path"] = [
                {"level": 1, "title": "概述"},
                {"level": 2, "title": "应用场景"}
            ]

        result["path_string"] = " > ".join([p["title"] for p in result["path"]])

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "document_id": document_id,
            "chunk_index": chunk_index
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def search_by_hierarchy(
    collection_name: str = "knowledge_base",
    level: Optional[int] = None,
    section_title: Optional[str] = None
) -> str:
    """
    根据文档结构搜索

    Args:
        collection_name: 向量集合名称
        level: 层级（可选）
        section_title: 章节标题（可选）

    Returns:
        JSON 格式的搜索结果
    """
    try:
        result = {
            "collection_name": collection_name,
            "filters": {
                "level": level,
                "section_title": section_title
            },
            "results": []
        }

        # 模拟搜索结果
        if section_title:
            result["results"] = [
                {
                    "document_id": "doc_1",
                    "document_name": "建账规则指南.md",
                    "chunk_indices": [0, 1, 2, 3],
                    "match_type": "exact"
                }
            ]
        elif level:
            result["results"] = [
                {
                    "document_id": "doc_1",
                    "document_name": "建账规则指南.md",
                    "chunk_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
                    "match_type": "level"
                }
            ]
        else:
            result["results"] = []

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "collection_name": collection_name
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


@tool
def export_hierarchy(
    document_id: str,
    format: str = "json",
    collection_name: str = "knowledge_base"
) -> str:
    """
    导出文档分层结构

    Args:
        document_id: 文档ID
        format: 导出格式（json/markdown/tree）
        collection_name: 向量集合名称

    Returns:
        导出的分层结构
    """
    try:
        # 获取分层结构
        hierarchy_result = build_document_hierarchy.invoke({
            "document_id": document_id,
            "collection_name": collection_name
        })
        hierarchy_data = json.loads(hierarchy_result)

        if format == "json":
            return json.dumps(hierarchy_data, ensure_ascii=False, indent=2)

        elif format == "markdown":
            # 转换为 Markdown 格式
            markdown = hierarchy_to_markdown(hierarchy_data["structure"], 0)
            return markdown

        elif format == "tree":
            # 转换为树形格式
            tree = hierarchy_to_tree(hierarchy_data["structure"], "")
            return tree

        else:
            return json.dumps({"error": f"不支持的格式: {format}"}, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": str(e),
            "document_id": document_id
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


def hierarchy_to_markdown(structure: Dict, level: int) -> str:
    """
    将分层结构转换为 Markdown 格式

    Args:
        structure: 分层结构
        level: 当前层级

    Returns:
        Markdown 文本
    """
    prefix = "#" * (level + 1)
    markdown = f"{prefix} {structure['title']}\n\n"

    if "children" in structure:
        for child in structure["children"]:
            markdown += hierarchy_to_markdown(child, level + 1)

    if "chunks" in structure:
        markdown += f"*(文本块: {', '.join(map(str, structure['chunks']))})*\n\n"

    return markdown


def hierarchy_to_tree(structure: Dict, prefix: str) -> str:
    """
    将分层结构转换为树形格式

    Args:
        structure: 分层结构
        prefix: 前缀字符串

    Returns:
        树形文本
    """
    tree = f"{prefix}├─ {structure['title']}\n"

    if "children" in structure:
        for i, child in enumerate(structure["children"]):
            is_last = i == len(structure["children"]) - 1
            new_prefix = prefix + ("   " if is_last else "│  ")
            tree += hierarchy_to_tree(child, new_prefix)

    if "chunks" in structure:
        tree += f"{prefix}   └─ [文本块: {', '.join(map(str, structure['chunks']))}]\n"

    return tree


if __name__ == "__main__":
    # 测试文档分层结构
    print("测试构建文档分层结构:")
    hierarchy = build_document_hierarchy.invoke({
        "document_id": "doc_1",
        "collection_name": "knowledge_base"
    })
    print(hierarchy)

    print("\n测试获取层级内容:")
    level_content = get_hierarchy_level.invoke({
        "document_id": "doc_1",
        "level": 2,
        "collection_name": "knowledge_base"
    })
    print(level_content)

    print("\n测试获取路径:")
    path = get_hierarchy_path.invoke({
        "document_id": "doc_1",
        "chunk_index": 0,
        "collection_name": "knowledge_base"
    })
    print(path)

    print("\n测试导出为 Markdown:")
    markdown = export_hierarchy.invoke({
        "document_id": "doc_1",
        "format": "markdown",
        "collection_name": "knowledge_base"
    })
    print(markdown)

    print("\n测试导出为 Tree:")
    tree = export_hierarchy.invoke({
        "document_id": "doc_1",
        "format": "tree",
        "collection_name": "knowledge_base"
    })
    print(tree)
