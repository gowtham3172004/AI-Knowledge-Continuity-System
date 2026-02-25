"""
Knowledge Dashboard routes.

Provides APIs for:
- Knowledge health score
- Knowledge gap tracking
- Onboarding paths for new developers
- Document coverage analysis
- Stale knowledge detection
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.supabase_client import get_current_user

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _get_db():
    """Lazy import of db functions."""
    from backend.db import (
        get_gap_stats, get_knowledge_gaps, resolve_knowledge_gap,
        get_document_stats, get_all_documents,
    )
    return {
        "get_gap_stats": get_gap_stats,
        "get_knowledge_gaps": get_knowledge_gaps,
        "resolve_knowledge_gap": resolve_knowledge_gap,
        "get_document_stats": get_document_stats,
        "get_all_documents": get_all_documents,
    }


# --- Response Models ---

class KnowledgeHealthResponse(BaseModel):
    health_score: float  # 0-100
    total_documents: int
    total_chunks: int
    coverage: dict  # {tacit: n, decision: n, explicit: n}
    unresolved_gaps: int
    stale_documents: int
    recommendations: List[str]


class GapResponse(BaseModel):
    id: int
    query: str
    confidence_score: float
    severity: str
    detected_at: str
    resolved: bool


class GapStatsResponse(BaseModel):
    total_gaps: int
    unresolved: int
    resolved: int
    by_severity: dict


class OnboardingTopic(BaseModel):
    title: str
    description: str
    category: str  # architecture, codebase, decisions, processes
    priority: int  # 1-5, 5=highest
    document_count: int
    status: str  # not_started, in_progress, completed


class OnboardingPathResponse(BaseModel):
    topics: List[OnboardingTopic]
    completion_percentage: float
    estimated_time_hours: float


class SuggestedQuestion(BaseModel):
    question: str
    category: str  # architecture, decisions, tacit, technology, codebase, process
    icon: str  # emoji
    context: str  # why this question is relevant


class SuggestQuestionsResponse(BaseModel):
    questions: List[SuggestedQuestion]
    total_documents: int


# --- Routes ---

@router.get("/health", response_model=KnowledgeHealthResponse)
async def knowledge_health():
    """
    Get overall knowledge health score and recommendations.
    """
    try:
        db = _get_db()
        doc_stats = db["get_document_stats"]()
        gap_stats = db["get_gap_stats"]()
        all_docs = db["get_all_documents"]()
    except Exception as e:
        # Return a safe default if Supabase is unavailable
        return KnowledgeHealthResponse(
            health_score=0,
            total_documents=0,
            total_chunks=0,
            coverage={},
            unresolved_gaps=0,
            stale_documents=0,
            recommendations=[f"Database connection error: {str(e)[:100]}. Ensure Supabase tables exist."],
        )

    # Calculate stale documents (>90 days old)
    stale_count = 0
    for doc in all_docs:
        if doc.get("uploaded_at"):
            try:
                uploaded = datetime.fromisoformat(str(doc["uploaded_at"]))
                if (datetime.utcnow() - uploaded) > timedelta(days=90):
                    stale_count += 1
            except (ValueError, TypeError):
                pass

    total_docs = doc_stats.get("total_documents", 0)
    coverage = doc_stats.get("by_type", {})
    unresolved = gap_stats.get("unresolved", 0)

    # Calculate health score (0-100)
    score = 100.0

    # Penalize for low document count
    if total_docs < 5:
        score -= 30
    elif total_docs < 10:
        score -= 15

    # Penalize for missing knowledge types
    if not coverage.get("tacit", 0):
        score -= 15
    if not coverage.get("decision", 0):
        score -= 15

    # Penalize for unresolved gaps
    score -= min(unresolved * 5, 25)

    # Penalize for stale documents
    if total_docs > 0:
        stale_ratio = stale_count / total_docs
        score -= stale_ratio * 15

    score = max(0, min(100, score))

    # Generate recommendations
    recommendations = []
    if total_docs < 5:
        recommendations.append("Upload more documents to build a comprehensive knowledge base")
    if not coverage.get("tacit", 0):
        recommendations.append("Add tacit knowledge documents (lessons learned, retrospectives, exit interviews)")
    if not coverage.get("decision", 0):
        recommendations.append("Add architectural decision records (ADRs) for decision traceability")
    if unresolved > 0:
        recommendations.append(f"Resolve {unresolved} knowledge gap(s) by documenting missing information")
    if stale_count > 0:
        recommendations.append(f"Review and update {stale_count} stale document(s) (>90 days old)")
    if not recommendations:
        recommendations.append("Knowledge base is healthy! Keep adding new documents as projects evolve.")

    return KnowledgeHealthResponse(
        health_score=round(score, 1),
        total_documents=total_docs,
        total_chunks=doc_stats.get("total_chunks", 0),
        coverage=coverage,
        unresolved_gaps=unresolved,
        stale_documents=stale_count,
        recommendations=recommendations,
    )


@router.get("/gaps", response_model=List[GapResponse])
async def list_gaps(resolved: bool = False):
    """List knowledge gaps detected by the system."""
    try:
        db = _get_db()
        gaps = db["get_knowledge_gaps"](resolved=resolved)
        return [
            GapResponse(
                id=g["id"],
                query=g["query"],
                confidence_score=g["confidence_score"],
                severity=g["severity"],
                detected_at=g.get("detected_at") or "",
                resolved=bool(g.get("resolved")),
            )
            for g in gaps
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.get("/gaps/stats", response_model=GapStatsResponse)
async def gap_statistics():
    """Get knowledge gap statistics."""
    try:
        db = _get_db()
        return db["get_gap_stats"]()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.post("/gaps/{gap_id}/resolve")
async def mark_gap_resolved(gap_id: int, user=Depends(get_current_user)):
    """Mark a knowledge gap as resolved (after documentation is added)."""
    try:
        db = _get_db()
        db["resolve_knowledge_gap"](gap_id, user["id"])
        return {"status": "resolved", "id": gap_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.get("/onboarding", response_model=OnboardingPathResponse)
async def get_onboarding_path():
    """
    Generate an AI-powered onboarding path for new developers.
    """
    try:
        db = _get_db()
        doc_stats = db["get_document_stats"]()
        all_docs = db["get_all_documents"]()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")
    coverage = doc_stats.get("by_type", {})

    topics = []

    # Architecture Overview
    arch_count = sum(1 for d in all_docs if any(
        kw in (d.get("original_name", "").lower())
        for kw in ["architecture", "system", "design", "overview"]
    ))
    topics.append(OnboardingTopic(
        title="System Architecture",
        description="Understand the overall system design, components, and how they interact",
        category="architecture",
        priority=5,
        document_count=arch_count,
        status="not_started",
    ))

    # Technology Stack
    tech_count = sum(1 for d in all_docs if any(
        kw in (d.get("original_name", "").lower())
        for kw in ["technology", "stack", "tech", "framework"]
    ))
    topics.append(OnboardingTopic(
        title="Technology Stack & Tools",
        description="Learn the technologies, frameworks, and tools used in the project",
        category="architecture",
        priority=5,
        document_count=tech_count,
        status="not_started",
    ))

    # Key Decisions
    decision_count = coverage.get("decision", 0)
    topics.append(OnboardingTopic(
        title="Architectural Decisions (ADRs)",
        description="Review key decisions, their rationale, alternatives considered, and trade-offs",
        category="decisions",
        priority=4,
        document_count=decision_count,
        status="not_started",
    ))

    # Lessons Learned
    tacit_count = coverage.get("tacit", 0)
    topics.append(OnboardingTopic(
        title="Lessons Learned & Tribal Knowledge",
        description="Understand past mistakes, workarounds, and experiential knowledge from the team",
        category="processes",
        priority=4,
        document_count=tacit_count,
        status="not_started",
    ))

    # Codebase Structure
    code_count = sum(1 for d in all_docs if any(
        kw in (d.get("original_name", "").lower())
        for kw in ["code", "api", "module", "service", "backend", "frontend"]
    ))
    topics.append(OnboardingTopic(
        title="Codebase Structure & APIs",
        description="Explore the codebase organization, key modules, and API contracts",
        category="codebase",
        priority=3,
        document_count=code_count,
        status="not_started",
    ))

    # Meeting Notes / Context
    meeting_count = sum(1 for d in all_docs if any(
        kw in (d.get("original_name", "").lower())
        for kw in ["meeting", "notes", "standup", "retro"]
    ))
    topics.append(OnboardingTopic(
        title="Meeting Notes & Context",
        description="Catch up on recent discussions, decisions, and action items from team meetings",
        category="processes",
        priority=2,
        document_count=meeting_count,
        status="not_started",
    ))

    # Deployment & Operations
    ops_count = sum(1 for d in all_docs if any(
        kw in (d.get("original_name", "").lower())
        for kw in ["deploy", "ops", "ci", "cd", "pipeline", "infra"]
    ))
    topics.append(OnboardingTopic(
        title="Deployment & Operations",
        description="Learn how the application is deployed, monitored, and maintained",
        category="codebase",
        priority=3,
        document_count=ops_count,
        status="not_started",
    ))

    total_with_docs = sum(1 for t in topics if t.document_count > 0)
    completion = (total_with_docs / len(topics) * 100) if topics else 0
    est_hours = len(topics) * 0.5 + sum(t.document_count for t in topics) * 0.15

    return OnboardingPathResponse(
        topics=sorted(topics, key=lambda t: t.priority, reverse=True),
        completion_percentage=round(completion, 1),
        estimated_time_hours=round(est_hours, 1),
    )


@router.get("/suggest-questions", response_model=SuggestQuestionsResponse)
async def suggest_questions():
    """
    Generate smart suggested questions based on uploaded documents.
    """
    try:
        db = _get_db()
        all_docs = db["get_all_documents"]()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")
    # Deduplicate documents by original name
    seen_names: set = set()
    unique_docs: list = []
    for d in all_docs:
        name = d.get("original_name", "")
        if name and name not in seen_names:
            seen_names.add(name)
            unique_docs.append(d)
    all_docs = unique_docs

    try:
        doc_stats = db["get_document_stats"]()
        gap_stats = db["get_gap_stats"]()
    except Exception:
        doc_stats = {"total_documents": 0, "total_chunks": 0, "by_type": {}}
        gap_stats = {"total_gaps": 0, "unresolved": 0, "resolved": 0, "by_severity": {}}
    coverage = doc_stats.get("by_type", {})
    total = doc_stats.get("total_documents", 0)

    questions: list = []

    def _add(q: str, cat: str, icon: str, ctx: str):
        questions.append(SuggestedQuestion(
            question=q, category=cat, icon=icon, context=ctx
        ))

    # ----- Architecture questions (from actual doc names) -----
    arch_docs = [d for d in all_docs if any(
        kw in d.get("original_name", "").lower()
        for kw in ["architecture", "design", "system", "overview"]
    )]
    if arch_docs:
        names = ", ".join(d["original_name"] for d in arch_docs[:3])
        _add(
            "What is the overall system architecture and how do the components interact?",
            "architecture", "🏗️",
            f"Based on: {names}"
        )
        _add(
            "What are the main services/modules and their responsibilities?",
            "architecture", "🧩",
            "Your architecture docs cover this"
        )

    # ----- Technology stack questions -----
    tech_docs = [d for d in all_docs if any(
        kw in d.get("original_name", "").lower()
        for kw in ["technology", "stack", "tech", "rationale", "framework", "tool"]
    )]
    if tech_docs:
        names = ", ".join(d["original_name"] for d in tech_docs[:3])
        _add(
            "What technology stack is used and why were these choices made?",
            "technology", "⚡",
            f"Based on: {names}"
        )
        _add(
            "What alternatives were considered before choosing the current tech stack?",
            "decisions", "🔄",
            "Understanding trade-offs helps avoid repeating past discussions"
        )

    # ----- Decision-related questions -----
    if coverage.get("decision", 0) > 0:
        _add(
            "What were the key architectural decisions and their rationale?",
            "decisions", "📋",
            f"{coverage['decision']} decision document(s) available"
        )
        _add(
            "Are there any decisions that were controversial or had significant trade-offs?",
            "decisions", "⚖️",
            "Understanding past trade-offs prevents costly re-decisions"
        )

    # ----- Tacit knowledge questions -----
    if coverage.get("tacit", 0) > 0:
        _add(
            "What are the known gotchas and lessons learned from this project?",
            "tacit", "🧠",
            f"{coverage['tacit']} tacit knowledge document(s) with tribal knowledge"
        )
        _add(
            "What mistakes were made in the past that I should avoid?",
            "tacit", "⚠️",
            "Lessons learned help new developers avoid known pitfalls"
        )
    else:
        _add(
            "What tribal knowledge or lessons learned should a new developer know?",
            "tacit", "🧠",
            "No tacit knowledge docs uploaded yet — consider adding retrospectives"
        )

    # ----- Meeting notes / context -----
    meeting_docs = [d for d in all_docs if any(
        kw in d.get("original_name", "").lower()
        for kw in ["meeting", "notes", "standup", "retro", "minutes"]
    )]
    if meeting_docs:
        _add(
            "What were the recent important discussions and decisions from team meetings?",
            "process", "📝",
            f"{len(meeting_docs)} meeting document(s) available"
        )

    # ----- Document-specific questions (from actual uploaded files) -----
    for doc in all_docs[:5]:
        name = doc.get("original_name", "")
        kt = doc.get("knowledge_type", "explicit")
        if name:
            _add(
                f"Summarize the key points from {name}",
                "document", "📄",
                f"Directly from your uploaded {kt} knowledge"
            )

    # ----- Knowledge gap questions -----
    unresolved = gap_stats.get("unresolved", 0)
    if unresolved > 0:
        _add(
            "What areas of this project are NOT well-documented?",
            "gaps", "🔍",
            f"{unresolved} knowledge gap(s) detected — these need documentation"
        )

    # ----- Onboarding questions (always useful) -----
    if total >= 2:
        _add(
            "If I'm new to this project, what should I read first?",
            "onboarding", "🎯",
            f"{total} documents available for onboarding"
        )
        _add(
            "What are the critical things I need to understand before writing code?",
            "onboarding", "🚀",
            "Essential context for productive contribution"
        )

    return SuggestQuestionsResponse(questions=questions, total_documents=total)
