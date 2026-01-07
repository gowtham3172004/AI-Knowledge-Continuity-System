/**
 * TypeScript types for AI Knowledge Continuity System API
 * 
 * These types match the backend Pydantic schemas exactly.
 */

// ==================== Enums ====================

export enum KnowledgeType {
  TACIT = 'tacit',
  EXPLICIT = 'explicit',
  DECISION = 'decision',
  UNKNOWN = 'unknown',
}

export enum QueryRole {
  DEVELOPER = 'developer',
  MANAGER = 'manager',
  ANALYST = 'analyst',
  EXECUTIVE = 'executive',
  GENERAL = 'general',
}

export enum GapSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

// ==================== Request Types ====================

export interface QueryRequest {
  question: string;
  role?: QueryRole;
  department?: string;
  conversation_id?: string;
  use_knowledge_features?: boolean;
}

export interface IngestRequest {
  file_paths?: string[];
  urls?: string[];
  content_type?: string;
  metadata?: Record<string, any>;
}

// ==================== Response Components ====================

export interface SourceDocument {
  source: string;
  content_preview: string;
  knowledge_type: KnowledgeType;
  relevance_score?: number;
  
  // Decision metadata (if applicable)
  decision_id?: string;
  decision_author?: string;
  decision_date?: string;
}

export interface DecisionTrace {
  decision_id?: string;
  title?: string;
  author?: string;
  date?: string;
  rationale?: string;
  alternatives: string[];
  tradeoffs: string[];
}

export interface KnowledgeGapInfo {
  detected: boolean;
  severity?: GapSeverity;
  confidence_score: number;
  reason?: string;
}

// ==================== Main Response Types ====================

export interface QueryResponse {
  // Core response
  answer: string;
  query: string;
  
  // Sources
  sources: SourceDocument[];
  
  // Knowledge features metadata
  query_type: string;
  knowledge_types_used: string[];
  
  // Feature 1: Tacit Knowledge
  tacit_knowledge_used: boolean;
  
  // Feature 2: Decision Traceability
  decision_trace?: DecisionTrace;
  
  // Feature 3: Knowledge Gap Detection
  knowledge_gap: KnowledgeGapInfo;
  
  // Metadata
  warnings: string[];
  confidence: number;
  processing_time_ms: number;
  timestamp: string;
}

export interface IngestResponse {
  status: string;
  message: string;
  documents_processed: number;
  chunks_created: number;
  processing_time_ms: number;
  warnings?: string[];
}

export interface HealthResponse {
  status: string;
  version?: string;
  vector_store_initialized?: boolean;
  model_loaded?: boolean;
  uptime_seconds?: number;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

// ==================== UI-Specific Types ====================

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  
  // Assistant-specific fields
  response?: QueryResponse;
  isLoading?: boolean;
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: Date;
  updated_at: Date;
}

export interface ChatState {
  conversations: Conversation[];
  activeConversationId?: string;
  currentMessage: string;
  isLoading: boolean;
  error?: string;
}
