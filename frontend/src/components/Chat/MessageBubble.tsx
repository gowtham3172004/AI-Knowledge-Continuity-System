/**
 * MessageBubble Component
 * 
 * Individual message with knowledge-type awareness.
 */

import React from 'react';
import { User, Bot } from 'lucide-react';
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
    <div className={`flex items-start space-x-4 mb-6 ${
      isUser ? 'flex-row-reverse space-x-reverse' : ''
    }`}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-gray-600' 
              : 'bg-primary-600'
          }`}
        >
          {isUser ? (
            <User className="h-5 w-5 text-white" />
          ) : (
            <Bot className="h-5 w-5 text-white" />
          )}
        </div>
      </div>

      {/* Message Content */}
      <div className={`flex-1 ${
        isUser ? 'items-end' : 'items-start'
      } flex flex-col max-w-4xl`}>
        {/* Timestamp */}
        <div className="flex items-center space-x-2 mb-1">
          {!isUser && (
            <span className="text-xs font-medium text-gray-700">AI Assistant</span>
          )}
          <span className="text-xs text-gray-500">
            {format(message.timestamp, 'HH:mm')}
          </span>
        </div>

        {/* Message Bubble */}
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          {/* Loading State */}
          {message.isLoading ? (
            <div className="flex items-center space-x-3">
              <div className="flex space-x-1.5">
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <span className="text-sm text-gray-600 font-medium">Analyzing knowledge base...</span>
            </div>
          ) : (
            <>
              {/* Message Text */}
              <div className={`text-sm leading-relaxed prose prose-sm max-w-none ${
                isUser ? 'text-white prose-invert' : 'text-gray-900'
              }`}>
                <ReactMarkdown
                  components={{
                    p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                    ul: ({node, ...props}) => <ul className="mb-2 last:mb-0 ml-4 list-disc" {...props} />,
                    ol: ({node, ...props}) => <ol className="mb-2 last:mb-0 ml-4 list-decimal" {...props} />,
                    li: ({node, ...props}) => <li className="mb-1" {...props} />,
                    code: ({node, className, children, ...props}) => {
                      const isInline = !className;
                      return isInline ? (
                        <code className={`px-1.5 py-0.5 rounded text-xs ${isUser ? 'bg-primary-700' : 'bg-gray-200'}`} {...props}>
                          {children}
                        </code>
                      ) : (
                        <code className={`block p-2 rounded mt-1 text-xs ${isUser ? 'bg-primary-700' : 'bg-gray-200'} overflow-x-auto`} {...props}>
                          {children}
                        </code>
                      );
                    },
                    strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
                    em: ({node, ...props}) => <em className="italic" {...props} />,
                    h1: ({node, ...props}) => <h1 className="text-lg font-bold mb-2 mt-3 first:mt-0" {...props} />,
                    h2: ({node, ...props}) => <h2 className="text-base font-bold mb-2 mt-2 first:mt-0" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-sm font-bold mb-1 mt-2 first:mt-0" {...props} />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>

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
                  {message.response.tacit_knowledge_used && (
                    <div>
                      <TacitInsightBadge />
                    </div>
                  )}

                  {/* Knowledge Gap Alert */}
                  {message.response.knowledge_gap.detected && (
                    <KnowledgeGapAlert gapInfo={message.response.knowledge_gap} />
                  )}

                  {/* Decision Trace */}
                  {message.response.decision_trace && (
                    <DecisionTracePanel trace={message.response.decision_trace} />
                  )}

                  {/* Warnings */}
                  {message.response.warnings && message.response.warnings.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-yellow-800 text-xs">
                      {message.response.warnings.map((warning, idx) => (
                        <p key={idx}>⚠️ {warning}</p>
                      ))}
                    </div>
                  )}

                  {/* Metadata Footer */}
                  <div className="flex items-center justify-between text-xs text-gray-500 pt-3 mt-3 border-t border-gray-100">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                        <span className="font-semibold">Confidence: {(message.response.confidence * 100).toFixed(1)}%</span>
                      </div>
                      <span className="text-gray-400">•</span>
                      <span className="font-medium">{message.response.processing_time_ms.toFixed(0)}ms</span>
                    </div>
                    {message.response.sources && message.response.sources.length > 0 && (
                      <span className="bg-gray-100 px-2 py-1 rounded-lg font-semibold">
                        {message.response.sources.length} sources
                      </span>
                    )}
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
