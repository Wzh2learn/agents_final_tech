"""
文档存储服务
使用对象存储保存和管理原始文档
"""
import os
import logging
from typing import Optional, List
from datetime import datetime

from storage.s3.s3_storage import S3SyncStorage

logger = logging.getLogger(__name__)


class LocalSyncStorage:
    """本地文件系统存储（替代 S3，用于开发/单机环境）"""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def _resolve_path(self, file_key: str) -> str:
        """解析文件路径，确保路径在 root_dir 内（防止路径遍历攻击）"""
        # 清理路径分隔符
        safe_key = file_key.strip("/").replace("\\", "/")
        # 构建并规范化完整路径
        full_path = os.path.normpath(os.path.join(self.root_dir, safe_key))
        # 确保路径在 root_dir 内，防止 "../../etc/passwd" 等路径遍历攻击
        abs_root = os.path.abspath(self.root_dir)
        if not full_path.startswith(abs_root):
            raise ValueError(f"Invalid file key: path traversal detected")
        return full_path

    def upload_file(self, *, file_content: bytes, file_name: str, content_type: Optional[str] = None) -> str:
        file_path = self._resolve_path(file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
        return file_name

    def stream_upload_file(self, *, fileobj, file_name: str, content_type: Optional[str] = None) -> str:
        file_path = self._resolve_path(file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(fileobj.read())
        return file_name

    def read_file(self, *, file_key: str) -> bytes:
        file_path = self._resolve_path(file_key)
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, *, file_key: str) -> bool:
        file_path = self._resolve_path(file_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def generate_presigned_url(self, *, key: str, expire_time: int = 3600) -> str:
        file_path = self._resolve_path(key)
        return f"file://{os.path.abspath(file_path)}"

    def file_exists(self, *, file_key: str) -> bool:
        return os.path.exists(self._resolve_path(file_key))

    def list_files(self, *, prefix: str = "", max_keys: int = 100):
        base_dir = self._resolve_path(prefix)
        if not os.path.exists(base_dir):
            return {"keys": [], "is_truncated": False, "next_continuation_token": None}
        keys = []
        for root, _, files in os.walk(base_dir):
            for name in files:
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")
                keys.append(rel_path)
                if len(keys) >= max_keys:
                    return {"keys": keys, "is_truncated": True, "next_continuation_token": None}
        return {"keys": keys, "is_truncated": False, "next_continuation_token": None}


class DocumentStorage:
    """文档存储服务，封装S3对象存储"""

    def __init__(self):
        """初始化对象存储客户端"""
        endpoint_url = os.getenv("BUCKET_ENDPOINT_URL")
        use_local = os.getenv("STORAGE_BACKEND", "").lower() == "local" or not endpoint_url
        if use_local:
            root_dir = os.getenv("BUCKET_LOCAL_ROOT", os.path.join("data", "local_bucket"))
            logger.warning("BUCKET_ENDPOINT_URL 未配置，使用本地存储目录: %s", root_dir)
            self.storage = LocalSyncStorage(root_dir=root_dir)
        else:
            self.storage = S3SyncStorage(
                endpoint_url=endpoint_url,
                access_key=os.getenv("BUCKET_ACCESS_KEY", ""),
                secret_key=os.getenv("BUCKET_SECRET_KEY", ""),
                bucket_name=os.getenv("BUCKET_NAME", ""),
                region=os.getenv("BUCKET_REGION", "cn-beijing"),
            )
        self.prefix = "documents/"  # 文档存储前缀

    def upload_document(
        self,
        file_content: bytes,
        file_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        上传文档到对象存储

        Args:
            file_content: 文件内容（bytes）
            file_name: 文件名
            content_type: MIME类型
            metadata: 文档元数据

        Returns:
            对象key
        """
        try:
            # 确定Content-Type
            if content_type is None:
                content_type = self._guess_content_type(file_name)

            # 构建对象key
            object_key = f"{self.prefix}{file_name}"

            # 上传文件
            key = self.storage.upload_file(
                file_content=file_content,
                file_name=object_key,
                content_type=content_type
            )

            logger.info(f"文档上传成功: {file_name} -> {key}")
            return key

        except Exception as e:
            logger.error(f"文档上传失败: {file_name}, 错误: {str(e)}")
            raise

    def stream_upload_document(
        self,
        file_obj,
        file_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        流式上传大文档

        Args:
            file_obj: 文件对象（支持read()方法）
            file_name: 文件名
            content_type: MIME类型

        Returns:
            对象key
        """
        try:
            # 确定Content-Type
            if content_type is None:
                content_type = self._guess_content_type(file_name)

            # 构建对象key
            object_key = f"{self.prefix}{file_name}"

            # 流式上传
            key = self.storage.stream_upload_file(
                fileobj=file_obj,
                file_name=object_key,
                content_type=content_type
            )

            logger.info(f"文档流式上传成功: {file_name} -> {key}")
            return key

        except Exception as e:
            logger.error(f"文档流式上传失败: {file_name}, 错误: {str(e)}")
            raise

    def download_document(self, object_key: str) -> bytes:
        """
        下载文档内容

        Args:
            object_key: 对象key

        Returns:
            文档内容（bytes）
        """
        try:
            content = self.storage.read_file(file_key=object_key)
            logger.info(f"文档下载成功: {object_key}")
            return content

        except Exception as e:
            logger.error(f"文档下载失败: {object_key}, 错误: {str(e)}")
            raise

    def delete_document(self, object_key: str) -> bool:
        """
        删除文档

        Args:
            object_key: 对象key

        Returns:
            是否删除成功
        """
        try:
            success = self.storage.delete_file(file_key=object_key)
            if success:
                logger.info(f"文档删除成功: {object_key}")
            return success

        except Exception as e:
            logger.error(f"文档删除失败: {object_key}, 错误: {str(e)}")
            return False

    def generate_download_url(
        self,
        object_key: str,
        expire_time: int = 3600
    ) -> str:
        """
        生成临时下载URL

        Args:
            object_key: 对象key
            expire_time: 过期时间（秒）

        Returns:
            签名URL
        """
        try:
            url = self.storage.generate_presigned_url(
                key=object_key,
                expire_time=expire_time
            )
            logger.info(f"生成下载URL成功: {object_key}, 过期时间: {expire_time}秒")
            return url

        except Exception as e:
            logger.error(f"生成下载URL失败: {object_key}, 错误: {str(e)}")
            raise

    def file_exists(self, object_key: str) -> bool:
        """
        检查文件是否存在

        Args:
            object_key: 对象key

        Returns:
            是否存在
        """
        try:
            return self.storage.file_exists(file_key=object_key)

        except Exception as e:
            logger.error(f"检查文件存在性失败: {object_key}, 错误: {str(e)}")
            return False

    def list_documents(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 100
    ) -> List[dict]:
        """
        列出文档

        Args:
            prefix: 前缀过滤
            max_keys: 最大返回数量

        Returns:
            文档列表
        """
        try:
            list_prefix = f"{self.prefix}{prefix}" if prefix else self.prefix
            result = self.storage.list_files(
                prefix=list_prefix,
                max_keys=max_keys
            )

            documents = []
            for key in result.get("keys", []):
                # 移除前缀，只保留文件名
                doc_name = key.replace(self.prefix, "", 1)
                documents.append({
                    "key": key,
                    "name": doc_name,
                    "size": 0,  # 可以根据需要获取size信息
                })

            return documents

        except Exception as e:
            logger.error(f"列出文档失败: {str(e)}")
            return []

    @staticmethod
    def _guess_content_type(file_name: str) -> str:
        """根据文件名猜测Content-Type"""
        ext = os.path.splitext(file_name)[1].lower()
        content_types = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.markdown': 'text/markdown',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.json': 'application/json',
            '.html': 'text/html',
            '.xml': 'application/xml',
            '.csv': 'text/csv',
        }
        return content_types.get(ext, 'application/octet-stream')


# 全局实例
_document_storage_instance = None


def get_document_storage() -> DocumentStorage:
    """获取文档存储服务单例"""
    global _document_storage_instance
    if _document_storage_instance is None:
        _document_storage_instance = DocumentStorage()
    return _document_storage_instance
