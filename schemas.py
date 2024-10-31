from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True