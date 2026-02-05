from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
import json
from datetime import datetime
from database import get_session
from middleware.auth import get_current_user_id as get_current_user
from schemas.chat_schemas import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessageResponse
from services.chat_service import ChatService
from mcp_server import MCPServer
import google.generativeai as genai
from config import settings


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def send_message(chat_request: ChatRequest, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    Send a message to the AI chatbot and receive a response
    """
    try:
        # Initialize chat service
        chat_service = ChatService(db)

        # Get or create chat session
        session = chat_service.get_or_create_session(current_user_id, chat_request.session_id)

        # Add user message to session
        from schemas.chat_schemas import ChatMessageCreate
        user_message = ChatMessageCreate(
            user_id=current_user_id,
            session_id=session.id,
            role="user",
            content=chat_request.message
        )
        chat_service.add_message(user_message)

        # Initialize MCP server
        mcp_server = MCPServer(db)

        # Get chat history for context
        messages = chat_service.get_session_history(session.id, current_user_id)

        # Configure Gemini
        if not settings.gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        # Configure the Gemini API
        genai.configure(api_key=settings.gemini_api_key)

        # Select the model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Prepare the prompt with context
        system_prompt = "You are a helpful AI assistant that helps users manage their tasks. You can add, list, complete, update, and delete tasks. Always respond in a helpful and friendly manner. Recognize task creation requests in natural language. When a user expresses an intention to remember, do, schedule, or complete something, treat it as an 'add_task' request. For example: 'buy groceries', 'call mom', 'write report', 'schedule dentist appointment' should all be interpreted as tasks to add. Respond with specific JSON format indicating the action: {'action': 'add_task', 'params': {'title': '...', 'description': '...'}}, {'action': 'list_tasks', 'params': {'status': 'all'}}, {'action': 'complete_task', 'params': {'task_id': 1}}, {'action': 'delete_task', 'params': {'task_id': 1}}, or {'action': 'update_task', 'params': {'task_id': 1, 'title': '...', 'description': '...'}}. Only suggest these actions for actual task operations, not for simple questions."

        # Build the conversation history
        full_prompt = system_prompt + "\n\nConversation history:\n"

        for msg in messages:
            # Skip the current user message since we're adding it separately below
            if not (msg.role == "user" and msg.content == chat_request.message):
                full_prompt += f"User: {msg.content}\n" if msg.role == "user" else f"Assistant: {msg.content}\n"

        # Add current user message
        full_prompt += f"User: {chat_request.message}\nAssistant:"

        # Generate content using Gemini
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500
                )
            )

            # Get the AI response text
            ai_response_text = response.text if response.text else "I processed your request."

            # Try to parse for potential action commands in the response
            import re
            import json as json_lib

            # Look for JSON-like structures in the response that might indicate actions
            json_match = re.search(r'\{.*\}', ai_response_text, re.DOTALL)

            ai_response = ai_response_text
            tools_used = []

            if json_match:
                try:
                    # Extract and parse the JSON
                    json_str = json_match.group()
                    action_data = json_lib.loads(json_str)

                    if 'action' in action_data and 'params' in action_data:
                        action_name = action_data['action']
                        action_params = action_data['params']

                        try:
                            # Execute the appropriate tool
                            result = await mcp_server.execute_tool(action_name, action_params, current_user_id)

                            tools_used.append({"tool": action_name, "result": result, "parameters": action_params})

                            # Generate appropriate response based on the tool used
                            if action_name == "add_task":
                                ai_response = f"I've added the task '{result.get('title', 'unnamed task')}' for you."
                            elif action_name == "list_tasks":
                                tasks = result.get('tasks', [])
                                if tasks:
                                    task_list = [f"• {task['title']}" for task in tasks[:5]]  # Show first 5 tasks
                                    ai_response = f"Here are your tasks:\n" + "\n".join(task_list)
                                    if len(tasks) > 5:
                                        ai_response += f"\n\n...and {len(tasks) - 5} more tasks."
                                else:
                                    ai_response = "You don't have any tasks right now."
                            elif action_name == "complete_task":
                                ai_response = f"I've marked the task '{result.get('title', 'unnamed task')}' as completed!"
                            elif action_name == "delete_task":
                                ai_response = f"I've deleted the task '{result.get('title', 'unnamed task')}'."
                            elif action_name == "update_task":
                                ai_response = f"I've updated the task '{result.get('title', 'unnamed task')}' for you."
                            else:
                                ai_response = f"I've completed the requested action: {result}"
                        except Exception as e:
                            # If action execution fails, return the original response
                            ai_response = ai_response_text
                    else:
                        # If the JSON doesn't match our action format, use the original response
                        ai_response = ai_response_text
                except (json_lib.JSONDecodeError, KeyError):
                    # If JSON parsing fails, use the original response
                    ai_response = ai_response_text
            else:
                # If no JSON found in response, use the original response
                ai_response = ai_response_text

        except Exception as e:
            # Handle any Gemini API errors
            ai_response = f"Sorry, I encountered an error processing your request: {str(e)}. Please try again."
            tools_used = []

        # Add AI response to session
        ai_message = ChatMessageCreate(
            user_id=current_user_id,
            session_id=session.id,
            role="assistant",
            content=ai_response
        )
        chat_service.add_message(ai_message)

        # Update session timestamp
        session.updated_at = datetime.utcnow()
        db.add(session)
        db.commit()

        # Prepare response
        response_data = {
            "response": ai_response,
            "session_id": session.id,
            "tools_used": tools_used
        }

        return ChatResponse(success=True, data=response_data)

    except Exception as e:
        # Log the full error for debugging
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    Retrieve chat history for a specific session
    """
    try:
        chat_service = ChatService(db)

        # Get session history
        messages = chat_service.get_session_history(session_id, current_user_id)

        # Convert to response format
        message_responses = []
        for msg in messages:
            message_responses.append(ChatMessageResponse(
                id=msg.id,
                user_id=msg.user_id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            ))

        return ChatHistoryResponse(messages=message_responses)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_user_sessions(current_user_id: str = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    List all chat sessions for the current user
    """
    try:
        chat_service = ChatService(db)

        # Get user sessions
        sessions = chat_service.get_user_sessions(current_user_id)

        # Convert to response format
        session_responses = []
        for session in sessions:
            session_responses.append({
                "id": session.id,
                "user_id": session.user_id,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            })

        return {"sessions": session_responses}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{session_id}")
async def clear_chat_history(session_id: str, current_user_id: str = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    Clear chat history for a specific session
    """
    try:
        chat_service = ChatService(db)

        # Clear session history
        chat_service.clear_session_history(session_id, current_user_id)

        return {"success": True, "message": "Chat history cleared successfully"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))