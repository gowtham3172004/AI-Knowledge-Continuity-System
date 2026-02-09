/**
 * useChat Hook
 * 
 * Manages chat state, messages, and conversations.
 * Persists everything to the backend DB (per-user isolation).
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { apiClient, query } from '../services/api';
import {
  Message,
  Conversation,
  QueryRequest,
  QueryRole,
} from '../types/api';

interface UseChatOptions {
  defaultRole?: QueryRole;
}

export const useChat = (options: UseChatOptions = {}) => {
  const { defaultRole = QueryRole.GENERAL } = options;

  // State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const hasFetched = useRef(false);

  // Get active conversation
  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  // Load conversations from backend on mount
  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    apiClient.listConversations()
      .then((data) => {
        const convs: Conversation[] = data.map((c: any) => ({
          id: c.id,
          title: c.title,
          messages: [],
          created_at: new Date(c.created_at),
          updated_at: new Date(c.updated_at),
        }));
        setConversations(convs);
      })
      .catch((e) => {
        if (process.env.NODE_ENV === 'development') {
          console.error('Failed to load conversations:', e);
        }
      });
  }, []);

  // Load messages when active conversation changes
  const selectConversation = useCallback((id: string | undefined) => {
    setActiveConversationId(id);
    if (!id) return;

    // Check if messages are already loaded
    const conv = conversations.find((c) => c.id === id);
    if (conv && conv.messages.length > 0) return;

    // Fetch messages from backend
    apiClient.getMessages(id)
      .then((data) => {
        const msgs: Message[] = data.map((m: any) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: new Date(m.created_at),
          response: m.response_data ? JSON.parse(m.response_data) : undefined,
        }));
        setConversations((prev) =>
          prev.map((c) => c.id === id ? { ...c, messages: msgs } : c)
        );
      })
      .catch((e) => {
        if (process.env.NODE_ENV === 'development') {
          console.error('Failed to load messages:', e);
        }
      });
  }, [conversations]);

  /**
   * Create a new conversation
   */
  const createConversation = useCallback((title?: string) => {
    const id = uuidv4();
    const convTitle = title || 'New Conversation';
    const newConversation: Conversation = {
      id,
      title: convTitle,
      messages: [],
      created_at: new Date(),
      updated_at: new Date(),
    };

    setConversations((prev) => [newConversation, ...prev]);
    setActiveConversationId(id);

    // Persist to backend (fire-and-forget)
    apiClient.createConversation(id, convTitle).catch((e) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to create conversation:', e);
      }
    });

    return id;
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

      // Update title if this is the first message
      const conv = conversations.find((c) => c.id === conversationId);
      const isFirstMessage = conv && conv.messages.length === 0;
      const newTitle = isFirstMessage ? content.trim().slice(0, 50) : undefined;

      // Add messages to conversation (optimistic UI)
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? {
                ...c,
                messages: [...c.messages, userMessage, assistantMessage],
                updated_at: new Date(),
                title: newTitle || c.title,
              }
            : c
        )
      );

      // Save user message to backend
      apiClient.saveMessage(conversationId, {
        id: userMessage.id,
        role: 'user',
        content: userMessage.content,
      }).catch(() => {});

      // Update title if first message
      if (newTitle) {
        apiClient.updateConversation(conversationId, newTitle).catch(() => {});
      }

      setIsLoading(true);
      setError(undefined);

      try {
        // Call RAG API
        const request: QueryRequest = {
          question: content,
          role,
          conversation_id: conversationId,
          use_knowledge_features: true,
        };

        const response = await query(request);

        // Update assistant message with response
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((msg) =>
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
              : c
          )
        );

        // Save assistant message to backend
        apiClient.saveMessage(conversationId, {
          id: assistantMessage.id,
          role: 'assistant',
          content: response.answer,
          response_data: JSON.stringify(response),
        }).catch(() => {});
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);

        // Update assistant message with error
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((msg) =>
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
              : c
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeConversationId, conversations, createConversation, defaultRole]
  );

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    setActiveConversationId((current) => (current === id ? undefined : current));

    // Delete from backend
    apiClient.deleteConversation(id).catch((e) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to delete conversation:', e);
      }
    });
  }, []);

  /**
   * Clear all conversations
   */
  const clearAllConversations = useCallback(() => {
    // Delete each from backend
    conversations.forEach((c) => {
      apiClient.deleteConversation(c.id).catch(() => {});
    });
    setConversations([]);
    setActiveConversationId(undefined);
  }, [conversations]);

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
    setActiveConversationId: selectConversation,
    deleteConversation,
    clearAllConversations,
  };
};
