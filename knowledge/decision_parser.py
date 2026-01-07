"""
Decision Metadata Parser for AI Knowledge Continuity System.

This module extracts structured decision metadata from Architecture Decision
Records (ADR), meeting notes, and design documents. It supports Feature 2:
Decision Traceability by capturing what, why, when, and by whom decisions were made.

The parser uses deterministic pattern matching to extract:
- Decision titles and IDs
- Authors and stakeholders
- Dates and timestamps
- Alternatives considered
- Trade-offs and rationale
- Outcomes and consequences
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DecisionMetadata:
    """
    Structured metadata for an organizational decision.
    
    This captures the full context needed to understand why a decision
    was made, supporting future knowledge retrieval and decision tracing.
    """
    # Core identifiers
    decision_id: Optional[str] = None
    decision_title: Optional[str] = None
    
    # Attribution
    author: Optional[str] = None
    stakeholders: List[str] = field(default_factory=list)
    
    # Temporal context
    date: Optional[str] = None
    date_parsed: Optional[datetime] = None
    
    # Decision content
    context: Optional[str] = None
    decision_statement: Optional[str] = None
    rationale: Optional[str] = None
    
    # Alternatives and trade-offs
    alternatives: List[str] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    
    # Outcomes
    outcome: Optional[str] = None
    status: Optional[str] = None  # e.g., "accepted", "superseded", "deprecated"
    
    # Extraction confidence
    extraction_confidence: float = 0.0
    extracted_fields: List[str] = field(default_factory=list)
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dictionary for document enrichment."""
        metadata = {
            "decision_id": self.decision_id,
            "decision_title": self.decision_title,
            "decision_author": self.author,
            "decision_date": self.date,
            "decision_status": self.status,
            "has_alternatives": len(self.alternatives) > 0,
            "has_tradeoffs": len(self.tradeoffs) > 0,
            "decision_extraction_confidence": self.extraction_confidence,
        }
        
        # Include lists only if non-empty
        if self.alternatives:
            metadata["decision_alternatives"] = self.alternatives
        if self.tradeoffs:
            metadata["decision_tradeoffs"] = self.tradeoffs
        if self.stakeholders:
            metadata["decision_stakeholders"] = self.stakeholders
        if self.pros:
            metadata["decision_pros"] = self.pros
        if self.cons:
            metadata["decision_cons"] = self.cons
            
        return metadata
    
    def get_summary(self) -> str:
        """Generate a human-readable summary of the decision."""
        parts = []
        
        if self.decision_title:
            parts.append(f"**Decision:** {self.decision_title}")
        
        if self.author:
            parts.append(f"**Author:** {self.author}")
        
        if self.date:
            parts.append(f"**Date:** {self.date}")
        
        if self.rationale:
            parts.append(f"**Rationale:** {self.rationale[:200]}...")
        
        if self.alternatives:
            parts.append(f"**Alternatives considered:** {', '.join(self.alternatives)}")
        
        if self.tradeoffs:
            parts.append(f"**Trade-offs:** {'; '.join(self.tradeoffs)}")
        
        return "\n".join(parts) if parts else "No decision metadata extracted."


