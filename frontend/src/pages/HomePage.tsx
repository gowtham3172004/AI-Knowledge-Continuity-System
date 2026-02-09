import React from 'react';
import { Brain, FileText, BarChart3, ArrowRight, CheckCircle } from 'lucide-react';
import { Header } from '../components/Layout/Header';

interface HomePageProps {
  onGetStarted: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onGetStarted }) => {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <Header currentPage="home" showAuth={false} />
      <div className="border-b border-gray-200 bg-white py-4">
        <div className="max-w-7xl mx-auto px-6 flex justify-end">
          <button onClick={onGetStarted} className="btn-primary">
            Sign In
          </button>
        </div>
      </div>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          Knowledge Continuity System
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          AI-powered knowledge management system for capturing, organizing, and retrieving your organization's critical information.
        </p>
        <button onClick={onGetStarted} className="btn-primary text-lg px-8 py-3">
          Get Started <ArrowRight className="ml-2 h-5 w-5 inline" />
        </button>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { icon: <FileText className="h-8 w-8 text-primary-600" />, title: 'Document Management', desc: 'Upload and organize your documents with smart categorization.' },
            { icon: <Brain className="h-8 w-8 text-primary-600" />, title: 'AI-Powered Search', desc: 'Get accurate answers from your documents using advanced RAG.' },
            { icon: <BarChart3 className="h-8 w-8 text-primary-600" />, title: 'Analytics Dashboard', desc: 'Track knowledge coverage and identify gaps in your database.' },
          ].map((f, i) => (
            <div key={i} className="card p-6">
              <div className="mb-4">{f.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Benefits */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Why Choose Us</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              'Secure per-user document isolation',
              'Real-time AI responses with source citations',
              'Knowledge gap detection and alerts',
              'Easy document upload and management',
            ].map((benefit, i) => (
              <div key={i} className="flex items-center space-x-3">
                <CheckCircle className="h-6 w-6 text-success-500 flex-shrink-0" />
                <span className="text-gray-700">{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm text-gray-600">
          <p>© 2026 Knowledge Continuity System. Built for enterprise knowledge transfer.</p>
        </div>
      </footer>
    </div>
  );
};
