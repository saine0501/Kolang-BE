from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True