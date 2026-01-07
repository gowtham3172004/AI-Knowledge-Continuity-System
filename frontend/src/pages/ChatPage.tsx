/**
 * ChatPage Component
 * 
 * Main page integrating all chat and knowledge features.
 */

import React, { useState } from 'react';
import { Header } from '../components/Layout/Header';
import { Sidebar } from '../components/Layout/Sidebar';
import { ChatWindow } from '../components/Chat/ChatWindow';
import { SourcePanel } from '../components/Chat/SourcePanel';
import { useChat } from '../hooks/useChat';
import { useKnowledge } from '../hooks/useKnowledge';
import { QueryRole, SourceDocument } from '../types/api';

export const ChatPage: React.FC = () => {
  const [selectedRole, setSelectedRole] = useState<QueryRole>(QueryRole.GENERAL);

  const {
    conversations,
    activeConversation,
    activeConversationId,
    isLoading,
    sendMessage,
    createConversation,
    setActiveConversationId,
    deleteConversation,
  } = useChat({ defaultRole: selectedRole });

  const { isHealthy } = useKnowledge();

  // Get sources from last assistant message
  const lastAssistantMessage = activeConversation?.messages
    .slice()
    .reverse()
    .find((m) => m.role === 'assistant' && m.response);

  const sources: SourceDocument[] = lastAssistantMessage?.response?.sources || [];

  return (
    <div className="h-screen flex flex-col bg-primary-50">
      {/* Header */}
      <Header
        selectedRole={selectedRole}
        onRoleChange={setSelectedRole}
        isHealthy={isHealthy}
      />

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
              onSendMessage={(msg) => sendMessage(msg, selectedRole)}
              isLoading={isLoading}
            />
          </div>

          {/* Source Panel (Right Sidebar) */}
          {sources.length > 0 && (
            <div className="w-80 border-l border-gray-200 bg-primary-50 overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 z-10">
                <h2 className="text-sm font-semibold text-primary-900">Source Documents</h2>
                <p className="text-xs text-primary-600 mt-0.5">
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
