#!/usr/bin/env python3
"""
Rebuild the FAISS vector store from data/ documents.

Uses sentence-transformers/all-MiniLM-L6-v2 (384 dims) via HuggingFace.
"""

import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestion.load_documents import load_documents
from ingestion.chunk_documents import chunk_documents
from vector_store.create_store import VectorStoreManager, EmbeddingManager


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    print(f"[1/4] Loading documents from {data_dir} ...")
    docs = load_documents(data_dir)
    print(f"       Loaded {len(docs)} raw documents")

    if not docs:
        print("ERROR: No documents found. Aborting.")
        sys.exit(1)

    print("[2/4] Chunking documents ...")
    chunks = chunk_documents(docs)
    print(f"       Created {len(chunks)} chunks")

    # Reset the EmbeddingManager singleton so it picks up fresh state
    EmbeddingManager._instance = None
    EmbeddingManager._embeddings = None

    print("[3/4] Building FAISS index with HuggingFace embeddings ...")
    manager = VectorStoreManager()
    # Delete old index if it somehow exists
    if manager.exists:
        manager.delete(confirm=True)
    vs = manager.create(chunks)

    stats = manager.get_stats()
    print(f"       Index created: {stats['num_documents']} vectors, model={stats['embedding_model']}")

    print("[4/4] Verifying search works ...")
    results = manager.search("system architecture", k=2)
    for doc, score in results:
        src = doc.metadata.get("source", "?")
        print(f"       score={score:.4f}  source={os.path.basename(src)}")

    print("\n✅ Vector store rebuilt successfully!")


if __name__ == "__main__":
    main()
