"""
Evaluation Metrics Module for AI Knowledge Continuity System.

This module provides comprehensive evaluation metrics for RAG systems
including relevance, faithfulness, and answer quality assessments.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from langchain_core.documents import Document

from config.settings import get_settings
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationResult:
    """
    Container for evaluation results.
    
    Attributes:
        query: The original query.
        answer: The generated answer.
        relevance_score: How relevant the answer is to the query (0-1).
        faithfulness_score: How faithful the answer is to sources (0-1).
        completeness_score: How complete the answer is (0-1).
        overall_score: Weighted average of all scores (0-1).
        details: Detailed breakdown of evaluation.
        timestamp: When the evaluation was performed.
    """
    query: str
    answer: str
    relevance_score: float
    faithfulness_score: float
    completeness_score: float
    overall_score: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "answer": self.answer[:200] + "..." if len(self.answer) > 200 else self.answer,
            "scores": {
                "relevance": round(self.relevance_score, 3),
                "faithfulness": round(self.faithfulness_score, 3),
                "completeness": round(self.completeness_score, 3),
                "overall": round(self.overall_score, 3),
            },
            "details": self.details,
            "timestamp": self.timestamp,
        }
    
    def is_acceptable(self, threshold: float = 0.6) -> bool:
        """Check if the evaluation meets the quality threshold."""
        return self.overall_score >= threshold


class RAGEvaluator:
    """
    Comprehensive RAG evaluation system.
    
    Provides multiple evaluation strategies:
    - Heuristic-based evaluation (fast, no LLM needed)
    - LLM-based evaluation (more accurate, requires LLM)
    - Ground truth comparison (if references available)
    
    Features:
    - Multiple scoring dimensions
    - Configurable weights
    - Batch evaluation support
    - Evaluation history tracking
    
    Example:
        >>> evaluator = RAGEvaluator()
        >>> result = evaluator.evaluate(
        ...     query="What is the deployment process?",
        ...     answer="The deployment process involves...",
        ...     source_documents=[doc1, doc2]
        ... )
        >>> print(f"Overall score: {result.overall_score}")
    """
    
    # Default weights for scoring dimensions
    DEFAULT_WEIGHTS = {
        "relevance": 0.4,
        "faithfulness": 0.4,
        "completeness": 0.2,
    }
    
    # Indicators of uncertainty/inability to answer
    UNCERTAINTY_PHRASES = [
        "i don't know",
        "i'm not sure",
        "i cannot answer",
        "no information",
        "not found",
        "don't have sufficient information",
        "cannot determine",
        "unclear from the context",
    ]
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        llm=None,
    ):
        """
        Initialize the evaluator.
        
        Args:
            weights: Custom weights for scoring dimensions.
            llm: Optional LLM for advanced evaluation.
        """
        self.settings = get_settings()
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._llm = llm
        
        # Normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        # Evaluation history
        self._history: List[EvaluationResult] = []
        
        logger.info("RAGEvaluator initialized")
    
    def set_llm(self, llm) -> None:
        """Set LLM for advanced evaluation."""
        self._llm = llm
    
    def evaluate(
        self,
        query: str,
        answer: str,
        source_documents: Optional[List[Document]] = None,
        ground_truth: Optional[str] = None,
        use_llm: bool = False,
    ) -> EvaluationResult:
        """
        Evaluate a RAG response.
        
        Args:
            query: The original query.
            answer: The generated answer.
            source_documents: Documents used to generate the answer.
            ground_truth: Optional ground truth answer for comparison.
            use_llm: Whether to use LLM for evaluation.
            
        Returns:
            EvaluationResult with scores and details.
        """
        logger.debug(f"Evaluating response for query: {query[:50]}...")
        
        # Calculate individual scores
        relevance = self._evaluate_relevance(query, answer, source_documents)
        faithfulness = self._evaluate_faithfulness(answer, source_documents)
        completeness = self._evaluate_completeness(query, answer)
        
        # If ground truth is provided, factor it in
        if ground_truth:
            ground_truth_score = self._compare_to_ground_truth(answer, ground_truth)
            # Adjust scores based on ground truth
            relevance = (relevance + ground_truth_score) / 2
        
        # Use LLM evaluation if requested and available
        if use_llm and self._llm:
            llm_scores = self._llm_evaluate(query, answer, source_documents)
            if llm_scores:
                # Blend heuristic and LLM scores
                relevance = (relevance + llm_scores.get("relevance", relevance)) / 2
                faithfulness = (faithfulness + llm_scores.get("faithfulness", faithfulness)) / 2
                completeness = (completeness + llm_scores.get("completeness", completeness)) / 2
        
        # Calculate overall score
        overall = (
            self.weights["relevance"] * relevance +
            self.weights["faithfulness"] * faithfulness +
            self.weights["completeness"] * completeness
        )
        
        # Create result
        result = EvaluationResult(
            query=query,
            answer=answer,
            relevance_score=relevance,
            faithfulness_score=faithfulness,
            completeness_score=completeness,
            overall_score=overall,
            details={
                "num_sources": len(source_documents) if source_documents else 0,
                "answer_length": len(answer),
                "has_ground_truth": ground_truth is not None,
                "used_llm": use_llm and self._llm is not None,
            },
        )
        
        # Store in history
        self._history.append(result)
        
        logger.debug(f"Evaluation complete: overall={overall:.3f}")
        return result
    
    def _evaluate_relevance(
        self,
        query: str,
        answer: str,
        source_documents: Optional[List[Document]],
    ) -> float:
        """
        Evaluate how relevant the answer is to the query.
        
        Uses keyword overlap and semantic similarity heuristics.
        """
        # Extract query keywords
        query_words = set(self._extract_keywords(query))
        answer_words = set(self._extract_keywords(answer))
        
        if not query_words:
            return 0.5  # Neutral score
        
        # Calculate keyword overlap
        overlap = len(query_words & answer_words)
        keyword_score = min(overlap / len(query_words), 1.0)
        
        # Check for uncertainty indicators
        answer_lower = answer.lower()
        is_uncertain = any(phrase in answer_lower for phrase in self.UNCERTAINTY_PHRASES)
        
        # If answer admits uncertainty, it's still relevant (honest response)
        if is_uncertain:
            return 0.7  # Moderate relevance for honest uncertainty
        
        # Check if answer seems to address the query topic
        query_topic_words = self._extract_topic_words(query)
        topic_addressed = any(word in answer_lower for word in query_topic_words)
        topic_score = 0.8 if topic_addressed else 0.3
        
        # Combine scores
        relevance = (keyword_score * 0.4 + topic_score * 0.6)
        
        return min(max(relevance, 0.0), 1.0)
    
    def _evaluate_faithfulness(
        self,
        answer: str,
        source_documents: Optional[List[Document]],
    ) -> float:
        """
        Evaluate how faithful the answer is to the source documents.
        
        Checks if claims in the answer can be traced to sources.
        """
        if not source_documents:
            # If no sources, check if answer admits this
            if any(phrase in answer.lower() for phrase in self.UNCERTAINTY_PHRASES):
                return 0.9  # Honest about lack of information
            return 0.3  # No sources to verify against
        
        # Combine source content
        source_content = " ".join([doc.page_content.lower() for doc in source_documents])
        
        # Extract key claims/statements from answer
        answer_sentences = self._split_sentences(answer)
        
        if not answer_sentences:
            return 0.5
        
        # Check each sentence for source support
        supported_count = 0
        for sentence in answer_sentences:
            # Extract key terms from sentence
            key_terms = self._extract_keywords(sentence)
            
            # Check if key terms appear in sources
            if key_terms:
                matches = sum(1 for term in key_terms if term.lower() in source_content)
                if matches >= len(key_terms) * 0.3:  # 30% term overlap
                    supported_count += 1
        
        faithfulness = supported_count / len(answer_sentences) if answer_sentences else 0.5
        
        return min(max(faithfulness, 0.0), 1.0)
    
    def _evaluate_completeness(
        self,
        query: str,
        answer: str,
    ) -> float:
        """
        Evaluate how complete the answer is.
        
        Considers answer length, structure, and query complexity.
        """
        # Check if answer is too short
        if len(answer.strip()) < 20:
            # Unless it's an appropriate short response
            if any(phrase in answer.lower() for phrase in self.UNCERTAINTY_PHRASES):
                return 0.7  # Acceptable to be short if uncertain
            return 0.2  # Too short otherwise
        
        # Check for structure (paragraphs, lists, etc.)
        has_structure = (
            "\n" in answer or
            ":" in answer or
            "-" in answer or
            "1." in answer
        )
        structure_score = 0.8 if has_structure else 0.5
        
        # Check answer length relative to query complexity
        query_complexity = len(self._extract_keywords(query))
        expected_length = query_complexity * 50  # Rough heuristic
        length_ratio = min(len(answer) / max(expected_length, 50), 2.0)
        length_score = min(length_ratio, 1.0)
        
        # Check for reasoning/explanation
        has_reasoning = any(
            indicator in answer.lower()
            for indicator in ["because", "therefore", "this means", "as a result", "the reason"]
        )
        reasoning_score = 0.8 if has_reasoning else 0.5
        
        # Combine scores
        completeness = (structure_score * 0.3 + length_score * 0.4 + reasoning_score * 0.3)
        
        return min(max(completeness, 0.0), 1.0)
    
    def _compare_to_ground_truth(
        self,
        answer: str,
        ground_truth: str,
    ) -> float:
        """Compare answer to ground truth using text similarity."""
        answer_words = set(self._extract_keywords(answer))
        truth_words = set(self._extract_keywords(ground_truth))
        
        if not truth_words:
            return 0.5
        
        # Calculate Jaccard similarity
        intersection = len(answer_words & truth_words)
        union = len(answer_words | truth_words)
        
        if union == 0:
            return 0.5
        
        return intersection / union
    
    def _llm_evaluate(
        self,
        query: str,
        answer: str,
        source_documents: Optional[List[Document]],
    ) -> Optional[Dict[str, float]]:
        """Use LLM to evaluate the response."""
        if not self._llm:
            return None
        
        try:
            sources_text = ""
            if source_documents:
                sources_text = "\n\n".join([
                    f"Source {i+1}: {doc.page_content[:500]}"
                    for i, doc in enumerate(source_documents[:3])
                ])
            
            prompt = f"""Evaluate the following RAG response on a scale of 0 to 1.

