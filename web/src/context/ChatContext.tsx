import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { ChatMessage } from '../types';
import type { MessageProps } from '../components/Message';
import * as chatbotService from '../services/chatbot';

interface ChatContextValue {
  messages: MessageProps[];
  sessionId: string;
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
  loadHistory: () => Promise<void>;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: React.ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize session on mount
  useEffect(() => {
    const id = chatbotService.getOrCreateSessionId();
    setSessionId(id);
  }, []);

  // Load conversation history on mount
  useEffect(() => {
    if (sessionId) {
      loadHistory();
    }
  }, [sessionId]);

  const convertChatMessageToMessageProps = (msg: ChatMessage): MessageProps => {
    return {
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp,
      data: msg.data,
      visualization: msg.visualization,
      status: 'sent',
    };
  };

  const loadHistory = useCallback(async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      setError(null);
      const response = await chatbotService.getConversationHistory(sessionId);
      
      const historyMessages = response.messages.map(convertChatMessageToMessageProps);
      setMessages(historyMessages);
    } catch (err) {
      console.error('Failed to load conversation history:', err);
      // Don't show error for history loading failure - just start fresh
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Create temporary user message
    const tempUserMessage: MessageProps = {
      id: `temp_${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
      status: 'sending',
    };

    setMessages((prev) => [...prev, tempUserMessage]);
    setIsLoading(true);
    setIsTyping(true);
    setError(null);

    try {
      const response = await chatbotService.sendMessage(message, sessionId);

      // Update user message to sent status
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempUserMessage.id
            ? { ...msg, id: response.message.id || msg.id, status: 'sent' as const }
            : msg
        )
      );

      // Add assistant response
      const assistantMessage = convertChatMessageToMessageProps(response.message);
      setMessages((prev) => [...prev, assistantMessage]);

      // Update session ID if it changed
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
        localStorage.setItem('chatbot_session_id', response.session_id);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      
      // Mark user message as error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempUserMessage.id
            ? { ...msg, status: 'error' as const }
            : msg
        )
      );

      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  }, [sessionId, isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    chatbotService.clearSession();
    const newSessionId = chatbotService.createSessionId();
    setSessionId(newSessionId);
    localStorage.setItem('chatbot_session_id', newSessionId);
    setError(null);
  }, []);

  const value: ChatContextValue = {
    messages,
    sessionId,
    isLoading,
    isTyping,
    error,
    sendMessage,
    clearMessages,
    loadHistory,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
