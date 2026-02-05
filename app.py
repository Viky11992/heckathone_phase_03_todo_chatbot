import gradio as gr
import google.generativeai as genai
import os
from backend.services.chat_service import ChatService
from backend.mcp_server import MCPServer
from sqlmodel import create_engine, Session
from backend.database import get_session
from backend.models import ChatSession, ChatMessage
import uuid
from datetime import datetime

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def chat_with_bot(message, history):
    """
    Function to handle chat with the bot
    """
    try:
        # Prepare context with conversation history
        context = "You are a helpful AI assistant that helps users manage their tasks. You can add, list, complete, update, and delete tasks. Always respond in a helpful and friendly manner. Recognize task creation requests in natural language. When a user expresses an intention to remember, do, schedule, or complete something, treat it as an 'add_task' request. For example: 'buy groceries', 'call mom', 'write report', 'schedule dentist appointment' should all be interpreted as tasks to add."

        full_prompt = context + "\n\nConversation history:\n"
        for user_msg, bot_msg in history:
            full_prompt += f"User: {user_msg}\nAssistant: {bot_msg}\n"

        full_prompt += f"User: {message}\nAssistant:"

        # Generate response using Gemini
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500
            )
        )

        return response.text if response.text else "I processed your request."

    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Todo AI Assistant") as demo:
    gr.Markdown("# 🤖 Todo AI Assistant")
    gr.Markdown("Chat with your AI assistant to manage tasks using natural language!")

    chatbot = gr.Chatbot(label="Conversation", height=400)
    msg = gr.Textbox(label="Your Message", placeholder="Type your message here...")
    clear = gr.Button("Clear Conversation")

    def respond(message, chat_history):
        bot_message = chat_with_bot(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

# Launch the app
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))