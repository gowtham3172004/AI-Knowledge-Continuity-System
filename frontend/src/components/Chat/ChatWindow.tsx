/**
 * ChatWindow Component
 * 
 * Main chat interface with message list and input.
 */

import React, { useRef, useEffect, useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { Message } from '../../types/api';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 ? (
          // Empty State
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="bg-gradient-to-br from-accent-500 to-primary-600 p-4 rounded-2xl inline-block mb-4">
                <Sparkles className="h-12 w-12 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-primary-900 mb-2">
                Welcome to Knowledge Continuity
              </h2>
              <p className="text-primary-600 mb-4">
                Ask questions about organizational knowledge, past decisions, and lessons learned.
              </p>
              <div className="text-left bg-primary-50 rounded-lg p-4 text-sm text-primary-700">
                <p className="font-medium mb-2">Try asking about:</p>
                <ul className="space-y-1 text-xs">
                  <li>• Design decisions and their rationale</li>
                  <li>• Lessons learned from past projects</li>
                  <li>• Technology choices and trade-offs</li>
                  <li>• Team retrospectives and insights</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          // Messages
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about organizational knowledge, decisions, or lessons learned..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none
                       focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent
                       text-primary-900 placeholder-primary-400 max-h-32"
              rows={1}
              disabled={isLoading}
            />
            <p className="text-xs text-primary-500 mt-1">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="bg-accent-500 text-white p-3 rounded-lg hover:bg-accent-600
                     disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors
                     flex-shrink-0"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
