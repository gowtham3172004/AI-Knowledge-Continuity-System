"""
Knowledge Gap Detection Module for AI Knowledge Continuity System.

This module implements Feature 3: Knowledge Gap Detection by providing
mechanisms to detect when organizational knowledge is insufficient to
answer a query confidently. It prevents hallucinations by flagging
low-confidence scenarios and logging knowledge gaps for improvement.

Key capabilities:
- Retrieval confidence evaluation based on similarity scores
- Gap detection using configurable thresholds
- Safe response generation when knowledge is insufficient
- Knowledge gap logging for organizational learning
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.documents import Document

from config.settings import get_settings
from core.logger import get_logger

logger = get_logger(__name__)


class GapSeverity(str, Enum):
    """Severity levels for knowledge gaps."""
    LOW = "low"       # Partial information available
    MEDIUM = "medium"  # Significant gaps in knowledge
    HIGH = "high"      # No relevant information found
    CRITICAL = "critical"  # Query about important topic with no coverage


@dataclass
class GapDetectionResult:
    """
    Result of knowledge gap detection analysis.
    
    This encapsulates whether a query can be answered confidently
    and provides detailed information for gap logging and response.
    """
    # Core detection result
    has_sufficient_knowledge: bool
    confidence_score: float  # 0.0 to 1.0
    
    # Gap details (if insufficient knowledge)
    gap_detected: bool = False
    gap_severity: GapSeverity = GapSeverity.LOW
    gap_reason: str = ""
    
    # Analysis details
    num_relevant_documents: int = 0
    avg_similarity_score: float = 0.0
    max_similarity_score: float = 0.0
    min_similarity_score: float = 0.0
    
    # Knowledge type coverage
    tacit_coverage: bool = False
    decision_coverage: bool = False
    explicit_coverage: bool = False
    
    # Safe response (when gap detected)
    safe_response: Optional[str] = None
    
    # Metadata
    query: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    department: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and serialization."""
        return {
            "has_sufficient_knowledge": self.has_sufficient_knowledge,
            "confidence_score": self.confidence_score,
            "gap_detected": self.gap_detected,
            "gap_severity": self.gap_severity.value if self.gap_severity else None,
            "gap_reason": self.gap_reason,
            "num_relevant_documents": self.num_relevant_documents,
            "avg_similarity_score": self.avg_similarity_score,
            "max_similarity_score": self.max_similarity_score,
            "tacit_coverage": self.tacit_coverage,
            "decision_coverage": self.decision_coverage,
            "explicit_coverage": self.explicit_coverage,
            "query": self.query,
            "timestamp": self.timestamp,
            "department": self.department,
        }


