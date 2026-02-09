/**
 * Header Component
 * 
 * Top navigation with logo, nav buttons, user info.
 */

import React from 'react';
import { Brain, MessageSquare, FileText, LayoutDashboard, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps {
  onNavigate?: (page: 'home' | 'chat' | 'documents' | 'dashboard') => void;
  currentPage?: 'home' | 'chat' | 'documents' | 'dashboard';
  showAuth?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onNavigate, currentPage = 'chat', showAuth = true }) => {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navItems = [
    { id: 'home' as const, label: 'Home', icon: Brain },
    { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
    { id: 'documents' as const, label: 'Documents', icon: FileText },
    { id: 'dashboard' as const, label: 'Dashboard', icon: LayoutDashboard },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="bg-primary-600 p-2 rounded-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-lg font-medium text-gray-900 hidden sm:block">Knowledge Continuity System</h1>
          </div>

          {/* Desktop Navigation */}
          {onNavigate && (
            <nav className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === item.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          )}

          {/* Right side - User Menu */}
          <div className="flex items-center space-x-4">
            {showAuth && user && (
              <>
                <div className="hidden sm:flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                      {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium text-gray-700">
                      {user.full_name || user.email.split('@')[0]}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                    title="Sign out"
                  >
                    <LogOut className="h-5 w-5" />
                  </button>
                </div>

                {/* Mobile menu button */}
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
                >
                  {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && onNavigate && (
          <div className="md:hidden border-t border-gray-200 py-2">
            <nav className="flex flex-col space-y-1">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    onNavigate(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`flex items-center space-x-3 px-4 py-3 text-sm font-medium transition-colors ${
                    currentPage === item.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </button>
              ))}
              <button
                onClick={logout}
                className="flex items-center space-x-3 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <LogOut className="h-5 w-5" />
                <span>Sign out</span>
              </button>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};
