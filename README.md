# AI Knowledge Continuity System

> 🧠 Enterprise RAG System with Tacit Knowledge, Decision Traceability, and Knowledge Gap Detection

A production-grade AI system powered by FastAPI and LangChain that preserves organizational knowledge, extracts lessons learned, traces architectural decisions, and prevents knowledge loss through intelligent gap detection.

## 🎯 Problem Statement

Modern organizations suffer significant knowledge loss when experienced employees leave. Critical information exists in fragmented formats, and traditional systems fail to capture:
- **Tacit knowledge**: Lessons learned, mistakes to avoid, unwritten expertise
- **Decision context**: Why decisions were made, alternatives considered, trade-offs accepted
- **Knowledge gaps**: When the system doesn't know enough to answer safely

## ✨ Three Enterprise Features

### 1. 📚 Tacit Knowledge Extraction
- Automatically identifies and prioritizes experiential knowledge
- Extracts insights from exit interviews, retrospectives, postmortems
- Uses deterministic pattern matching (no LLM hallucinations)
- 1.3x boost for tacit content in retrieval

### 2. 📋 Decision Traceability
- Parses Architecture Decision Records (ADRs)
- Extracts structured metadata: ID, author, date, alternatives, trade-offs
- Enables "Why?" queries about past decisions
- Preserves full decision context

### 3. ⚠️ Knowledge Gap Detection
- Detects when the system lacks knowledge
- Calculates confidence scores (0.0 - 1.0)
- Returns safe responses instead of hallucinating
- Logs all gaps for knowledge base improvement

## 🏗️ Architecture

### Backend API (FastAPI)
```
backend/
├── main.py              # FastAPI app entry point
├── api/
│   ├── routes/          # query, ingest, health endpoints
│   └── deps.py          # Dependency injection
├── core/
│   ├── config.py        # API settings
│   ├── exceptions.py    # Typed exceptions
│   ├── lifecycle.py     # Startup/shutdown
│   └── logging.py       # Structured logging
├── schemas/             # Pydantic models
├── services/            # RAG & Ingest services
```

### Core System
```
├── knowledge/           # Enterprise features
│   ├── knowledge_classifier.py  # Feature 1: Tacit detection
│   ├── decision_parser.py       # Feature 2: ADR parsing
│   └── gap_detector.py          # Feature 3: Gap detection
├── rag/                 # RAG pipeline
│   ├── qa_chain.py      # Main RAG chain
│   ├── knowledge_retriever.py  # Knowledge-aware retrieval
│   ├── llm.py           # LLM management
│   └── retriever.py     # Advanced retrieval
├── ingestion/           # Document processing
├── vector_store/        # FAISS operations
├── memory/              # Conversation memory
│
├── evaluation/             # Quality metrics
│   ├── __init__.py
│   └── metrics.py          # RAG evaluation
│
├── ui/                     # User interface
│   ├── __init__.py
│   └── app.py              # Streamlit application
│
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project configuration
├── .env.example            # Environment template
└── README.md
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-knowledge-continuity-system.git
cd ai-knowledge-continuity-system

# Create virtual environment
# Note: Python 3.12 is recommended for local embedding support (sentence-transformers)
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install sentence-transformers  # Required for local embeddings
```

### 2. Configuration

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_api_key_here
```

### 3. Add Your Documents

Place organizational documents in `data/`:
- Architecture Decision Records (ADRs)
- Exit interviews, retrospectives
- Meeting notes, design docs
- PDF, TXT, MD, CSV formats supported

### 4. Run Ingestion

```bash
# CLI: Process documents and create vector store
python main.py --ingest

# Or via FastAPI
curl -X POST http://localhost:8000/api/ingest \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"source": "directory_scan", "directory_path": "data"}'
```

### 5. Start the API Server

```bash
# Start FastAPI server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Access API docs
open http://localhost:8000/docs
```

### 6. Query Knowledge

```bash
# Via API
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What lessons were learned from the backend project?"}'

# Or via CLI
python main.py --query "What lessons were learned?"

# Or launch Streamlit UI
python main.py --ui
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Query with knowledge features |
| POST | `/api/query/batch` | Batch queries (max 10) |
| POST | `/api/ingest` | Ingest documents (admin) |
| GET | `/api/ingest/status` | Check ingestion progress |
| GET | `/api/health` | Health check |
| GET | `/api/health/ready` | Readiness probe |
| GET | `/docs` | Interactive API documentation |

## 📖 Usage Examples

### Python API

```python
from rag.qa_chain import RAGChain

# Initialize RAG chain with knowledge features
chain = RAGChain()

# Query with all features enabled
response = chain.query(
    question="What lessons were learned from the backend project?",
    use_knowledge_features=True,
    session_id="user123",
)

# Access response
print(response.answer)
print(f"Query Type: {response.query_type}")  # tacit, decision, general
print(f"Confidence: {response.confidence}")
print(f"Gap Detected: {response.knowledge_gap_detected}")
print(f"Sources: {response.get_sources_summary()}")
```

### FastAPI Client

```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "question": "Why did we choose PostgreSQL?",
        "role": "developer",
        "use_knowledge_features": True
    }
)

data = response.json()
print(data["answer"])
print(data["decision_trace"])  # Full decision context
print(data["knowledge_gap"])   # Gap detection result
```

### CLI Commands

```bash
# Check system status
python main.py --status

# Ingest documents
python main.py --ingest

# Query knowledge base
python main.py --query "What lessons were learned?"

# Launch Streamlit UI
python main.py --ui
```

3. Uncomment the local LLM code in `rag/llm.py`

## 📊 Evaluation

The system includes built-in evaluation metrics:

```python
from evaluation.metrics import RAGEvaluator

evaluator = RAGEvaluator()
result = evaluator.evaluate(
    query="What is the deployment process?",
    answer=response.answer,
    source_documents=response.source_documents,
)

print(f"Relevance: {result.relevance_score}")
print(f"Faithfulness: {result.faithfulness_score}")
print(f"Overall: {result.overall_score}")
```

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .

# Type checking
mypy .
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📧 Support

For questions or issues, please open a GitHub issue or contact the maintainers.

---

Built with ❤️ using [LangChain](https://langchain.com/) and [Streamlit](https://streamlit.io/)

