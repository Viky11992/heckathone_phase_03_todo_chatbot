from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
import uuid


class ChatSessionBase(SQLModel):
    user_id: str = Field(index=True)


class ChatSession(ChatSessionBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessageBase(SQLModel):
    user_id: str = Field(index=True)
    session_id: str = Field(index=True, foreign_key="chatsession.id")
    role: str = Field(index=True)  # 'user' or 'assistant'
    content: str


class ChatMessage(ChatMessageBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to session
    session: ChatSession = Relationship(back_populates="messages")


class AiActionLogBase(SQLModel):
    user_id: str = Field(index=True)
    session_id: str = Field(index=True, foreign_key="chatsession.id")
    action_type: str = Field(index=True)  # 'add_task', 'list_tasks', etc.
    request_params: str  # JSON string of the parameters passed
    result: str  # JSON string of the result


class AiActionLog(AiActionLogBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to session
    session: ChatSession = Relationship()


# Add relationship to ChatSession
ChatSession.model_rebuild()