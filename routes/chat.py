# AI Chat 기능 구현

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
import json
from datetime import datetime
import random
from typing import Optional, Dict, Tuple
from string import Template

from db.database import get_db
from db import models
from routes import routes_schemas
from routes.auth import get_current_user

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
SUMMARY_PATH = os.environ.get('SUMMARY_PATH')
FEEDBACK_PATH = os.environ.get('FEEDBACK_PATH')

# 상황 별 프롬프트 파일 매핑
SITUATION_PROMPTS = {
    "go shopping": "shopping.txt",
    "talk with friends": "friend.txt",
    "travel": "travel.txt",
    "learn alphabet": "alphabet.txt",
    "airport": "airport.txt"
}

client = OpenAI(api_key = OPENAI_API_KEY)

# 온보딩 정보 불러오기
def get_user_onboarding(db: Session, userid: str):
    user = db.query(models.User).filter(models.User.user_id == userid).first()
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

# 상황 별 prompt 불러오기
def read_situation_prompt(situation: str, level: str, purpose: str, age: str) -> str:
    
    if situation not in SITUATION_PROMPTS:
        raise ValueError(f"유효하지 않은 상황입니다: {situation}")
        
    prompt_file = os.path.join(PROMPT_PATH, SITUATION_PROMPTS[situation])
    
    with open(prompt_file, 'r', encoding='utf-8') as file:
        prompt = file.read().strip()
        
    template = Template(prompt)
    prompt = template.substitute(
        level=level,
        purpose=purpose,
        age=age
    )
    
    return prompt

# prompt 불러오기
def read_prompt(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        prompt = file.read().strip()
    return prompt

# 대화 요약 및 피드백 생성
def generate_summary_and_feedback(db: Session, chat_id: str) -> Tuple[str, dict]:
    
    # 전체 대화 불러오기
    messages = db.query(models.Message).filter(
        models.Message.chat_id == chat_id
    ).order_by(models.Message.created_at).all()
    
    conversation = "\n".join([
        f"{'AI' if msg.is_answer else 'User'}: {msg.message}"
        for msg in messages
    ])
    
    # 요약 생성
    summary_prompt = read_prompt(SUMMARY_PATH)
    summary_messages = [
        {"role": "system", "content": summary_prompt},
        {"role": "user", "content": conversation}
    ]
    summary_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=summary_messages,
        temperature=0.3,
        max_tokens=50,
        response_format={"type": "json_object"}
    )

    try:
        summary_data = json.loads(summary_response.choices[0].message.content)
        summary = summary_data.get("summary", "요약을 생성할 수 없습니다.")
    except json.JSONDecodeError:
        summary = "요약을 생성할 수 없습니다."
    
    # 피드백 생성
    
    user = db.query(models.User).filter(
        models.User.user_id == messages[0].user_id
    ).first()
    
    if not user or not user.onboarding_info:
        raise HTTPException(status_code=400, detail="사용자 정보를 찾을 수 없습니다.")
    
    level, purpose, age = user.onboarding_info
    
    feedback_prompt = read_prompt(FEEDBACK_PATH)
    feedback_template = Template(feedback_prompt)
    formatted_feedback_prompt = feedback_template.substitute(
        level=level,
        purpose=purpose,
        age=age
    )
    
    feedback_messages = [
        {"role": "system", "content": formatted_feedback_prompt},
        {"role": "user", "content": conversation}
    ]
    
    feedback_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=feedback_messages,
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    try:
        feedback_content = feedback_response.choices[0].message.content
        feedback = json.loads(feedback_content)
            
        if not isinstance(feedback, dict) or \
           not all(key in feedback for key in ["grammar_points", "study_tips"]):
            raise ValueError("Invalid feedback format")

        chat = db.query(models.ChatList).filter(models.ChatList.chat_id == chat_id).first()
        if chat:
            chat.feedback = feedback
            db.commit()
            
        return summary, feedback
        
    except (json.JSONDecodeError, ValueError) as e:
        print("Error processing feedback:", str(e))
        feedback = {
            "grammar_points": "문법 피드백을 생성할 수 없습니다.",
            "study_tips": "학습 팁을 생성할 수 없습니다."
        }
        return summary, feedback

# Chat 모델 : OpenAI 4o-mini
def get_completion(db: Session, current_user: models.User, situation: str, inst: str, chatid: Optional[str] = None):
    situations = ["go shopping", "talk with friends", "travel", "learn alphabet", "airport"]
    actual_situation = situation
    userid = current_user.user_id
    
    # random course인 경우 처리 (랜덤 상황 선택)
    if situation == "random course":
        if chatid:
            chat = db.query(models.ChatList).filter(models.ChatList.chat_id == chatid).first()
            if chat:
                actual_situation = chat.situation
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
            situation=actual_situation,
            summary="New conversation",
            active=True
        )
        db.add(new_chat)
        db.commit()
    else:
        chat = db.query(models.ChatList).filter(
            models.ChatList.chat_id == chatid,
            models.ChatList.active == True
        ).first()
        
        if not chat:
            raise HTTPException(status_code=404, detail="유효하지 않은 대화입니다.") 

    # 기존 대화 이어가기
    chat_messages = db.query(models.Message).filter(
        models.Message.chat_id == chatid
    ).order_by(models.Message.created_at).all()

    # 온보딩 정보 가져오기
    level, purpose, age = get_user_onboarding(db, userid)
    
    # 상황 별 프롬프트 불러오기
    prompt = read_situation_prompt(actual_situation, level, purpose, age)

    messages = [{"role": "system", "content": prompt}]

    # 이전 대화 내역 추가
    for msg in chat_messages:
        role = "assistant" if msg.is_answer else "user"
        messages.append({
            "role": role,
            "content": f"[이전 대화 기록] {msg.message}"
        })

    # 현재 메시지 추가
    messages.append({
        "role": "user", 
        "content": f"[현재 메시지] {inst}"
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"}
    )

    try:
        response_data = json.loads(response.choices[0].message.content)
        is_conversation_end = response_data.get("error", False)
        assistant_response = response_data.get("response", "응답을 처리할 수 없습니다.")
    except json.JSONDecodeError:
        is_conversation_end = False
        assistant_response = "응답을 처리할 수 없습니다."

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
    
    if is_conversation_end:
        chat = db.query(models.ChatList).filter(models.ChatList.chat_id == chatid).first()
        summary, feedback = generate_summary_and_feedback(db, chatid)
        chat.summary = summary
        chat.feedback = feedback
        chat.active = False
        chat.completed_at = datetime.now()

    db.commit()

    return chatid, assistant_response, actual_situation


@router.post("/chat", response_model=routes_schemas.ChatResponse)
async def aichat(
    request: routes_schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    chatid, response, actual_situation = get_completion(
        db,
        current_user,
        request.situation,
        request.message,
        request.chat_id
    )
    
    return routes_schemas.ChatResponse(
        user_id=current_user.user_id,
        chat_id=chatid,
        response=response,
        situation=actual_situation
    )