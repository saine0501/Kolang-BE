from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime

from sqlalchemy import String, DateTime

# users 테이블
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(255), primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime(6), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(6), nullable=True)
    onboarding = Column(Boolean, nullable=False, default=False)
    onboarding_info = Column(JSON(String(255)), nullable=True)
    
    messages = relationship("Message", back_populates="user")
    chats = relationship("ChatList", back_populates="user")

# chatlist 테이블
class ChatList(Base):
    __tablename__ = "chatlist"
    
    chat_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    summary = Column(String(255))
    category = Column(String(255))
    created_at = Column(DateTime(6), nullable=False, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

# messages 테이블
class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    chat_id = Column(String(255), ForeignKey("chatlist.chat_id"), nullable=False)
    created_at = Column(DateTime(6), nullable=False, default=datetime.utcnow)
    message = Column(String(255))
    is_answer = Column(Boolean, nullable=False, default=False)
    
    user = relationship("User", back_populates="messages")
    chat = relationship("ChatList", back_populates="messages")