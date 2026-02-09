# AI Knowledge Continuity System - Technical Documentation

**Version:** 1.0.0  
**Last Updated:** February 2026  
**Status:** Production

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Getting Started](#getting-started)
4. [API Reference](#api-reference)
5. [RAG Pipeline](#rag-pipeline)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Knowledge Continuity System is an enterprise knowledge transfer (KT) platform that combines Retrieval-Augmented Generation (RAG) with organizational document analysis to help teams preserve and share critical knowledge.

**Key Features:**
- **Smart Document Ingestion:** Upload PDFs, Markdown, TXT files with automatic classification
- **Context-Aware Q&A:** Query your internal docs using natural language
- **Knowledge Gap Detection:** Identify what's not documented before it's too late
- **Personalized Suggestions:** AI-generated questions based on YOUR actual documents
- **Tacit Knowledge Capture:** Learn from retrospectives, lessons learned, exit interviews

**Tech Stack:**
- Backend: FastAPI + SQLite + LangChain
- Frontend: React 19 + TypeScript + Tailwind CSS
- AI: Google Gemini 2.5 Flash (LLM) + sentence-transformers (embeddings)
- Search: FAISS (local vector search, 384-dimensional)

---

## System Architecture

### High-Level Flow

```
User Uploads Doc
    ↓
[Ingestion Pipeline]
  - Extract text (PDF/MD/TXT)
  - Classify knowledge type (tacit/decision/explicit)
  - Chunk into 500-char segments
    ↓
[Embedding & Indexing]
  - Embed chunks with sentence-transformers/all-MiniLM-L6-v2
  - Store in FAISS index (384-dim vectors)
    ↓
[Storage]
  - Chunks → SQLite (full text + metadata)
  - Index → FAISS (vector_store/faiss_index/)
    ↓
User Asks Question
    ↓
[Query Pipeline]
  - Embed query (same model, same 384 dims)
  - Search FAISS for top-5 similar chunks
  - Re-rank by knowledge type relevance
  - Format context
    ↓
[Generation]
  - Send context + question to Gemini LLM
  - Get answer with source attribution
  - Log knowledge gaps (if confidence low)
```

### Components

| Component | Technology | Role |
|-----------|-----------|------|
| **Web Server** | FastAPI + Uvicorn | HTTP API, request handling |
| **Database** | SQLite (app.db) | Document metadata, conversations, gaps |
| **Vector Search** | FAISS | Semantic similarity search |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Query/chunk vectorization |
| **LLM** | Gemini 2.5 Flash | Q&A generation |
| **Frontend** | React 19 + TypeScript | Web UI |
| **Auth** | JWT (PyJWT) | User authentication |

---

## Getting Started

### Prerequisites

- **Python 3.12+** (3.13 not supported by sentence-transformers)
- **Node.js 16+** (for frontend)
- **Google Gemini API Key** (free tier available)
- **~2GB disk** (for FAISS index + dependencies)

### Installation

#### 1. Clone & Setup Backend

```bash
cd "AI Knowledge Continuity System"

# Use project-local virtual environment (Python 3.12)
# DO NOT use workspace .venv (Python 3.13)
source .venv/bin/activate

# Verify Python version
python --version  # Should output Python 3.12.x

# Install dependencies
pip install -r requirements.txt
```

#### 2. Setup Environment Variables

Create a `.env` file in the project root:

```bash
# Google Gemini API
GEMINI_API_KEY=your-api-key-here

# LLM Configuration
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu  # or 'mps' for Mac M1/M2, 'cuda' for GPU

# Database
DATABASE_URL=sqlite:///app.db

# Debug
DEBUG=False
LOG_LEVEL=INFO
```

#### 3. Initialize Database

```bash
.venv/bin/python backend/db.py
# Creates app.db with users, documents, conversations tables
```

#### 4. Rebuild Vector Store

```bash
.venv/bin/python rebuild_vector_store.py
# Indexes documents from data/ directory into FAISS
# Output: vector_store/faiss_index/ with 384-dim vectors
```

#### 5. Start Backend

```bash
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
# Starts at http://localhost:8000
# API docs at http://localhost:8000/docs (Swagger)
```

#### 6. Setup & Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm start
# Runs at http://localhost:3000
```

#### 7. Login

Default test user (created during setup):
- **Email:** dev@test.com
- **Password:** pass123

---

## API Reference

### Authentication

#### POST `/api/auth/register`

Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "developer"
  }
}
```

#### POST `/api/auth/login`

Authenticate and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass"
}
```

**Response:** Same as register (with token)

---

### Documents

#### POST `/api/documents/upload`

Upload a document for indexing.

**Headers:**
```
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request Body:**
```
- file: Binary file (PDF, MD, TXT)
- knowledge_type: "tacit" | "decision" | "explicit" (optional)
```

**Response:**
```json
{
  "id": 5,
  "filename": "architecture_decisions.md",
  "original_name": "architecture_decisions.md",
  "chunk_count": 2,
  "knowledge_type": "decision",
  "status": "indexed",
  "uploaded_at": "2026-02-09T12:00:00"
}
```

#### GET `/api/documents/list`

List all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "id": 5,
      "original_name": "architecture_decisions.md",
      "chunk_count": 2,
      "knowledge_type": "decision",
      "file_size": 1064,
      "uploaded_at": "2026-02-09T12:00:00"
    }
  ],
  "total": 5,
  "total_chunks": 12
}
```

---

### Query & RAG

#### POST `/api/query`

Ask a question about your knowledge base.

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "question": "What is the system architecture?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "use_knowledge_features": true
}
```

