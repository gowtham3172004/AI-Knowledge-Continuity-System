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
    <aside className="w-72 bg-gradient-to-b from-gray-50 to-white border-r border-gray-200/50 flex flex-col h-full shadow-lg">
      {/* New Conversation Button */}
      <div className="p-6 border-b border-gray-200/50">
        <button
          onClick={() => onNewConversation()}
          className="w-full btn-primary group relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity"></div>
          <Plus className="h-5 w-5 group-hover:rotate-90 transition-transform duration-300" />
          <span className="font-semibold">New Conversation</span>
        </button>
        <p className="text-xs text-gray-500 text-center mt-3 font-medium">Start exploring knowledge</p>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {conversations.length === 0 ? (
          <div className="p-8 text-center animate-fade-in">
            <div className="bg-gradient-to-br from-accent-50 to-primary-50 rounded-2xl p-8 mb-4">
              <MessageSquare className="h-16 w-16 text-accent-400 mx-auto mb-4" />
              <p className="text-sm font-semibold text-gray-700">No conversations yet</p>
              <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                Click the button above to start your<br/>first knowledge exploration
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2 p-4">
            {conversations.map((conversation, index) => (
              <div
                key={conversation.id}
                className={`group relative rounded-xl p-4 cursor-pointer transition-all duration-200
                          animate-slide-up ${
                            activeConversationId === conversation.id
                              ? 'card-pro bg-gradient-to-br from-accent-50 to-primary-50 border-accent-200 shadow-md scale-[1.02]'
                              : 'hover:bg-gray-50 hover:shadow-sm border border-transparent hover:border-gray-200'
                          }`}
                onClick={() => onSelectConversation(conversation.id)}
                style={{ animationDelay: `${index * 50}ms` }}
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
      <div className="p-6 border-t border-gray-200/50 bg-gradient-to-br from-gray-50 to-white">
        <div className="text-center">
          <p className="text-xs font-bold text-gradient">AI Knowledge Continuity</p>
          <p className="text-xs text-gray-500 mt-1.5 font-medium">v1.0.0 · Enterprise Edition</p>
          <div className="flex items-center justify-center space-x-1 mt-2">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
            <span className="text-xs text-gray-600 font-medium">Production Ready</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
