/**
 * useChat Hook
 * 
 * Manages chat state, messages, and conversations.
 */

import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { query } from '../services/api';
import {
  Message,
  Conversation,
  QueryRequest,
  QueryRole,
} from '../types/api';

interface UseChatOptions {
  defaultRole?: QueryRole;
  saveToLocalStorage?: boolean;
}

export const useChat = (options: UseChatOptions = {}) => {
  const { defaultRole = QueryRole.GENERAL, saveToLocalStorage = true } = options;

  // State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  // Get active conversation
  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  // Load conversations from localStorage on mount
  useEffect(() => {
    if (saveToLocalStorage) {
      const saved = localStorage.getItem('conversations');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setConversations(
            parsed.map((c: any) => ({
              ...c,
              created_at: new Date(c.created_at),
              updated_at: new Date(c.updated_at),
              messages: c.messages.map((m: any) => ({
                ...m,
                timestamp: new Date(m.timestamp),
              })),
            }))
          );
        } catch (e) {
          if (process.env.NODE_ENV === 'development') {
            console.error('Failed to load conversations:', e);
          }
          // Clear corrupted data
          localStorage.removeItem('conversations');
        }
      }
    }
  }, [saveToLocalStorage]);

  // Save conversations to localStorage when they change
  useEffect(() => {
    if (saveToLocalStorage && conversations.length > 0) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations, saveToLocalStorage]);

  /**
   * Create a new conversation
   */
  const createConversation = useCallback((title?: string) => {
    const newConversation: Conversation = {
      id: uuidv4(),
      title: title || 'New Conversation',
      messages: [],
      created_at: new Date(),
      updated_at: new Date(),
    };

    setConversations((prev) => [newConversation, ...prev]);
    setActiveConversationId(newConversation.id);
    return newConversation.id;
  }, []);

  /**
   * Send a message
   */
  const sendMessage = useCallback(
    async (content: string, role: QueryRole = defaultRole) => {
      if (!content.trim()) return;

      // Ensure we have an active conversation
      let conversationId = activeConversationId;
      if (!conversationId) {
        conversationId = createConversation();
      }

      // Create user message
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      // Create loading assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
      };

      // Add messages to conversation
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === conversationId
            ? {
                ...conv,
                messages: [...conv.messages, userMessage, assistantMessage],
                updated_at: new Date(),
                // Update title if this is the first message
                title: conv.messages.length === 0 ? content.slice(0, 50) : conv.title,
              }
            : conv
        )
      );

      setIsLoading(true);
      setError(undefined);

      try {
        // Call API
        const request: QueryRequest = {
          question: content,
          role,
          conversation_id: conversationId,
          use_knowledge_features: true,
        };

        const response = await query(request);

        // Update assistant message with response
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === assistantMessage.id
                      ? {
                          ...msg,
                          content: response.answer,
                          response,
                          isLoading: false,
                        }
                      : msg
                  ),
                  updated_at: new Date(),
                }
              : conv
          )
        );
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);

        // Update assistant message with error
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === assistantMessage.id
                      ? {
                          ...msg,
                          content: 'Sorry, I encountered an error processing your request.',
                          error: errorMessage,
                          isLoading: false,
                        }
                      : msg
                  ),
                }
              : conv
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeConversationId, createConversation, defaultRole]
  );

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    setActiveConversationId((current) => (current === id ? undefined : current));
  }, []);

  /**
   * Clear all conversations
   */
  const clearAllConversations = useCallback(() => {
    setConversations([]);
    setActiveConversationId(undefined);
    if (saveToLocalStorage) {
      localStorage.removeItem('conversations');
    }
  }, [saveToLocalStorage]);

  return {
    // State
    conversations,
    activeConversation,
    activeConversationId,
    isLoading,
    error,

    // Actions
    sendMessage,
    createConversation,
    setActiveConversationId,
    deleteConversation,
    clearAllConversations,
  };
};
