"""
文件上传验证器 - 安全检查
"""
import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.md', '.docx', '.pdf', '.txt'}

# 允许的 MIME 类型
ALLOWED_MIMES = {
    'text/plain',
    'text/markdown',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# 文件大小限制（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024

# Magic bytes 签名
MAGIC_BYTES = {
    '.pdf': b'%PDF',
    '.docx': b'PK\x03\x04',
}


class FileValidator:
    """文件验证器"""

    @staticmethod
    def check_extension(filename: str) -> Tuple[bool, str]:
        """检查文件扩展名"""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"不支持的文件类型: {ext}"
        return True, ""

    @staticmethod
    def check_size(content: bytes) -> Tuple[bool, str]:
        """检查文件大小"""
        if len(content) > MAX_FILE_SIZE:
            size_mb = len(content) / (1024 * 1024)
            return False, f"文件过大: {size_mb:.1f}MB，最大允许 10MB"
        return True, ""

    @staticmethod
    def check_magic_bytes(filename: str, content: bytes) -> Tuple[bool, str]:
        """检查文件内容签名"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in MAGIC_BYTES:
            expected = MAGIC_BYTES[ext]
            if not content.startswith(expected):
                return False, f"文件内容与扩展名不匹配"
        return True, ""

    @classmethod
    def validate(cls, filename: str, content: bytes) -> Tuple[bool, str]:
        """完整验证"""
        # 1. 扩展名检查
        ok, msg = cls.check_extension(filename)
        if not ok:
            return False, msg

        # 2. 大小检查
        ok, msg = cls.check_size(content)
        if not ok:
            return False, msg

        # 3. 内容签名检查
        ok, msg = cls.check_magic_bytes(filename, content)
        if not ok:
            return False, msg

        return True, ""


def validate_upload(filename: str, content: bytes) -> Tuple[bool, str]:
    """验证上传文件（便捷函数）"""
    return FileValidator.validate(filename, content)