class KnowledgeGapDetector:
    """
    Detects knowledge gaps in retrieval results.
    
    This class analyzes retrieval results to determine if the organizational
    knowledge base has sufficient information to answer a query confidently.
    When gaps are detected, it provides safe responses and logs the gaps.
    
    Configuration:
    - confidence_threshold: Minimum confidence to proceed with generation
    - min_relevant_docs: Minimum number of relevant documents required
    - similarity_threshold: Minimum similarity score to consider relevant
    
    Example:
        >>> detector = KnowledgeGapDetector()
        >>> result = detector.evaluate(query, documents_with_scores)
        >>> if result.gap_detected:
        ...     return result.safe_response
    """
    
    # Default safe response templates
    SAFE_RESPONSES = {
        GapSeverity.LOW: (
            "I found some related information, but I cannot provide a complete answer "
            "with high confidence. The available information may be partial or outdated. "
            "Consider consulting with domain experts for a comprehensive response."
        ),
        GapSeverity.MEDIUM: (
            "This information is not sufficiently documented in the organizational "
            "knowledge base. While some related documents exist, they don't directly "
            "address your question. This has been logged as a knowledge gap."
        ),
        GapSeverity.HIGH: (
            "I don't have sufficient information in the knowledge base to answer "
            "this question. No relevant documents were found that address this topic. "
            "This gap has been logged for future knowledge improvement."
        ),
        GapSeverity.CRITICAL: (
            "IMPORTANT: No organizational knowledge exists for this query. "
            "This appears to be a critical knowledge gap. "
            "Please document this information and consult with relevant stakeholders."
        ),
    }
    
    def __init__(
        self,
        confidence_threshold: Optional[float] = None,
        min_relevant_docs: int = 2,
        similarity_threshold: Optional[float] = None,
        gap_logger: Optional['KnowledgeGapLogger'] = None,
    ):
        """
        Initialize the knowledge gap detector.
        
        Args:
            confidence_threshold: Minimum confidence score (0-1) to proceed.
                                Defaults to settings.KNOWLEDGE_GAP_THRESHOLD.
            min_relevant_docs: Minimum documents needed for confident answer.
            similarity_threshold: Minimum similarity for relevance.
                                Defaults to settings.RETRIEVER_SCORE_THRESHOLD.
            gap_logger: Optional gap logger instance for persistent logging.
        """
        self.settings = get_settings()
        
        # Use settings values with fallbacks
        self.confidence_threshold = confidence_threshold or getattr(
            self.settings, 'KNOWLEDGE_GAP_THRESHOLD', 0.6
        )
        self.min_relevant_docs = min_relevant_docs
        self.similarity_threshold = similarity_threshold or self.settings.RETRIEVER_SCORE_THRESHOLD
        
        # Initialize gap logger
        self.gap_logger = gap_logger or KnowledgeGapLogger()
        
        logger.info(
            f"KnowledgeGapDetector initialized: "
            f"confidence_threshold={self.confidence_threshold}, "
            f"min_docs={self.min_relevant_docs}, "
            f"similarity_threshold={self.similarity_threshold}"
        )
    
    def evaluate(
        self,
        query: str,
        documents_with_scores: List[Tuple[Document, float]],
        department: Optional[str] = None,
        log_gap: bool = True,
    ) -> GapDetectionResult:
        """
        Evaluate retrieval results for knowledge gaps.
        
        This method analyzes the retrieved documents and their similarity
        scores to determine if sufficient knowledge exists to answer the query.
        
        Args:
            query: The user's question.
            documents_with_scores: List of (document, similarity_score) tuples.
            department: Optional department context for logging.
            log_gap: Whether to log detected gaps.
            
        Returns:
            GapDetectionResult with detailed analysis.
        """
        # Handle empty results
        if not documents_with_scores:
            result = self._create_gap_result(
                query=query,
                gap_severity=GapSeverity.HIGH,
                reason="No documents retrieved from knowledge base",
                department=department,
            )
            if log_gap:
                self.gap_logger.log(result)
            return result
        
        # Calculate similarity statistics
        scores = [score for _, score in documents_with_scores]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        # Count relevant documents (above threshold)
        relevant_docs = [
            (doc, score) for doc, score in documents_with_scores
            if score >= self.similarity_threshold
        ]
        num_relevant = len(relevant_docs)
        
        # Analyze knowledge type coverage
        tacit_coverage = any(
            doc.metadata.get("knowledge_type") == "tacit"
            for doc, _ in relevant_docs
        )
        decision_coverage = any(
            doc.metadata.get("knowledge_type") == "decision"
            for doc, _ in relevant_docs
        )
        explicit_coverage = any(
            doc.metadata.get("knowledge_type") == "explicit"
            for doc, _ in relevant_docs
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(
            num_relevant=num_relevant,
            avg_score=avg_score,
            max_score=max_score,
            total_docs=len(documents_with_scores),
        )
        
        # Determine if knowledge is sufficient
        has_sufficient = confidence >= self.confidence_threshold
        
        # Create result
        if has_sufficient:
            result = GapDetectionResult(
                has_sufficient_knowledge=True,
                confidence_score=confidence,
                gap_detected=False,
                num_relevant_documents=num_relevant,
                avg_similarity_score=avg_score,
                max_similarity_score=max_score,
                min_similarity_score=min_score,
                tacit_coverage=tacit_coverage,
                decision_coverage=decision_coverage,
                explicit_coverage=explicit_coverage,
                query=query,
                department=department,
            )
        else:
            # Determine gap severity
            severity = self._determine_severity(
                confidence=confidence,
                num_relevant=num_relevant,
                max_score=max_score,
            )
            
            reason = self._generate_gap_reason(
                confidence=confidence,
                num_relevant=num_relevant,
                max_score=max_score,
            )
            
            result = GapDetectionResult(
                has_sufficient_knowledge=False,
                confidence_score=confidence,
                gap_detected=True,
                gap_severity=severity,
                gap_reason=reason,
                num_relevant_documents=num_relevant,
                avg_similarity_score=avg_score,
                max_similarity_score=max_score,
                min_similarity_score=min_score,
                tacit_coverage=tacit_coverage,
                decision_coverage=decision_coverage,
                explicit_coverage=explicit_coverage,
                safe_response=self.SAFE_RESPONSES[severity],
                query=query,
                department=department,
            )
            
            if log_gap:
                self.gap_logger.log(result)
        
        logger.debug(
            f"Gap detection for '{query[:50]}...': "
            f"sufficient={has_sufficient}, confidence={confidence:.2f}"
        )
        
        return result
    
    def _calculate_confidence(
        self,
        num_relevant: int,
        avg_score: float,
        max_score: float,
        total_docs: int,
    ) -> float:
        """
        Calculate overall confidence score.
        
        Confidence is based on:
        - Number of relevant documents (40%)
        - Average similarity score (30%)
        - Maximum similarity score (30%)
        """
        # Document count factor (0-1)
        doc_factor = min(1.0, num_relevant / self.min_relevant_docs)
        
        # Average score factor (already 0-1)
        avg_factor = avg_score
        
        # Max score factor (already 0-1)
        max_factor = max_score
        
        # Weighted combination
        confidence = (
            0.4 * doc_factor +
            0.3 * avg_factor +
            0.3 * max_factor
        )
        
        return round(confidence, 3)
    
    def _determine_severity(
        self,
        confidence: float,
        num_relevant: int,
        max_score: float,
    ) -> GapSeverity:
        """Determine the severity level of a knowledge gap."""
        if num_relevant == 0 and max_score < 0.3:
            return GapSeverity.HIGH
        elif num_relevant == 0:
            return GapSeverity.MEDIUM
        elif confidence < 0.3:
            return GapSeverity.HIGH
        elif confidence < 0.5:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _generate_gap_reason(
        self,
        confidence: float,
        num_relevant: int,
        max_score: float,
    ) -> str:
        """Generate a human-readable reason for the gap."""
        reasons = []
        
        if num_relevant < self.min_relevant_docs:
            reasons.append(
                f"Only {num_relevant} relevant document(s) found "
                f"(minimum {self.min_relevant_docs} required)"
            )
        
        if max_score < self.similarity_threshold:
            reasons.append(
                f"Best similarity score ({max_score:.2f}) below threshold "
                f"({self.similarity_threshold})"
            )
        
        if confidence < self.confidence_threshold:
            reasons.append(
                f"Overall confidence ({confidence:.2f}) below threshold "
                f"({self.confidence_threshold})"
            )
        
        return "; ".join(reasons) if reasons else "Insufficient knowledge coverage"
    
    def _create_gap_result(
        self,
        query: str,
        gap_severity: GapSeverity,
        reason: str,
        department: Optional[str] = None,
    ) -> GapDetectionResult:
        """Create a gap result for the case of no documents."""
        return GapDetectionResult(
            has_sufficient_knowledge=False,
            confidence_score=0.0,
            gap_detected=True,
            gap_severity=gap_severity,
            gap_reason=reason,
            num_relevant_documents=0,
            avg_similarity_score=0.0,
            max_similarity_score=0.0,
            min_similarity_score=0.0,
            safe_response=self.SAFE_RESPONSES[gap_severity],
            query=query,
            department=department,
        )


class KnowledgeGapLogger:
    """
    Logs knowledge gaps for organizational learning and improvement.
    
    Gaps are logged to a JSON file for analysis and can be used to:
    - Identify frequently asked questions with no documentation
    - Prioritize knowledge documentation efforts
    - Track knowledge base improvement over time
    
    Example:
        >>> logger = KnowledgeGapLogger()
        >>> logger.log(gap_result)
        >>> gaps = logger.get_recent_gaps(limit=10)
    """
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_filename: str = "knowledge_gaps.jsonl",
    ):
        """
        Initialize the gap logger.
        
        Args:
            log_dir: Directory for gap logs. Defaults to 'logs'.
            log_filename: Name of the log file.
        """
        self.log_dir = Path(log_dir or "logs")
        self.log_file = self.log_dir / log_filename
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"KnowledgeGapLogger initialized: {self.log_file}")
    
    def log(self, gap_result: GapDetectionResult) -> None:
        """
        Log a knowledge gap to persistent storage.
        
        Args:
            gap_result: The gap detection result to log.
        """
        if not gap_result.gap_detected:
            return  # Don't log non-gaps
        
        try:
            log_entry = {
                "timestamp": gap_result.timestamp,
                "query": gap_result.query,
                "confidence_score": gap_result.confidence_score,
                "gap_severity": gap_result.gap_severity.value,
                "gap_reason": gap_result.gap_reason,
                "num_relevant_documents": gap_result.num_relevant_documents,
                "avg_similarity_score": gap_result.avg_similarity_score,
                "department": gap_result.department,
            }
            
            # Append to JSONL file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            logger.info(
                f"Knowledge gap logged: severity={gap_result.gap_severity.value}, "
                f"query='{gap_result.query[:50]}...'"
            )
            
        except Exception as e:
            logger.error(f"Failed to log knowledge gap: {e}")
    
    def get_recent_gaps(
        self,
        limit: int = 100,
        severity: Optional[GapSeverity] = None,
        department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent knowledge gaps from the log.
        
        Args:
            limit: Maximum number of gaps to return.
            severity: Filter by severity level.
            department: Filter by department.
            
        Returns:
            List of gap log entries.
        """
        if not self.log_file.exists():
            return []
        
        gaps = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if severity and entry.get("gap_severity") != severity.value:
                            continue
                        if department and entry.get("department") != department:
                            continue
                        
                        gaps.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent first
            gaps.reverse()
            return gaps[:limit]
            
        except Exception as e:
            logger.error(f"Failed to read knowledge gaps: {e}")
            return []
    
    def get_gap_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged knowledge gaps.
        
        Returns:
            Dictionary with gap statistics.
        """
        gaps = self.get_recent_gaps(limit=10000)
        
        if not gaps:
            return {"total_gaps": 0}
        
        # Count by severity
        severity_counts = {}
        for gap in gaps:
            severity = gap.get("gap_severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by department
        dept_counts = {}
        for gap in gaps:
            dept = gap.get("department") or "unknown"
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        # Calculate averages
        avg_confidence = sum(g.get("confidence_score", 0) for g in gaps) / len(gaps)
        
        return {
            "total_gaps": len(gaps),
            "by_severity": severity_counts,
            "by_department": dept_counts,
            "avg_confidence": round(avg_confidence, 3),
            "earliest": gaps[-1].get("timestamp") if gaps else None,
            "latest": gaps[0].get("timestamp") if gaps else None,
        }
    
    def clear_old_logs(self, days: int = 90) -> int:
        """
        Clear log entries older than specified days.
        
        Args:
            days: Number of days to retain.
            
        Returns:
            Number of entries removed.
        """
        if not self.log_file.exists():
            return 0
        
        cutoff = datetime.now().isoformat()[:10]  # Simplified: compare dates
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        kept_entries = []
        removed_count = 0
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_date = datetime.fromisoformat(
                            entry.get("timestamp", "2000-01-01")[:19]
                        )
                        
                        if entry_date >= cutoff_date:
                            kept_entries.append(line)
                        else:
                            removed_count += 1
                    except (json.JSONDecodeError, ValueError):
                        kept_entries.append(line)  # Keep malformed entries
            
            # Rewrite file with kept entries
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.writelines(kept_entries)
            
            logger.info(f"Cleared {removed_count} old gap log entries")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to clear old logs: {e}")
            return 0
