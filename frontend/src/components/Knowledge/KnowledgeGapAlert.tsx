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
        return 'bg-red-50 border-red-300 text-red-900';
      case GapSeverity.HIGH:
        return 'bg-orange-50 border-orange-300 text-orange-900';
      case GapSeverity.MEDIUM:
        return 'bg-warning-50 border-warning-300 text-warning-900';
      default:
        return 'bg-yellow-50 border-yellow-300 text-yellow-900';
    }
  };

  const getSeverityIcon = () => {
    if (gapInfo.severity === GapSeverity.CRITICAL || gapInfo.severity === GapSeverity.HIGH) {
      return <AlertTriangle className="h-5 w-5 flex-shrink-0" />;
    }
    return <Info className="h-5 w-5 flex-shrink-0" />;
  };

  return (
    <div className={`rounded-lg border-2 p-4 ${getSeverityStyles()}`}>
      <div className="flex items-start space-x-3">
        {getSeverityIcon()}
        <div className="flex-1">
          <h4 className="font-semibold text-sm mb-1">Knowledge Gap Detected</h4>
          <p className="text-sm">
            {gapInfo.reason ||
              'This knowledge is currently missing or incomplete in the organization.'}
          </p>
          <div className="mt-2 flex items-center space-x-4 text-xs">
            <span>
              <strong>Confidence:</strong> {(gapInfo.confidence_score * 100).toFixed(1)}%
            </span>
            {gapInfo.severity && (
              <span>
                <strong>Severity:</strong>{' '}
                <span className="uppercase">{gapInfo.severity}</span>
              </span>
            )}
          </div>
          <p className="text-xs mt-2 opacity-75">
            This response may be incomplete or uncertain. Consider consulting subject matter
            experts or documenting this knowledge for future reference.
          </p>
        </div>
      </div>
    </div>
  );
};
