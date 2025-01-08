from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, BigInteger, UniqueConstraint
from .base import Base
from datetime import datetime

class Warning(Base):
    __tablename__ = 'warnings'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    warning_count = Column(Integer, default=0)
    last_warning = Column(DateTime, default=datetime.utcnow)

    # Добавляем составной индекс
    __table_args__ = (
        Index('idx_chat_user', 'chat_id', 'user_id'),
    )

    def __repr__(self):
        return f"<Warning(user_id={self.user_id}, chat_id={self.chat_id}, count={self.warning_count})>"

class UserStats(Base):
    __tablename__ = 'user_stats'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    message_count = Column(Integer, default=0)
    last_message_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'chat_id', name='unique_user_chat'),
    )