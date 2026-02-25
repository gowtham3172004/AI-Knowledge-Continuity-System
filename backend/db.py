"""
Database module — Supabase for all persistent data.

Replaces the old SQLite implementation with Supabase Postgres.
All tables are created via Supabase Dashboard / SQL editor (see setup_supabase.sql).
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def init_db():
    """
    Verify Supabase connection on startup.
    Tables are created via Supabase SQL editor, not at runtime.
    """
    try:
        sb = get_supabase()
        # Quick connectivity check — use conversations table (always present)
        sb.table("conversations").select("id").limit(1).execute()
        logger.info("Supabase database connection verified")
    except RuntimeError as e:
        logger.warning(f"Supabase not configured: {e}")
    except Exception as e:
        logger.warning(f"Supabase connection check: {e} (tables may not exist yet — run setup_supabase.sql)")


# ═══════════════════════════════════════════════════════════
#  DOCUMENT OPERATIONS
# ═══════════════════════════════════════════════════════════

def add_document(user_id: str, filename: str, original_name: str,
                 file_type: str, file_size: int, knowledge_type: str = "explicit") -> int:
    sb = get_supabase()
    result = sb.table("documents").insert({
        "user_id": user_id,
        "filename": filename,
        "original_name": original_name,
        "file_type": file_type,
        "file_size": file_size,
        "knowledge_type": knowledge_type,
    }).execute()
    return result.data[0]["id"]


def update_document_status(doc_id: int, status: str, chunk_count: int = 0,
                           knowledge_type: Optional[str] = None):
    sb = get_supabase()
    updates: Dict[str, Any] = {"status": status, "chunk_count": chunk_count}
    if knowledge_type:
        updates["knowledge_type"] = knowledge_type
    sb.table("documents").update(updates).eq("id", doc_id).execute()


def get_user_documents(user_id: str) -> List[Dict]:
    sb = get_supabase()
    result = sb.table("documents").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute()
    return result.data


def get_all_documents() -> List[Dict]:
    sb = get_supabase()
    result = sb.table("documents").select("*").order("uploaded_at", desc=True).execute()
    return result.data


def delete_document(doc_id: int, user_id: str) -> bool:
    sb = get_supabase()
    result = sb.table("documents").delete().eq("id", doc_id).eq("user_id", user_id).execute()
    return len(result.data) > 0


def get_document_stats() -> Dict:
    sb = get_supabase()
    docs = sb.table("documents").select("knowledge_type, chunk_count, status").eq("status", "indexed").execute().data
    total = len(docs)
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)
    by_type: Dict[str, int] = {}
    for d in docs:
        kt = d.get("knowledge_type", "explicit")
        by_type[kt] = by_type.get(kt, 0) + 1
    return {
        "total_documents": total,
        "total_chunks": total_chunks,
        "by_type": by_type,
    }


# ═══════════════════════════════════════════════════════════
#  KNOWLEDGE GAP OPERATIONS
# ═══════════════════════════════════════════════════════════

def log_knowledge_gap(query: str, confidence_score: float, severity: str) -> int:
    sb = get_supabase()
    result = sb.table("knowledge_gaps").insert({
        "query": query,
        "confidence_score": confidence_score,
        "severity": severity,
    }).execute()
    return result.data[0]["id"]


def get_knowledge_gaps(resolved: bool = False, limit: int = 50) -> List[Dict]:
    sb = get_supabase()
    result = (
        sb.table("knowledge_gaps")
        .select("*")
        .eq("resolved", resolved)
        .order("detected_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def resolve_knowledge_gap(gap_id: int, user_id: str):
    sb = get_supabase()
    sb.table("knowledge_gaps").update({
        "resolved": True,
        "resolved_by": user_id,
        "resolved_at": datetime.utcnow().isoformat(),
    }).eq("id", gap_id).execute()


def get_gap_stats() -> Dict:
    sb = get_supabase()
    all_gaps = sb.table("knowledge_gaps").select("resolved, severity").execute().data
    total = len(all_gaps)
    unresolved = sum(1 for g in all_gaps if not g.get("resolved"))
    by_severity: Dict[str, int] = {}
    for g in all_gaps:
        if not g.get("resolved"):
            sev = g.get("severity", "medium")
            by_severity[sev] = by_severity.get(sev, 0) + 1
    return {
        "total_gaps": total,
        "unresolved": unresolved,
        "resolved": total - unresolved,
        "by_severity": by_severity,
    }


# ═══════════════════════════════════════════════════════════
#  CONVERSATION OPERATIONS
# ═══════════════════════════════════════════════════════════

def create_conversation(conversation_id: str, user_id: str, title: str = "New Conversation") -> str:
    sb = get_supabase()
    sb.table("conversations").upsert({
        "id": conversation_id,
        "user_id": user_id,
        "title": title,
    }, on_conflict="id").execute()
    return conversation_id


def get_user_conversations(user_id: str) -> List[Dict]:
    sb = get_supabase()
    try:
        result = (
            sb.table("conversations")
            .select("*, messages(count)")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
    except Exception:
        # Fallback without embedded count if the relationship query fails
        logger.warning("Embedded messages(count) query failed, falling back to simple select")
        result = (
            sb.table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return [
            {**c, "message_count": 0}
            for c in result.data
        ]
    convos = []
    for c in result.data:
        msg_count = 0
        if isinstance(c.get("messages"), list) and len(c["messages"]) > 0:
            msg_count = c["messages"][0].get("count", 0)
        convos.append({
            **c,
            "message_count": msg_count,
        })
    return convos


def get_conversation(conversation_id: str, user_id: str) -> Optional[Dict]:
    sb = get_supabase()
    try:
        result = (
            sb.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data
    except Exception:
        # Fallback: some SDK versions don't support maybe_single()
        result = (
            sb.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None


def update_conversation(conversation_id: str, user_id: str, title: Optional[str] = None):
    sb = get_supabase()
    updates: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}
    if title:
        updates["title"] = title
    sb.table("conversations").update(updates).eq("id", conversation_id).eq("user_id", user_id).execute()


def delete_conversation(conversation_id: str, user_id: str) -> bool:
    sb = get_supabase()
    result = sb.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()
    return len(result.data) > 0


# ═══════════════════════════════════════════════════════════
#  MESSAGE OPERATIONS
# ═══════════════════════════════════════════════════════════

def add_message(message_id: str, conversation_id: str, role: str, content: str,
                response_data: Optional[str] = None):
    sb = get_supabase()
    sb.table("messages").upsert({
        "id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "response_data": response_data,
    }, on_conflict="id").execute()
    # Update conversation timestamp
    sb.table("conversations").update({
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", conversation_id).execute()


def get_conversation_messages(conversation_id: str) -> List[Dict]:
    sb = get_supabase()
    result = (
        sb.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return result.data
