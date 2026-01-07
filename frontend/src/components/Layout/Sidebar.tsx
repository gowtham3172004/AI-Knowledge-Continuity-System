/**
 * Sidebar Component
 * 
 * Conversation history and navigation.
 */

import React from 'react';
import { MessageSquare, Plus, Trash2, Clock } from 'lucide-react';
import { Conversation } from '../../types/api';
import { formatDistanceToNow } from 'date-fns';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
}) => {
  return (
    <aside className="w-64 bg-primary-50 border-r border-gray-200 flex flex-col h-full">
      {/* New Conversation Button */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center space-x-2 bg-accent-500 
                   text-white px-4 py-2.5 rounded-lg hover:bg-accent-600 
                   transition-colors font-medium"
        >
          <Plus className="h-5 w-5" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-6 text-center">
            <MessageSquare className="h-12 w-12 text-primary-300 mx-auto mb-2" />
            <p className="text-sm text-primary-600">No conversations yet</p>
            <p className="text-xs text-primary-500 mt-1">
              Start a new conversation to begin
            </p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`group relative rounded-lg p-3 cursor-pointer transition-all
                          ${
                            activeConversationId === conversation.id
                              ? 'bg-white shadow-sm border border-accent-200'
                              : 'hover:bg-primary-100'
                          }`}
                onClick={() => onSelectConversation(conversation.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3
                      className={`text-sm font-medium truncate ${
                        activeConversationId === conversation.id
                          ? 'text-primary-900'
                          : 'text-primary-700'
                      }`}
                    >
                      {conversation.title}
                    </h3>
                    <div className="flex items-center space-x-1 mt-1">
                      <Clock className="h-3 w-3 text-primary-400" />
                      <span className="text-xs text-primary-500">
                        {formatDistanceToNow(conversation.updated_at, { addSuffix: true })}
                      </span>
                    </div>
                    <p className="text-xs text-primary-600 mt-1">
                      {conversation.messages.length} messages
                    </p>
                  </div>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conversation.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity
                             p-1 hover:bg-red-50 rounded"
                    title="Delete conversation"
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="text-xs text-primary-600 text-center">
          <p className="font-medium">AI Knowledge Continuity</p>
          <p className="text-primary-500 mt-0.5">v1.0.0 · Enterprise Edition</p>
        </div>
      </div>
    </aside>
  );
};
