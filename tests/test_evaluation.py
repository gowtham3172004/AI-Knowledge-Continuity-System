"""
Tests for the evaluation metrics module.
"""

import pytest
from unittest.mock import MagicMock

from evaluation.metrics import RAGEvaluator, EvaluationResult, evaluate_response


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""
    
    def test_creation(self):
        """Test EvaluationResult creation."""
        result = EvaluationResult(
            query="Test query",
            answer="Test answer",
            relevance_score=0.8,
            faithfulness_score=0.7,
            completeness_score=0.9,
            overall_score=0.8,
        )
        
        assert result.relevance_score == 0.8
        assert result.overall_score == 0.8
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = EvaluationResult(
            query="Test query",
            answer="Test answer",
            relevance_score=0.8,
            faithfulness_score=0.7,
            completeness_score=0.9,
            overall_score=0.8,
        )
        
        data = result.to_dict()
        
        assert data["query"] == "Test query"
        assert data["scores"]["relevance"] == 0.8
    
    def test_is_acceptable(self):
        """Test acceptability threshold."""
        good_result = EvaluationResult(
            query="q", answer="a",
            relevance_score=0.8,
            faithfulness_score=0.8,
            completeness_score=0.8,
            overall_score=0.8,
        )
        
        bad_result = EvaluationResult(
            query="q", answer="a",
            relevance_score=0.3,
            faithfulness_score=0.3,
            completeness_score=0.3,
            overall_score=0.3,
        )
        
        assert good_result.is_acceptable(threshold=0.6)
        assert not bad_result.is_acceptable(threshold=0.6)


class TestRAGEvaluator:
    """Tests for RAGEvaluator class."""
    
    def test_init(self):
        """Test evaluator initialization."""
        evaluator = RAGEvaluator()
        
        assert "relevance" in evaluator.weights
        assert "faithfulness" in evaluator.weights
        assert "completeness" in evaluator.weights
    
    def test_custom_weights(self):
        """Test custom weights initialization."""
        weights = {"relevance": 0.5, "faithfulness": 0.3, "completeness": 0.2}
        evaluator = RAGEvaluator(weights=weights)
        
        # Weights should be normalized
        assert abs(sum(evaluator.weights.values()) - 1.0) < 0.01
    
    def test_evaluate_basic(self):
        """Test basic evaluation."""
        evaluator = RAGEvaluator()
        
        result = evaluator.evaluate(
            query="What is the deployment process?",
            answer="The deployment process involves CI/CD pipeline with automated tests.",
        )
        
        assert isinstance(result, EvaluationResult)
        assert 0 <= result.overall_score <= 1
    
    def test_evaluate_with_sources(self):
        """Test evaluation with source documents."""
        evaluator = RAGEvaluator()
        
        mock_doc = MagicMock()
        mock_doc.page_content = "The deployment process involves CI/CD pipeline."
        
        result = evaluator.evaluate(
            query="What is the deployment process?",
            answer="The deployment process involves CI/CD pipeline with automated tests.",
            source_documents=[mock_doc],
        )
        
        # Faithfulness should be higher with matching sources
        assert result.faithfulness_score > 0.5
    
    def test_evaluate_uncertain_answer(self):
        """Test evaluation of uncertain answers."""
        evaluator = RAGEvaluator()
        
        result = evaluator.evaluate(
            query="What is the secret project?",
            answer="I don't have sufficient information to answer this question.",
        )
        
        # Uncertain but honest answers should have decent relevance
        assert result.relevance_score >= 0.5
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        evaluator = RAGEvaluator()
        
        keywords = evaluator._extract_keywords(
            "What is the deployment process for production?"
        )
        
        assert "deployment" in keywords
        assert "process" in keywords
        assert "production" in keywords
        # Stop words should be removed
        assert "the" not in keywords
        assert "is" not in keywords
    
    def test_batch_evaluate(self):
        """Test batch evaluation."""
        evaluator = RAGEvaluator()
        
        evaluations = [
            {"query": "Question 1", "answer": "Answer 1"},
            {"query": "Question 2", "answer": "Answer 2"},
        ]
        
        results = evaluator.batch_evaluate(evaluations)
        
        assert len(results) == 2
        assert all(isinstance(r, EvaluationResult) for r in results)
    
    def test_evaluation_summary(self):
        """Test evaluation summary."""
        evaluator = RAGEvaluator()
        
        # Perform some evaluations
        evaluator.evaluate("Q1", "A1")
        evaluator.evaluate("Q2", "A2")
        
        summary = evaluator.get_evaluation_summary()
        
        assert summary["count"] == 2
        assert "avg_overall" in summary


class TestConvenienceFunction:
    """Tests for convenience function."""
    
    def test_evaluate_response(self):
        """Test the evaluate_response convenience function."""
        result = evaluate_response(
            query="What is the deployment process?",
            answer="The deployment uses CI/CD.",
        )
        
        assert isinstance(result, EvaluationResult)
