"""
文件写入工具：将内容写入文件或对象存储
对应 Dify 工作流：写入规则库
"""
from pydantic import BaseModel, Field
import os
import json
from datetime import datetime
from typing import Optional
from langchain.tools import tool
from storage.s3.s3_storage import S3SyncStorage


def _get_storage():
    """初始化对象存储"""
    return S3SyncStorage(
        endpoint_url=os.getenv("BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("BUCKET_NAME"),
        region="cn-beijing",
    )


@tool
def write_to_file(
    content: str,
    file_path: str,
    file_type: str = "text",
    runtime=None
) -> str:
    """
    将内容写入本地文件

    Args:
        content: 要写入的内容
        file_path: 文件路径（相对于 assets/ 目录）
        file_type: 文件类型（text/json/markdown）

    Returns:
        写入结果
    """
    try:
        # 构建完整路径
        full_path = os.path.join("assets", file_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"✅ 成功写入文件：{full_path}\n📁 文件大小：{len(content)} 字节"
    except Exception as e:
        return f"❌ 写入文件失败：{str(e)}"


class WriteToStorageInput(BaseModel):
    content: str = Field(..., description="要写入的内容")
    file_name: str = Field(..., description="文件名")
    content_type: str = Field("text/plain", description="内容类型（text/plain, application/json等）")
    folder: str = Field("knowledge_base", description="存储文件夹")

@tool
def write_to_storage(
    content: str,
    file_name: str,
    content_type: str = "text/plain",
    folder: str = "knowledge_base",
    runtime=None
) -> str:
    """
    将内容写入对象存储（知识库）

    Args:
        content: 要写入的内容
        file_name: 文件名
        content_type: 内容类型（text/plain, application/json等）
        folder: 存储文件夹

    Returns:
        写入结果
    """
    # I/O Guard 校验
    validated = WriteToStorageInput(
        content=content,
        file_name=file_name,
        content_type=content_type,
        folder=folder
    )
    content = validated.content
    file_name = validated.file_name
    content_type = validated.content_type
    folder = validated.folder

    try:
        from storage.provider import get_storage_provider
        provider = get_storage_provider()
        
        # 统一由 Provider 处理持久化
        object_key = provider.ingest_document(
            file_content=content.encode('utf-8'),
            file_name=file_name,
            metadata={"content_type": content_type, "folder": folder}
        )

        return f"""✅ 成功写入对象存储 (via StorageProvider)
📁 对象Key：{object_key}
📄 文件名：{file_name}
📝 类型：{content_type}
📊 大小：{len(content)} 字节
"""
    except Exception as e:
        return f"❌ 写入对象存储失败：{str(e)}"


@tool
def save_rule_to_knowledge(
    rule_table: str,
    rule_name: str,
    runtime=None
) -> str:
    """
    保存规则表格到知识库

    Args:
        rule_table: 规则表格（Markdown格式）
        rule_name: 规则名称

    Returns:
        保存结果
    """
    try:
        # 准备元数据
        metadata = {
            "rule_name": rule_name,
            "created_at": datetime.now().isoformat(),
            "type": "rule_table"
        }

        # 构建完整内容（包含元数据）
        full_content = f"""# {rule_name}

## 元数据
- 创建时间：{metadata['created_at']}
- 规则类型：{metadata['type']}

## 规则内容
{rule_table}
"""

        # 保存到本地
        local_path = f"knowledge/rules/{rule_name}_{datetime.now().strftime('%Y%m%d')}.md"
        result_local = write_to_file(
            content=full_content,
            file_path=local_path,
            file_type="markdown"
        )

        # 上传到对象存储
        result_storage = write_to_storage(
            content=full_content,
            file_name=f"{rule_name}.md",
            content_type="text/markdown",
            folder="knowledge/rules"
        )

        return f"""{result_local}\n\n{result_storage}"""
    except Exception as e:
        return f"❌ 保存规则失败：{str(e)}"


@tool
def save_qa_answer(
    question: str,
    answer: str,
    category: str = "general",
    runtime=None
) -> str:
    """
    保存问答对到知识库

    Args:
        question: 问题
        answer: 答案
        category: 分类（rule/technical/business/general）

    Returns:
        保存结果
    """
    try:
        # 准备元数据
        metadata = {
            "question": question,
            "answer": answer,
            "category": category,
            "created_at": datetime.now().isoformat()
        }

        # 构建JSON格式
        qa_record = json.dumps(metadata, ensure_ascii=False, indent=2)

        # 保存到本地
        local_path = f"knowledge/qa/{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_local = write_to_file(
            content=qa_record,
            file_path=local_path,
            file_type="json"
        )

        # 上传到对象存储
        result_storage = write_to_storage(
            content=qa_record,
            file_name=f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            content_type="application/json",
            folder="knowledge/qa"
        )

        return f"""✅ 问答对已保存
❓ 问题：{question}
📁 分类：{category}
\n{result_local}\n\n{result_storage}"""
    except Exception as e:
        return f"❌ 保存问答对失败：{str(e)}"


@tool
def read_from_storage(
    file_key: str,
    runtime=None
) -> str:
    """
    从对象存储读取文件

    Args:
        file_key: 对象Key

    Returns:
        文件内容
    """
    try:
        storage = _get_storage()

        # 读取文件
        content_bytes = storage.read_file(file_key=file_key)
        content = content_bytes.decode('utf-8')

        return f"""📄 文件内容
🔑 Key：{file_key}
📊 大小：{len(content)} 字节

---
{content}
---"""
    except Exception as e:
        return f"❌ 读取文件失败：{str(e)}"


@tool
def list_storage_files(
    prefix: str = "",
    max_keys: int = 10,
    runtime=None
) -> str:
    """
    列出对象存储中的文件

    Args:
        prefix: 前缀过滤
        max_keys: 最大返回数量

    Returns:
        文件列表
    """
    try:
        storage = _get_storage()

        # 列出文件
        result = storage.list_files(prefix=prefix, max_keys=max_keys)

        output = f"📁 对象存储文件列表（前缀：{prefix}）\n\n"
        for key in result.get("keys", []):
            output += f"- {key}\n"

        return output
    except Exception as e:
        return f"❌ 列出文件失败：{str(e)}"
