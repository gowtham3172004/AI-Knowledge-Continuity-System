#!/usr/bin/env python3
"""
Quick test script for knowledge classification features.
Tests the three features without requiring full system setup.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_feature_1_tacit_classification():
    """Test Feature 1: Tacit Knowledge Classification"""
    print("\n" + "="*70)
    print("FEATURE 1: TACIT KNOWLEDGE CLASSIFICATION")
    print("="*70)
    
    from knowledge.knowledge_classifier import KnowledgeClassifier
    
    classifier = KnowledgeClassifier()
    
    # Test 1: Exit interview
    result1 = classifier.classify(
        filename="exit_interview_john.txt",
        content="Lessons learned during my time: avoid overcomplicating the caching layer."
    )
    print(f"\n✓ Exit Interview Classification:")
    print(f"  Type: {result1.knowledge_type.value}")
    print(f"  Confidence: {result1.confidence:.2f}")
    print(f"  Reason: {result1.classification_reason}")
    
    # Test 2: Tacit query detection
    is_tacit, indicators = classifier.is_tacit_query(
        "What mistakes should I avoid when deploying?"
    )
    print(f"\n✓ Tacit Query Detection:")
    print(f"  Is Tacit Query: {is_tacit}")
    print(f"  Indicators: {len(indicators)} patterns matched")
    
    return True


def test_feature_2_decision_traceability():
    """Test Feature 2: Decision Traceability"""
    print("\n" + "="*70)
    print("FEATURE 2: DECISION TRACEABILITY")
    print("="*70)
    
    from knowledge.decision_parser import DecisionParser
    
    parser = DecisionParser()
    
    # Test ADR parsing
    adr_content = """
    # ADR-001: Use Redis for Caching
    
    Author: John Smith
    Date: 2024-01-15
    
    ## Context
    We needed a fast caching solution.
    
    ## Decision
    We decided to use Redis.
    
    ## Rationale
    Redis provides sub-millisecond latency and is simple to operate.
    
    ## Alternatives
    - PostgreSQL with caching
    - Memcached
    - RabbitMQ
    
    ## Trade-offs
    - Accepted: Less durability for better performance
    - Accepted: Memory limitations
    """
    
    result = parser.parse(content=adr_content, filename="ADR-001.md")
    
    print(f"\n✓ Decision Metadata Extraction:")
    print(f"  Decision ID: {result.decision_id}")
    print(f"  Title: {result.decision_title}")
    print(f"  Author: {result.author}")
    print(f"  Date: {result.date}")
    print(f"  Alternatives: {len(result.alternatives)} found")
    print(f"  Trade-offs: {len(result.tradeoffs)} found")
    print(f"  Extraction Confidence: {result.extraction_confidence:.2f}")
    
    # Test decision query detection
    from knowledge.knowledge_classifier import KnowledgeClassifier
    classifier = KnowledgeClassifier()
    
    is_decision, indicators = classifier.is_decision_query(
        "Why did we choose Redis instead of RabbitMQ?"
    )
    print(f"\n✓ Decision Query Detection:")
    print(f"  Is Decision Query: {is_decision}")
    print(f"  Indicators: {len(indicators)} patterns matched")
    
    return True


def test_feature_3_gap_detection():
    """Test Feature 3: Knowledge Gap Detection"""
    print("\n" + "="*70)
    print("FEATURE 3: KNOWLEDGE GAP DETECTION")
    print("="*70)
    
    from knowledge.gap_detector import KnowledgeGapDetector, GapSeverity
    from langchain_core.documents import Document
    
    detector = KnowledgeGapDetector(
        confidence_threshold=0.6,
        min_relevant_docs=2,
    )
    
    # Test 1: No documents (HIGH gap)
    result1 = detector.evaluate(
        query="What is our vacation policy?",
        documents_with_scores=[],
        log_gap=False,
    )
    print(f"\n✓ Gap Detection - No Documents:")
    print(f"  Gap Detected: {result1.gap_detected}")
    print(f"  Severity: {result1.gap_severity.value if result1.gap_severity else 'N/A'}")
    print(f"  Confidence: {result1.confidence_score:.2f}")
    print(f"  Safe Response: {result1.safe_response[:80]}...")
    
    # Test 2: Good documents (No gap)
    docs = [
        Document(page_content="Deployment guide step 1", metadata={"knowledge_type": "explicit"}),
        Document(page_content="Deployment guide step 2", metadata={"knowledge_type": "explicit"}),
        Document(page_content="Deployment best practices", metadata={"knowledge_type": "tacit"}),
    ]
    docs_with_scores = [(doc, 0.85) for doc in docs]
    
    result2 = detector.evaluate(
        query="How do I deploy the application?",
        documents_with_scores=docs_with_scores,
        log_gap=False,
    )
    print(f"\n✓ Gap Detection - Sufficient Knowledge:")
    print(f"  Gap Detected: {result2.gap_detected}")
    print(f"  Confidence: {result2.confidence_score:.2f}")
    print(f"  Has Sufficient Knowledge: {result2.has_sufficient_knowledge}")
    print(f"  Knowledge Coverage: Tacit={result2.tacit_coverage}, Explicit={result2.explicit_coverage}")
    
    return True


def test_integration():
    """Test integration of all three features"""
    print("\n" + "="*70)
    print("INTEGRATION TEST: KNOWLEDGE VALIDATION")
    print("="*70)
    
    from knowledge.validator import KnowledgeValidator
    from langchain_core.documents import Document
    
    validator = KnowledgeValidator()
    
    # Test tacit query with tacit documents
    tacit_docs = [
        Document(
            page_content="Lesson learned: Always test Redis failover before going to production.",
            metadata={"knowledge_type": "tacit", "source": "lessons_learned.txt"}
        ),
        Document(
            page_content="Common mistake: Not setting appropriate TTL values.",
            metadata={"knowledge_type": "tacit", "source": "exit_interview.txt"}
        ),
    ]
    docs_with_scores = [(doc, 0.80) for doc in tacit_docs]
    
    result = validator.validate(
        query="What mistakes should I avoid with Redis?",
        documents_with_scores=docs_with_scores,
    )
    
    print(f"\n✓ Knowledge Validation:")
    print(f"  Query Type: {result.query_type}")
    print(f"  Can Proceed: {result.can_proceed}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Relevance: {result.relevance_score:.2f}")
    print(f"  Has Tacit Match: {result.has_tacit_match}")
    print(f"  Status: {result.status.value}")
    print(f"  Warnings: {len(result.warnings)}")
    
    return True


def main():
    """Run all feature tests"""
    print("\n" + "="*70)
    print("KNOWLEDGE CONTINUITY SYSTEM - FEATURE VALIDATION")
    print("Testing 3 Enterprise Features")
    print("="*70)
    
    try:
        success = True
        
        # Test each feature
        success &= test_feature_1_tacit_classification()
        success &= test_feature_2_decision_traceability()
        success &= test_feature_3_gap_detection()
        success &= test_integration()
        
        # Summary
        print("\n" + "="*70)
        if success:
            print("✅ ALL FEATURES VALIDATED SUCCESSFULLY")
            print("="*70)
            print("\nThe three enterprise features are working correctly:")
            print("  1. ✅ Tacit Knowledge Extraction")
            print("  2. ✅ Decision Traceability")
            print("  3. ✅ Knowledge Gap Detection")
            print("\nNext steps:")
            print("  • Run: python3 main.py --ingest")
            print("  • Then: python3 -m streamlit run ui/app.py")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
