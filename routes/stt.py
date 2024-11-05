# AI STT 기능 구현

from fastapi import APIRouter, File, UploadFile, HTTPException
import os
from openai import OpenAI
from dotenv import load_dotenv
import glob

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# 파일 관리 설정
MAX_FILES = 5
FILE_DIR = "././file"

client = OpenAI(api_key = OPENAI_API_KEY)

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

def remove_files():
    if not os.path.exists(FILE_DIR):
        os.makedirs(FILE_DIR)
        return
    
    # 디렉토리 내의 모든 파일 목록 가져오기
    files = glob.glob(os.path.join(FILE_DIR, "*"))
    
    # 생성 시간 기준으로 파일 정렬
    files.sort(key=os.path.getctime)
    
    # 최대 파일 개수를 초과하면 오래된 파일부터 삭제
    while len(files) > MAX_FILES:
        oldest_file = files.pop(0)
        try:
            os.remove(oldest_file)
        except Exception:
            print("파일을 삭제할 수 없습니다.")

@router.post("/speech2text")
async def stt(file: UploadFile = File(...)):
    if file.filename == '':
        raise HTTPException(status_code=400, detail="음성 파일을 입력해주세요.")
    
    remove_files()
    
    # 입력받은 파일 저장
    file_path = os.path.join(FILE_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        result = speech2text(file_path)
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="STT를 실행할 수 없습니다.")
    