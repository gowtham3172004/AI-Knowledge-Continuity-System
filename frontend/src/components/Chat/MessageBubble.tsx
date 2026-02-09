/**
 * MessageBubble Component
 *
 * Individual message with knowledge-type awareness.
 */

import React from 'react';
import { User, Bot, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';

import { Message } from '../../types/api';
import { TacitInsightBadge } from '../Knowledge/TacitInsightBadge';
import { KnowledgeGapAlert } from '../Knowledge/KnowledgeGapAlert';
import { DecisionTracePanel } from '../Knowledge/DecisionTracePanel';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex items-start space-x-3 ${
        isUser ? 'flex-row-reverse space-x-reverse' : ''
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-accent-500' : 'bg-primary-600'
        }`}
      >
        {isUser ? (
          <User className="h-5 w-5 text-white" />
        ) : (
          <Bot className="h-5 w-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Timestamp */}
        <span className="text-xs text-primary-500 mb-1">
          {format(message.timestamp, 'HH:mm')}
        </span>

        {/* Message Bubble */}
        <div
          className={`rounded-lg px-4 py-3 max-w-3xl ${
            isUser
              ? 'bg-accent-500 text-white'
              : 'bg-white border border-gray-200 text-primary-900'
          }`}
        >
          {/* Loading State */}
          {message.isLoading ? (
            <div className="flex items-center space-x-2 text-primary-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Processing your question...</span>
            </div>
          ) : (
            <>
              {/* Message Text (Markdown-safe) */}
              <ReactMarkdown
                components={{
                  h1: ({ children }) =>
                    children ? (
                      <h1 className="text-lg font-bold mb-2">{children}</h1>
                    ) : null,

                  h2: ({ children }) =>
                    children ? (
                      <h2 className="text-base font-bold mb-2">{children}</h2>
                    ) : null,

                  h3: ({ children }) =>
                    children ? (
                      <h3 className="text-sm font-bold mb-1">{children}</h3>
                    ) : null,

                  p: ({ children }) => (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {children}
                    </p>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>


              {/* Error Display */}
              {message.error && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-xs">
                  <strong>Error:</strong> {message.error}
                </div>
              )}

              {/* Assistant-specific metadata */}
              {!isUser && message.response && (
                <div className="mt-4 space-y-3">
                  {/* Tacit Knowledge Badge */}
                  {message.response.tacit_knowledge_used && <TacitInsightBadge />}

                  {/* Knowledge Gap Alert */}
                  {message.response.knowledge_gap.detected && (
                    <KnowledgeGapAlert gapInfo={message.response.knowledge_gap} />
                  )}

                  {/* Decision Trace */}
                  {message.response.decision_trace && (
                    <DecisionTracePanel trace={message.response.decision_trace} />
                  )}

                  {/* Warnings */}
                  {message.response.warnings?.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-yellow-800 text-xs">
                      {message.response.warnings.map((warning, idx) => (
                        <p key={idx}>⚠️ {warning}</p>
                      ))}
                    </div>
                  )}

                  {/* Metadata Footer */}
                  <div className="flex items-center justify-between text-xs text-primary-500 pt-2 border-t border-gray-100">
                    <span>
                      Confidence: {(message.response.confidence * 100).toFixed(1)}%
                    </span>
                    <span>
                      {message.response.processing_time_ms.toFixed(0)}ms
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
