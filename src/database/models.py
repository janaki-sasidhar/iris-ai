"""Database models for the bot"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for storing user information and settings"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # User settings
    model = Column(String(50), default="gemini-2.5-flash")
    max_tokens = Column(Integer, default=8192)
    temperature = Column(Float, default=0.7)
    thinking_mode = Column(Integer, default=0)  # Deprecated
    web_search_mode = Column(Integer, default=0)  # 0 = off, 1 = on (Gemini only)
    # New provider-specific settings
    gemini_thinking_tokens = Column(Integer, default=2048)
    gpt_reasoning_effort = Column(String(10), default="medium")  # minimal/low/medium/high
    gpt_verbosity = Column(String(10), default="medium")  # low/medium/high
    gpt_search_context_size = Column(String(10), default="medium")  # low/medium/high
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for managing chat sessions"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # SQLite doesn't have boolean
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing conversation history"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    image_path = Column(String(500), nullable=True)  # Path to stored image file
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Whitelist(Base):
    """Whitelist model for storing authorized users"""
    __tablename__ = "whitelist"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(Integer, nullable=True)  # Telegram ID of who added this user
    comment = Column(String(500), nullable=True)  # Optional comment about the user
