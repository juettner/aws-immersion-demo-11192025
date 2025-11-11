import React, { useRef, useEffect } from 'react';
import Message, { type MessageProps } from './Message';
import MessageInput from './MessageInput';
import './ChatContainer.css';

export interface ChatContainerProps {
  messages: MessageProps[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  isTyping?: boolean;
  error?: string | null;
  disabled?: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  onSendMessage,
  isLoading = false,
  isTyping = false,
  error = null,
  disabled = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Concert AI Assistant</h2>
        <p>Ask me about artists, venues, concerts, or get recommendations!</p>
      </div>

      <div className="chat-messages" ref={messagesContainerRef}>
        {messages.length === 0 && !isLoading && (
          <div className="chat-empty-state">
            <div className="empty-state-icon">💬</div>
            <h3>Start a conversation</h3>
            <p>Ask me anything about concerts, artists, venues, or ticket sales!</p>
            <div className="example-queries">
              <p className="example-label">Try asking:</p>
              <ul>
                <li>"What are the most popular venues?"</li>
                <li>"Show me upcoming concerts in New York"</li>
                <li>"Recommend artists similar to The Rolling Stones"</li>
                <li>"Predict ticket sales for Madison Square Garden"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <Message key={message.id} {...message} />
        ))}

        {isTyping && (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <span className="typing-text">AI is thinking...</span>
          </div>
        )}

        {error && (
          <div className="chat-error">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-wrapper">
        <MessageInput
          onSend={onSendMessage}
          disabled={disabled || isLoading}
          placeholder={
            disabled
              ? 'Chat is disabled'
              : isLoading
              ? 'Waiting for response...'
              : 'Ask about concerts, artists, venues...'
          }
        />
      </div>
    </div>
  );
};

export default ChatContainer;
