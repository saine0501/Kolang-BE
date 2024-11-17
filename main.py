import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from db.database import engine
from db import models

from routes import chat, chatlist, stt, auth

env_state = os.getenv("ENV_STATE", "dev")
env_file = ".env.prod" if env_state == "prod" else ".env.dev"
load_dotenv(env_file)

SECRET_KEY=os.getenv("SECRET_KEY")

models.Base.metadata.create_all(bind=engine)

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

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="google-login",
    same_site="lax",
    https_only=False
)

@app.get("/")
async def read_root():
    return {"Hello" : "World"}

app.include_router(chatlist.router)
app.include_router(stt.router)
app.include_router(chat.router)
app.include_router(auth.router)