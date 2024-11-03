from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from db.database import Base
from datetime import datetime

from sqlalchemy import String, DateTime

# users 테이블
class User(Base):
    __tablename__ = "users"
    
    userid = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime(6), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(6), nullable=True)
    onboarding = Column(Boolean, nullable=False, default=False)
    onboarding_info = Column(JSON(String(255)), nullable=True)

# chatlist 테이블
class ChatList(Base):
    __tablename__ = "chatlist"
    
    chatid = Column(String(255), primary_key=True, index=True)
    userid = Column(String(255), ForeignKey("users.userid"), nullable=False)
    summary = Column(String(255))
    category = Column(String(255))
    created_at = Column(DateTime(6), nullable=False, default=datetime.utcnow)

# messages 테이블
class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(Integer, primary_key=True, index=True)
    userid = Column(String(255), ForeignKey("users.userid"), nullable=False)
    chatid = Column(String(255), ForeignKey("chatlist.chatid"), nullable=False)
    created_at = Column(DateTime(6), nullable=False, default=datetime.utcnow)
    message = Column(String(255))
    answer = Column(String(255))