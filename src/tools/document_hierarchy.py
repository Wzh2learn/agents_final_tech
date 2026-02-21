"""
Document hierarchy tools.

Build and export parent/child chunk structures for knowledge base documents.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from langchain.tools import tool


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        if text.startswith("parent_"):
            text = text.split("_", 1)[1]
        if "_" in text:
            text = text.split("_", 1)[-1]
        try:
            return int(text)
        except ValueError:
            return default
    return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", "", "none", "null", "nan"}:
            return False
    return False


def _normalize_parent_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "none", "null", "nan"}:
        return None
    return text


def _infer_parent_child_from_chunk_index(value: Any) -> Tuple[Optional[str], Optional[int]]:
    if value is None:
        return None, None
    text = str(value).strip()
    if not text or "_" not in text:
        return None, None
    left, right = text.split("_", 1)
    if not left.isdigit():
        return None, None
    child_index: Optional[int] = None
    if right.isdigit():
        child_index = int(right)
    return f"parent_{int(left)}", child_index


def _determine_node_role(metadata: Dict[str, Any], parent_id: Optional[str]) -> Tuple[bool, Optional[str], Optional[int]]:
    inferred_parent_id, inferred_child_index = _infer_parent_child_from_chunk_index(metadata.get("chunk_index"))
    normalized_parent_id = parent_id or inferred_parent_id

    chunk_type = str(metadata.get("chunk_type") or metadata.get("node_type") or "").strip().lower()
    if "parent" in chunk_type:
        return True, normalized_parent_id, inferred_child_index
    if "child" in chunk_type:
        return False, normalized_parent_id, inferred_child_index

    if metadata.get("is_parent") is not None:
        return _safe_bool(metadata.get("is_parent")), normalized_parent_id, inferred_child_index

    if normalized_parent_id and (
        metadata.get("child_index") is not None
        or inferred_child_index is not None
    ):
        return False, normalized_parent_id, inferred_child_index

    if (
        normalized_parent_id is None
        and metadata.get("child_index") is None
        and inferred_child_index is None
    ):
        return True, normalized_parent_id, inferred_child_index

    return False, normalized_parent_id, inferred_child_index


def _clean_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.replace("\u3000", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\s*\n\s*", "\n", normalized)
    normalized = re.sub(r"\n{2,}", "\n", normalized)
    return normalized.strip()


def _summary(text: str, max_lines: int = 4, max_chars: int = 220) -> str:
    lines = text.split("\n")[:max_lines]
    merged = "\n".join(lines)
    if len(merged) > max_chars:
        return f"{merged[:max_chars]}..."
    return merged


def _build_hierarchy_data(document_id: str, collection_name: str) -> Dict[str, Any]:
    from storage.database.db import get_session
    from storage.database.document_manager import DocumentManager

    manager = DocumentManager()
    db = get_session()
    try:
        chunks = manager.get_document_chunks(
            db=db,
            document_name=document_id,
            collection_name=collection_name,
            skip=0,
            limit=10000,
        )
    finally:
        db.close()

    parent_nodes: Dict[str, Dict[str, Any]] = {}
    root_nodes: List[Dict[str, Any]] = []
    children_by_parent: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    orphan_children: List[Dict[str, Any]] = []

    for chunk in chunks:
        metadata = dict(chunk.get("metadata") or {})
        content = _clean_text(chunk.get("content") or "")
        metadata.setdefault("source", metadata.get("original_name") or metadata.get("source"))

        chunk_index = metadata.get("chunk_index")
        parent_id = _normalize_parent_id(metadata.get("parent_id"))
        is_parent, parent_id, inferred_child_index = _determine_node_role(metadata, parent_id)

        parent_order = _safe_int(parent_id or chunk_index)
        child_order = _safe_int(
            metadata.get("child_index"),
            default=inferred_child_index if inferred_child_index is not None else _safe_int(chunk_index),
        )
        normalized_node_parent = parent_id or f"parent_{parent_order}"
        metadata["parent_id"] = normalized_node_parent
        metadata["is_parent"] = is_parent
        metadata["chunk_type"] = "parent" if is_parent else "child"

        if is_parent:
            display_title = f"父块 {parent_order + 1}"
        else:
            display_title = f"子块 {parent_order + 1}.{child_order + 1}"

        node = {
            "id": chunk.get("id"),
            "title": display_title,
            "display_title": display_title,
            "content": content,
            "summary": _summary(content),
            "metadata": metadata,
            "children": [],
            "order_key": (parent_order, -1 if is_parent else child_order),
        }

        if is_parent:
            node_key = normalized_node_parent
            parent_nodes[node_key] = node
            root_nodes.append(node)
            continue

        if normalized_node_parent:
            children_by_parent[normalized_node_parent].append(node)
        else:
            orphan_children.append(node)

    # Attach children under existing parents.
    for parent_key, child_nodes in children_by_parent.items():
        parent = parent_nodes.get(parent_key)
        if parent is None:
            # Create virtual parent for legacy data where parent chunk is missing.
            parent_order = _safe_int(parent_key)
            parent = {
                "id": f"virtual_parent:{parent_key}",
                "title": f"父块 {parent_order + 1}",
                "display_title": f"父块 {parent_order + 1}",
                "content": "",
                "summary": "",
                "metadata": {
                    "is_parent": True,
                    "parent_id": parent_key,
                    "virtual_parent": True,
                    "chunk_type": "parent",
                },
                "children": [],
                "order_key": (parent_order, -1),
            }
            parent_nodes[parent_key] = parent
            root_nodes.append(parent)
        parent["children"].extend(child_nodes)

    # Keep children with no parent visible as independent nodes (marked as child).
    root_nodes.extend(orphan_children)

    for node in root_nodes:
        if node.get("children"):
            node["children"].sort(key=lambda item: item.get("order_key", (0, 0)))
    root_nodes.sort(key=lambda item: item.get("order_key", (0, 0)))

    first_meta = (chunks[0].get("metadata") or {}) if chunks else {}
    return {
        "document_id": document_id,
        "title": document_id,
        "children": root_nodes,
        "metadata": {
            "total_chunks": len(chunks),
            "collection_name": collection_name,
            "content_type": first_meta.get("content_type"),
            "object_key": first_meta.get("object_key"),
            "original_name": first_meta.get("original_name"),
            "source": first_meta.get("source"),
        },
    }


@tool
def build_document_hierarchy(document_id: str, collection_name: str = "knowledge_base") -> str:
    """Build document hierarchy data in JSON string format."""
    try:
        result = _build_hierarchy_data(document_id=document_id, collection_name=collection_name)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "document_id": document_id}, ensure_ascii=False, indent=2)


@tool
def get_hierarchy_level(
    document_id: str,
    level: int,
    collection_name: str = "knowledge_base",
) -> str:
    """Get hierarchy sections at a specific level."""
    try:
        hierarchy = _build_hierarchy_data(document_id=document_id, collection_name=collection_name)
        sections: List[Dict[str, Any]] = []

        if level <= 1:
            for idx, parent in enumerate(hierarchy.get("children", [])):
                sections.append(
                    {
                        "title": parent.get("display_title") or parent.get("title") or f"节点 {idx + 1}",
                        "chunks": [parent.get("metadata", {}).get("chunk_index", idx)],
                    }
                )
        elif level == 2:
            for parent in hierarchy.get("children", []):
                children = parent.get("children") or []
                if not children:
                    continue
                sections.append(
                    {
                        "title": parent.get("display_title") or parent.get("title") or "父块",
                        "chunks": [child.get("metadata", {}).get("chunk_index") for child in children],
                    }
                )
        else:
            sections = []

        result = {"document_id": document_id, "level": level, "sections": sections}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps(
            {"error": str(exc), "document_id": document_id, "level": level},
            ensure_ascii=False,
            indent=2,
        )


@tool
def get_hierarchy_path(
    document_id: str,
    chunk_index: int,
    collection_name: str = "knowledge_base",
) -> str:
    """Get hierarchy path for a specific chunk index."""
    try:
        hierarchy = _build_hierarchy_data(document_id=document_id, collection_name=collection_name)
        path: List[Dict[str, Any]] = []

        for parent in hierarchy.get("children", []):
            parent_title = parent.get("display_title") or parent.get("title") or "父块"
            parent_chunk = parent.get("metadata", {}).get("chunk_index")
            if parent_chunk == chunk_index:
                path = [{"level": 1, "title": parent_title}]
                break

            for child in parent.get("children") or []:
                child_chunk = child.get("metadata", {}).get("chunk_index")
                if child_chunk == chunk_index:
                    child_title = child.get("display_title") or child.get("title") or "子块"
                    path = [{"level": 1, "title": parent_title}, {"level": 2, "title": child_title}]
                    break
            if path:
                break

        result = {
            "document_id": document_id,
            "chunk_index": chunk_index,
            "path": path,
            "path_string": " > ".join(item["title"] for item in path),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps(
            {"error": str(exc), "document_id": document_id, "chunk_index": chunk_index},
            ensure_ascii=False,
            indent=2,
        )


@tool
def search_by_hierarchy(
    collection_name: str = "knowledge_base",
    level: Optional[int] = None,
    section_title: Optional[str] = None,
) -> str:
    """Search documents by hierarchy filters."""
    try:
        result = {
            "collection_name": collection_name,
            "filters": {"level": level, "section_title": section_title},
            "results": [],
        }
        # Reserved lightweight tool: current UI does not require heavy indexed search here.
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "collection_name": collection_name}, ensure_ascii=False, indent=2)


@tool
def export_hierarchy(
    document_id: str,
    format: str = "json",
    collection_name: str = "knowledge_base",
) -> str:
    """Export hierarchy as json/markdown/tree text."""
    try:
        hierarchy = _build_hierarchy_data(document_id=document_id, collection_name=collection_name)
        fmt = (format or "json").strip().lower()

        if fmt == "json":
            return json.dumps(hierarchy, ensure_ascii=False, indent=2)
        if fmt in {"md", "markdown"}:
            return hierarchy_to_markdown(hierarchy, level=1)
        if fmt == "tree":
            return hierarchy_to_tree(hierarchy, prefix="")

        return json.dumps({"error": f"unsupported format: {format}"}, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "document_id": document_id}, ensure_ascii=False, indent=2)


def hierarchy_to_markdown(structure: Dict[str, Any], level: int = 1) -> str:
    """Render hierarchy to markdown."""
    heading = "#" * max(1, level)
    lines: List[str] = [f"{heading} {structure.get('title', 'Document')}"]

    for node in structure.get("children", []):
        node_title = node.get("display_title") or node.get("title") or "节点"
        lines.append(f"- **{node_title}**")
        summary = node.get("summary")
        if summary:
            lines.append(f"  - {summary}")
        for child in node.get("children", []):
            child_title = child.get("display_title") or child.get("title") or "子块"
            lines.append(f"  - {child_title}")
            child_summary = child.get("summary")
            if child_summary:
                lines.append(f"    - {child_summary}")
    return "\n".join(lines)


def hierarchy_to_tree(structure: Dict[str, Any], prefix: str = "") -> str:
    """Render hierarchy to tree text."""
    lines: List[str] = [f"{prefix}{structure.get('title', 'Document')}"]
    children = structure.get("children") or []
    for idx, node in enumerate(children):
        is_last = idx == len(children) - 1
        connector = "└── " if is_last else "├── "
        child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
        node_title = node.get("display_title") or node.get("title") or "节点"
        lines.append(f"{prefix}{connector}{node_title}")
        for child in node.get("children") or []:
            child_title = child.get("display_title") or child.get("title") or "子块"
            lines.append(f"{child_prefix}└── {child_title}")
    return "\n".join(lines)
