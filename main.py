from fastapi import FastAPI, HTTPException, Depends, APIRouter
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.orm import Session

from db.database import engine, get_db
from db import models, schemas

from routes import api, chatlist, stt
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

app.include_router(router)
app.include_router(chatlist.router)
app.include_router(stt.router)
