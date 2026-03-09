from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class SessionCreate(BaseModel):
    title: str = "New Chat"
    is_persistent: bool = False

class SessionResponse(BaseModel):
    id: str
    user_id: int
    title: str
    is_persistent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionUpdate(BaseModel):
    title: Optional[str] = None
