"""
Qdrant Vector Store for AI Knowledge Continuity System.

Production-grade vector store with per-user document isolation.
Uses Qdrant for persistent, scalable vector search with metadata filtering.
"""

import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import VectorStoreError, EmbeddingError
from vector_store.create_store import EmbeddingManager

logger = get_logger(__name__)

COLLECTION_NAME = "knowledge_base"
VECTOR_DIM = 384  # all-MiniLM-L6-v2


class QdrantVectorStore:
    """
    Production-grade Qdrant vector store with per-user isolation.

    Every document chunk is stored with a ``user_id`` payload field.
    Queries always filter by ``user_id`` so users only see their own data.
    """

    _instance: Optional["QdrantVectorStore"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, path: Optional[str] = None):
        if self._initialized:
            return
        self.settings = get_settings()
        self.store_path = path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "vector_store", "qdrant_data"
        )
        Path(self.store_path).mkdir(parents=True, exist_ok=True)
        self.embedding_manager = EmbeddingManager()
        self.client = QdrantClient(path=self.store_path)
        self._ensure_collection()
        self._initialized = True
        logger.info(f"QdrantVectorStore initialised at {self.store_path}")

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def _ensure_collection(self):
        """Create the collection if it doesn't already exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qmodels.VectorParams(
                    size=VECTOR_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", COLLECTION_NAME)
        
        # Ensure user_id payload index exists (KEYWORD type for UUID strings)
        try:
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="user_id",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            # Index may already exist (possibly with different type) — that's OK
            pass

    # ------------------------------------------------------------------
    # Add / index documents
    # ------------------------------------------------------------------

    def add_documents(
        self,
        documents: List[Document],
        user_id: Any,
        batch_size: int = 64,
    ) -> int:
        """
        Embed and upsert documents into Qdrant for a specific user.

        Returns the number of points added.
        """
        if not documents:
            return 0

        # Store user_id as string to support both UUID and integer IDs
        texts = [doc.page_content for doc in documents]
        embeddings = self.embedding_manager.embed_documents(texts)

        points: List[qmodels.PointStruct] = []
        for doc, vec in zip(documents, embeddings):
            # Build payload – must be JSON-safe
            payload: Dict[str, Any] = {
                "user_id": str(user_id),
                "page_content": doc.page_content,
            }
            for k, v in (doc.metadata or {}).items():
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    payload[k] = v
                elif isinstance(v, (list, tuple)):
                    payload[k] = ", ".join(str(i) for i in v) if v else ""
                else:
                    payload[k] = str(v)

            points.append(
                qmodels.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload=payload,
                )
            )

        # Upsert in batches
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=COLLECTION_NAME, points=batch)

        logger.info("Added %d vectors for user %s", len(points), user_id)
        return len(points)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        user_id: Any,
        k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Tuple[Document, float]]:
        """
        Similarity search filtered to a specific user.

        Returns list of (Document, score) tuples sorted by relevance.
        """
        query_vec = self.embedding_manager.embed_query(query)

        response = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec,
            query_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=str(user_id)),
                    )
                ]
            ),
            limit=k,
            score_threshold=score_threshold if score_threshold > 0 else None,
        )

        docs_with_scores: List[Tuple[Document, float]] = []
        for hit in response.points:
            payload = hit.payload or {}
            content = payload.pop("page_content", "")
            payload.pop("user_id", None)
            doc = Document(page_content=content, metadata=payload)
            docs_with_scores.append((doc, hit.score))

        return docs_with_scores

    # ------------------------------------------------------------------
    # Deletion helpers
    # ------------------------------------------------------------------

    def delete_by_source(self, user_id: Any, source_name: str) -> int:
        """Delete all vectors matching a given source name for a user."""
        result = self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="user_id",
                            match=qmodels.MatchValue(value=str(user_id)),
                        ),
                        qmodels.FieldCondition(
                            key="source",
                            match=qmodels.MatchValue(value=source_name),
                        ),
                    ]
                )
            ),
        )
        logger.info("Deleted vectors for user %s, source '%s'", user_id, source_name)
        return 0  # Qdrant delete doesn't return count easily

    def delete_all_user_docs(self, user_id: Any):
        """Delete ALL vectors for a user."""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="user_id",
                            match=qmodels.MatchValue(value=str(user_id)),
                        )
                    ]
                )
            ),
        )
        logger.info("Deleted all vectors for user %s", user_id)

    # ------------------------------------------------------------------
    # Stats / helpers
    # ------------------------------------------------------------------

    def count_user_vectors(self, user_id: Any) -> int:
        """Count vectors belonging to a user."""
        result = self.client.count(
            collection_name=COLLECTION_NAME,
            count_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=str(user_id)),
                    )
                ]
            ),
            exact=True,
        )
        return result.count

    def get_stats(self, user_id: Optional[Any] = None) -> Dict[str, Any]:
        """Get collection statistics, optionally filtered to a user."""
        info = self.client.get_collection(COLLECTION_NAME)
        total = info.points_count or 0
        stats: Dict[str, Any] = {
            "status": "loaded",
            "total_vectors": total,
            "embedding_model": self.settings.EMBEDDING_MODEL,
        }
        if user_id is not None:
            stats["user_vectors"] = self.count_user_vectors(user_id)
        return stats

    @property
    def exists(self) -> bool:
        """Always True – Qdrant persists automatically."""
        return True

    @property
    def is_loaded(self) -> bool:
        return True
