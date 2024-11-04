from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, APIRouter
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from routes import api, chat

from sqlalchemy.orm import Session

from db.database import engine, get_db
from db import models
from db import schemas

from routes import routes_schemas

models.Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api")

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello" : "World"}

@router.post("/ai/chat", response_model=routes_schemas.ChatResponse)
async def aichat(request: routes_schemas.ChatRequest):
    chatid, response, message_count, actual_situation = api.get_completion(
        request.userid,
        request.situation,
        request.message,
        request.chatid
    )
    
    return routes_schemas.ChatResponse(
        chatid=chatid,
        response=response,
        message_count=message_count,
        situation=actual_situation
    )
    
@router.post("/ai/speech2text")
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
    
    return api.speech2text(file_path)

app.include_router(router)
app.include_router(chat.router)
