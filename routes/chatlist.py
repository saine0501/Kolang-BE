from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from routes.schemas import ChatListResponse, ChatDetailResponse
from db.models import User
from routes.auth import get_current_user
from db import crud

router = APIRouter(
    prefix="/api/chatlist",
    tags=["Chatlist"]
)

@router.get("", response_model=List[ChatListResponse], description="채팅방 내역 조회")
async def get_user_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_user_chats(db=db, user_id=current_user.user_id)

@router.get("/detail/{chatId}", response_model=ChatDetailResponse)
async def get_chat_messages(
    chatId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_chat_detail(db=db, chat_id=chatId, current_user=current_user)
