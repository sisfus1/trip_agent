from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    chats = relationship("ChatSession", back_populates="owner")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)  # UUID or random string
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    is_persistent = Column(Boolean, default=False) # False = Temporary, True = Persistent
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Store chat history as a JSON string for simplicity in MVP SaaS
    messages_json = Column(String, default="[]")

    owner = relationship("User", back_populates="chats")
