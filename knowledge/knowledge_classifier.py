"""
Knowledge Classification Module for AI Knowledge Continuity System.

This module provides deterministic classification of organizational documents
into knowledge types: explicit, tacit, and decision. Classification is based
on filename patterns, path heuristics, and content analysis.

This supports Feature 1: Tacit Knowledge Extraction by enabling the system
to identify and prioritize experiential, lessons-learned content.
"""

import re
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

from core.logger import get_logger

logger = get_logger(__name__)


class KnowledgeType(str, Enum):
    """
    Enumeration of knowledge types in the organization.
    
    - EXPLICIT: Formal documentation, procedures, technical docs
    - TACIT: Lessons learned, pitfalls, best practices, exit interviews
    - DECISION: Architecture decisions, rationale, trade-offs
    """
    EXPLICIT = "explicit"
    TACIT = "tacit"
    DECISION = "decision"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class ClassificationResult:
    """Result of knowledge classification."""
    knowledge_type: KnowledgeType
    confidence: float  # 0.0 to 1.0
    classification_reason: str
    tacit_indicators: List[str] = field(default_factory=list)
    decision_indicators: List[str] = field(default_factory=list)
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dictionary for document enrichment."""
        return {
            "knowledge_type": str(self.knowledge_type),
            "knowledge_confidence": self.confidence,
            "classification_reason": self.classification_reason,
            "tacit_indicators": self.tacit_indicators,
            "decision_indicators": self.decision_indicators,
        }


class KnowledgeClassifier:
    """
    Classifies documents into knowledge types using deterministic heuristics.
    
    Classification Strategy:
    1. Filename pattern matching (highest priority)
    2. Path-based heuristics
    3. Content keyword analysis
    
    This approach is deterministic and explainable, avoiding LLM-based
    classification which could introduce hallucination risks.
    
    Example:
        >>> classifier = KnowledgeClassifier()
        >>> result = classifier.classify(filename="exit_interview.txt", content="...")
        >>> print(result.knowledge_type)  # KnowledgeType.TACIT
    """
    
    # Filename patterns for tacit knowledge (lessons, experience, pitfalls)
    TACIT_FILENAME_PATTERNS = [
        r"exit[_\-\s]*(interview|knowledge|transfer)?",
        r"lessons[_\-\s]*(learned)?",
        r"postmortem",
        r"post[_\-\s]mortem",
        r"retrospective",
        r"retro",
        r"pitfall",
        r"gotcha",
        r"tips?[_\-\s]*(and)?[_\-\s]*tricks?",
        r"best[_\-\s]practices?",
        r"do[_\-\s]*(s)?[_\-\s]*(and)?[_\-\s]*don['\"]?t[_\-\s]*(s)?",
        r"avoid",
        r"mistake",
        r"war[_\-\s]stories?",
        r"handover",
        r"hand[_\-\s]over",
        r"knowledge[_\-\s]transfer",
        r"onboarding[_\-\s]notes?",
    ]
    
    # Filename patterns for decision documents
    DECISION_FILENAME_PATTERNS = [
        r"adr[_\-\s]?\d*",  # ADR, ADR-001
        r"architecture[_\-\s]decision",
        r"decision[_\-\s]record",
        r"design[_\-\s]doc(ument)?",
        r"tech[_\-\s]spec",
        r"technical[_\-\s]specification",
        r"rfc[_\-\s]?\d*",  # RFC, RFC-001
        r"proposal",
        r"rationale",
        r"trade[_\-\s]off",
        r"meeting[_\-\s]notes?",  # Often contain decision context
        r"system[_\-\s]design",
        r"tech(nology)?[_\-\s]stack",
    ]
    
    # Content keywords for tacit knowledge
    TACIT_CONTENT_KEYWORDS = [
        "lesson learned",
        "lessons learned",
        "we learned",
        "i learned",
        "mistake",
        "pitfall",
        "gotcha",
        "tip",
        "trick",
        "avoid",
        "don't",
        "do not",
        "never",
        "always remember",
        "best practice",
        "recommendation",
        "insight",
        "hindsight",
        "looking back",
        "if i had to do it again",
        "pro tip",
        "word of caution",
        "common pitfall",
        "watch out",
        "be careful",
        "important to note",
        "key insight",
        "experience taught",
        "in my experience",
        "over the years",
        "hard way",
    ]
    
    # Content keywords for decision documents
    DECISION_CONTENT_KEYWORDS = [
        "decision",
        "decided",
        "rationale",
        "trade-off",
        "tradeoff",
        "trade off",
        "alternative",
        "option",
        "considered",
        "chose",
        "selected",
        "rejected",
        "why we",
        "reason for",
        "context",
        "consequence",
        "outcome",
        "impact",
        "pros and cons",
        "pros:",
        "cons:",
        "benefits",
        "drawbacks",
        "adr",
        "architecture decision",
    ]
    
    # Path components suggesting tacit knowledge
    TACIT_PATH_COMPONENTS = [
        "lessons",
        "lessons_learned",
        "exit",
        "handover",
        "knowledge_transfer",
        "postmortems",
        "retrospectives",
        "onboarding",
    ]
    
    # Path components suggesting decision documents
    DECISION_PATH_COMPONENTS = [
        "decisions",
        "adr",
        "adrs",
        "design_docs",
        "rfcs",
        "proposals",
        "architecture",
        "specs",
        "specifications",
    ]
    
    def __init__(
        self,
        tacit_filename_patterns: Optional[List[str]] = None,
        decision_filename_patterns: Optional[List[str]] = None,
        tacit_content_keywords: Optional[List[str]] = None,
        decision_content_keywords: Optional[List[str]] = None,
        content_keyword_threshold: int = 3,
    ):
        """
        Initialize the knowledge classifier.
        
        Args:
            tacit_filename_patterns: Additional patterns for tacit knowledge files.
            decision_filename_patterns: Additional patterns for decision files.
            tacit_content_keywords: Additional keywords for tacit content.
            decision_content_keywords: Additional keywords for decision content.
            content_keyword_threshold: Minimum keywords to classify by content.
        """
        # Combine default and custom patterns
        self.tacit_filename_patterns = self.TACIT_FILENAME_PATTERNS.copy()
        if tacit_filename_patterns:
            self.tacit_filename_patterns.extend(tacit_filename_patterns)
        
        self.decision_filename_patterns = self.DECISION_FILENAME_PATTERNS.copy()
        if decision_filename_patterns:
            self.decision_filename_patterns.extend(decision_filename_patterns)
        
        # Combine default and custom keywords
        self.tacit_content_keywords = self.TACIT_CONTENT_KEYWORDS.copy()
        if tacit_content_keywords:
            self.tacit_content_keywords.extend(tacit_content_keywords)
        
        self.decision_content_keywords = self.DECISION_CONTENT_KEYWORDS.copy()
        if decision_content_keywords:
            self.decision_content_keywords.extend(decision_content_keywords)
        
        self.content_keyword_threshold = content_keyword_threshold
        
        # Compile regex patterns for efficiency
        self._tacit_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.tacit_filename_patterns
        ]
        self._decision_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.decision_filename_patterns
        ]
        
        logger.info("KnowledgeClassifier initialized")
    
    def classify(
        self,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        content: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify a document into a knowledge type.
        
        Classification priority:
        1. Filename pattern matching (most reliable)
        2. Path component matching
        3. Content keyword analysis (fallback)
        
        Args:
            filename: Name of the file.
            filepath: Full path to the file.
            content: Document content for keyword analysis.
            
        Returns:
            ClassificationResult with knowledge type and confidence.
        """
        # Track indicators found
        tacit_indicators: List[str] = []
        decision_indicators: List[str] = []
        
        # Phase 1: Filename pattern matching
        if filename:
            filename_lower = filename.lower()
            
            # Check tacit patterns
            for pattern in self._tacit_patterns:
                if pattern.search(filename_lower):
                    tacit_indicators.append(f"filename_pattern:{pattern.pattern}")
            
            # Check decision patterns
            for pattern in self._decision_patterns:
                if pattern.search(filename_lower):
                    decision_indicators.append(f"filename_pattern:{pattern.pattern}")
        
        # Phase 2: Path component matching
        if filepath:
            path_parts = Path(filepath).parts
            path_lower = [p.lower() for p in path_parts]
            
            for component in self.TACIT_PATH_COMPONENTS:
                if any(component in p for p in path_lower):
                    tacit_indicators.append(f"path_component:{component}")
            
            for component in self.DECISION_PATH_COMPONENTS:
                if any(component in p for p in path_lower):
                    decision_indicators.append(f"path_component:{component}")
        
        # Phase 3: Content keyword analysis
        if content:
            content_lower = content.lower()
            
            for keyword in self.tacit_content_keywords:
                if keyword.lower() in content_lower:
                    tacit_indicators.append(f"content_keyword:{keyword}")
            
            for keyword in self.decision_content_keywords:
                if keyword.lower() in content_lower:
                    decision_indicators.append(f"content_keyword:{keyword}")
        
        # Determine classification based on indicators
        return self._determine_classification(
            tacit_indicators=tacit_indicators,
            decision_indicators=decision_indicators,
        )
    
    def _determine_classification(
        self,
        tacit_indicators: List[str],
        decision_indicators: List[str],
    ) -> ClassificationResult:
        """
        Determine the final classification based on collected indicators.
        
        Priority:
        1. Filename/path indicators (weight: 3x)
        2. Content indicators (weight: 1x)
        
        Returns:
            ClassificationResult with the determined type.
        """
        # Calculate weighted scores
        def calculate_score(indicators: List[str]) -> float:
            score = 0.0
            for indicator in indicators:
                if indicator.startswith("filename_pattern:"):
                    score += 3.0  # High confidence for filename match
                elif indicator.startswith("path_component:"):
                    score += 2.0  # Medium-high confidence for path match
                elif indicator.startswith("content_keyword:"):
                    score += 1.0  # Lower confidence for content match
            return score
        
        tacit_score = calculate_score(tacit_indicators)
        decision_score = calculate_score(decision_indicators)
        
        # Determine knowledge type
        if tacit_score >= 3.0 and tacit_score > decision_score:
            knowledge_type = KnowledgeType.TACIT
            confidence = min(1.0, tacit_score / 10.0)  # Normalize to 0-1
            reason = f"Tacit knowledge indicators found (score: {tacit_score:.1f})"
        elif decision_score >= 3.0 and decision_score >= tacit_score:
            knowledge_type = KnowledgeType.DECISION
            confidence = min(1.0, decision_score / 10.0)
            reason = f"Decision indicators found (score: {decision_score:.1f})"
        else:
            # Default to explicit knowledge
            knowledge_type = KnowledgeType.EXPLICIT
            confidence = 0.8  # Default confidence for explicit
            reason = "No strong tacit/decision indicators; classified as explicit"
        
        return ClassificationResult(
            knowledge_type=knowledge_type,
            confidence=confidence,
            classification_reason=reason,
            tacit_indicators=tacit_indicators,
            decision_indicators=decision_indicators,
        )
    
    def is_tacit_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Determine if a query is asking for tacit knowledge.
        
        Tacit queries typically ask about:
        - Mistakes to avoid
        - Best practices
        - Lessons learned
        - Recommendations
        
        Args:
            query: The user's query string.
            
        Returns:
            Tuple of (is_tacit_query, matched_indicators).
        """
        tacit_query_patterns = [
            r"(what|any)\s*(are\s*)?(the\s*)?(common\s*)?(mistake|pitfall|gotcha)",
            r"(lesson|tip|trick|insight|recommendation)",
            r"(best\s*practice|avoid|don['\"]?t)",
            r"(what\s*(should|to)\s*avoid)",
            r"(thing|something)\s*to\s*(watch|look)\s*(out|for)",
            r"(advice|suggestion|recommend)",
            r"(experience|experienc)",
            r"what\s*(did|have)\s*(you|they|we)\s*learn",
        ]
        
        query_lower = query.lower()
        matched = []
        
        for pattern in tacit_query_patterns:
            if re.search(pattern, query_lower):
                matched.append(pattern)
        
        return len(matched) > 0, matched
    
    def is_decision_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Determine if a query is asking about decisions.
        
        Decision queries typically ask about:
        - Why something was chosen
        - Rationale behind decisions
        - Trade-offs considered
        - Alternatives evaluated
        
        Args:
            query: The user's query string.
            
        Returns:
            Tuple of (is_decision_query, matched_indicators).
        """
        decision_query_patterns = [
            r"why\s*(did|do|was|were|is)\s*(we|they|you|it)?",
            r"(what|why)\s*(was|is)\s*(the\s*)?(rationale|reason|decision)",
            r"(who|when)\s*(made|decided|chose)",
            r"(trade[- ]?off|alternative|option)\s*(consider|evaluat)",
            r"(decid|chose|select|pick)\s*(to|between)",
            r"(reason|rationale)\s*(for|behind)",
            r"(how|why)\s*(come|did)\s*we\s*(decide|choose|end up)",
            r"what\s*(led|drove)\s*(to|us)",
        ]
        
        query_lower = query.lower()
        matched = []
        
        for pattern in decision_query_patterns:
            if re.search(pattern, query_lower):
                matched.append(pattern)
        
        return len(matched) > 0, matched


# Module-level convenience function
def classify_document(
    filename: Optional[str] = None,
    filepath: Optional[str] = None,
    content: Optional[str] = None,
) -> ClassificationResult:
    """
    Classify a document into a knowledge type.
    
    Convenience function that uses a default classifier instance.
    For production use with custom settings, instantiate KnowledgeClassifier directly.
    
    Args:
        filename: Name of the file.
        filepath: Full path to the file.
        content: Document content for keyword analysis.
        
    Returns:
        ClassificationResult with knowledge type and confidence.
    """
    classifier = KnowledgeClassifier()
    return classifier.classify(filename=filename, filepath=filepath, content=content)
