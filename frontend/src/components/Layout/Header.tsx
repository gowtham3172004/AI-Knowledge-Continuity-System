/**
 * Header Component
 * 
 * Top navigation with logo, role selector, and health indicator.
 */

import React from 'react';
import { Brain, Activity, User } from 'lucide-react';
import { QueryRole } from '../../types/api';

interface HeaderProps {
  selectedRole: QueryRole;
  onRoleChange: (role: QueryRole) => void;
  isHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({ selectedRole, onRoleChange, isHealthy }) => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-full mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-accent-500 to-primary-600 p-2 rounded-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-primary-900">
                Knowledge Continuity System
              </h1>
              <p className="text-xs text-primary-600">
                Enterprise AI · Decision Traceability · Knowledge Preservation
              </p>
            </div>
          </div>

          {/* Right side controls */}
          <div className="flex items-center space-x-6">
            {/* Role Selector */}
            <div className="flex items-center space-x-2">
              <User className="h-4 w-4 text-primary-600" />
              <select
                value={selectedRole}
                onChange={(e) => onRoleChange(e.target.value as QueryRole)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white 
                         text-primary-700 focus:outline-none focus:ring-2 focus:ring-accent-500
                         focus:border-transparent cursor-pointer"
              >
                <option value={QueryRole.GENERAL}>General User</option>
                <option value={QueryRole.DEVELOPER}>Developer</option>
                <option value={QueryRole.MANAGER}>Manager</option>
                <option value={QueryRole.ANALYST}>Analyst</option>
                <option value={QueryRole.EXECUTIVE}>Executive</option>
              </select>
            </div>

            {/* Health Indicator */}
            <div className="flex items-center space-x-2">
              <Activity
                className={`h-4 w-4 ${isHealthy ? 'text-green-500' : 'text-red-500'}`}
              />
              <span className="text-sm text-primary-600">
                {isHealthy ? 'System Online' : 'System Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
