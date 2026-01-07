/**
 * SourcePanel Component
 * 
 * Right sidebar showing source documents and attribution.
 */

import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronRight, Award } from 'lucide-react';
import { SourceDocument, KnowledgeType } from '../../types/api';

interface SourcePanelProps {
  sources: SourceDocument[];
}

export const SourcePanel: React.FC<SourcePanelProps> = ({ sources }) => {
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());

  const toggleSource = (index: number) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSources(newExpanded);
  };

  const getKnowledgeTypeBadge = (type: KnowledgeType) => {
    switch (type) {
      case KnowledgeType.TACIT:
        return (
          <span className="text-xs bg-tacit-100 text-tacit-700 px-2 py-0.5 rounded-full">
            Tacit
          </span>
        );
      case KnowledgeType.DECISION:
        return (
          <span className="text-xs bg-decision-100 text-decision-700 px-2 py-0.5 rounded-full">
            Decision
          </span>
        );
      case KnowledgeType.EXPLICIT:
        return (
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
            Explicit
          </span>
        );
      default:
        return (
          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
            Unknown
          </span>
        );
    }
  };

  if (sources.length === 0) {
    return (
      <div className="p-6 text-center">
        <FileText className="h-12 w-12 text-primary-300 mx-auto mb-2" />
        <p className="text-sm text-primary-600">No sources available</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sources.map((source, index) => (
        <div
          key={index}
          className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:border-accent-300 transition-colors"
        >
          {/* Source Header */}
          <button
            onClick={() => toggleSource(index)}
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2 flex-1 min-w-0">
              <FileText className="h-4 w-4 text-primary-600 flex-shrink-0" />
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm font-medium text-primary-900 truncate">
                  {source.source.split('/').pop()}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                  {getKnowledgeTypeBadge(source.knowledge_type)}
                  {source.relevance_score !== undefined && (
                    <div className="flex items-center space-x-1">
                      <Award className="h-3 w-3 text-accent-500" />
                      <span className="text-xs text-primary-600">
                        {(source.relevance_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            {expandedSources.has(index) ? (
              <ChevronDown className="h-4 w-4 text-primary-600 flex-shrink-0" />
            ) : (
              <ChevronRight className="h-4 w-4 text-primary-600 flex-shrink-0" />
            )}
          </button>

          {/* Expanded Content */}
          {expandedSources.has(index) && (
            <div className="px-3 pb-3 border-t border-gray-100">
              <p className="text-xs text-primary-700 leading-relaxed mt-2 bg-primary-50 p-2 rounded">
                {source.content_preview}
              </p>

              {/* Decision Metadata */}
              {source.knowledge_type === KnowledgeType.DECISION && (
                <div className="mt-2 space-y-1 text-xs">
                  {source.decision_author && (
                    <p className="text-primary-600">
                      <strong>Author:</strong> {source.decision_author}
                    </p>
                  )}
                  {source.decision_date && (
                    <p className="text-primary-600">
                      <strong>Date:</strong> {source.decision_date}
                    </p>
                  )}
                </div>
              )}

              {/* Full Path */}
              <p className="text-xs text-primary-500 mt-2 font-mono bg-gray-50 p-1 rounded">
                {source.source}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
