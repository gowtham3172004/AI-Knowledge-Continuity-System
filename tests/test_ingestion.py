"""
Tests for the document ingestion module.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from ingestion.load_documents import DocumentLoader
from ingestion.chunk_documents import DocumentChunker
from core.exceptions import DocumentLoadError, ChunkingError


class TestDocumentLoader:
    """Tests for DocumentLoader class."""
    
    def test_init_default_settings(self):
        """Test initialization with default settings."""
        with patch('ingestion.load_documents.get_settings') as mock_settings:
            mock_settings.return_value.DATA_DIR = "test_data"
            loader = DocumentLoader()
            assert loader.data_dir == Path("test_data")
    
    def test_init_custom_data_dir(self):
        """Test initialization with custom data directory."""
        loader = DocumentLoader(data_dir="custom_data")
        assert loader.data_dir == Path("custom_data")
    
    def test_validate_nonexistent_directory(self, tmp_path):
        """Test validation fails for non-existent directory."""
        loader = DocumentLoader(data_dir=str(tmp_path / "nonexistent"))
        
        with pytest.raises(DocumentLoadError) as exc_info:
            loader._validate_data_directory()
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_extract_metadata(self, tmp_path):
        """Test metadata extraction from documents."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        loader = DocumentLoader(data_dir=str(tmp_path))
        
        mock_doc = MagicMock()
        mock_doc.metadata = {"source": str(test_file)}
        
        metadata = loader._extract_metadata(mock_doc, "text")
        
        assert metadata["source_type"] == "text"
        assert metadata["file_name"] == "test.txt"
        assert metadata["file_extension"] == ".txt"
        assert "ingestion_timestamp" in metadata


class TestDocumentChunker:
    """Tests for DocumentChunker class."""
    
    def test_init_default_settings(self):
        """Test initialization with default settings."""
        with patch('ingestion.chunk_documents.get_settings') as mock_settings:
            mock_settings.return_value.CHUNK_SIZE = 1000
            mock_settings.return_value.CHUNK_OVERLAP = 200
            
            chunker = DocumentChunker()
            
            assert chunker.chunk_size == 1000
            assert chunker.chunk_overlap == 200
    
    def test_init_custom_settings(self):
        """Test initialization with custom settings."""
        chunker = DocumentChunker(
            chunk_size=500,
            chunk_overlap=100,
        )
        
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 100
    
    def test_init_invalid_overlap(self):
        """Test initialization fails with invalid overlap."""
        with pytest.raises(ChunkingError) as exc_info:
            DocumentChunker(
                chunk_size=100,
                chunk_overlap=150,  # Overlap > chunk size
            )
        
        assert "must be less than" in str(exc_info.value).lower()
    
    def test_chunk_empty_list(self):
        """Test chunking with empty document list."""
        chunker = DocumentChunker()
        
        with pytest.raises(ChunkingError) as exc_info:
            chunker.chunk([])
        
        assert "no documents" in str(exc_info.value).lower()
    
    def test_chunk_creates_metadata(self):
        """Test that chunking adds metadata to chunks."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        mock_doc = MagicMock()
        mock_doc.page_content = "A" * 300  # Content that will be split
        mock_doc.metadata = {"source": "test.txt"}
        
        chunks = chunker.chunk([mock_doc])
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert "chunk_index" in chunk.metadata
            assert "global_chunk_id" in chunk.metadata
            assert "chunk_size" in chunk.metadata


class TestChunkMetrics:
    """Tests for chunking metrics."""
    
    def test_metrics_calculation(self):
        """Test metrics are calculated correctly."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        mock_docs = []
        for i in range(3):
            doc = MagicMock()
            doc.page_content = f"Content {i} " * 50
            doc.metadata = {"source": f"doc{i}.txt"}
            mock_docs.append(doc)
        
        chunks = chunker.chunk(mock_docs)
        metrics = chunker._calculate_metrics(mock_docs, chunks)
        
        assert metrics.total_documents == 3
        assert metrics.total_chunks == len(chunks)
        assert metrics.avg_chunk_size > 0
