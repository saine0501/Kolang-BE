# db에 테스트 데이터 넣기

from datetime import datetime
from sqlalchemy.orm import Session
from db.models import User, ChatList, Message
from db.database import engine, SessionLocal

def seed_database():
    db = SessionLocal()
    try:
        # 기존 데이터 삭제
        db.query(Message).delete()
        db.query(ChatList).delete()
        db.query(User).delete()
        
        # 테스트 유저 생성
        test_user = User(
            user_id="test",
            email="test@example.com",
            name="테스트",
            created_at=datetime.now(),
            onboarding=True,
            onboarding_info=["Intermediate", "culture", "30s"]
        )
        db.add(test_user)
        db.commit()
        
        # 채팅방 생성
        chat_rooms = []
        for i in range(1, 12):  # 11개의 채팅방 생성 (최근 10개만 보이는지 테스트하기 위해)
            chat = ChatList(
                chat_id=f"chat_{i}",
                user_id="test",
                summary=f"테스트 채팅방 {i}",
                category="test",
                created_at=datetime.now()
            )
            chat_rooms.append(chat)
        db.add_all(chat_rooms)
        db.commit()
        
        # 메시지 생성
        messages = []
        for chat in chat_rooms:
            # 각 채팅방마다 3개의 메시지 생성
            for j in range(1, 4):
                message = Message(
                    chat_id=chat.chat_id,
                    user_id="test",
                    created_at=datetime.now(),
                    message=f"테스트 메시지 {j}",
                    is_answer=False,
                )
                messages.append(message)
        db.add_all(messages)
        db.commit()
        
        print("테스트 데이터 생성 완료")
        
    except Exception as e:
        print(f"에러 발생: {e}")
        db.rollback()
    finally:
        db.close()    
        
seed_database()