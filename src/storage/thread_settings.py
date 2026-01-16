"""
线程设置服务 - 持久化会话角色
"""
import logging
from typing import Optional
from storage.database.db import get_session
from storage.collaboration.models import ThreadSettings

logger = logging.getLogger(__name__)


class ThreadSettingsService:
    """线程设置服务"""

    def get_role(self, thread_id: str) -> Optional[str]:
        """获取线程角色"""
        db = get_session()
        try:
            setting = db.query(ThreadSettings).filter(
                ThreadSettings.thread_id == thread_id
            ).first()
            return setting.role_key if setting else None
        except Exception as e:
            logger.error(f"获取线程角色失败: {e}")
            return None
        finally:
            db.close()

    def set_role(self, thread_id: str, role_key: str) -> bool:
        """设置线程角色"""
        db = get_session()
        try:
            setting = db.query(ThreadSettings).filter(
                ThreadSettings.thread_id == thread_id
            ).first()
            if setting:
                setting.role_key = role_key
            else:
                setting = ThreadSettings(thread_id=thread_id, role_key=role_key)
                db.add(setting)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"设置线程角色失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def delete(self, thread_id: str) -> bool:
        """删除线程设置"""
        db = get_session()
        try:
            db.query(ThreadSettings).filter(
                ThreadSettings.thread_id == thread_id
            ).delete()
            db.commit()
            return True
        except Exception as e:
            logger.error(f"删除线程设置失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()


_service = None

def get_thread_settings_service() -> ThreadSettingsService:
    """获取服务实例"""
    global _service
    if _service is None:
        _service = ThreadSettingsService()
    return _service
