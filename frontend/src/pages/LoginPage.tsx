import React, { useState } from 'react';
import { Brain, Mail, Lock, ArrowLeft, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface LoginPageProps {
  onBackToHome?: () => void;
  onSwitchToSignup?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onBackToHome, onSwitchToSignup }) => {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {onBackToHome && (
          <button onClick={onBackToHome} className="flex items-center text-gray-600 hover:text-gray-900 mb-8">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </button>
        )}

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-primary-600 p-3 rounded-lg">
              <Brain className="h-8 w-8 text-white" />
            </div>
          </div>

          <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">Sign In</h1>
          <p className="text-gray-600 text-center mb-8">Knowledge Continuity System</p>

          {error && (
            <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-md flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 text-error-500 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-error-700">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button type="submit" disabled={isLoading} className="w-full btn-primary">
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-xs text-gray-500 text-center">
            Sign in with your registered email and password
          </p>

          {onSwitchToSignup && (
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <button
                  onClick={onSwitchToSignup}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Sign Up
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
