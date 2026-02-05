from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# Chat Session Schemas
class ChatSessionCreate(BaseModel):
    user_id: str


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# Chat Message Schemas
class ChatMessageBase(BaseModel):
    user_id: str
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: str
    created_at: datetime


# AI Action Log Schemas
class AiActionLogCreate(BaseModel):
    user_id: str
    session_id: str
    action_type: str
    request_params: str
    result: str


class AiActionLogResponse(AiActionLogCreate):
    id: str
    timestamp: datetime


# Chat API Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]