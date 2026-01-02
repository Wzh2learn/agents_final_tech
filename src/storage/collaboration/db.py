"""
协作会话数据库管理
提供会话、参与者、消息的CRUD操作
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from .models import Base, Session, Participant, SessionMessage, create_tables


class CollaborationDB:
    """协作会话数据库管理类"""

    def __init__(self, database_url: str = None):
        """
        初始化数据库连接

        Args:
            database_url: 数据库连接URL，默认使用环境变量 PGDATABASE_URL
        """
        import os

        if database_url is None:
            database_url = os.getenv('PGDATABASE_URL', 'postgresql://user:password@localhost:5432/database')

        # 创建引擎
        self.engine = create_engine(database_url, pool_pre_ping=True)
        
        # 创建表
        create_tables(self.engine)
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_db_session(self) -> Session:
        """获取数据库会话（SQLAlchemy）"""
        return self.SessionLocal()

    # ==================== 会话管理 ====================

    def create_session(self, name: str, description: str = None) -> Optional[Session]:
        """创建新会话"""
        with self.get_db_session() as db:
            try:
                session = Session(name=name, description=description)
                db.add(session)
                db.commit()
                db.refresh(session)
                return session
            except Exception as e:
                db.rollback()
                print(f"创建会话失败: {e}")
                return None

    def get_session(self, session_id: int) -> Optional[Session]:
        """获取会话"""
        with self.get_db_session() as db:
            return db.query(Session).filter(Session.id == session_id).first()

    def get_all_sessions(self, active_only: bool = True) -> List[Session]:
        """获取所有会话"""
        with self.get_db_session() as db:
            query = db.query(Session)
            if active_only:
                query = query.filter(Session.is_active == True)
            return query.order_by(Session.updated_at.desc()).all()

    def update_session(self, session_id: int, name: str = None, description: str = None) -> bool:
        """更新会话"""
        with self.get_db_session() as db:
            try:
                session = db.query(Session).filter(Session.id == session_id).first()
                if session:
                    if name is not None:
                        session.name = name
                    if description is not None:
                        session.description = description
                    session.updated_at = datetime.utcnow()
                    db.commit()
                    return True
                return False
            except Exception as e:
                db.rollback()
                print(f"更新会话失败: {e}")
                return False

    def delete_session(self, session_id: int) -> bool:
        """删除会话"""
        with self.get_db_session() as db:
            try:
                session = db.query(Session).filter(Session.id == session_id).first()
                if session:
                    db.delete(session)
                    db.commit()
                    return True
                return False
            except Exception as e:
                db.rollback()
                print(f"删除会话失败: {e}")
                return False

    # ==================== 参与者管理 ====================

    def add_participant(self, session_id: int, nickname: str, avatar_color: str = '#667eea') -> Optional[Participant]:
        """添加参与者到会话"""
        with self.get_db_session() as db:
            try:
                participant = Participant(
                    session_id=session_id,
                    nickname=nickname,
                    avatar_color=avatar_color,
                    joined_at=datetime.utcnow(),
                    is_online=True,
                    last_seen=datetime.utcnow()
                )
                db.add(participant)
                db.commit()
                db.refresh(participant)
                return participant
            except Exception as e:
                db.rollback()
                print(f"添加参与者失败: {e}")
                return None

    def get_participant(self, participant_id: int) -> Optional[Participant]:
        """获取参与者"""
        with self.get_db_session() as db:
            return db.query(Participant).filter(Participant.id == participant_id).first()

    def get_session_participants(self, session_id: int, online_only: bool = False) -> List[Participant]:
        """获取会话的所有参与者"""
        with self.get_db_session() as db:
            query = db.query(Participant).filter(Participant.session_id == session_id)
            if online_only:
                query = query.filter(Participant.is_online == True)
            return query.all()

    def update_participant_status(self, participant_id: int, is_online: bool = None) -> bool:
        """更新参与者状态"""
        with self.get_db_session() as db:
            try:
                participant = db.query(Participant).filter(Participant.id == participant_id).first()
                if participant:
                    if is_online is not None:
                        participant.is_online = is_online
                    participant.last_seen = datetime.utcnow()
                    db.commit()
                    return True
                return False
            except Exception as e:
                db.rollback()
                print(f"更新参与者状态失败: {e}")
                return False

    def remove_participant(self, participant_id: int) -> bool:
        """移除参与者"""
        with self.get_db_session() as db:
            try:
                participant = db.query(Participant).filter(Participant.id == participant_id).first()
                if participant:
                    db.delete(participant)
                    db.commit()
                    return True
                return False
            except Exception as e:
                db.rollback()
                print(f"移除参与者失败: {e}")
                return False

    # ==================== 消息管理 ====================

    def add_message(self, session_id: int, role: str, content: str, participant_id: int = None) -> Optional[SessionMessage]:
        """添加消息"""
        with self.get_db_session() as db:
            try:
                message = SessionMessage(
                    session_id=session_id,
                    participant_id=participant_id,
                    role=role,
                    content=content,
                    created_at=datetime.utcnow()
                )
                db.add(message)
                
                # 更新会话时间
                session = db.query(Session).filter(Session.id == session_id).first()
                if session:
                    session.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(message)
                return message
            except Exception as e:
                db.rollback()
                print(f"添加消息失败: {e}")
                return None

    def get_session_messages(self, session_id: int, limit: int = 100) -> List[SessionMessage]:
        """获取会话消息"""
        with self.get_db_session() as db:
            return db.query(SessionMessage)\
                .filter(SessionMessage.session_id == session_id)\
                .order_by(SessionMessage.created_at.asc())\
                .limit(limit)\
                .all()

    def get_messages_after(self, session_id: int, message_id: int, limit: int = 50) -> List[SessionMessage]:
        """获取指定消息之后的消息（用于增量同步）"""
        with self.get_db_session() as db:
            return db.query(SessionMessage)\
                .filter(SessionMessage.session_id == session_id)\
                .filter(SessionMessage.id > message_id)\
                .order_by(SessionMessage.created_at.asc())\
                .limit(limit)\
                .all()


# 全局数据库实例
_collab_db_instance = None


def get_collaboration_db() -> CollaborationDB:
    """获取协作数据库实例（单例）"""
    global _collab_db_instance
    if _collab_db_instance is None:
        _collab_db_instance = CollaborationDB()
    return _collab_db_instance
