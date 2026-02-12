/**
 * Knowledge Hub — The developer's command center for Knowledge Transfer
 *
 * This is NOT a vanity dashboard. Every element helps developers:
 * 1. Know what questions to ask about the project
 * 2. See what's documented vs what's missing
 * 3. Find critical knowledge gaps before they cause problems
 * 4. Get actionable recommendations for better KT
 *
 * This is something ChatGPT/Claude CANNOT do — they don't know
 * what's in YOUR internal documents or what's missing.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft, FileText, Brain, AlertTriangle, CheckCircle2,
  Upload, ArrowRight, RefreshCw, Zap,
  TrendingUp, HelpCircle, Sparkles, FolderOpen
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { API_URL } from '../config/api.config';

const API = API_URL;

interface SuggestedQuestion {
  question: string;
  category: string;
  icon: string;
  context: string;
}

interface KnowledgeHealth {
  health_score: number;
  total_documents: number;
  total_chunks: number;
  coverage: Record<string, number>;
  unresolved_gaps: number;
  stale_documents: number;
  recommendations: string[];
}

interface Gap {
  id: number;
  query: string;
  confidence_score: number;
  severity: string;
  detected_at: string;
  resolved: boolean;
}

interface DashboardPageProps {
  onBack: () => void;
  currentPage?: 'home' | 'chat' | 'documents' | 'dashboard';
  onNavigate?: (page: 'home' | 'chat' | 'documents' | 'dashboard') => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onBack, currentPage, onNavigate }) => {
  const { token } = useAuth();
  const [questions, setQuestions] = useState<SuggestedQuestion[]>([]);
  const [health, setHealth] = useState<KnowledgeHealth | null>(null);
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedQ, setCopiedQ] = useState<string | null>(null);

  const headers = useCallback(() => ({ Authorization: `Bearer ${token}` }), [token]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const h = headers();
      const [qRes, hRes, gRes] = await Promise.all([
        fetch(`${API}/api/knowledge/suggest-questions`, { headers: h }),
        fetch(`${API}/api/knowledge/health`, { headers: h }),
        fetch(`${API}/api/knowledge/gaps`, { headers: h }),
      ]);
      if (qRes.ok) {
        const data = await qRes.json();
        setQuestions(data.questions || []);
      }
      if (hRes.ok) setHealth(await hRes.json());
      if (gRes.ok) setGaps(await gRes.json());
    } catch (e) {
      console.error('Dashboard fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const resolveGap = async (id: number) => {
    await fetch(`${API}/api/knowledge/gaps/${id}/resolve`, { method: 'POST', headers: headers() });
    fetchData();
  };

  const copyQuestion = (q: string) => {
    navigator.clipboard.writeText(q);
    setCopiedQ(q);
    setTimeout(() => setCopiedQ(null), 2000);
  };

  const getSeverityColor = (s: string) => {
    switch (s) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default: return 'bg-blue-100 text-blue-700 border-blue-200';
    }
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'architecture': return 'bg-blue-50 border-blue-200 hover:bg-blue-100';
      case 'technology': return 'bg-purple-50 border-purple-200 hover:bg-purple-100';
      case 'decisions': return 'bg-amber-50 border-amber-200 hover:bg-amber-100';
      case 'tacit': return 'bg-pink-50 border-pink-200 hover:bg-pink-100';
      case 'process': return 'bg-green-50 border-green-200 hover:bg-green-100';
      case 'gaps': return 'bg-red-50 border-red-200 hover:bg-red-100';
      case 'onboarding': return 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100';
      default: return 'bg-gray-50 border-gray-200 hover:bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-3" />
          <p className="text-gray-600 font-medium">Analyzing your knowledge base...</p>
        </div>
      </div>
    );
  }

  const totalDocs = health?.total_documents || 0;
  const hasDocuments = totalDocs > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900 flex items-center">
                <Sparkles className="w-5 h-5 text-blue-500 mr-2" />
                Knowledge Hub
              </h1>
              <p className="text-sm text-gray-500">Your team's knowledge transfer command center</p>
            </div>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* ======= NO DOCUMENTS STATE ======= */}
        {!hasDocuments && (
          <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-8 text-white text-center">
            <Upload className="w-12 h-12 mx-auto mb-4 opacity-80" />
            <h2 className="text-2xl font-bold mb-2">Upload Your First Documents</h2>
            <p className="text-blue-100 max-w-lg mx-auto mb-6">
              Upload your project's architecture docs, meeting notes, decision records, and lessons learned.
              The AI will analyze them and generate personalized knowledge transfer insights.
            </p>
            <button
              onClick={onBack}
              className="px-6 py-3 bg-white text-blue-600 rounded-xl font-bold hover:bg-blue-50 transition-colors"
            >
              Go to Documents →
            </button>
          </div>
        )}

        {/* ======= KNOWLEDGE STATUS BAR ======= */}
        {hasDocuments && health && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{health.total_documents}</p>
                <p className="text-xs text-gray-500 font-medium">Documents Indexed</p>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center space-x-4">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <Brain className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{health.total_chunks}</p>
                <p className="text-xs text-gray-500 font-medium">Knowledge Chunks</p>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center space-x-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                health.unresolved_gaps > 0 ? 'bg-orange-100' : 'bg-green-100'
              }`}>
                {health.unresolved_gaps > 0
                  ? <AlertTriangle className="w-6 h-6 text-orange-600" />
                  : <CheckCircle2 className="w-6 h-6 text-green-600" />
                }
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{health.unresolved_gaps}</p>
                <p className="text-xs text-gray-500 font-medium">Knowledge Gaps</p>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center space-x-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                health.health_score >= 70 ? 'bg-green-100' : health.health_score >= 40 ? 'bg-yellow-100' : 'bg-red-100'
              }`}>
                <Zap className={`w-6 h-6 ${
                  health.health_score >= 70 ? 'text-green-600' : health.health_score >= 40 ? 'text-yellow-600' : 'text-red-600'
                }`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{Math.round(health.health_score)}%</p>
                <p className="text-xs text-gray-500 font-medium">KT Readiness</p>
              </div>
            </div>
          </div>
        )}

        {/* ======= SMART SUGGESTED QUESTIONS ======= */}
        {questions.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900 flex items-center">
                  <HelpCircle className="w-5 h-5 text-blue-500 mr-2" />
                  Questions You Should Be Asking
                </h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  Generated from your uploaded documents — click to copy, then paste in chat
                </p>
              </div>
              <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-bold">
                {questions.length} questions
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {questions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => copyQuestion(q.question)}
                  className={`text-left p-4 rounded-xl border transition-all group cursor-pointer ${getCategoryColor(q.category)} ${
                    copiedQ === q.question ? 'ring-2 ring-green-400 scale-[0.98]' : 'hover:shadow-md'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <span className="text-xl flex-shrink-0 mt-0.5">{q.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 group-hover:text-gray-700 leading-snug">
                        {q.question}
                      </p>
                      <p className="text-xs text-gray-500 mt-1.5 truncate">{q.context}</p>
                    </div>
                    {copiedQ === q.question ? (
                      <span className="text-xs text-green-600 font-bold flex-shrink-0">Copied!</span>
                    ) : (
                      <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 flex-shrink-0 mt-1 transition-transform group-hover:translate-x-1" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ======= KNOWLEDGE COVERAGE MAP ======= */}
        {hasDocuments && health && (
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center mb-4">
              <FolderOpen className="w-5 h-5 text-purple-500 mr-2" />
              Knowledge Coverage
              <span className="ml-2 text-xs font-normal text-gray-500">What's documented vs what's missing</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {
                  type: 'tacit', label: 'Tacit Knowledge', icon: '🧠',
                  desc: 'Lessons learned, tribal knowledge, retrospectives, exit interviews',
                  missing: 'Upload retrospectives, post-mortems, or lessons-learned docs',
                },
                {
                  type: 'decision', label: 'Decision Records', icon: '📋',
                  desc: 'Architecture decision records, design rationale, trade-off analysis',
                  missing: 'Upload ADRs or documents explaining WHY decisions were made',
                },
                {
                  type: 'explicit', label: 'Technical Docs', icon: '📄',
                  desc: 'API docs, system guides, onboarding notes, setup instructions',
                  missing: 'Upload README files, API docs, or technical guides',
                },
              ].map((item) => {
                const count = health.coverage[item.type] || 0;
                const hasDocs = count > 0;
                return (
                  <div
                    key={item.type}
                    className={`rounded-2xl border-2 p-5 transition-all ${
                      hasDocs
                        ? 'bg-white border-gray-200'
                        : 'bg-gray-50 border-dashed border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-2xl">{item.icon}</span>
                      {hasDocs ? (
                        <span className="flex items-center space-x-1 text-green-600">
                          <CheckCircle2 className="w-4 h-4" />
                          <span className="text-sm font-bold">{count} docs</span>
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-orange-500">
                          <AlertTriangle className="w-4 h-4" />
                          <span className="text-xs font-bold">Missing</span>
                        </span>
                      )}
                    </div>
                    <p className="font-bold text-gray-900 text-sm">{item.label}</p>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                      {hasDocs ? item.desc : item.missing}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ======= KNOWLEDGE GAPS (if any) ======= */}
        {gaps.filter(g => !g.resolved).length > 0 && (
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center mb-4">
              <AlertTriangle className="w-5 h-5 text-orange-500 mr-2" />
              Knowledge Gaps Detected
              <span className="ml-2 text-xs font-normal text-gray-500">
                Questions the AI couldn't fully answer — these need documentation
              </span>
            </h2>
            <div className="space-y-3">
              {gaps.filter(g => !g.resolved).slice(0, 8).map((gap) => (
                <div key={gap.id} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between hover:shadow-sm transition-shadow">
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${getSeverityColor(gap.severity)}`}>
                      {gap.severity}
                    </span>
                    <p className="text-sm font-medium text-gray-900 truncate">{gap.query}</p>
                  </div>
                  <button
                    onClick={() => resolveGap(gap.id)}
                    className="ml-3 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-xs font-bold hover:bg-green-200 transition-colors flex-shrink-0"
                  >
                    Mark Resolved
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ======= ACTIONABLE RECOMMENDATIONS ======= */}
        {health && health.recommendations.length > 0 && (
          <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-6 text-white">
            <h3 className="font-bold text-lg mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 text-blue-400 mr-2" />
              What To Do Next
            </h3>
            <div className="space-y-3">
              {health.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-white/10 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-xs font-bold text-blue-300">{i + 1}</span>
                  </div>
                  <p className="text-sm text-gray-300 leading-relaxed">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