**Response:**
```json
{
  "id": "req-123",
  "answer": "The system architecture consists of...",
  "sources": [
    {
      "doc_name": "architecture_decisions.md",
      "chunk_text": "Core components: API layer, services layer...",
      "relevance_score": 0.92,
      "knowledge_type": "decision"
    }
  ],
  "confidence": 0.88,
  "processing_time_ms": 1245,
  "gaps_detected": 0
}
```

---

### Knowledge Insights

#### GET `/api/knowledge/health`

Get knowledge base health score.

**Response:**
```json
{
  "health_score": 72.5,
  "total_documents": 5,
  "total_chunks": 12,
  "coverage": {
    "tacit": 1,
    "decision": 6,
    "explicit": 0
  },
  "unresolved_gaps": 2,
  "recommendations": [
    "Add technical documentation (API guides, setup instructions)",
    "Document more tacit knowledge (lessons learned, retrospectives)"
  ]
}
```

#### GET `/api/knowledge/gaps`

List detected knowledge gaps.

**Response:**
```json
[
  {
    "id": 1,
    "query": "How do we handle database failover?",
    "confidence_score": 0.35,
    "severity": "high",
    "detected_at": "2026-02-09T11:50:00",
    "resolved": false
  }
]
```

#### GET `/api/knowledge/suggest-questions`

Get AI-generated questions personalized to your documents.

**Response:**
```json
{
  "questions": [
    {
      "question": "What is the overall system architecture and how do the components interact?",
      "category": "architecture",
      "icon": "🏗️",
      "context": "Based on: architecture_decisions.md"
    },
    {
      "question": "What are the known gotchas and lessons learned from this project?",
      "category": "tacit",
      "icon": "🧠",
      "context": "No tacit knowledge docs uploaded yet — consider adding retrospectives"
    }
  ],
  "total_documents": 5
}
```

---

## RAG Pipeline

### Query Processing

1. **Embed Query**
   ```python
   from langchain_huggingface import HuggingFaceEmbeddings
   embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
   query_vector = embeddings.embed_query("What is the architecture?")
   # Output: 384-dimensional vector
   ```

2. **Search FAISS Index**
   ```python
   from vector_store.create_store import VectorStoreManager
   manager = VectorStoreManager()
   results = manager.search(query="What is the architecture?", k=5)
   # Output: [(Document, score), ...] sorted by relevance
   ```

3. **Re-Rank by Knowledge Type**
   - Boost scores for "decision" documents (high priority for KT)
   - Penalize low-confidence matches from "explicit" docs

4. **Format Context**
   ```
   Context from knowledge base:
   - [Decision] From architecture_decisions.md: "..."
   - [Decision] From technology_stack_rationale.md: "..."
   ```

