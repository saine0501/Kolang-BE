from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import os
import platform
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from contextlib import contextmanager
from db import models
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

client = OpenAI(api_key = OPENAI_API_KEY)

# 임시 파일 저장 및 삭제
@contextmanager
def temporary_file(file: UploadFile):
    is_windows = platform.system() == 'Windows'
    
    default_extension = '.webm'
    file_extension = os.path.splitext(file.filename)[1] if file.filename else default_extension
    
    if is_windows:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=file_extension)
    
    try:
        # 파일 저장
        content = file.file.read()
        tmp.write(content)
        tmp.flush()
        
        # OS가 windows인 경우 처리
        if is_windows:
            tmp.close()
        
        # 파일 포인터 리셋
        file.file.seek(0)
        
        # 파일 경로 반환
        yield tmp.name
        
    finally:
        if is_windows:
            try:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
            except Exception as e:
                print(f"임시 파일 삭제 중 오류 발생: {e}")
        else:
            pass

# STT 모델 : OpenAI whisper-1
async def speech2text(file_path):
    try:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko",
                temperature=0
            )
            return transcription.text
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"STT 처리 중 오류 발생: {str(e)}"
        )

@router.post("/speech2text")
async def stt(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user)):
    if not file.file:
        raise HTTPException(status_code=400, detail="음성 파일을 입력해주세요.")

    content_type = file.content_type or ''
    allowed_content_types = {
        'audio/mp3', 'audio/mp4', 'audio/mpeg', 'audio/mpga', 
        'audio/m4a', 'audio/wav', 'audio/webm'
    }
    
    if content_type and content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_content_types)}"
        )
    
    try:
        with temporary_file(file) as temp_path:
            result = await speech2text(temp_path)
            return {
                "result": result,
                "user_id": current_user.user_id
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 처리 중 오류 발생: {str(e)}"
        )