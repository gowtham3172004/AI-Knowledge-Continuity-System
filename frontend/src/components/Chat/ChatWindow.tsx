/**
 * ChatWindow Component
 * 
 * Main chat interface with message list, smart starter questions, and input.
 * Empty state fetches personalized questions from the knowledge base.
 */

import React, { useRef, useEffect, useState } from 'react';
import { Send, ArrowRight, Brain, RefreshCw } from 'lucide-react';
import { Message } from '../../types/api';
import { MessageBubble } from './MessageBubble';
import { useAuth } from '../../contexts/AuthContext';
import { API_URL } from '../../config/api.config';

const API = API_URL;

interface SuggestedQuestion {
  question: string;
  category: string;
  icon: string;
  context: string;
}

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const [suggestedQuestions, setSuggestedQuestions] = useState<SuggestedQuestion[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { token } = useAuth();

  // Fetch suggested questions when chat is empty
  useEffect(() => {
    if (messages.length === 0 && token) {
      setLoadingQuestions(true);
      fetch(`${API}/api/knowledge/suggest-questions`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data?.questions) setSuggestedQuestions(data.questions);
        })
        .catch(() => {})
        .finally(() => setLoadingQuestions(false));
    }
  }, [messages.length, token]);

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
    <div className="flex flex-col h-full bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-8 py-6 scrollbar">
        {messages.length === 0 ? (
          // Smart Empty State with personalized questions
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-2xl w-full px-4">
              <div className="mb-6">
                <div className="bg-primary-600 p-5 rounded-2xl inline-block">
                  <Brain className="h-12 w-12 text-white" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Ask About Your Project
              </h2>
              <p className="text-gray-600 text-sm mb-6">
                Get answers from your team's internal documents — architecture, decisions, lessons learned
              </p>

              {loadingQuestions ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-5 h-5 text-gray-400 animate-spin mr-2" />
                  <span className="text-sm text-gray-400">Loading suggested questions...</span>
                </div>
              ) : suggestedQuestions.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
                  {suggestedQuestions.slice(0, 6).map((q, i) => (
                    <button
                      key={i}
                      onClick={() => onSendMessage(q.question)}
                      className="flex items-start space-x-3 p-3.5 rounded-xl border border-gray-200 
                               bg-white hover:bg-gray-50 hover:border-gray-300 hover:shadow-md
                               transition-all group cursor-pointer text-left"
                    >
                      <span className="text-lg flex-shrink-0">{q.icon}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 group-hover:text-gray-900 leading-snug line-clamp-2">
                          {q.question}
                        </p>
                        <p className="text-xs text-gray-400 mt-1 truncate">{q.context}</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 flex-shrink-0 mt-1 transition-all group-hover:translate-x-0.5" />
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400 mt-2">
                  Upload documents and start asking questions about your project knowledge.
                </p>
              )}
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
      <div className="border-t border-gray-200 bg-white px-8 py-6">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about organizational knowledge, decisions, or lessons learned..."
                className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl resize-none
                         focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent
                         text-gray-900 placeholder-gray-400 max-h-32 transition-all duration-200
                         hover:border-gray-300 shadow-sm hover:shadow-md font-medium"
                rows={1}
                disabled={isLoading}
              />
              <div className="flex items-center justify-between mt-2 px-2">
                <p className="text-xs text-gray-500 font-medium">
                  <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-semibold">Enter</kbd> to send · <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-semibold">Shift+Enter</kbd> for new line
                </p>
              </div>
            </div>
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="btn-primary px-6 py-4 shadow-lg hover:shadow-xl disabled:shadow-none"
            >
              <Send className="h-5 w-5" />
              <span className="font-bold">Send</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
