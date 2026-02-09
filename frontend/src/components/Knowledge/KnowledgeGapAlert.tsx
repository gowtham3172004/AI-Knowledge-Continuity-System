/**
 * KnowledgeGapAlert Component
 * 
 * Warning banner for detected knowledge gaps (CRITICAL feature).
 */

import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { KnowledgeGapInfo, GapSeverity } from '../../types/api';

interface KnowledgeGapAlertProps {
  gapInfo: KnowledgeGapInfo;
}

export const KnowledgeGapAlert: React.FC<KnowledgeGapAlertProps> = ({ gapInfo }) => {
  if (!gapInfo.detected) return null;

  const getSeverityStyles = () => {
    switch (gapInfo.severity) {
      case GapSeverity.CRITICAL:
        return 'bg-gradient-to-r from-red-50 to-red-100 border-red-400 text-red-900 shadow-lg shadow-red-500/10';
      case GapSeverity.HIGH:
        return 'bg-gradient-to-r from-orange-50 to-orange-100 border-orange-400 text-orange-900 shadow-lg shadow-orange-500/10';
      case GapSeverity.MEDIUM:
        return 'bg-gradient-to-r from-warning-50 to-yellow-100 border-warning-400 text-warning-900 shadow-lg shadow-warning-500/10';
      default:
        return 'bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-400 text-yellow-900 shadow-lg shadow-yellow-500/10';
    }
  };

  const getSeverityIcon = () => {
    if (gapInfo.severity === GapSeverity.CRITICAL || gapInfo.severity === GapSeverity.HIGH) {
      return <AlertTriangle className="h-5 w-5 flex-shrink-0" />;
    }
    return <Info className="h-5 w-5 flex-shrink-0" />;
  };

  return (
    <div className={`rounded-2xl border-2 p-6 transition-all duration-300 hover:scale-[1.01] ${getSeverityStyles()}`}>
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          {getSeverityIcon()}
        </div>
        <div className="flex-1">
          <h4 className="font-bold text-base mb-2 flex items-center space-x-2">
            <span>Knowledge Gap Detected</span>
            <span className="bg-white/50 px-2 py-0.5 rounded-lg text-xs font-bold uppercase">
              {gapInfo.severity}
            </span>
          </h4>
          <p className="text-sm leading-relaxed font-medium">
            {gapInfo.reason ||
              'This knowledge is currently missing or incomplete in the organization.'}
          </p>
          <div className="mt-3 flex items-center space-x-6 text-xs font-semibold">
            <span className="flex items-center space-x-1">
              <strong>Confidence:</strong>
              <span className="bg-white/50 px-2 py-0.5 rounded">{(gapInfo.confidence_score * 100).toFixed(1)}%</span>
            </span>
            {gapInfo.severity && (
              <span className="flex items-center space-x-1">
                <strong>Severity:</strong>
                <span className="uppercase">{gapInfo.severity}</span>
              </span>
            )}
          </div>
          <p className="text-xs mt-3 bg-white/30 p-3 rounded-lg font-medium leading-relaxed">
            💡 This response may be incomplete or uncertain. Consider consulting subject matter
            experts or documenting this knowledge for future reference.
          </p>
        </div>
      </div>
    </div>
  );
};