5. **Generate Answer**
   ```python
   response = llm.predict(
       input="Context: ...\n\nQuestion: What is the architecture?\n\nAnswer:",
       max_tokens=500
   )
   ```

### Knowledge-Aware Features

- **Gap Detection:** If average confidence < 0.6, mark as gap
- **Tacit Knowledge Highlighting:** Tag responses mentioning lessons learned
- **Decision Tracing:** Link answers back to specific ADRs (Architecture Decision Records)

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong `GEMINI_API_KEY` (rotate monthly)
- [ ] Set `LOG_LEVEL=INFO` (not DEBUG)
- [ ] Configure database backup (daily)
- [ ] Enable HTTPS (use reverse proxy)
- [ ] Set up monitoring for query latency (target: <2s)
- [ ] Configure Gemini API quota alerts
- [ ] Test disaster recovery: `rebuild_vector_store.py`

### Scaling Considerations

**Current Bottlenecks:**
- FAISS index loaded entirely in memory (2.1 MB for 12 vectors)
- Gemini API rate limits (check quota usage)
- SQLite single-writer limitation

**For >100k chunks:**
- Migrate to PostgreSQL + pgvector
- Use Faiss IVF index (faster approximate search)
- Implement Redis caching layer
- Consider GPU-accelerated embeddings

---

## Troubleshooting

### "AssertionError" in Vector Store Search

**Symptoms:** `assert d == self.d` error when querying

**Cause:** FAISS index dimension doesn't match query embedding dimension

**Fix:**
```bash
# Rebuild vector store (forces consistent embeddings)
.venv/bin/python rebuild_vector_store.py

# Verify:
# - FAISS index has 384 dims
# - sentence-transformers embeddings are used (not Gemini)
```

### ModuleNotFoundError: jwt, sentence_transformers

**Cause:** Using wrong Python/venv

**Fix:**
```bash
# Verify you're using project-local venv
which python  # Should output: .../AI Knowledge Continuity System/.venv/bin/python

# NOT the workspace venv:
# .../Final-Year Project/.venv/bin/python  ← WRONG

# Use absolute path:
"/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System/.venv/bin/python" --version
```

### "GEMINI_API_KEY not provided"

**Fix:**
```bash
# Create .env file in project root (same level as backend/, frontend/)
GEMINI_API_KEY=your-key-here

# Restart backend:
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Slow Queries (>3 seconds)

**Checklist:**
1. Check if it's the first query (cold start): expected ~5s
2. Check FAISS index size: `ls -lh vector_store/faiss_index/`
3. Monitor Gemini API latency: check response times in logs
4. Look for background processes: `ps aux | grep python`

### React Component Crashes

**"Objects are not valid as React child"**

**Fix:** Ensure event handlers use arrow functions:
```tsx
// ❌ WRONG
<button onClick={onNewConversation}>New</button>

// ✅ CORRECT
<button onClick={() => onNewConversation()}>New</button>
```

**"Cannot read properties of undefined"**

**Fix:** Verify API client uses arrow functions:
```ts
// ❌ WRONG
async query(request: QueryRequest) { ... }

// ✅ CORRECT
query = async (request: QueryRequest) => { ... }
```

---

## Performance Tips

### Optimize Embeddings
- Use `device=mps` on Mac M1/M2 for 5x speedup
- Use `device=cuda` on GPU for 10x speedup
- Default `cpu` is safe but slow

### Reduce Query Latency
- Implement result caching (Redis)
- Pre-compute embeddings for common queries
- Use FAISS IVF index for large datasets

### Control Gemini Costs
- Use `gemini-1.5-flash` for cost savings (same quality)
- Cache full responses in SQLite (avoid re-queries)
- Batch similar queries

---

## Support & Contributing

**Issues:** Open an issue in the repository with:
- Python/Node version
- OS (macOS/Linux/Windows)
- Exact error message + logs
- Minimal reproduction steps

**Contributing:** See CONTRIBUTING.md

---

**Last Updated:** February 9, 2026  
**Maintainers:** AI Engineering Team
