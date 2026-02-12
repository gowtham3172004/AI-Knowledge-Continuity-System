/**
 * Document Upload & Management Page
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  FileText, Trash2, RefreshCw, CheckCircle, AlertCircle,
  Loader2, FileUp, Brain, ChevronLeft, File, FileCode, FileSpreadsheet
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { API_URL } from '../config/api.config';

const API = API_URL;

interface Document {
  id: number;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  knowledge_type: string;
  chunk_count: number;
  status: string;
  uploaded_at: string;
}

const getFileIcon = (type: string) => {
  switch (type) {
    case 'pdf': return <FileText className="w-5 h-5 text-red-500" />;
    case 'md': return <FileCode className="w-5 h-5 text-blue-500" />;
    case 'csv': return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
    default: return <File className="w-5 h-5 text-gray-500" />;
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'indexed':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" />Indexed</span>;
    case 'processing':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800"><Loader2 className="w-3 h-3 mr-1 animate-spin" />Processing</span>;
    case 'error':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800"><AlertCircle className="w-3 h-3 mr-1" />Error</span>;
    default:
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-100 text-gray-800">{status}</span>;
  }
};

const getTypeBadge = (type: string) => {
  const colors: Record<string, string> = {
    tacit: 'bg-amber-100 text-amber-800',
    decision: 'bg-purple-100 text-purple-800',
    explicit: 'bg-blue-100 text-blue-800',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${colors[type] || 'bg-gray-100 text-gray-600'}`}>
      {type}
    </span>
  );
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

interface DocumentsPageProps {
  onBack: () => void;
  currentPage?: 'home' | 'chat' | 'documents' | 'dashboard';
  onNavigate?: (page: 'home' | 'chat' | 'documents' | 'dashboard') => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({ onBack, currentPage, onNavigate }) => {
  const { token } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchDocs = useCallback(async () => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const res = await fetch(`${API}/api/documents/`, { headers: h });
      if (res.ok) setDocuments(await res.json());
    } catch (e) { console.error('Failed to fetch docs:', e); }
  }, [token]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  // Auto-refresh processing documents
  useEffect(() => {
    const hasProcessing = documents.some(d => d.status === 'processing');
    if (hasProcessing) {
      const interval = setInterval(fetchDocs, 3000);
      return () => clearInterval(interval);
    }
  }, [documents, fetchDocs]);

  const uploadFiles = async (files: FileList | File[]) => {
    setUploading(true);
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append('files', f));

    try {
      const res = await fetch(`${API}/api/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || 'Upload failed');
      }
      await fetchDocs();
    } catch (e) {
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const deleteDoc = async (id: number) => {
    if (!window.confirm('Remove this document from the knowledge base?')) return;
    try {
      await fetch(`${API}/api/documents/${id}`, { method: 'DELETE', headers });
      await fetchDocs();
    } catch (e) { alert('Delete failed'); }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files.length > 0) uploadFiles(e.dataTransfer.files);
  };

  const refresh = async () => {
    setRefreshing(true);
    await fetchDocs();
    setTimeout(() => setRefreshing(false), 500);
  };

  const indexedCount = documents.filter(d => d.status === 'indexed').length;
  const totalChunks = documents.reduce((sum, d) => sum + d.chunk_count, 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button onClick={onBack} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Knowledge Base</h1>
              <p className="text-sm text-gray-500">Upload and manage your team's documents</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-right mr-4">
              <p className="text-sm font-bold text-gray-900">{indexedCount} documents</p>
              <p className="text-xs text-gray-500">{totalChunks} knowledge chunks</p>
            </div>
            <button onClick={refresh} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Upload Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer
            ${dragActive ? 'border-blue-500 bg-blue-50 scale-[1.01]' : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50/50'}
            ${uploading ? 'pointer-events-none opacity-60' : ''}`}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.md,.docx,.csv,.json,.py,.js,.ts,.yaml,.yml,.html"
            onChange={(e) => e.target.files && uploadFiles(e.target.files)}
            className="hidden"
          />
          {uploading ? (
            <div className="flex flex-col items-center">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-3" />
              <p className="text-lg font-semibold text-blue-700">Processing documents...</p>
              <p className="text-sm text-gray-500 mt-1">Documents are being classified and indexed</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20 mb-4">
                <FileUp className="w-8 h-8 text-white" />
              </div>
              <p className="text-lg font-semibold text-gray-900">Drop files here or click to upload</p>
              <p className="text-sm text-gray-500 mt-1">PDF, DOCX, TXT, MD, CSV, JSON, code files • Max 20MB each</p>
              <div className="flex items-center space-x-2 mt-4">
                <Brain className="w-4 h-4 text-purple-500" />
                <span className="text-xs text-purple-600 font-medium">Documents are auto-classified as Tacit, Decision, or Explicit knowledge</span>
              </div>
            </div>
          )}
        </div>

        {/* Documents Table */}
        {documents.length > 0 && (
          <div className="mt-8 bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="font-bold text-gray-900">Uploaded Documents</h2>
            </div>
            <div className="divide-y divide-gray-100">
              {documents.map((doc) => (
                <div key={doc.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors group">
                  <div className="flex items-center space-x-4 flex-1 min-w-0">
                    <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                      {getFileIcon(doc.file_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">{doc.original_name}</p>
                      <div className="flex items-center space-x-3 mt-1">
                        <span className="text-xs text-gray-500">{formatSize(doc.file_size)}</span>
                        {doc.chunk_count > 0 && (
                          <span className="text-xs text-gray-500">{doc.chunk_count} chunks</span>
                        )}
                        <span className="text-xs text-gray-400">{doc.uploaded_at}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 ml-4">
                    {getTypeBadge(doc.knowledge_type)}
                    {getStatusBadge(doc.status)}
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteDoc(doc.id); }}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {documents.length === 0 && !uploading && (
          <div className="text-center mt-16">
            <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No documents yet</h3>
            <p className="text-gray-500 max-w-md mx-auto">
              Upload your project documents, meeting notes, design decisions, and lessons learned to build your knowledge base.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
