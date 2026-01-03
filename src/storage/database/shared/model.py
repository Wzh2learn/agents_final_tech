# Using pgvector 0.3.6
from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, Index, Integer, JSON, PrimaryKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as Uuid
from typing import Any, Optional
import datetime
import uuid as uuid_module

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class CollaborationSessions(Base):
    __tablename__ = 'collaboration_sessions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='collaboration_sessions_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='会话名称')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='会话描述')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否活跃')

    session_participants: Mapped[list['SessionParticipants']] = relationship('SessionParticipants', back_populates='session')
    session_messages: Mapped[list['SessionMessages']] = relationship('SessionMessages', back_populates='session')


class LangchainPgCollection(Base):
    __tablename__ = 'langchain_pg_collection'
    __table_args__ = (
        PrimaryKeyConstraint('uuid', name='langchain_pg_collection_pkey'),
        UniqueConstraint('name', name='langchain_pg_collection_name_key')
    )

    uuid: Mapped[uuid_module.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSON)

    langchain_pg_embedding: Mapped[list['LangchainPgEmbedding']] = relationship('LangchainPgEmbedding', back_populates='collection')


class LangchainPgEmbedding(Base):
    __tablename__ = 'langchain_pg_embedding'
    __table_args__ = (
        ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], ondelete='CASCADE', name='langchain_pg_embedding_collection_id_fkey'),
        PrimaryKeyConstraint('id', name='langchain_pg_embedding_pkey'),
        Index('ix_cmetadata_gin', 'cmetadata')
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(Uuid)
    embedding: Mapped[Optional[Any]] = mapped_column(VECTOR)
    document: Mapped[Optional[str]] = mapped_column(String)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    collection: Mapped[Optional['LangchainPgCollection']] = relationship('LangchainPgCollection', back_populates='langchain_pg_embedding')


class SessionParticipants(Base):
    __tablename__ = 'session_participants'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE', name='session_participants_session_id_fkey'),
        PrimaryKeyConstraint('id', name='session_participants_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='会话ID')
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, comment='昵称')
    avatar_color: Mapped[Optional[str]] = mapped_column(String(7), comment='头像颜色')
    joined_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='加入时间')
    is_online: Mapped[Optional[bool]] = mapped_column(Boolean, comment='是否在线')
    last_seen: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='最后在线时间')

    session: Mapped['CollaborationSessions'] = relationship('CollaborationSessions', back_populates='session_participants')
    session_messages: Mapped[list['SessionMessages']] = relationship('SessionMessages', back_populates='participant')


class SessionMessages(Base):
    __tablename__ = 'session_messages'
    __table_args__ = (
        ForeignKeyConstraint(['participant_id'], ['session_participants.id'], ondelete='CASCADE', name='session_messages_participant_id_fkey'),
        ForeignKeyConstraint(['session_id'], ['collaboration_sessions.id'], ondelete='CASCADE', name='session_messages_session_id_fkey'),
        PrimaryKeyConstraint('id', name='session_messages_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='会话ID')
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment='角色: user/agent')
    content: Mapped[str] = mapped_column(Text, nullable=False, comment='消息内容')
    participant_id: Mapped[Optional[int]] = mapped_column(Integer, comment='参与者ID（AI消息为空）')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')

    participant: Mapped[Optional['SessionParticipants']] = relationship('SessionParticipants', back_populates='session_messages')
    session: Mapped['CollaborationSessions'] = relationship('CollaborationSessions', back_populates='session_messages')
