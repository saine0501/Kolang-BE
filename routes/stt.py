from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import os
import platform
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from contextlib import contextmanager
from db import models
from routes.auth import get_current_user
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

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

# content_type에 따른 적절한 파일 확장자 반환
def get_extension_from_content_type(content_type: str) -> str:
    content_type_map = {
        'audio/webm': '.webm',
        'audio/mp3': '.mp3',
        'audio/mpeg': '.mpeg',
        'audio/wav': '.wav',
        'audio/m4a': '.m4a',
        'audio/x-m4a': '.m4a',
        'audio/mp4': '.mp4',
        'audio/x-wav': '.wav',
        'video/webm': '.webm'
    }
    extension = content_type_map.get(content_type, '.webm')
    logger.debug(f"Content type {content_type} mapped to extension {extension}")
    return extension

@contextmanager
def temporary_file(file_content: bytes, extension: str):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(file_content)
            tmp.flush()
            yield tmp.name
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Deleted temporary file: {temp_path}")
            except Exception as e:
                logger.error(f"Failed to remove temp file: {e}")

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

    try:
        content = await file.read()
        content_type = file.content_type or 'audio/webm'
        logger.info(f"Processing file: {file.filename}, type: {content_type}")
        
        # content_type에 따른 확장자 결정
        extension = get_extension_from_content_type(content_type)
        
        with temporary_file(content, extension) as temp_path:
            result = await speech2text(temp_path)
            return {"result": result, "user_id": current_user.user_id}
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"파일 처리 중 오류 발생: {str(e)}"
        )