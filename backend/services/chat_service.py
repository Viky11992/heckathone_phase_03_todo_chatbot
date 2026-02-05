from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from models import ChatSession, ChatMessage
from schemas.chat_schemas import ChatMessageCreate, ChatSessionCreate


class ChatService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_session(self, user_id: str) -> ChatSession:
        """Create a new chat session for a user"""
        session = ChatSession(user_id=user_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create a new one if session_id is not provided"""
        if session_id:
            # Get existing session
            session = self.db.exec(
                select(ChatSession).where(ChatSession.id == session_id).where(ChatSession.user_id == user_id)
            ).first()
            if not session:
                raise ValueError("Session not found or doesn't belong to user")
            return session
        else:
            # Create new session
            return self.create_session(user_id)

    def add_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """Add a message to a chat session"""
        message = ChatMessage(
            user_id=message_data.user_id,
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_session_history(self, session_id: str, user_id: str) -> List[ChatMessage]:
        """Retrieve chat history for a session"""
        # Verify session belongs to user
        session = self.db.exec(
            select(ChatSession).where(ChatSession.id == session_id).where(ChatSession.user_id == user_id)
        ).first()

        if not session:
            raise ValueError("Session not found or doesn't belong to user")

        # Get messages for the session
        messages = self.db.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        ).all()

        return messages

    def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        sessions = self.db.exec(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        ).all()

        return sessions

    def clear_session_history(self, session_id: str, user_id: str):
        """Clear chat history for a session"""
        # Verify session belongs to user
        session = self.db.exec(
            select(ChatSession).where(ChatSession.id == session_id).where(ChatSession.user_id == user_id)
        ).first()

        if not session:
            raise ValueError("Session not found or doesn't belong to user")

        # Delete all messages in the session
        messages = self.db.exec(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        ).all()

        for message in messages:
            self.db.delete(message)

        self.db.commit()