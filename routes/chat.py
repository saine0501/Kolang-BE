# AI Chat 기능 구현

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime
from typing import Optional
import random
import json

from db.database import get_db
from db import models
from routes import routes_schemas

router = APIRouter(
    prefix="/api/ai",
    tags=["AI"]
)

# 환경 변수 로드
env_state = os.getenv("ENV_STATE", "dev")
env_file = ".env.prod" if env_state == "prod" else ".env.dev"
load_dotenv(env_file)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
PROMPT_PATH = os.environ.get('PROMPT_PATH')

client = OpenAI(api_key = OPENAI_API_KEY)

# 온보딩 정보 불러오기
def get_user_onboarding(db: Session, userid: str):
    user = db.query(models.User).filter(models.User.user_id == userid).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {userid} not found"
        )
    if not user.onboarding or not user.onboarding_info:
        raise HTTPException(
            status_code=400,
            detail="User onboarding information not available"
        )
    
    return user.onboarding_info

# prompt 불러오기
def read_prompt(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        prompt = file.read().strip()
    return prompt

# 대화 요약 함수
def summarize_conversation(db: Session, chat_id: str) -> str:
    # 해당 채팅의 모든 메시지 가져오기
    messages = db.query(models.Message).filter(
        models.Message.chat_id == chat_id
    ).order_by(models.Message.created_at).all()
    
    # 메시지들을 하나의 문자열로 변환
    conversation = "\n".join([
        f"{'AI' if msg.is_answer else 'User'}: {msg.message}"
        for msg in messages
    ])
    
    prompt_path = "C:/Users/USER/Desktop/kolang_api/prompts/summary.txt"
    prompt = read_prompt(prompt_path)
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": conversation}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=50
    )
    
    return response.choices[0].message.content

# Chat 모델 : OpenAI 4o-mini
def get_completion(db: Session, userid: str, situation: str, inst: str, chatid: Optional[str] = None):
    situations = ["go shopping", "talk with friends", "travel", "learn alphabet", "airport"]
    actual_situation = situation
    
    # random course인 경우 처리
    if situation == "random course":
        if chatid:
            chat = db.query(models.ChatList).filter(models.ChatList.chat_id == chatid).first()
            if chat:
                actual_situation = chat.category
            else:
                actual_situation = random.choice(situations)
        else:
            actual_situation = random.choice(situations)

    # 새로운 대화 시작
    if chatid is None:
        chatid = str(uuid.uuid4())
        new_chat = models.ChatList(
            chat_id=chatid,
            user_id=userid,
            category=actual_situation,
            summary="New conversation"
        )
        db.add(new_chat)
        db.commit()
    else:
        chat = db.query(models.ChatList).filter(
            models.ChatList.chat_id == chatid
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="유효하지 않은 대화입니다.")
            
        message_count = db.query(models.Message).filter(
            models.Message.chat_id == chatid
        ).count()
        
        if message_count >= 20:
            raise HTTPException(
                status_code=400,
                detail="대화 제한에 도달했습니다. 새로운 대화를 시작해주세요."
            )

    # 기존 대화 이어가기
    chat_messages = db.query(models.Message).filter(
        models.Message.chat_id == chatid
    ).order_by(models.Message.created_at).all()

    # 온보딩 정보 가져오기
    onboarding_info = get_user_onboarding(db, userid)
    level, purpose, age = onboarding_info

    # system 프롬프트 불러오기
    prompt = read_prompt(PROMPT_PATH)
    prompt = prompt.format(
        level=level,
        purpose=purpose,
        age=age,
        actual_situation=actual_situation
    )

    messages = [{"role": "system", "content": prompt}]

    # 이전 대화 내역 추가
    for msg in chat_messages:
        role = "assistant" if msg.is_answer else "user"
        messages.append({
            "role": role,
            "content": f"[이전 대화 기록] {msg.message}"
        })

    # 현재 메시지 추가
    messages.append({"role": "user", "content": f"[현재 메시지] {inst}"})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )

    assistant_response = response.choices[0].message.content

    # 사용자 메시지 저장
    user_message = models.Message(
        chat_id=chatid,
        user_id=userid,
        message=inst,
        is_answer=False
    )
    db.add(user_message)
    
    # AI 응답 저장
    assistant_message = models.Message(
        chat_id=chatid,
        user_id=userid,
        message=assistant_response,
        is_answer=True
    )
    db.add(assistant_message)
    
    # 현재 메시지 수 계산
    new_message_count = len(chat_messages) + 2
    
    # 메시지가 20개(10회)가 되면 요약 생성 및 저장
    if new_message_count == 20:
        summary = summarize_conversation(db, chatid)
        chat = db.query(models.ChatList).filter(models.ChatList.chat_id == chatid).first()
        chat.summary = summary
    
    db.commit()

    message_count = new_message_count // 2

    return chatid, assistant_response, message_count, actual_situation

@router.post("/chat", response_model=routes_schemas.ChatResponse)
async def aichat(
    request: routes_schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    chatid, response, message_count, actual_situation = get_completion(
        db,
        request.user_id,
        request.situation,
        request.message,
        request.chat_id
    )
    
    return routes_schemas.ChatResponse(
        chat_id=chatid,
        response=response,
        message_count=message_count,
        situation=actual_situation
    )