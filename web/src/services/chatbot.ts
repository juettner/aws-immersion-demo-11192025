import { chatbotClient, apiRequest } from './api';
import type { ChatMessage, ChatResponse } from '../types';

export interface SendMessageRequest {
  message: string;
  session_id?: string;
}

export interface SendMessageResponse {
  message: ChatMessage;
  session_id: string;
}

export interface ConversationHistoryResponse {
  messages: ChatMessage[];
  session_id: string;
}

/**
 * Send a message to the chatbot
 */
export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<SendMessageResponse> {
  return apiRequest<SendMessageResponse>(chatbotClient, {
    method: 'POST',
    url: '/chat',
    data: {
      message,
      session_id: sessionId,
    },
  });
}

/**
 * Get conversation history for a session
 */
export async function getConversationHistory(
  sessionId: string
): Promise<ConversationHistoryResponse> {
  return apiRequest<ConversationHistoryResponse>(chatbotClient, {
    method: 'GET',
    url: '/history',
    params: {
      session_id: sessionId,
    },
  });
}

/**
 * Create a new chat session
 */
export function createSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Get or create session ID from localStorage
 */
export function getOrCreateSessionId(): string {
  const storageKey = 'chatbot_session_id';
  let sessionId = localStorage.getItem(storageKey);
  
  if (!sessionId) {
    sessionId = createSessionId();
    localStorage.setItem(storageKey, sessionId);
  }
  
  return sessionId;
}

/**
 * Clear current session
 */
export function clearSession(): void {
  localStorage.removeItem('chatbot_session_id');
}
