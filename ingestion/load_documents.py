"""
Document Loading Module for AI Knowledge Continuity System.

This module provides production-grade document loading capabilities
with support for multiple file formats, metadata extraction, and
comprehensive error handling.

Extended to support:
- Knowledge type classification (explicit, tacit, decision)
- Decision metadata extraction for ADR and design documents
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
    JSONLoader,
)
from langchain_core.documents import Document
from tqdm import tqdm

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import DocumentLoadError

# Import knowledge classification components
try:
    from knowledge.knowledge_classifier import KnowledgeClassifier, classify_document
    from knowledge.decision_parser import DecisionParser, parse_decision_document
    KNOWLEDGE_FEATURES_AVAILABLE = True
except ImportError:
    KNOWLEDGE_FEATURES_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class LoaderConfig:
    """Configuration for a document loader."""
    glob_pattern: str
    loader_class: type
    loader_kwargs: Dict[str, Any] = field(default_factory=dict)
    source_type: str = ""


class DocumentLoader:
    """
    Production-grade document loader with support for multiple formats.
    
    Features:
    - Multiple file format support (PDF, TXT, MD, CSV, JSON)
    - Automatic metadata extraction (file info, timestamps)
    - Progress tracking with tqdm
    - Comprehensive error handling and logging
    - Configurable loader options
    
    Example:
        >>> loader = DocumentLoader(data_dir="data")
        >>> documents = loader.load()
        >>> print(f"Loaded {len(documents)} documents")
    """
    
    # Default loader configurations
    DEFAULT_LOADERS: List[LoaderConfig] = [
        LoaderConfig(
            glob_pattern="**/*.pdf",
            loader_class=PyPDFLoader,
            source_type="pdf"
        ),
        LoaderConfig(
            glob_pattern="**/*.txt",
            loader_class=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            source_type="text"
        ),
        LoaderConfig(
            glob_pattern="**/*.md",
            loader_class=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            source_type="markdown"
        ),
        LoaderConfig(
            glob_pattern="**/*.csv",
            loader_class=CSVLoader,
            source_type="csv"
        ),
    ]
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        custom_loaders: Optional[List[LoaderConfig]] = None,
        show_progress: bool = True,
        enable_knowledge_classification: bool = True,
    ):
        """
        Initialize the document loader.
        
        Args:
            data_dir: Directory containing documents. Defaults to config setting.
            custom_loaders: Additional loader configurations to use.
            show_progress: Whether to show progress bar during loading.
            enable_knowledge_classification: Whether to classify documents by knowledge type.
        """
        self.settings = get_settings()
        self.data_dir = Path(data_dir or self.settings.DATA_DIR)
        self.show_progress = show_progress
        
        # Knowledge classification settings
        self.enable_knowledge_classification = (
            enable_knowledge_classification and 
            KNOWLEDGE_FEATURES_AVAILABLE and
            getattr(self.settings, 'ENABLE_KNOWLEDGE_CLASSIFICATION', True)
        )
        
        # Initialize classifiers if enabled
        if self.enable_knowledge_classification:
            self._knowledge_classifier = KnowledgeClassifier()
            self._decision_parser = DecisionParser()
            logger.info("Knowledge classification enabled for document loading")
        else:
            self._knowledge_classifier = None
            self._decision_parser = None
        
        # Combine default and custom loaders
        self.loaders = self.DEFAULT_LOADERS.copy()
        if custom_loaders:
            self.loaders.extend(custom_loaders)
        
        logger.info(f"DocumentLoader initialized with data_dir: {self.data_dir}")
    
    def _validate_data_directory(self) -> None:
        """Validate that the data directory exists and is accessible."""
        if not self.data_dir.exists():
            raise DocumentLoadError(
                f"Data directory not found: {self.data_dir}",
                details={"path": str(self.data_dir)}
            )
        
        if not self.data_dir.is_dir():
            raise DocumentLoadError(
                f"Path is not a directory: {self.data_dir}",
                details={"path": str(self.data_dir)}
            )
        
        # Check if directory has any files
        file_count = sum(1 for _ in self.data_dir.rglob("*") if _.is_file())
        if file_count == 0:
            logger.warning(f"Data directory is empty: {self.data_dir}")
    
    def _extract_metadata(self, doc: Document, source_type: str) -> Dict[str, Any]:
        """
        Extract and enrich metadata from a document.
        
        This method now includes knowledge classification and decision
        metadata extraction for enhanced retrieval capabilities.
        
        Args:
            doc: The document to extract metadata from.
            source_type: Type of the source file.
            
        Returns:
            Enriched metadata dictionary including knowledge_type and decision metadata.
        """
        source_path = Path(doc.metadata.get("source", ""))
        
        metadata = {
            **doc.metadata,
            "source_type": source_type,
            "file_name": source_path.name if source_path else "",
            "file_extension": source_path.suffix if source_path else "",
            "ingestion_timestamp": datetime.now().isoformat(),
        }
        
        # Extract file stats if available
        if source_path and source_path.exists():
            stat = source_path.stat()
            metadata.update({
                "file_size_bytes": stat.st_size,
                "file_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
        
        # Extract directory structure as potential category
        if source_path:
            relative_path = source_path.relative_to(self.data_dir) if self.data_dir in source_path.parents else source_path
            parts = relative_path.parts[:-1]  # Exclude filename
            if parts:
                metadata["category"] = "/".join(parts)
                metadata["department"] = parts[0] if parts else "general"
        
        # === KNOWLEDGE CLASSIFICATION (Feature 1 & 2) ===
        if self.enable_knowledge_classification and self._knowledge_classifier:
            try:
                # Classify the document
                classification = self._knowledge_classifier.classify(
                    filename=source_path.name if source_path else None,
                    filepath=str(source_path) if source_path else None,
                    content=doc.page_content,
                )
                
                # Add classification metadata
                metadata.update(classification.to_metadata())
                
                # If it's a decision document, extract decision metadata
                if classification.knowledge_type.value == "decision" and self._decision_parser:
                    decision_meta = self._decision_parser.parse(
                        content=doc.page_content,
                        filename=source_path.name if source_path else None,
                        filepath=str(source_path) if source_path else None,
                    )
                    
                    # Add decision metadata
                    metadata.update(decision_meta.to_metadata())
                    
                    logger.debug(
                        f"Decision metadata extracted from {source_path.name}: "
                        f"confidence={decision_meta.extraction_confidence:.2f}"
                    )
                
                logger.debug(
                    f"Classified '{source_path.name}' as {classification.knowledge_type.value} "
                    f"(confidence: {classification.confidence:.2f})"
                )
                
            except Exception as e:
                # Don't fail loading if classification fails
                logger.warning(f"Knowledge classification failed for {source_path}: {e}")
                metadata["knowledge_type"] = "explicit"
                metadata["knowledge_confidence"] = 0.5
        else:
            # Default classification when feature is disabled
            metadata["knowledge_type"] = "explicit"
            metadata["knowledge_confidence"] = 1.0
        
        return metadata
    
    def _load_with_loader(self, loader_config: LoaderConfig) -> List[Document]:
        """
        Load documents using a specific loader configuration.
        
        Args:
            loader_config: Configuration for the loader to use.
            
        Returns:
            List of loaded documents.
        """
        try:
            directory_loader = DirectoryLoader(
                str(self.data_dir),
                glob=loader_config.glob_pattern,
                loader_cls=loader_config.loader_class,
                loader_kwargs=loader_config.loader_kwargs,
                show_progress=False,  # We handle progress ourselves
                use_multithreading=True,
                max_concurrency=4,
            )
            
            docs = directory_loader.load()
            
            # Enrich metadata for each document
            for doc in docs:
                doc.metadata = self._extract_metadata(doc, loader_config.source_type)
            
            return docs
            
        except Exception as e:
            logger.warning(
                f"Failed to load documents with pattern {loader_config.glob_pattern}: {e}"
            )
            return []
    
    def load(self) -> List[Document]:
        """
        Load all documents from the data directory.
        
        Returns:
            List of loaded and enriched documents.
            
        Raises:
            DocumentLoadError: If loading fails or no documents are found.
        """
        logger.info(f"Starting document loading from: {self.data_dir}")
        self._validate_data_directory()
        
        all_documents: List[Document] = []
        
        # Iterate through loaders with progress tracking
        loader_iterator = tqdm(
            self.loaders,
            desc="Loading documents",
            disable=not self.show_progress
        )
        
        for loader_config in loader_iterator:
            loader_iterator.set_postfix(pattern=loader_config.glob_pattern)
            docs = self._load_with_loader(loader_config)
            
            if docs:
                logger.info(
                    f"Loaded {len(docs)} documents with pattern: {loader_config.glob_pattern}"
                )
                all_documents.extend(docs)
        
        if not all_documents:
            raise DocumentLoadError(
                "No documents were loaded from the data directory",
                details={
                    "data_dir": str(self.data_dir),
                    "supported_patterns": [lc.glob_pattern for lc in self.loaders]
                }
            )
        
        # Log summary
        logger.info(f"Successfully loaded {len(all_documents)} documents")
        self._log_loading_summary(all_documents)
        
        return all_documents
    
    def _log_loading_summary(self, documents: List[Document]) -> None:
        """Log a summary of loaded documents by type."""
        type_counts: Dict[str, int] = {}
        for doc in documents:
            source_type = doc.metadata.get("source_type", "unknown")
            type_counts[source_type] = type_counts.get(source_type, 0) + 1
        
        logger.info(f"Document types loaded: {type_counts}")
    
    def load_single_file(self, file_path: str) -> List[Document]:
        """
        Load a single file and return its documents.
        
        Args:
            file_path: Path to the file to load.
            
        Returns:
            List of documents from the file.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")
        
        # Find appropriate loader
        extension = path.suffix.lower()
        loader_map = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".csv": CSVLoader,
        }
        
        loader_class = loader_map.get(extension)
        if not loader_class:
            raise DocumentLoadError(
                f"Unsupported file type: {extension}",
                details={"supported": list(loader_map.keys())}
            )
        
        try:
            loader = loader_class(str(path))
            docs = loader.load()
            
            # Enrich metadata
            for doc in docs:
                doc.metadata = self._extract_metadata(doc, extension[1:])
            
            return docs
            
        except Exception as e:
            raise DocumentLoadError(
                f"Failed to load file: {file_path}",
                details={"error": str(e)}
            )


# Convenience function for backward compatibility
def load_documents(data_dir: str) -> List[Document]:
    """
    Load documents from a directory.
    
    This is a convenience function for backward compatibility.
    For production use, prefer the DocumentLoader class.
    
    Args:
        data_dir: Directory containing documents.
        
    Returns:
        List of loaded documents.
    """
    loader = DocumentLoader(data_dir=data_dir)
    return loader.load()
