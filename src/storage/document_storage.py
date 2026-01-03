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


class DocumentStorage:
    """文档存储服务，封装S3对象存储"""

    def __init__(self):
        """初始化对象存储客户端"""
        self.storage = S3SyncStorage(
            endpoint_url=os.getenv("BUCKET_ENDPOINT_URL"),
            access_key="",
            secret_key="",
            bucket_name=os.getenv("BUCKET_NAME"),
            region="cn-beijing",
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
