from pydantic import BaseModel
from typing import Optional

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
