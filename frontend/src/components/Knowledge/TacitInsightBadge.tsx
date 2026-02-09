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
      className="inline-flex items-center space-x-2 bg-gradient-to-r from-tacit-50 to-green-50 
                 border-2 border-tacit-300 text-tacit-800 px-4 py-2 rounded-xl text-sm font-bold
                 shadow-sm hover:shadow-md transition-all duration-300 hover:scale-105"
    >
      <div className="bg-tacit-500 p-1.5 rounded-lg">
        <Lightbulb className="h-4 w-4 text-white" />
      </div>
      <span>Experience-Based Insight</span>
    </div>
  );
};
