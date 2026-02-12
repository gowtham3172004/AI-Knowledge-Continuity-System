/**
 * App Component
 * 
 * Root component for AI Knowledge Continuity System.
 * Handles auth-gated routing between pages.
 */

import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DashboardPage } from './pages/DashboardPage';
import './styles/global.css';

type Page = 'home' | 'chat' | 'documents' | 'dashboard';
type AuthPage = 'login' | 'signup';

const AuthenticatedApp: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('chat');

  const handleNavigate = (page: Page) => {
    if (page === 'home') {
      // Do nothing or scroll to top
      setCurrentPage('chat');
    } else {
      setCurrentPage(page);
    }
  };

  switch (currentPage) {
    case 'documents':
      return <DocumentsPage onBack={() => setCurrentPage('chat')} currentPage={currentPage} onNavigate={handleNavigate} />;
    case 'dashboard':
      return <DashboardPage onBack={() => setCurrentPage('chat')} currentPage={currentPage} onNavigate={handleNavigate} />;
    case 'chat':
    case 'home':
    default:
      return (
        <ChatPage
          onNavigate={handleNavigate}
          currentPage={currentPage}
        />
      );
  }
};

const AppRouter: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authPage, setAuthPage] = useState<AuthPage | null>(null);

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <AuthenticatedApp />;
  }

  // Show Login/Signup if user navigated to auth pages, otherwise show HomePage
  if (authPage === 'login') {
    return (
      <LoginPage
        onBackToHome={() => setAuthPage(null)}
        onSwitchToSignup={() => setAuthPage('signup')}
      />
    );
  }

  if (authPage === 'signup') {
    return (
      <SignupPage
        onBackToLogin={() => setAuthPage('login')}
        onBackToHome={() => setAuthPage(null)}
      />
    );
  }

  return <HomePage onGetStarted={() => setAuthPage('login')} />;
};

function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;