Query: {query}

Answer: {answer}

Sources Used:
{sources_text if sources_text else "No sources provided"}

Rate the following (respond with just the numbers, one per line):
1. Relevance (0-1): How relevant is the answer to the query?
2. Faithfulness (0-1): How well does the answer stick to the provided sources?
3. Completeness (0-1): How complete and thorough is the answer?

Scores (one per line):"""

            response = self._llm.invoke(prompt)
            
            # Parse scores from response
            if hasattr(response, 'content'):
                text = response.content
            else:
                text = str(response)
            
            # Extract numbers from response
            numbers = re.findall(r'(\d+\.?\d*)', text)
            
            if len(numbers) >= 3:
                return {
                    "relevance": float(numbers[0]),
                    "faithfulness": float(numbers[1]),
                    "completeness": float(numbers[2]),
                }
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed: {e}")
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'this',
            'that', 'with', 'they', 'from', 'what', 'which', 'there', 'their',
            'will', 'would', 'could', 'should', 'about', 'into', 'your', 'also',
            'how', 'when', 'where', 'why', 'who', 'does', 'did', 'done',
        }
        
        return [w for w in words if w not in stop_words]
    
    def _extract_topic_words(self, text: str) -> List[str]:
        """Extract main topic words from text."""
        keywords = self._extract_keywords(text)
        # Return first few keywords as likely topics
        return keywords[:5]
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def batch_evaluate(
        self,
        evaluations: List[Dict[str, Any]],
        **kwargs,
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple responses.
        
        Args:
            evaluations: List of dicts with 'query', 'answer', 'source_documents'.
            **kwargs: Additional arguments passed to evaluate().
            
        Returns:
            List of EvaluationResult objects.
        """
        results = []
        for item in evaluations:
            result = self.evaluate(
                query=item.get("query", ""),
                answer=item.get("answer", ""),
                source_documents=item.get("source_documents"),
                ground_truth=item.get("ground_truth"),
                **kwargs,
            )
            results.append(result)
        return results
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary statistics from evaluation history."""
        if not self._history:
            return {"count": 0}
        
        return {
            "count": len(self._history),
            "avg_relevance": sum(r.relevance_score for r in self._history) / len(self._history),
            "avg_faithfulness": sum(r.faithfulness_score for r in self._history) / len(self._history),
            "avg_completeness": sum(r.completeness_score for r in self._history) / len(self._history),
            "avg_overall": sum(r.overall_score for r in self._history) / len(self._history),
            "acceptable_rate": sum(1 for r in self._history if r.is_acceptable()) / len(self._history),
        }
    
    def clear_history(self) -> None:
        """Clear evaluation history."""
        self._history = []


# Convenience function
def evaluate_response(
    query: str,
    answer: str,
    source_documents: Optional[List[Document]] = None,
    **kwargs,
) -> EvaluationResult:
    """
    Convenience function to evaluate a single response.
    
    Args:
        query: The original query.
        answer: The generated answer.
        source_documents: Documents used for generation.
        **kwargs: Additional evaluation parameters.
        
    Returns:
        EvaluationResult with scores.
    """
    evaluator = RAGEvaluator()
    return evaluator.evaluate(
        query=query,
        answer=answer,
        source_documents=source_documents,
        **kwargs,
    )
