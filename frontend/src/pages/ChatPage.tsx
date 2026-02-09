/**
 * ChatPage Component
 * 
 * Main page integrating all chat and knowledge features.
 */

import React from 'react';
import { Header } from '../components/Layout/Header';
import { Sidebar } from '../components/Layout/Sidebar';
import { ChatWindow } from '../components/Chat/ChatWindow';
import { SourcePanel } from '../components/Chat/SourcePanel';
import { useChat } from '../hooks/useChat';
import { SourceDocument } from '../types/api';

interface ChatPageProps {
  onNavigate?: (page: 'home' | 'chat' | 'documents' | 'dashboard') => void;
  currentPage?: 'home' | 'chat' | 'documents' | 'dashboard';
}

export const ChatPage: React.FC<ChatPageProps> = ({ onNavigate, currentPage }) => {
  const {
    conversations,
    activeConversation,
    activeConversationId,
    isLoading,
    sendMessage,
    createConversation,
    setActiveConversationId,
    deleteConversation,
  } = useChat();

  // Get sources from last assistant message
  const lastAssistantMessage = activeConversation?.messages
    .slice()
    .reverse()
    .find((m) => m.role === 'assistant' && m.response);

  const sources: SourceDocument[] = lastAssistantMessage?.response?.sources || [];

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <Header onNavigate={onNavigate} currentPage={currentPage} />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={setActiveConversationId}
          onNewConversation={createConversation}
          onDeleteConversation={deleteConversation}
        />

        {/* Chat Window */}
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 bg-white">
            <ChatWindow
              messages={activeConversation?.messages || []}
              onSendMessage={(msg) => sendMessage(msg)}
              isLoading={isLoading}
            />
          </div>

          {/* Source Panel (Right Sidebar) */}
          {sources.length > 0 && (
            <div className="w-80 border-l border-gray-200 bg-gray-50 overflow-y-auto scrollbar">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 z-10">
                <h2 className="text-sm font-semibold text-gray-900">Source Documents</h2>
                <p className="text-xs text-gray-600 mt-0.5">
                  {sources.length} source{sources.length !== 1 ? 's' : ''} used
                </p>
              </div>
              <div className="p-4">
                <SourcePanel sources={sources} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
