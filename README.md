# AI Knowledge Continuity System

> 🧠 Preventing Organizational Knowledge Loss Using LangChain-powered RAG

A production-grade AI system that aggregates organizational knowledge from multiple sources, preserves employee expertise, and enables intelligent, context-aware querying using Large Language Models.

## 🎯 Problem Statement

Modern organizations suffer significant knowledge loss when experienced employees leave. Critical information often exists in fragmented formats such as documents, emails, chats, code repositories, and personal notes. Traditional documentation systems fail to capture tacit knowledge — the "how" and "why" behind decisions.

## ✨ Features

- **Multi-Source Document Ingestion**: Support for PDF, TXT, MD, CSV files
- **Intelligent Chunking**: Semantic text splitting with metadata preservation
- **Vector Search**: FAISS-powered similarity search for fast retrieval
- **Multiple LLM Providers**: Gemini (cloud), Local LLMs, HuggingFace API
- **Conversation Memory**: Multi-session conversation history
- **Source Attribution**: Track and cite sources in responses
- **Production-Ready**: Logging, error handling, configuration management
- **Modern UI**: Streamlit-based chat interface

## 🏗️ Architecture

```
┌──────────────────────────┐
│   Organizational Data     │
│ PDFs | Docs | Markdown   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Document Loading          │
│ (Multi-format support)   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Intelligent Chunking      │
│ (Metadata enrichment)    │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Embedding Generation      │
│ (Sentence Transformers)  │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Vector Database           │
│ (FAISS)                  │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ RAG Pipeline              │
│ (Retrieval + Generation) │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ LLM (Gemini/Local)        │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Answer + Sources + Memory │
└──────────────────────────┘
```

## 📁 Project Structure

```
ai-knowledge-continuity/
│
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Pydantic settings with env support
│
├── core/                   # Core utilities
│   ├── __init__.py
│   ├── logger.py           # Structured logging
│   └── exceptions.py       # Custom exceptions
│
├── data/                   # Your organizational documents
│   ├── docs/
│   └── notes/
│
├── ingestion/              # Document processing
│   ├── __init__.py
│   ├── load_documents.py   # Multi-format document loading
│   └── chunk_documents.py  # Intelligent text chunking
│
├── vector_store/           # Vector database operations
│   ├── __init__.py
│   └── create_store.py     # FAISS store management
│
├── rag/                    # RAG pipeline components
│   ├── __init__.py
│   ├── llm.py              # LLM provider management
│   ├── retriever.py        # Advanced retrieval strategies
│   ├── prompt.py           # Prompt templates
│   └── qa_chain.py         # Main RAG chain
│
├── memory/                 # Conversation memory
│   ├── __init__.py
│   └── conversation_memory.py
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
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_api_key_here
```

### 3. Add Your Documents

Place your organizational documents in the `data/` directory:
- PDF files (.pdf)
- Text files (.txt)
- Markdown files (.md)
- CSV files (.csv)

### 4. Run Ingestion

```bash
# Process documents and create vector store
python main.py --ingest
```

### 5. Query or Launch UI

```bash
# Ask a question via CLI
python main.py --query "What is our deployment process?"

# Or launch the web interface
python main.py --ui
```

## 🔧 Configuration Options

All settings can be configured via environment variables or `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `LLM_PROVIDER` | LLM provider (gemini/local/huggingface) | gemini |
| `EMBEDDING_MODEL` | HuggingFace embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| `CHUNK_SIZE` | Text chunk size | 1000 |
| `CHUNK_OVERLAP` | Overlap between chunks | 200 |
| `RETRIEVER_K` | Number of documents to retrieve | 5 |
| `DATA_DIR` | Documents directory | data |
| `VECTOR_STORE_PATH` | Vector store location | vector_store/faiss_index |

## 📖 Usage Examples

### Python API

```python
from rag.qa_chain import RAGChain

# Initialize the RAG chain
chain = RAGChain()

# Ask a question
response = chain.query(
    question="What are the best practices for code review?",
    session_id="user123",
)

print(response.answer)
print(f"Sources: {response.get_sources_summary()}")
```

### CLI Commands

```bash
# Check system status
python main.py --status

# Ingest documents
python main.py --ingest

# Query knowledge base
python main.py --query "How do I handle customer escalations?"

# Launch web UI
python main.py --ui
```

## 🔒 Using Local LLMs

When you have adequate hardware (GPU with 16GB+ VRAM), you can use local LLMs:

1. Install local LLM dependencies:
```bash
pip install accelerate bitsandbytes torch
```

2. Update `.env`:
```
LLM_PROVIDER=local
LOCAL_LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
LOCAL_LLM_DEVICE=cuda
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

