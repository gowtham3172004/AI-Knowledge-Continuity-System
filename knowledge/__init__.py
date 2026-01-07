"""
Knowledge Management Module for AI Knowledge Continuity System.

This module provides enterprise-grade knowledge classification,
decision traceability, and knowledge gap detection capabilities.
"""

from knowledge.knowledge_classifier import (
    KnowledgeType,
    KnowledgeClassifier,
    classify_document,
)
from knowledge.decision_parser import (
    DecisionMetadata,
    DecisionParser,
    parse_decision_document,
)
from knowledge.gap_detector import (
    GapDetectionResult,
    KnowledgeGapDetector,
    KnowledgeGapLogger,
)
from knowledge.validator import (
    KnowledgeValidator,
    ValidationResult,
)

__all__ = [
    # Knowledge Classification
    "KnowledgeType",
    "KnowledgeClassifier",
    "classify_document",
    # Decision Parsing
    "DecisionMetadata",
    "DecisionParser",
    "parse_decision_document",
    # Gap Detection
    "GapDetectionResult",
    "KnowledgeGapDetector",
    "KnowledgeGapLogger",
    # Validation
    "KnowledgeValidator",
    "ValidationResult",
]
