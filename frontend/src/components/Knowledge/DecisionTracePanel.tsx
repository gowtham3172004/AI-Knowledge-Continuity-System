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
    <div className="bg-gradient-to-r from-decision-50 to-blue-50 border-2 border-decision-300 rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300">
      {/* Header (Clickable) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-gradient-to-r hover:from-decision-100 hover:to-blue-100
                 transition-all duration-300 text-left group"
      >
        <div className="flex items-center space-x-4">
          <div className="bg-gradient-to-br from-decision-500 to-decision-600 p-3 rounded-xl shadow-lg shadow-decision-500/30 group-hover:scale-110 transition-transform">
            <FileText className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-decision-900 mb-1">
              Decision Trace Available
            </h3>
            <p className="text-sm text-decision-700 font-medium">
              {trace.title || 'View decision context and rationale'}
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-6 w-6 text-decision-700 group-hover:translate-y-0.5 transition-transform" />
        ) : (
          <ChevronRight className="h-6 w-6 text-decision-700 group-hover:translate-x-0.5 transition-transform" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-6 pb-6 space-y-5 border-t-2 border-decision-200 bg-gradient-to-b from-white/50 to-transparent">
          {/* Decision Metadata */}
          <div className="grid grid-cols-2 gap-6 pt-6">
            {trace.author && (
              <div className="flex items-start space-x-3 bg-white/70 p-4 rounded-xl border border-decision-200 hover:bg-white transition-colors">
                <div className="bg-decision-500 p-2 rounded-lg">
                  <User className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-xs text-decision-600 font-bold uppercase tracking-wide">Decision Author</p>
                  <p className="text-sm text-decision-900 font-semibold mt-1">{trace.author}</p>
                </div>
              </div>
            )}
            {trace.date && (
              <div className="flex items-start space-x-3 bg-white/70 p-4 rounded-xl border border-decision-200 hover:bg-white transition-colors">
                <div className="bg-decision-500 p-2 rounded-lg">
                  <Calendar className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-xs text-decision-600 font-bold uppercase tracking-wide">Date</p>
                  <p className="text-sm text-decision-900 font-semibold mt-1">{trace.date}</p>
                </div>
              </div>
            )}
          </div>

          {/* Rationale */}
          {trace.rationale && (
            <div>
              <h4 className="text-sm font-bold text-decision-700 mb-3 uppercase tracking-wide">
                Rationale
              </h4>
              <p className="text-sm text-decision-900 leading-relaxed bg-white p-5 rounded-xl border-2 border-decision-200 shadow-sm font-medium">
                {trace.rationale}
              </p>
            </div>
          )}

          {/* Alternatives Considered */}
          {trace.alternatives && trace.alternatives.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-decision-700 mb-3 uppercase tracking-wide">
                Alternatives Considered
              </h4>
              <ul className="space-y-2">
                {trace.alternatives.map((alt, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-decision-900 flex items-start space-x-3 bg-white p-4 rounded-xl border border-decision-200 hover:border-decision-300 transition-colors shadow-sm"
                  >
                    <span className="text-decision-500 font-bold text-base">{idx + 1}.</span>
                    <span className="font-medium">{alt}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Trade-offs */}
          {trace.tradeoffs && trace.tradeoffs.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <div className="bg-decision-500 p-2 rounded-lg">
                  <Scale className="h-4 w-4 text-white" />
                </div>
                <h4 className="text-sm font-bold text-decision-700 uppercase tracking-wide">
                  Trade-offs Accepted
                </h4>
              </div>
              <ul className="space-y-2">
                {trace.tradeoffs.map((tradeoff, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-decision-900 flex items-start space-x-3 bg-white p-4 rounded-xl border border-decision-200 hover:border-decision-300 transition-colors shadow-sm"
                  >
                    <span className="text-decision-500 font-bold text-lg">•</span>
                    <span className="font-medium">{tradeoff}</span>
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
