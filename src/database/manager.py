"""Database manager for handling all database operations"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import Base, User, Conversation, Message
from ..config.settings import settings


class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def init(self):
        """Initialize the database connection"""
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close the database connection"""
        if self.engine:
            await self.engine.dispose()
    
    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None,
                                first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Get or create a user"""
        async with self.async_session() as session:
            # Try to get existing user
            result = await session.execute(
                text("SELECT * FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": telegram_id}
            )
            user_data = result.fetchone()
            
            if user_data:
                user = User(
                    id=user_data[0],
                    telegram_id=user_data[1],
                    username=user_data[2],
                    first_name=user_data[3],
                    last_name=user_data[4],
                    created_at=user_data[5],
                    model=user_data[6],
                    max_tokens=user_data[7],
                    temperature=user_data[8],
                    thinking_mode=user_data[9] if len(user_data) > 9 else 0
                )
                
                # Update user info if changed
                if username != user.username or first_name != user.first_name or last_name != user.last_name:
                    await session.execute(
                        text("UPDATE users SET username = :username, first_name = :first_name, last_name = :last_name WHERE id = :id"),
                        {"username": username, "first_name": first_name, "last_name": last_name, "id": user.id}
                    )
                    await session.commit()
                
                return user
            
            # Create new user
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    async def get_active_conversation(self, user_id: int) -> Optional[Conversation]:
        """Get the active conversation for a user"""
        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT * FROM conversations WHERE user_id = :user_id AND is_active = 1 ORDER BY last_message_at DESC LIMIT 1"),
                {"user_id": user_id}
            )
            conv_data = result.fetchone()
            
            if conv_data:
                return Conversation(
                    id=conv_data[0],
                    user_id=conv_data[1],
                    started_at=conv_data[2],
                    last_message_at=conv_data[3],
                    is_active=conv_data[4]
                )
            return None
    
    async def create_conversation(self, user_id: int) -> Conversation:
        """Create a new conversation"""
        async with self.async_session() as session:
            # Deactivate any existing active conversations
            await session.execute(
                text("UPDATE conversations SET is_active = 0 WHERE user_id = :user_id AND is_active = 1"),
                {"user_id": user_id}
            )
            
            # Create new conversation
            conversation = Conversation(user_id=user_id)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation
    
    async def add_message(self, conversation_id: int, role: str, content: str, image_data: Optional[str] = None):
        """Add a message to a conversation"""
        async with self.async_session() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                image_data=image_data
            )
            session.add(message)
            
            # Update conversation last_message_at
            await session.execute(
                text("UPDATE conversations SET last_message_at = :last_message_at WHERE id = :id"),
                {"last_message_at": datetime.utcnow(), "id": conversation_id}
            )
            
            await session.commit()
    
    async def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get all messages in a conversation"""
        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT role, content, image_data FROM messages WHERE conversation_id = :conversation_id ORDER BY created_at"),
                {"conversation_id": conversation_id}
            )
            messages = []
            for row in result.fetchall():
                message = {
                    "role": row[0],
                    "content": row[1]
                }
                if row[2]:  # image_data
                    message["image_data"] = row[2]
                messages.append(message)
            return messages
    
    async def update_user_settings(self, user_id: int, model: Optional[str] = None,
                                 temperature: Optional[float] = None,
                                 thinking_mode: Optional[bool] = None):
        """Update user settings"""
        async with self.async_session() as session:
            query_params = {}
            set_clauses = []
            
            if model is not None:
                set_clauses.append("model = :model")
                query_params["model"] = model
            if temperature is not None:
                set_clauses.append("temperature = :temperature")
                query_params["temperature"] = temperature
            if thinking_mode is not None:
                set_clauses.append("thinking_mode = :thinking_mode")
                query_params["thinking_mode"] = 1 if thinking_mode else 0
            
            if set_clauses:
                query_params["user_id"] = user_id
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :user_id"
                await session.execute(text(query), query_params)
                await session.commit()
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT model, temperature, thinking_mode FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "model": row[0],
                    "temperature": row[1],
                    "thinking_mode": bool(row[2]) if len(row) > 2 else False
                }
            return {
                "model": settings.DEFAULT_MODEL,
                "temperature": settings.DEFAULT_TEMPERATURE,
                "thinking_mode": False
            }