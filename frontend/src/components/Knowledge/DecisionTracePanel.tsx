/**
 * DecisionTracePanel Component
 * 
 * Expandable panel showing decision audit trail (Feature #2).
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, User, Calendar, Scale } from 'lucide-react';
import { DecisionTrace } from '../../types/api';

interface DecisionTracePanelProps {
  trace: DecisionTrace;
}

export const DecisionTracePanel: React.FC<DecisionTracePanelProps> = ({ trace }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-decision-50 border border-decision-200 rounded-lg overflow-hidden">
      {/* Header (Clickable) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-decision-100 
                 transition-colors text-left"
      >
        <div className="flex items-center space-x-3">
          <div className="bg-decision-500 p-2 rounded">
            <FileText className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-decision-900">
              Decision Trace Available
            </h3>
            <p className="text-xs text-decision-700">
              {trace.title || 'View decision context and rationale'}
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-5 w-5 text-decision-700" />
        ) : (
          <ChevronRight className="h-5 w-5 text-decision-700" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-decision-200">
          {/* Decision Metadata */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            {trace.author && (
              <div className="flex items-start space-x-2">
                <User className="h-4 w-4 text-decision-600 mt-0.5" />
                <div>
                  <p className="text-xs text-decision-600 font-medium">Decision Author</p>
                  <p className="text-sm text-decision-900">{trace.author}</p>
                </div>
              </div>
            )}
            {trace.date && (
              <div className="flex items-start space-x-2">
                <Calendar className="h-4 w-4 text-decision-600 mt-0.5" />
                <div>
                  <p className="text-xs text-decision-600 font-medium">Date</p>
                  <p className="text-sm text-decision-900">{trace.date}</p>
                </div>
              </div>
            )}
          </div>

          {/* Rationale */}
          {trace.rationale && (
            <div>
              <h4 className="text-xs font-semibold text-decision-700 mb-2 uppercase tracking-wide">
                Rationale
              </h4>
              <p className="text-sm text-decision-900 leading-relaxed bg-white p-3 rounded border border-decision-200">
                {trace.rationale}
              </p>
            </div>
          )}

          {/* Alternatives Considered */}
          {trace.alternatives && trace.alternatives.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-decision-700 mb-2 uppercase tracking-wide">
                Alternatives Considered
              </h4>
              <ul className="space-y-1">
                {trace.alternatives.map((alt, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-decision-900 flex items-start space-x-2 bg-white p-2 rounded"
                  >
                    <span className="text-decision-500 font-medium">{idx + 1}.</span>
                    <span>{alt}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Trade-offs */}
          {trace.tradeoffs && trace.tradeoffs.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Scale className="h-4 w-4 text-decision-600" />
                <h4 className="text-xs font-semibold text-decision-700 uppercase tracking-wide">
                  Trade-offs Accepted
                </h4>
              </div>
              <ul className="space-y-1">
                {trace.tradeoffs.map((tradeoff, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-decision-900 flex items-start space-x-2 bg-white p-2 rounded"
                  >
                    <span className="text-decision-500 font-medium">•</span>
                    <span>{tradeoff}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Footer Note */}
          <div className="pt-2 border-t border-decision-200">
            <p className="text-xs text-decision-700">
              This decision trace provides full audit context for organizational knowledge continuity.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
