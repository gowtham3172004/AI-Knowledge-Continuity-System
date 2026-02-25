-- =============================================================================
-- Supabase Setup SQL for AI Knowledge Continuity System
-- =============================================================================
-- Run this in your Supabase Dashboard → SQL Editor
-- This creates all required tables with Row Level Security (RLS)
-- =============================================================================

-- 1. Documents table
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    knowledge_type TEXT DEFAULT 'explicit',
    chunk_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'processing',
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Knowledge gaps table
CREATE TABLE IF NOT EXISTS knowledge_gaps (
    id BIGSERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    severity TEXT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES auth.users(id),
    resolved_at TIMESTAMPTZ
);

-- 3. Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    response_data TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_gaps_resolved ON knowledge_gaps(resolved);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Documents: users can CRUD their own documents
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid() = user_id);

-- Knowledge gaps: all authenticated users can view, insert
CREATE POLICY "Authenticated users can view gaps" ON knowledge_gaps
    FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can insert gaps" ON knowledge_gaps
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can update gaps" ON knowledge_gaps
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Conversations: users can CRUD their own conversations
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own conversations" ON conversations
    FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (auth.uid() = user_id);

-- Messages: users can CRUD messages in their own conversations
CREATE POLICY "Users can view own messages" ON messages
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid())
    );
CREATE POLICY "Users can insert messages in own conversations" ON messages
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid())
    );
CREATE POLICY "Users can delete own messages" ON messages
    FOR DELETE USING (
        EXISTS (SELECT 1 FROM conversations c WHERE c.id = messages.conversation_id AND c.user_id = auth.uid())
    );

-- =============================================================================
-- SERVICE ROLE BYPASS
-- =============================================================================
-- The backend uses SUPABASE_SERVICE_ROLE_KEY which bypasses RLS automatically.
-- RLS policies above are for additional security if you ever use the anon key.
-- =============================================================================

-- Done! Your Supabase database is ready.
