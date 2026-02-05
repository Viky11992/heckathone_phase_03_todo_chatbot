'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../hooks/use-auth';
import { sendChatMessage, getChatHistory, getUserSessions } from '../../lib/api';

interface ChatMessage {
  id: string;
  userId: string;
  sessionId: string;
  role: string; // 'user', 'assistant', 'system'
  content: string;
  createdAt: Date;
}

const ChatPage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Initialize chat session when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user?.id) {
      initializeSession();
    }
  }, [isAuthenticated, user]);

  // Load chat history when session ID changes
  useEffect(() => {
    if (sessionId && isAuthenticated) {
      loadChatHistory();
    }
  }, [sessionId, isAuthenticated]);

  const initializeSession = async () => {
    try {
      // Try to get user's existing sessions
      const response = await getUserSessions();
      if (response.sessions && response.sessions.length > 0) {
        // Use the most recent session
        const mostRecentSession = response.sessions.reduce((latest: any, current: any) =>
          new Date(current.updated_at) > new Date(latest.updated_at) ? current : latest
        );
        setSessionId(mostRecentSession.id);
      } else {
        // No sessions exist, we'll create one when the user sends their first message
        setSessionId(null);
      }
    } catch (error) {
      console.error('Failed to initialize chat session:', error);
      // If session retrieval fails, we'll still allow the user to start a new session
      setSessionId(null);
    }
  };

  const loadChatHistory = async () => {
    if (!sessionId || !user?.id) return;

    try {
      const response = await getChatHistory(sessionId);
      setMessages(response.messages.map((msg: any) => ({
        id: msg.id,
        userId: msg.user_id,
        sessionId: msg.session_id,
        role: msg.role,
        content: msg.content,
        createdAt: new Date(msg.created_at),
      })));
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputMessage.trim() || !user?.id || isSending) return;

    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      id: Date.now().toString(), // Temporary ID
      userId: user.id,
      sessionId: sessionId || '',
      role: 'user',
      content: inputMessage,
      createdAt: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsSending(true);

    try {
      // Send message to backend
      const response = await sendChatMessage({
        message: inputMessage,
        session_id: sessionId || undefined,
      });

      if (response.success) {
        // Update session ID if new session was created
        if (response.data.session_id && !sessionId) {
          setSessionId(response.data.session_id);
        }

        // Add AI response to messages
        const aiMessage: ChatMessage = {
          id: `ai-${Date.now()}`,
          userId: user.id,
          sessionId: response.data.session_id,
          role: 'assistant',
          content: response.data.response,
          createdAt: new Date(),
        };

        setMessages(prev => [...prev, aiMessage]);

        // If tools were used, add a system message
        if (response.data.tools_used && response.data.tools_used.length > 0) {
          const toolMessage: ChatMessage = {
            id: `tool-${Date.now()}`,
            userId: user.id,
            sessionId: response.data.session_id,
            role: 'system',
            content: `Tools executed: ${response.data.tools_used.map((t: any) => t.tool).join(', ')}`,
            createdAt: new Date(),
          };
          setMessages(prev => [...prev, toolMessage]);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);

      // Add error message to UI
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        userId: user.id,
        sessionId: sessionId || '',
        role: 'system',
        content: 'Sorry, I encountered an error processing your request.',
        createdAt: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chat...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Store the current URL in sessionStorage so we can redirect back after login
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('redirectAfterAuth', window.location.pathname);
    }

    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">Please log in to use the chat</h2>
          <a href="/login?redirect=/chat" className="text-blue-500 hover:underline mr-4">Login</a>
          <a href="/signup?redirect=/chat" className="text-blue-500 hover:underline">Sign Up</a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 h-[calc(100vh-100px)] flex flex-col bg-gray-50 dark:bg-gray-900">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Todo AI Assistant</h1>
        <p className="text-gray-600 dark:text-gray-300">Chat with your personal AI assistant to manage your tasks</p>
      </div>

      <div className="flex-1 overflow-y-auto mb-4 bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <div className="mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium mb-2 text-gray-700 dark:text-gray-200">Start a conversation</h3>
            <p className="text-gray-600 dark:text-gray-300">Try asking me to:</p>
            <ul className="mt-2 space-y-1">
              <li className="text-sm text-gray-600 dark:text-gray-300">• Add a new task</li>
              <li className="text-sm text-gray-600 dark:text-gray-300">• List your tasks</li>
              <li className="text-sm text-gray-600 dark:text-gray-300">• Complete a task</li>
              <li className="text-sm text-gray-600 dark:text-gray-300">• Delete a task</li>
            </ul>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white dark:bg-blue-700'
                      : message.role === 'assistant'
                      ? 'bg-green-100 text-gray-800 dark:bg-green-800 dark:text-white'
                      : 'bg-yellow-100 text-gray-800 dark:bg-yellow-700 dark:text-white'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className={`text-xs mt-1 ${message.role === 'user' ? 'text-blue-200 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                    {message.createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg max-w-xs lg:max-w-md dark:bg-gray-700 dark:text-gray-200">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce dark:bg-gray-300"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-75 dark:bg-gray-300"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-150 dark:bg-gray-300"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type your message here..."
          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          disabled={isSending}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 dark:bg-blue-700 dark:hover:bg-blue-800"
          disabled={isSending || !inputMessage.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatPage;