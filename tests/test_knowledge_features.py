"""
Tests for Knowledge Management Features.

This module tests the three enterprise features:
- Feature 1: Tacit Knowledge Extraction
- Feature 2: Decision Traceability
- Feature 3: Knowledge Gap Detection
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from langchain_core.documents import Document

# Import knowledge components
from knowledge.knowledge_classifier import (
    KnowledgeClassifier,
    KnowledgeType,
    ClassificationResult,
    classify_document,
)
from knowledge.decision_parser import (
    DecisionParser,
    DecisionMetadata,
    parse_decision_document,
)
from knowledge.gap_detector import (
    KnowledgeGapDetector,
    GapDetectionResult,
    GapSeverity,
    KnowledgeGapLogger,
)
from knowledge.validator import (
    KnowledgeValidator,
    ValidationResult,
    ValidationStatus,
)


# =============================================================================
# FEATURE 1: TACIT KNOWLEDGE EXTRACTION TESTS
# =============================================================================

class TestKnowledgeClassifier:
    """Tests for knowledge classification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = KnowledgeClassifier()
    
    def test_classifies_exit_interview_as_tacit(self):
        """Exit interview documents should be classified as tacit."""
        result = self.classifier.classify(
            filename="exit_interview_john.txt",
            content="Lessons learned during my time at the company..."
        )
        
        assert result.knowledge_type == KnowledgeType.TACIT
        assert result.confidence >= 0.4  # Confidence varies by pattern matches
        assert "filename_pattern" in result.classification_reason.lower() or "tacit" in result.classification_reason.lower()
    
    def test_classifies_lessons_learned_as_tacit(self):
        """Lessons learned documents should be classified as tacit."""
        result = self.classifier.classify(
            filename="lessons_learned_q4.md",
            content="What we learned from the project..."
        )
        
        assert result.knowledge_type == KnowledgeType.TACIT
    
    def test_classifies_postmortem_as_tacit(self):
        """Postmortem documents should be classified as tacit."""
        result = self.classifier.classify(
            filename="postmortem_incident_2024.txt",
            content="Root cause analysis and lessons..."
        )
        
        assert result.knowledge_type == KnowledgeType.TACIT
    
    def test_classifies_adr_as_decision(self):
        """ADR documents should be classified as decision."""
        result = self.classifier.classify(
            filename="ADR-001-use-redis.md",
            content="## Decision\nWe decided to use Redis..."
        )
        
        assert result.knowledge_type == KnowledgeType.DECISION
    
    def test_classifies_architecture_decision_as_decision(self):
        """Architecture decision documents should be classified as decision."""
        result = self.classifier.classify(
            filename="architecture_decisions.md",
            content="### Rationale\nWe chose this approach because..."
        )
        
        assert result.knowledge_type == KnowledgeType.DECISION
    
    def test_classifies_regular_doc_as_explicit(self):
        """Regular documentation should be classified as explicit."""
        result = self.classifier.classify(
            filename="api_documentation.md",
            content="This API provides the following endpoints..."
        )
        
        assert result.knowledge_type == KnowledgeType.EXPLICIT
    
    def test_is_tacit_query_detects_mistakes_query(self):
        """Should detect queries about mistakes as tacit."""
        is_tacit, indicators = self.classifier.is_tacit_query(
            "What mistakes should I avoid when deploying?"
        )
        
        assert is_tacit is True
        assert len(indicators) > 0
    
    def test_is_tacit_query_detects_best_practices(self):
        """Should detect queries about best practices as tacit."""
        is_tacit, indicators = self.classifier.is_tacit_query(
            "What are the best practices for caching?"
        )
        
        assert is_tacit is True
    
    def test_is_decision_query_detects_why_questions(self):
        """Should detect 'why' questions as decision queries."""
        is_decision, indicators = self.classifier.is_decision_query(
            "Why did we choose Redis instead of RabbitMQ?"
        )
        
        assert is_decision is True
        assert len(indicators) > 0
    
    def test_is_decision_query_detects_rationale(self):
        """Should detect queries about rationale as decision queries."""
        is_decision, indicators = self.classifier.is_decision_query(
            "What was the rationale behind the microservices decision?"
        )
        
        assert is_decision is True


# =============================================================================
# FEATURE 2: DECISION TRACEABILITY TESTS
# =============================================================================

class TestDecisionParser:
    """Tests for decision metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DecisionParser()
    
    def test_extracts_decision_id_from_filename(self):
        """Should extract decision ID from ADR filename."""
        result = self.parser.parse(
            content="# Use Redis for Caching",
            filename="ADR-001.md"
        )
        
        assert result.decision_id == "ADR-001"
    
    def test_extracts_title_from_markdown(self):
        """Should extract decision title from markdown header."""
        result = self.parser.parse(
            content="# ADR-001: Use Redis for Caching\n\nSome content...",
            filename="adr.md"
        )
        
        assert "Redis" in result.decision_title or "Caching" in result.decision_title
    
    def test_extracts_author(self):
        """Should extract author information."""
        result = self.parser.parse(
            content="""
            # Decision Title
            
            Author: John Smith
            
            ## Context
            Some context...
            """,
            filename="decision.md"
        )
        
        assert result.author == "John Smith"
    
    def test_extracts_date(self):
        """Should extract date from document."""
        result = self.parser.parse(
            content="""
            # Decision
            
            Date: 2024-01-15
            
            ## Decision
            We decided to...
            """,
            filename="adr.md"
        )
        
        assert result.date == "2024-01-15"
    
    def test_extracts_rationale_section(self):
        """Should extract rationale from document."""
        result = self.parser.parse(
            content="""
            # Decision
            
            ## Rationale
            We chose this approach because it provides better performance
            and lower operational overhead.
            
            ## Outcome
            Successful implementation.
            """,
            filename="adr.md"
        )
        
        assert result.rationale is not None
        assert "performance" in result.rationale.lower() or "overhead" in result.rationale.lower()
    
    def test_extracts_alternatives(self):
        """Should extract alternatives from document."""
        result = self.parser.parse(
            content="""
            # Decision
            
            ## Alternatives
            - Option 1: Use PostgreSQL
            - Option 2: Use MongoDB
            - Option 3: Use Redis
            
            ## Decision
            We chose Option 3.
            """,
            filename="adr.md"
        )
        
        assert len(result.alternatives) >= 2
    
    def test_extracts_tradeoffs(self):
        """Should extract trade-offs from document."""
        result = self.parser.parse(
            content="""
            # Decision
            
            ## Trade-offs
            - Accepted: Less durability for better performance
            - Accepted: Simpler operations vs feature richness
            
            ## Outcome
            Successful.
            """,
            filename="adr.md"
        )
        
        assert len(result.tradeoffs) >= 1
    
    def test_to_metadata_returns_dict(self):
        """Metadata should be convertible to dictionary."""
        result = self.parser.parse(
            content="# Decision\nAuthor: Test\nDate: 2024-01-01",
            filename="ADR-001.md"
        )
        
        metadata = result.to_metadata()
        
        assert isinstance(metadata, dict)
        assert "decision_id" in metadata
        assert "decision_author" in metadata


# =============================================================================
# FEATURE 3: KNOWLEDGE GAP DETECTION TESTS
# =============================================================================

class TestKnowledgeGapDetector:
    """Tests for knowledge gap detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = KnowledgeGapDetector(
            confidence_threshold=0.6,
            min_relevant_docs=2,
            similarity_threshold=0.5,
        )
    
    def test_detects_gap_with_no_documents(self):
        """Should detect gap when no documents are retrieved."""
        result = self.detector.evaluate(
            query="What is our vacation policy?",
            documents_with_scores=[],
            log_gap=False,
        )
        
        assert result.gap_detected is True
        assert result.has_sufficient_knowledge is False
        assert result.gap_severity in [GapSeverity.HIGH, GapSeverity.CRITICAL]
    
    def test_detects_gap_with_low_scores(self):
        """Should detect gap when similarity scores are too low."""
        doc = Document(page_content="Unrelated content", metadata={"knowledge_type": "explicit"})
        
        result = self.detector.evaluate(
            query="Specific technical question",
            documents_with_scores=[(doc, 0.2)],  # Low score
            log_gap=False,
        )
        
        assert result.gap_detected is True
        assert result.confidence_score < 0.6
    
    def test_passes_with_good_documents(self):
        """Should pass when sufficient relevant documents exist."""
        docs = [
            Document(page_content="Relevant content 1", metadata={"knowledge_type": "explicit"}),
            Document(page_content="Relevant content 2", metadata={"knowledge_type": "explicit"}),
            Document(page_content="Relevant content 3", metadata={"knowledge_type": "explicit"}),
        ]
        docs_with_scores = [(doc, 0.8) for doc in docs]
        
        result = self.detector.evaluate(
            query="What is our deployment process?",
            documents_with_scores=docs_with_scores,
            log_gap=False,
        )
        
        assert result.has_sufficient_knowledge is True
        assert result.gap_detected is False
    
    def test_provides_safe_response_for_gap(self):
        """Should provide safe response when gap detected."""
        result = self.detector.evaluate(
            query="Unknown topic",
            documents_with_scores=[],
            log_gap=False,
        )
        
        assert result.safe_response is not None
        assert "knowledge base" in result.safe_response.lower()
    
    def test_tracks_knowledge_type_coverage(self):
        """Should track which knowledge types are present."""
        docs = [
            Document(page_content="Tacit content", metadata={"knowledge_type": "tacit"}),
            Document(page_content="Decision content", metadata={"knowledge_type": "decision"}),
        ]
        docs_with_scores = [(doc, 0.8) for doc in docs]
        
        result = self.detector.evaluate(
            query="Test query",
            documents_with_scores=docs_with_scores,
            log_gap=False,
        )
        
        assert result.tacit_coverage is True
        assert result.decision_coverage is True


class TestKnowledgeGapLogger:
    """Tests for knowledge gap logging."""
    
    def test_logs_gap_to_file(self, tmp_path):
        """Should log gaps to file."""
        logger = KnowledgeGapLogger(log_dir=str(tmp_path))
        
        gap_result = GapDetectionResult(
            has_sufficient_knowledge=False,
            confidence_score=0.3,
            gap_detected=True,
            gap_severity=GapSeverity.HIGH,
            gap_reason="No relevant documents",
            query="Test query",
        )
        
        logger.log(gap_result)
        
        # Verify log file exists and contains entry
        assert logger.log_file.exists()
        
        gaps = logger.get_recent_gaps(limit=10)
        assert len(gaps) == 1
        assert gaps[0]["query"] == "Test query"
    
    def test_does_not_log_non_gaps(self, tmp_path):
        """Should not log when no gap detected."""
        logger = KnowledgeGapLogger(log_dir=str(tmp_path))
        
        gap_result = GapDetectionResult(
            has_sufficient_knowledge=True,
            confidence_score=0.9,
            gap_detected=False,
            query="Test query",
        )
        
        logger.log(gap_result)
        
        gaps = logger.get_recent_gaps(limit=10)
        assert len(gaps) == 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestKnowledgeValidator:
    """Tests for knowledge validation layer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KnowledgeValidator(strict_mode=False)
    
    def test_validates_tacit_query_with_tacit_docs(self):
        """Should validate tacit query when tacit documents available."""
        docs = [
            Document(
                page_content="Lesson learned: avoid overcomplicating",
                metadata={"knowledge_type": "tacit"}
            ),
        ]
        docs_with_scores = [(doc, 0.8) for doc in docs]
        
        result = self.validator.validate(
            query="What mistakes should I avoid?",
            documents_with_scores=docs_with_scores,
        )
        
        assert result.query_type == "tacit"
        assert result.has_tacit_match is True
    
    def test_validates_decision_query_with_decision_docs(self):
        """Should validate decision query when decision documents available."""
        docs = [
            Document(
                page_content="Decision: Use Redis. Rationale: Performance.",
                metadata={"knowledge_type": "decision"}
            ),
        ]
        docs_with_scores = [(doc, 0.8) for doc in docs]
        
        result = self.validator.validate(
            query="Why did we choose Redis?",
            documents_with_scores=docs_with_scores,
        )
        
        assert result.query_type == "decision"
        assert result.has_decision_match is True
    
    def test_generates_guidance_for_response(self):
        """Should generate response guidance."""
        docs = [
            Document(
                page_content="Some content",
                metadata={"knowledge_type": "explicit"}
            ),
        ]
        docs_with_scores = [(doc, 0.8) for doc in docs]
        
        result = self.validator.validate(
            query="General question",
            documents_with_scores=docs_with_scores,
        )
        
        assert result.response_guidance is not None


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_classify_document_function(self):
        """Test the classify_document convenience function."""
        result = classify_document(
            filename="exit_interview.txt",
            content="Lessons from my experience..."
        )
        
        assert isinstance(result, ClassificationResult)
        assert result.knowledge_type == KnowledgeType.TACIT
    
    def test_parse_decision_document_function(self):
        """Test the parse_decision_document convenience function."""
        result = parse_decision_document(
            content="# ADR-001: Use Redis\nAuthor: John\nDate: 2024-01-01",
            filename="ADR-001.md"
        )
        
        assert isinstance(result, DecisionMetadata)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
