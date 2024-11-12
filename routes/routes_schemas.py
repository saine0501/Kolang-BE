# router들의 응답 모델 정의

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# chat.py

# Chat Request / Response 모델
class ChatRequest(BaseModel):
    user_id: str
    situation: str
    message: str
    chat_id: Optional[str] = None

class ChatResponse(BaseModel):
    user_id: str
    chat_id: str
    response: str
    message_count: int
    situation: str
    
# chatlist.py

# ChatList Response 모델 (채팅방 조회)
class ChatListResponse(BaseModel):
    user_id: str
    chat_id: str
    summary: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

# Message / ChatDetail Response 모델 (채팅 내역 조회)
class MessageResponse(BaseModel):
    message_id: int
    chat_id: str
    user_id: str
    message: Optional[str] = None
    created_at: datetime
    is_answer: bool

    class Config:
        from_attributes = True

class ChatDetailResponse(BaseModel):
    user_id: str
    chat_id: str
    summary: str
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True

# auth.py

class OnboardingRequest(BaseModel):
    level: str
    purpose: str
    age: str