from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from typing import List

from db import models
from db.models import ChatList, Message, User
from routes.schemas import ChatDetailResponse

# chat.py + stc.py

# 온보딩 정보 불러오기
def get_user_onboarding(db: Session, userid: str):
    user = db.query(User).filter(User.user_id == userid).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="사용자 정보가 없습니다."
        )
    if not user.onboarding or not user.onboarding_info:
        raise HTTPException(
            status_code=400,
            detail="사용자의 온보딩 정보를 불러올 수 없습니다."
        )
    
    return user.onboarding_info



# chatlist.py

# 최근 채팅방 목록 조회
def get_user_chats(db: Session, user_id: int, limit: int = 10) -> List[ChatList]:
    chats = db.query(ChatList).filter(
        ChatList.user_id == user_id
    ).order_by(
        desc(ChatList.created_at)
    ).limit(limit).all()
    
    if not chats:
        raise HTTPException(status_code=404, detail="No chats found")
    
    return chats

def get_chat_detail(db: Session, chat_id: str, current_user: User) -> ChatDetailResponse:

    # 채팅방 정보 조회 (chat_id)
    chat = db.query(ChatList).filter(ChatList.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="No chats found")
    
    # 메시지 내역 조회 (오름차순 정렬)
    messages = db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(
        Message.created_at
    ).all()
    
    return ChatDetailResponse(
        user_id=current_user.user_id,
        chat_id=chat.chat_id,
        situation=chat.situation,
        summary=chat.summary,
        messages=messages if messages else []
    )