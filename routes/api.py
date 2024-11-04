from fastapi import HTTPException
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import uuid
from datetime import datetime
from typing import Optional
import random

# 환경 변수 로드
load_dotenv()

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = OpenAI(api_key = OPENAI_API_KEY)

# 임시 데이터 로드 (data.json)
def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Data file not found"
        )

# 채팅 기록 저장
def save_chat_data(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# chat_id 생성
def generate_chat_id():
    return str(uuid.uuid4())

# 온보딩 정보 불러오기
def get_user_onboarding(userid: str):
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            
        # users 배열에서 해당 user_id를 가진 사용자 찾기
        for user in data.get('users', []):
            if user['user_id'] == userid:
                return user['onboarding']
                
        # 사용자를 찾지 못한 경우 에러 발생
        raise HTTPException(
            status_code=404,
            detail=f"User {userid} not found or onboarding data not available"
        )
    
    # 데이터 파일이 없는 경우
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Data file not found"
        )
        
    # json 형식에 맞지 않는 데이터인 경우
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Invalid data file format"
        )

# prompt 불러오기
def read_prompt(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        prompt = file.read().strip()
    return prompt

# STT 모델 : OpenAI whisper-1
def speech2text(file_path):
    audio_file= open(file_path, "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file,
    language="ko",
    temperature=0
    )

    return transcription.text

# Chat 모델 : OpenAI 4o-mini
def get_completion(userid: str, situation: str, inst: str, chatid: Optional[str] = None):
    data = load_data()
    
    situations = ["go shopping", "talk with friends", "travel", "learn alphabet", "airport"]
    
    # random course인 경우
    actual_situation = situation
    
    if situation == "random course":
        # 진행 중인 random 대화가 있는 경우
        if chatid and chatid in data["chats"]:
            actual_situation = data["chats"][chatid]["situation"]
        else:
            # 새로운 random 대화인 경우 상황 무작위 선택
            actual_situation = random.choice(situations)
            
    # 새로운 대화 시작
    if chatid is None:
        new_chat_id = generate_chat_id()
        data["chats"][new_chat_id] = {
            "user_id": userid,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "situation": actual_situation
        }
        chatid = new_chat_id
        
    # 기존 대화 확인
    elif chatid in data["chats"]:
        # 대화가 10회 이상이면 에러 반환
        if len(data["chats"][chatid]["messages"]) >= 20:  # 10회 대화는 20개의 메시지 (AI + User)
            raise HTTPException(status_code=400, detail="대화 제한에 도달했습니다. 새로운 대화를 시작해주세요.")
    else:
        raise HTTPException(status_code=404, detail="유효하지 않은 대화입니다.")
    
    # 현재 채팅의 메시지 가져오기
    chat_messages = data["chats"][chatid]["messages"]
    
    # 사용자 온보딩 정보 가져오기
    onboarding = get_user_onboarding(userid)
    level, purpose, age = onboarding
    
    # system 프롬프트 불러오기
    promt_path = "./prompts/onboarding.txt"
    prompt = read_prompt(promt_path)
    prompt = prompt.format(level=level, purpose=purpose, age=age, actual_situation=actual_situation)
    
    messages = [{"role": "system", "content": prompt}]
    
    # 이전 대화 내역 추가
    for msg in chat_messages:
        messages.append({
            "role": "user",
            "content": f"[이전 대화 기록] {msg['content']}"
        } if msg['role'] == "user" else {
            "role": "assistant",
            "content": f"[이전 대화 기록] {msg['content']}"
        })
    
    # 현재 메시지 추가
    messages.append({"role": "user", "content": f"[현재 메시지] {inst}"})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )
    
    assistant_response = response.choices[0].message.content
    data["chats"][chatid]["messages"].append({"role": "user", "content": inst})
    data["chats"][chatid]["messages"].append({"role": "assistant", "content": assistant_response})
    save_chat_data(data)
    
    return chatid, assistant_response, len(data["chats"][chatid]["messages"]) // 2, actual_situation