class DecisionParser:
    """
    Extracts structured decision metadata from documents.
    
    Supports multiple document formats:
    - Architecture Decision Records (ADR) with standard sections
    - Meeting notes with decision outcomes
    - Design documents with rationale sections
    - Free-form text with decision indicators
    
    The parser uses regex patterns to identify and extract information,
    providing a deterministic and explainable extraction process.
    
    Example:
        >>> parser = DecisionParser()
        >>> metadata = parser.parse(content, filename="ADR-001.md")
        >>> print(metadata.decision_title)
    """
    
    # Patterns for extracting decision ID from filename or content
    DECISION_ID_PATTERNS = [
        r"ADR[_\-\s]?(\d+)",  # ADR-001, ADR_001, ADR 001
        r"RFC[_\-\s]?(\d+)",  # RFC-001
        r"Decision[_\-\s]?(\d+)",  # Decision-001
        r"#\s*(\d+)",  # #001
    ]
    
    # Patterns for extracting decision title
    TITLE_PATTERNS = [
        r"#\s*(?:ADR|RFC|Decision)[_\-\s]?\d*[:\s]+(.+?)(?:\n|$)",  # # ADR-001: Title
        r"##?\s*(?:Decision|Title|Subject)[:\s]+(.+?)(?:\n|$)",  # ## Decision: Title
        r"^#\s+(.+?)(?:\n|$)",  # # Title (first h1)
        r"(?:Decision|Title)[:\s]+(.+?)(?:\n|$)",  # Decision: Title
    ]
    
    # Patterns for extracting author
    AUTHOR_PATTERNS = [
        r"(?:Author|Written by|By|Created by|Owner)[:\s]+([^\n]+)",
        r"(?:Submitted by|Proposed by|Authored by)[:\s]+([^\n]+)",
        r"(?:Author|By)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Name pattern
    ]
    
    # Patterns for extracting date
    DATE_PATTERNS = [
        r"(?:Date|Created|Written|Last updated)[:\s]+(\d{4}-\d{2}-\d{2})",  # ISO format
        r"(?:Date|Created)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # Various formats
        r"(\d{4}-\d{2}-\d{2})",  # ISO date anywhere
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})",  # Month DD, YYYY
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",  # DD Month YYYY
    ]
    
    # Section headers for ADR-style documents
    SECTION_PATTERNS = {
        "context": r"##?\s*(?:Context|Background|Problem|Situation)[:\s]*\n([\s\S]*?)(?=##?\s|\Z)",
        "decision": r"##?\s*(?:Decision|Solution|Approach|Resolution)[:\s]*\n([\s\S]*?)(?=##?\s|\Z)",
        "rationale": r"##?\s*(?:Rationale|Reasoning|Justification|Why)[:\s]*\n([\s\S]*?)(?=##?\s|\Z)",
        "alternatives": r"##?\s*(?:Alternatives?|Options?|Considered)[:\s]*\n([\s\S]*?)(?=##?\s|\Z)",
        "tradeoffs": r"##?\s*(?:Trade[_\-\s]?offs?|Consequences|Implications)[:\s]*\n([\s\S]*?)(?=##?\s|\Z)",
        "outcome": r"##?\s*(?:Outcome|Result|Status|Conclusion)[:\s]*\n([\s\S]*?)(?=##?\s|\Z)",
    }
    
    # Patterns for extracting lists of alternatives
    LIST_ITEM_PATTERNS = [
        r"[-*]\s+(.+?)(?:\n|$)",  # Bullet points
        r"\d+[.)]\s+(.+?)(?:\n|$)",  # Numbered lists
        r"Option\s*\d*[:\s]+(.+?)(?:\n|$)",  # Option 1: ...
    ]
    
    # Status keywords
    STATUS_KEYWORDS = {
        "accepted": ["accepted", "approved", "adopted", "implemented"],
        "proposed": ["proposed", "draft", "pending", "under review"],
        "superseded": ["superseded", "replaced", "deprecated", "obsolete"],
        "rejected": ["rejected", "declined", "not adopted"],
    }
    
    def __init__(self):
        """Initialize the decision parser."""
        # Compile patterns for efficiency
        self._id_patterns = [re.compile(p, re.IGNORECASE) for p in self.DECISION_ID_PATTERNS]
        self._title_patterns = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.TITLE_PATTERNS]
        self._author_patterns = [re.compile(p, re.IGNORECASE) for p in self.AUTHOR_PATTERNS]
        self._date_patterns = [re.compile(p, re.IGNORECASE) for p in self.DATE_PATTERNS]
        self._section_patterns = {
            k: re.compile(v, re.IGNORECASE | re.MULTILINE)
            for k, v in self.SECTION_PATTERNS.items()
        }
        self._list_patterns = [re.compile(p, re.MULTILINE) for p in self.LIST_ITEM_PATTERNS]
        
        logger.info("DecisionParser initialized")
    
    def parse(
        self,
        content: str,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
    ) -> DecisionMetadata:
        """
        Parse a document and extract decision metadata.
        
        Args:
            content: The document content to parse.
            filename: Optional filename for additional context.
            filepath: Optional filepath for additional context.
            
        Returns:
            DecisionMetadata with extracted information.
        """
        metadata = DecisionMetadata()
        extracted_fields: List[str] = []
        
        # Extract decision ID (from filename or content)
        decision_id = self._extract_id(content, filename)
        if decision_id:
            metadata.decision_id = decision_id
            extracted_fields.append("decision_id")
        
        # Extract title
        title = self._extract_title(content)
        if title:
            metadata.decision_title = title.strip()
            extracted_fields.append("decision_title")
        
        # Extract author
        author = self._extract_author(content)
        if author:
            metadata.author = author.strip()
            extracted_fields.append("author")
        
        # Extract date
        date_str, date_parsed = self._extract_date(content)
        if date_str:
            metadata.date = date_str
            metadata.date_parsed = date_parsed
            extracted_fields.append("date")
        
        # Extract sections
        for section_name, pattern in self._section_patterns.items():
            match = pattern.search(content)
            if match:
                section_content = match.group(1).strip()
                if section_name == "context":
                    metadata.context = section_content[:1000]  # Limit length
                    extracted_fields.append("context")
                elif section_name == "decision":
                    metadata.decision_statement = section_content[:1000]
                    extracted_fields.append("decision_statement")
                elif section_name == "rationale":
                    metadata.rationale = section_content[:1000]
                    extracted_fields.append("rationale")
                elif section_name == "alternatives":
                    alternatives = self._extract_list_items(section_content)
                    if alternatives:
                        metadata.alternatives = alternatives
                        extracted_fields.append("alternatives")
                elif section_name == "tradeoffs":
                    tradeoffs = self._extract_list_items(section_content)
                    if tradeoffs:
                        metadata.tradeoffs = tradeoffs
                        extracted_fields.append("tradeoffs")
                elif section_name == "outcome":
                    metadata.outcome = section_content[:500]
                    extracted_fields.append("outcome")
        
        # Extract pros and cons
        pros, cons = self._extract_pros_cons(content)
        if pros:
            metadata.pros = pros
            extracted_fields.append("pros")
        if cons:
            metadata.cons = cons
            extracted_fields.append("cons")
        
        # Detect status
        status = self._detect_status(content)
        if status:
            metadata.status = status
            extracted_fields.append("status")
        
        # Calculate extraction confidence
        metadata.extracted_fields = extracted_fields
        metadata.extraction_confidence = self._calculate_confidence(extracted_fields)
        
        logger.debug(
            f"Extracted {len(extracted_fields)} fields from decision document, "
            f"confidence: {metadata.extraction_confidence:.2f}"
        )
        
        return metadata
    
    def _extract_id(
        self,
        content: str,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """Extract decision ID from filename or content."""
        # Try filename first
        if filename:
            for pattern in self._id_patterns:
                match = pattern.search(filename)
                if match:
                    return f"ADR-{match.group(1).zfill(3)}"
        
        # Try content
        for pattern in self._id_patterns:
            match = pattern.search(content)
            if match:
                return f"ADR-{match.group(1).zfill(3)}"
        
        return None
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract decision title from content."""
        for pattern in self._title_patterns:
            match = pattern.search(content)
            if match:
                title = match.group(1).strip()
                # Clean up common prefixes
                title = re.sub(r"^(?:ADR|RFC|Decision)[_\-\s]?\d*[:\s]*", "", title, flags=re.IGNORECASE)
                if len(title) > 5:  # Minimum meaningful title length
                    return title
        return None
    
    def _extract_author(self, content: str) -> Optional[str]:
        """Extract author from content."""
        for pattern in self._author_patterns:
            match = pattern.search(content)
            if match:
                author = match.group(1).strip()
                # Clean up common suffixes
                author = re.sub(r"\s*\(.*?\)\s*$", "", author)  # Remove (email) etc.
                author = author.strip(".,;:")
                if len(author) > 2 and len(author) < 100:  # Sanity check
                    return author
        return None
    
    def _extract_date(self, content: str) -> Tuple[Optional[str], Optional[datetime]]:
        """Extract and parse date from content."""
        for pattern in self._date_patterns:
            match = pattern.search(content)
            if match:
                date_str = match.group(1).strip()
                
                # Try to parse the date
                date_parsed = self._parse_date(date_str)
                return date_str, date_parsed
        
        return None, None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse a date string into datetime."""
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_list_items(self, content: str) -> List[str]:
        """Extract list items from content."""
        items = []
        for pattern in self._list_patterns:
            matches = pattern.findall(content)
            for match in matches:
                item = match.strip()
                if len(item) > 3 and len(item) < 500:  # Sanity check
                    items.append(item)
        
        # Deduplicate while preserving order
        seen = set()
        unique_items = []
        for item in items:
            if item.lower() not in seen:
                seen.add(item.lower())
                unique_items.append(item)
        
        return unique_items[:10]  # Limit to 10 items
    
    def _extract_pros_cons(self, content: str) -> Tuple[List[str], List[str]]:
        """Extract pros and cons from content."""
        pros = []
        cons = []
        
        # Look for explicit pros/cons sections
        pros_pattern = re.compile(
            r"(?:Pros|Benefits|Advantages|Strengths)[:\s]*\n([\s\S]*?)(?=(?:Cons|Drawbacks|Disadvantages|Weaknesses)|##?\s|\Z)",
            re.IGNORECASE
        )
        cons_pattern = re.compile(
            r"(?:Cons|Drawbacks|Disadvantages|Weaknesses)[:\s]*\n([\s\S]*?)(?=(?:Pros|Benefits|Advantages)|##?\s|\Z)",
            re.IGNORECASE
        )
        
        pros_match = pros_pattern.search(content)
        if pros_match:
            pros = self._extract_list_items(pros_match.group(1))
        
        cons_match = cons_pattern.search(content)
        if cons_match:
            cons = self._extract_list_items(cons_match.group(1))
        
        return pros, cons
    
    def _detect_status(self, content: str) -> Optional[str]:
        """Detect decision status from content."""
        content_lower = content.lower()
        
        for status, keywords in self.STATUS_KEYWORDS.items():
            for keyword in keywords:
                # Look for status in explicit sections
                if re.search(rf"(?:status|state)[:\s]*{keyword}", content_lower):
                    return status
                # Look for status declarations
                if re.search(rf"(?:is|was|been)\s+{keyword}", content_lower):
                    return status
        
        return None
    
    def _calculate_confidence(self, extracted_fields: List[str]) -> float:
        """
        Calculate confidence score based on extracted fields.
        
        Higher weight for core decision fields.
        """
        weights = {
            "decision_id": 0.1,
            "decision_title": 0.15,
            "author": 0.1,
            "date": 0.1,
            "context": 0.1,
            "decision_statement": 0.15,
            "rationale": 0.15,
            "alternatives": 0.05,
            "tradeoffs": 0.05,
            "outcome": 0.05,
        }
        
        total_weight = sum(weights.values())
        extracted_weight = sum(
            weights.get(field, 0.02) for field in extracted_fields
        )
        
        return min(1.0, extracted_weight / total_weight)
    
    def is_decision_document(
        self,
        content: str,
        filename: Optional[str] = None,
    ) -> bool:
        """
        Check if a document appears to be a decision document.
        
        Args:
            content: Document content.
            filename: Optional filename.
            
        Returns:
            True if the document appears to contain decision information.
        """
        # Quick filename check
        if filename:
            filename_lower = filename.lower()
            if any(kw in filename_lower for kw in ["adr", "decision", "rfc", "rationale"]):
                return True
        
        # Check for decision-related sections
        content_lower = content.lower()
        decision_indicators = [
            "## decision",
            "## rationale",
            "### context",
            "trade-off",
            "tradeoff",
            "alternative",
            "we decided",
            "the decision",
            "was selected",
            "was chosen",
        ]
        
        indicator_count = sum(1 for ind in decision_indicators if ind in content_lower)
        return indicator_count >= 2


# Module-level convenience function
def parse_decision_document(
    content: str,
    filename: Optional[str] = None,
    filepath: Optional[str] = None,
) -> DecisionMetadata:
    """
    Parse a document and extract decision metadata.
    
    Convenience function that uses a default parser instance.
    
    Args:
        content: The document content to parse.
        filename: Optional filename for additional context.
        filepath: Optional filepath for additional context.
        
    Returns:
        DecisionMetadata with extracted information.
    """
    parser = DecisionParser()
    return parser.parse(content=content, filename=filename, filepath=filepath)
