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
          <span className="text-xs bg-gradient-to-r from-tacit-500 to-tacit-600 text-white px-3 py-1 rounded-lg font-bold shadow-sm">
            Tacit
          </span>
        );
      case KnowledgeType.DECISION:
        return (
          <span className="text-xs bg-gradient-to-r from-decision-500 to-decision-600 text-white px-3 py-1 rounded-lg font-bold shadow-sm">
            Decision
          </span>
        );
      case KnowledgeType.EXPLICIT:
        return (
          <span className="text-xs bg-gradient-to-r from-blue-500 to-blue-600 text-white px-3 py-1 rounded-lg font-bold shadow-sm">
            Explicit
          </span>
        );
      default:
        return (
          <span className="text-xs bg-gradient-to-r from-gray-500 to-gray-600 text-white px-3 py-1 rounded-lg font-bold shadow-sm">
            Unknown
          </span>
        );
    }
  };

  if (sources.length === 0) {
    return (
      <div className="p-8 text-center bg-gradient-to-br from-primary-50 to-accent-50 rounded-2xl border-2 border-dashed border-primary-300 m-4">
        <div className="bg-gradient-to-br from-primary-500 to-accent-500 p-4 rounded-2xl inline-block shadow-lg mb-4">
          <FileText className="h-8 w-8 text-white" />
        </div>
        <p className="text-base font-bold text-primary-900 mb-1">No Sources Available</p>
        <p className="text-sm text-primary-600 font-medium">Source documents will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      {sources.map((source, index) => (
        <div
          key={index}
          className="bg-white border-2 border-gray-200 rounded-2xl overflow-hidden hover:border-accent-400 hover:shadow-lg transition-all duration-300 group"
        >
          {/* Source Header */}
          <button
            onClick={() => toggleSource(index)}
            className="w-full flex items-center justify-between p-4 hover:bg-gradient-to-r hover:from-gray-50 hover:to-accent-50 transition-all duration-300"
          >
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              <div className="bg-gradient-to-br from-primary-500 to-accent-500 p-2 rounded-xl shadow-md flex-shrink-0 group-hover:scale-110 transition-transform">
                <FileText className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm font-bold text-primary-900 truncate mb-1.5">
                  {source.source.split('/').pop()}
                </p>
                <div className="flex items-center space-x-2.5 mt-1">
                  {getKnowledgeTypeBadge(source.knowledge_type)}
                  {source.relevance_score !== undefined && (
                    <div className="flex items-center space-x-1.5 bg-accent-50 px-2 py-1 rounded-lg">
                      <Award className="h-3.5 w-3.5 text-accent-600" />
                      <span className="text-xs text-accent-900 font-bold">
                        {(source.relevance_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            {expandedSources.has(index) ? (
              <ChevronDown className="h-5 w-5 text-primary-600 flex-shrink-0 group-hover:translate-y-0.5 transition-transform" />
            ) : (
              <ChevronRight className="h-5 w-5 text-primary-600 flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
            )}
          </button>

          {/* Expanded Content */}
          {expandedSources.has(index) && (
            <div className="px-4 pb-4 border-t-2 border-gray-100 bg-gradient-to-b from-gray-50/50 to-transparent">
              <p className="text-sm text-primary-700 leading-relaxed mt-4 bg-primary-50 p-4 rounded-xl border border-primary-200 font-medium">
                {source.content_preview}
              </p>

              {/* Decision Metadata */}
              {source.knowledge_type === KnowledgeType.DECISION && (
                <div className="mt-4 space-y-2 bg-white p-4 rounded-xl border border-decision-200">
                  {source.decision_author && (
                    <p className="text-sm text-primary-900 font-medium">
                      <strong className="text-decision-700">Author:</strong> {source.decision_author}
                    </p>
                  )}
                  {source.decision_date && (
                    <p className="text-sm text-primary-900 font-medium">
                      <strong className="text-decision-700">Date:</strong> {source.decision_date}
                    </p>
                  )}
                </div>
              )}

              {/* Full Path */}
              <p className="text-xs text-primary-500 mt-4 font-mono bg-gray-100 p-3 rounded-lg border border-gray-200">
                {source.source}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
