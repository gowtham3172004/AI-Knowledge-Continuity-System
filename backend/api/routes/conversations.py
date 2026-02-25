"""
Conversation management routes.

Handles CRUD for conversations and message persistence.
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.supabase_client import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)


def _get_db():
    """Lazy import of db functions to catch import errors gracefully."""
    from backend.db import (
        create_conversation,
        get_user_conversations,
        get_conversation,
        update_conversation,
        delete_conversation,
        add_message,
        get_conversation_messages,
    )
    return {
        "create_conversation": create_conversation,
        "get_user_conversations": get_user_conversations,
        "get_conversation": get_conversation,
        "update_conversation": update_conversation,
        "delete_conversation": delete_conversation,
        "add_message": add_message,
        "get_conversation_messages": get_conversation_messages,
    }


# --- Schemas ---

class CreateConversationRequest(BaseModel):
    id: str
    title: str = "New Conversation"


class UpdateConversationRequest(BaseModel):
    title: str


class SaveMessageRequest(BaseModel):
    id: str
    role: str  # "user" or "assistant"
    content: str
    response_data: Optional[str] = None  # JSON string for assistant metadata


class ConversationResponse(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    response_data: Optional[str] = None
    created_at: str


# --- Endpoints ---

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(user=Depends(get_current_user)):
    """List all conversations for the current user."""
    try:
        db = _get_db()
        convos = db["get_user_conversations"](user["id"])
        return [
            ConversationResponse(
                id=c["id"],
                title=c["title"],
                message_count=c.get("message_count", 0),
                created_at=c.get("created_at") or "",
                updated_at=c.get("updated_at") or "",
            )
            for c in convos
        ]
    except Exception as e:
        logger.exception(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.post("/", response_model=ConversationResponse)
async def create_new_conversation(
    req: CreateConversationRequest,
    user=Depends(get_current_user),
):
    """Create a new conversation."""
    try:
        db = _get_db()
        db["create_conversation"](req.id, user["id"], req.title)
        return ConversationResponse(
            id=req.id,
            title=req.title,
            message_count=0,
            created_at="",
            updated_at="",
        )
    except Exception as e:
        logger.exception(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.put("/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    req: UpdateConversationRequest,
    user=Depends(get_current_user),
):
    """Rename a conversation."""
    try:
        db = _get_db()
        conv = db["get_conversation"](conversation_id, user["id"])
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        db["update_conversation"](conversation_id, user["id"], req.title)
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error renaming conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    user=Depends(get_current_user),
):
    """Delete a conversation and all its messages."""
    try:
        db = _get_db()
        success = db["delete_conversation"](conversation_id, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: str,
    user=Depends(get_current_user),
):
    """Get all messages in a conversation."""
    try:
        db = _get_db()
        conv = db["get_conversation"](conversation_id, user["id"])
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        msgs = db["get_conversation_messages"](conversation_id)
        return [
            MessageResponse(
                id=m["id"],
                conversation_id=m["conversation_id"],
                role=m["role"],
                content=m["content"],
                response_data=m.get("response_data"),
                created_at=m.get("created_at") or "",
            )
            for m in msgs
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error listing messages: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")


@router.post("/{conversation_id}/messages")
async def save_message(
    conversation_id: str,
    req: SaveMessageRequest,
    user=Depends(get_current_user),
):
    """Save a message to a conversation."""
    try:
        db = _get_db()
        # Auto-create conversation if it doesn't exist
        conv = db["get_conversation"](conversation_id, user["id"])
        if not conv:
            db["create_conversation"](conversation_id, user["id"])

        db["add_message"](
            message_id=req.id,
            conversation_id=conversation_id,
            role=req.role,
            content=req.content,
            response_data=req.response_data,
        )
        return {"status": "saved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error saving message: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:200]}")
