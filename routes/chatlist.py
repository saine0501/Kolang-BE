from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from db.database import get_db
from routes.routes_schemas import ChatListResponse, ChatDetailResponse
from db.models import ChatList, Message, User
from routes.auth import get_current_user

router = APIRouter(
    prefix="/api",
    tags=["Chatlist"]
)

@router.get("/chatlist", response_model=List[ChatListResponse], description="채팅방 내역 조회")
async def get_user_chats(db: Session = Depends(get_db), 
                         current_user: User = Depends(get_current_user)
                         ):
    
    user_id = current_user.user_id
   
    # 최근 채팅방 10개 조회
    chats = db.query(ChatList).filter(
        ChatList.user_id == user_id
    ).order_by(
        desc(ChatList.created_at)
    ).limit(10).all()
    
    if not chats:
        raise HTTPException(status_code=404, detail="No chats found")
    
    return chats

@router.get("/chatlist/detail/{chatId}", response_model=ChatDetailResponse)
async def get_chat_messages(chatId: str, db: Session = Depends(get_db), 
                            current_user: User = Depends(get_current_user)
                            ):

    # chatId에 해당하는 채팅방 정보 조회
    chat = db.query(ChatList).filter(ChatList.chat_id == chatId).first()
    if not chat:
        raise HTTPException(status_code=404, detail="No chats found")
    
    # 메시지 내역 조회 (오래된 순으로 정렬)
    messages = db.query(Message).filter(
        Message.chat_id == chatId
    ).order_by(
        Message.created_at
    ).all()
    
    if not messages:
        # 채팅방은 존재하지만 메시지가 없는 경우
        return ChatDetailResponse(
            chat_id=chat.chat_id,
            summary=chat.summary,
            messages=[]
        )
    
    return ChatDetailResponse(
        user_id=current_user.user_id,
        chat_id=chat.chat_id,
        summary=chat.summary,
        messages=messages
    )