"""
Test script to verify the chat functionality works end-to-end
"""
import asyncio
from sqlmodel import Session, select
from database import engine
from models import User, ChatSession, ChatMessage
from services.chat_service import ChatService
from mcp_server import MCPServer


def test_chat_functionality():
    """Test the full chat functionality"""
    print("Testing chat functionality...")

    # Create a database session
    with Session(engine) as db:
        # Check if test user already exists
        existing_user = db.exec(select(User).where(User.id == "test-chat-user")).first()

        if existing_user:
            user = existing_user
            print(f"Using existing test user: {user.email}")
        else:
            # Create a test user
            user = User(
                id="test-chat-user",
                email="chat-test@example.com",
                name="Chat Test User",
                hashed_password=User.hash_password("password123")
            )

            # Add user to database
            db.add(user)
            db.commit()
            db.refresh(user)

            print(f"Created test user: {user.email}")

        # Test ChatService
        chat_service = ChatService(db)

        # Create a chat session
        session = chat_service.create_session(user.id)
        print(f"Created chat session: {session.id}")

        # Add a user message
        from schemas.chat_schemas import ChatMessageCreate
        user_message = ChatMessageCreate(
            user_id=user.id,
            session_id=session.id,
            role="user",
            content="Add a task to buy groceries"
        )

        message = chat_service.add_message(user_message)
        print(f"Added user message: {message.content}")

        # Test MCP Server
        mcp_server = MCPServer(db)

        # Test add_task functionality
        try:
            result = asyncio.run(
                mcp_server.execute_tool(
                    "add_task",
                    {"title": "Buy groceries", "description": "Milk, bread, eggs"},
                    user.id
                )
            )
            print(f"MCP add_task result: {result}")
        except Exception as e:
            print(f"MCP add_task error: {e}")

        # Test list_tasks functionality
        try:
            result = asyncio.run(
                mcp_server.execute_tool(
                    "list_tasks",
                    {"status": "all"},
                    user.id
                )
            )
            print(f"MCP list_tasks result: {result}")
        except Exception as e:
            print(f"MCP list_tasks error: {e}")

    print("Chat functionality test completed!")


if __name__ == "__main__":
    test_chat_functionality()