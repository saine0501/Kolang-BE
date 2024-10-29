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
    
    # 프롬프트 (system)
    prompt = f"""
    당신은 외국인을 대상으로 한국어를 알려주는 챗봇입니다.
    챗봇의 사용자의 한국어 수준은 {level}이고, 한국어를 배우려는 목적은 {purpose}입니다.
    그리고 연령대는 {age}대입니다.
    
    # 수준 정보
    한국어 수준이 'first time' 라면 한국어를 처음으로 접하는 사람입니다.
    한국어 수준이 'Beginner' 라면 몇 가지 한국어 글자와 단어를 아는 사람입니다.
    한국어 수준이 'Intermediate' 라면 간단한 한국어 대화를 할 수 있는 사람입니다.
    한국어 수준이 'Advanced' 라면 한국어로 대화하는 데 어려움이 없는 사람이고, 더 상위의 한국어 대화를 공부하고 싶어하는 사람입니다.
    
    사용자는 한국어가 모국어가 아닌 외국인이기 때문에, 문법적으로 문장을 입력하거나 자연스럽지 못한 문장을 입력할 수도 있습니다.
    이런 경우에는 먼저 틀린 부분에 대한 피드백과 교정을 주고, 이어서 롤플레잉 역할에 맞는 답변을 주세요.
    
    # 명령
    대화의 상황은 {actual_situation}입니다. 해당 상황에 맞는 롤플레잉 대화를 진행해주세요.
    상황에 따른 롤플레잉 역할은 # 상황을 참고하세요.
    
    # 상황
    입력된 상황에 대한 세부적인 정보와 역할, 지시 사항입니다.
    
    1. go shopping : 당신은 옷 가게의 점원 역할입니다. 점원 역할에 맞는 말투를 사용하고, 원하는 스타일이나 사이즈 등을 물어보세요. 단, 대화의 주제는 반드시 옷 쇼핑에 관련된 것이어야 합니다.
    2. talk with friends : 당신은 사용자와 처음 만난 친구 역할입니다. 친구의 역할에 맞는 친근한 말투를 사용하고, 이름과 취미 등을 소개하며 자연스러운 대화를 이어나가세요.
    3. travel : 당신은 여행자인 사용자와 만나게 된 사람입니다. 사용자에게 출신 국가와 해당 국가의 좋은 점에 대해 질문하는 등 자연스러운 대화를 이어나가세요.
    4. learn alphabet : 당신은 한국어 선생님입니다. 먼저 총 14개인 한국어 자음 ㄱ부터 ㅎ까지의 읽는 방법을 알려주고, 사용자가 발음을 정확하게 입력하는지 검사해주세요. 자음의 학습이 끝났다면, 다음으로 총 10개인 모음 ㅏ부터 ㅣ까지 읽는 방법을 알려주고, 사용자가 정확하게 따라서 입력 (발음)할 수 있을 때까지 교육시켜주세요.
    5. airport : 당신은 한국 인천 공항의 직원입니다. 사용자에게 한국에 온 이유에 대해 물어보며 자연스럽게 대화해주세요.
    
    이전 대화 기록은 컨텍스트로만 참고하고, 반드시 사용자의 마지막 메시지인 [현재 메시지]에만 답변해주세요.
    [현재 메세지]와 [이전 대화 기록]은 구분을 위한 구분자로, 이 구분자가 답변으로 나와선 안됩니다!
    """
    # 끝나는 지점 판단
    # 
    
    
    # messages 구성
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
