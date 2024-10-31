from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from router import *

from sqlalchemy.orm import Session
from database import *
import models, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # cross-origin request에서 cookie를 포함할 것인지 (default=False)
    allow_methods=["*"],     # cross-origin request에서 허용할 method들을 나타냄 (default=['GET']
    allow_headers=["*"],     # cross-origin request에서 허용할 HTTP Header 목록
)

@app.get("/")
async def read_root():
    return {"Hello" : "World"}

# Chat Request / Response 모델
class ChatRequest(BaseModel):
    userid: str
    situation: str
    message: str
    chatid: Optional[str] = None

class ChatResponse(BaseModel):
    chatid: str
    response: str
    message_count: int
    situation: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    chatid, response, message_count, actual_situation = get_completion(
        request.userid,
        request.situation,
        request.message,
        request.chatid
    )
    
    return ChatResponse(
        chatid=chatid,
        response=response,
        message_count=message_count,
        situation=actual_situation
    )
    
@app.post("/speech2text")
async def stt(file: UploadFile = File(...)):
    if file.filename == '':
        raise HTTPException(status_code=400, detail="음성 파일을 입력해주세요.")
    
    # 입력받은 파일 저장
    file_path = "./voice_file"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    
    file_path = os.path.join(file_path, file.filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    return speech2text(file_path)


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(email=user.email, username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user