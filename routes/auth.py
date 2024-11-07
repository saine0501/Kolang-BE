# 구글 로그인 구현

import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

# from httpx_oauth.clients.google import GoogleOAuth2
from db.database import get_db
from db import schemas
from db import models

# 환경 변수 설정
env_state = os.getenv("ENV_STATE", "dev")
env_file = ".env.prod" if env_state == "prod" else ".env.dev"
load_dotenv(env_file)

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_CALLBACK_URI = "http://localhost:8000/auth/google/callback"

auth_router = APIRouter(
    tags=['User'],
    prefix='/user'
)

def auth_google(code: str):
    try:
        # google에 access token 요청
        token_url = f"https://oauth2.googleapis.com/token?client_id={GOOGLE_CLIENT_ID}&client_secret={GOOGLE_CLIENT_SECRET}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}"
        token_response = requests.post(token_url)
        if token_response.status_code != 200:
            raise Exception

        # google에 회원 정보 요청
        access_token = token_response.json()['access_token']
        user_info = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
        user_response = requests.get(user_info)
        if user_response.status_code != 200:
            raise Exception
    except:
        raise Exception("google oauth error")

    info = user_response.json()
    # return models.User(
    #     name=info.get('name'),
    #     email=info.get('email'),
    #     created_at=
    # )
    return info
