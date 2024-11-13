# 구글 로그인 구현

import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from db.database import get_db
from db import models
from datetime import datetime, timedelta
from jose import jwt, JWTError
import uuid
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from fastapi.responses import RedirectResponse
from routes.routes_schemas import OnboardingRequest

# 환경 변수 설정
env_state = os.getenv("ENV_STATE", "dev")
env_file = ".env.prod" if env_state == "prod" else ".env.dev"
load_dotenv(env_file)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY=os.getenv("SECRET_KEY")
GOOGLE_REDIRECT_URI=os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL=os.getenv("FRONTEND_URL")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

router = APIRouter(
    tags=['User'],
    prefix='/api/user'
)

# OAuth2 스키마 정의
oauth2_schema = OAuth2PasswordBearer(tokenUrl='/token')

# 구글 OAuth 설정 초기화 및 사용자 정보 접근 권한 요청 (email, profile)
oauth = OAuth(Config(env_file))
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# 토큰 생성 함수
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 현재 유저 정보 반환
async def get_current_user(
    token: str | None = Depends(oauth2_schema),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(
        models.User.user_id == user_id,
        models.User.deleted_at.is_(None)
    ).first()
    
    if user is None:
        raise credentials_exception
        
    return user

# 사용자를 구글 로그인 페이지로 리다이렉트
@router.get("/login")
async def login(request: Request):
    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(
        request, 
        redirect_uri,
        prompt='select_account'  # 계정 선택 화면 표시
    )
    
# 구글 로그인 콜백 처리
@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # 구글 토큰 검증 및 사용자 정보 획득
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.userinfo(token=token)
        email = user_info.get('email')
        name = user_info.get('name')

        # DB에서 사용자 조회 (deleted_at이 None인 경우만)
        user = db.query(models.User).filter(
            models.User.email == email,
            models.User.deleted_at.is_(None)
        ).first()
        
        # 신규 사용자인 경우 회원가입 진행
        if not user:
            user = models.User(
                user_id=str(uuid.uuid4()),
                email=email,
                name=name,
                created_at=datetime.utcnow(),
                onboarding=False,
                onboarding_info=None
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # JWT 토큰 생성
        access_token = create_access_token(
            data={
                "sub": user.user_id,
                "email": user.email,
                "name": user.name
            }
        )

        # 응답 데이터
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "onboarding": user.onboarding,
                "onboarding_info": user.onboarding_info
            }
        }

        # dev: JSON 응답
        if env_state == "dev":
            return response_data
        
        # prod: 프론트엔드로 리다이렉트 or JSON 응답
        else:
            if FRONTEND_URL:
                redirect_url = f"{FRONTEND_URL}/login/redirect?token={access_token}&user_id={user.user_id}"
                return RedirectResponse(url=redirect_url)
            else:
                return response_data

    except Exception as e:
        error_message = f"Failed to authenticate with Google: {str(e)}"
        if env_state == "dev":
            raise HTTPException(
                status_code=400,
                detail=error_message
            )
        elif FRONTEND_URL:
            error_redirect_url = f"{FRONTEND_URL}/login/redirect?error={error_message}"
            return RedirectResponse(url=error_redirect_url)
        else:
            raise HTTPException(
                status_code=400,
                detail=error_message
            )

# 현재 로그인한 사용자 정보 조회
@router.get("/me")
async def get_user_info(current_user: models.User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "onboarding": current_user.onboarding,
        "onboarding_info": current_user.onboarding_info,
        "created_at": current_user.created_at
    }
    
# 온보딩 정보 저장
@router.post("/start")
async def save_onboarding(
    onboarding_data: OnboardingRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 온보딩 정보를 JSON 형태로 변환
        onboarding_info = [
            onboarding_data.level,
            onboarding_data.purpose,
            onboarding_data.age
        ]
        
        # 현재 사용자의 온보딩 정보 저장
        current_user.onboarding = True
        current_user.onboarding_info = onboarding_info
        
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "user_id": current_user.user_id,
            "onboarding": current_user.onboarding,
            "onboarding_info": current_user.onboarding_info
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"온보딩 정보 저장 중 오류가 발생했습니다: {str(e)}"
        )
 