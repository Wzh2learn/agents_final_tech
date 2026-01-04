"""
协作会话服务
处理会话管理、WebSocket 集成等
"""
import threading
import time
from typing import List, Optional
import asyncio
from storage.collaboration import get_collaboration_db
from web.websocket_server import broadcast_agent_message

# 存储 WebSocket 服务线程
websocket_server_thread = None


def start_websocket_thread(host='0.0.0.0', port=8765):
    """启动 WebSocket 服务器线程"""
    global websocket_server_thread

    if websocket_server_thread is None:
        def run_server():
            from web.websocket_server import start_websocket_server
            start_websocket_server(host, port)

        websocket_server_thread = threading.Thread(target=run_server, daemon=True)
        websocket_server_thread.start()
        return True
    return False


class CollaborationService:
    """协作会话服务"""

    def __init__(self):
        self.db = get_collaboration_db()

    # ==================== 会话管理 ====================

    def create_session(self, name: str, description: str = None, session_type: str = 'private', role_key: str = 'default_engineer') -> Optional[dict]:
        """创建新会话"""
        session = self.db.create_session(name, description, session_type, role_key)
        if session:
            return self._serialize_session(session)
        return None

    def get_session(self, session_id: int) -> Optional[dict]:
        """获取会话信息"""
        session = self.db.get_session(session_id)
        if session:
            return self._serialize_session(session)
        return None

    def get_all_sessions(self, active_only: bool = True, session_type: str = None) -> List[dict]:
        """获取所有会话"""
        sessions = self.db.get_all_sessions(active_only, session_type)
        return [self._serialize_session(s) for s in sessions]

    def update_session(self, session_id: int, name: str = None, description: str = None, role_key: str = None) -> bool:
        """更新会话"""
        return self.db.update_session(session_id, name, description, role_key)

    def _serialize_session(self, session) -> dict:
        """序列化会话"""
        return {
            'id': session.id,
            'name': session.name,
            'description': session.description,
            'type': session.type,
            'role_key': session.role_key,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'is_active': session.is_active
        }

    def delete_session(self, session_id: int) -> bool:
        """删除会话"""
        return self.db.delete_session(session_id)

    # ==================== 参与者管理 ====================

    def add_participant(self, session_id: int, nickname: str, avatar_color: str = '#667eea') -> Optional[dict]:
        """添加参与者"""
        participant = self.db.add_participant(session_id, nickname, avatar_color)
        if participant:
            return {
                'id': participant.id,
                'session_id': participant.session_id,
                'nickname': participant.nickname,
                'avatar_color': participant.avatar_color,
                'joined_at': participant.joined_at.isoformat(),
                'is_online': participant.is_online,
                'last_seen': participant.last_seen.isoformat()
            }
        return None

    def get_session_participants(self, session_id: int, online_only: bool = False) -> List[dict]:
        """获取会话参与者"""
        participants = self.db.get_session_participants(session_id, online_only)
        return [
            {
                'id': p.id,
                'session_id': p.session_id,
                'nickname': p.nickname,
                'avatar_color': p.avatar_color,
                'joined_at': p.joined_at.isoformat(),
                'is_online': p.is_online,
                'last_seen': p.last_seen.isoformat()
            }
            for p in participants
        ]

    # ==================== 消息管理 ====================

    def get_session_messages(self, session_id: int, limit: int = 100) -> List[dict]:
        """获取会话消息"""
        messages = self.db.get_session_messages(session_id, limit)
        return [self._serialize_message(msg) for msg in messages]

    def _serialize_message(self, message) -> dict:
        """序列化消息"""
        return {
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'participant_id': message.participant_id,
            'nickname': message.participant.nickname if message.participant else None,
            'avatar_color': message.participant.avatar_color if message.participant else None
        }


# 全局服务实例
_collab_service = None


def get_collaboration_service() -> CollaborationService:
    """获取协作服务实例（单例）"""
    global _collab_service
    if _collab_service is None:
        _collab_service = CollaborationService()
    return _collab_service
