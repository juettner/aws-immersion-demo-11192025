import React from 'react';
import { ChatProvider, useChatContext } from '../context/ChatContext';
import { ChatContainer } from '../components';
import './ChatbotPage.css';

const ChatbotPageContent: React.FC = () => {
  const { messages, isLoading, isTyping, error, sendMessage } = useChatContext();

  return (
    <div className="chatbot-page">
      <div className="chatbot-page-container">
        <ChatContainer
          messages={messages}
          onSendMessage={sendMessage}
          isLoading={isLoading}
          isTyping={isTyping}
          error={error}
          disabled={false}
        />
      </div>
    </div>
  );
};

const ChatbotPage: React.FC = () => {
  return (
    <ChatProvider>
      <ChatbotPageContent />
    </ChatProvider>
  );
};

export default ChatbotPage;
