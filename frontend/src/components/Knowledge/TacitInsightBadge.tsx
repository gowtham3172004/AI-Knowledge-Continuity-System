/**
 * TacitInsightBadge Component
 * 
 * Visual indicator for tacit (experience-based) knowledge.
 */

import React from 'react';
import { Lightbulb } from 'lucide-react';

export const TacitInsightBadge: React.FC = () => {
  return (
    <div
      className="inline-flex items-center space-x-1.5 bg-tacit-50 border border-tacit-200 
                 text-tacit-700 px-3 py-1 rounded-full text-xs font-medium"
    >
      <Lightbulb className="h-3.5 w-3.5" />
      <span>Experience-Based Insight</span>
    </div>
  );
};
