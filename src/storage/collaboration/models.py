"""
协作会话数据库模型
用于支持实时协作会话功能
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Session(Base):
    """会话表 (支持个人和协作)"""
    __tablename__ = 'collaboration_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='会话名称')
    description = Column(Text, nullable=True, comment='会话描述')
    type = Column(String(20), default='private', comment='类型: private/collaborative')
    role_key = Column(String(50), default='default_engineer', comment='关联角色')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    is_active = Column(Boolean, default=True, comment='是否活跃')

    # 关系
    participants = relationship("Participant", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("SessionMessage", back_populates="session", cascade="all, delete-orphan")


class Participant(Base):
    """会话参与者表"""
    __tablename__ = 'session_participants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('collaboration_sessions.id', ondelete='CASCADE'), nullable=False, comment='会话ID')
    nickname = Column(String(50), nullable=False, comment='昵称')
    avatar_color = Column(String(7), default='#667eea', comment='头像颜色')
    joined_at = Column(DateTime, default=datetime.utcnow, comment='加入时间')
    is_online = Column(Boolean, default=True, comment='是否在线')
    last_seen = Column(DateTime, default=datetime.utcnow, comment='最后在线时间')

    # 关系
    session = relationship("Session", back_populates="participants")
    messages = relationship("SessionMessage", back_populates="participant")


class SessionMessage(Base):
    """会话消息表"""
    __tablename__ = 'session_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('collaboration_sessions.id', ondelete='CASCADE'), nullable=False, comment='会话ID')
    participant_id = Column(Integer, ForeignKey('session_participants.id', ondelete='CASCADE'), nullable=True, comment='参与者ID（AI消息为空）')
    role = Column(String(20), nullable=False, comment='角色: user/agent')
    content = Column(Text, nullable=False, comment='消息内容')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系
    session = relationship("Session", back_populates="messages")
    participant = relationship("Participant", back_populates="messages")


def create_tables(engine):
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
