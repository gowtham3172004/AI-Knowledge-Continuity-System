"""
Conversation management routes.

Handles CRUD for conversations and message persistence.
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.db import (
    create_conversation,
    get_user_conversations,
    get_conversation,
    update_conversation,
    delete_conversation,
    add_message,
    get_conversation_messages,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)


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
    convos = get_user_conversations(user["id"])
    return [
        ConversationResponse(
            id=c["id"],
            title=c["title"],
            message_count=c["message_count"],
            created_at=c["created_at"] or "",
            updated_at=c["updated_at"] or "",
        )
        for c in convos
    ]


@router.post("/", response_model=ConversationResponse)
async def create_new_conversation(
    req: CreateConversationRequest,
    user=Depends(get_current_user),
):
    """Create a new conversation."""
    create_conversation(req.id, user["id"], req.title)
    return ConversationResponse(
        id=req.id,
        title=req.title,
        message_count=0,
        created_at="",
        updated_at="",
    )


@router.put("/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    req: UpdateConversationRequest,
    user=Depends(get_current_user),
):
    """Rename a conversation."""
    conv = get_conversation(conversation_id, user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    update_conversation(conversation_id, user["id"], req.title)
    return {"status": "updated"}


@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    user=Depends(get_current_user),
):
    """Delete a conversation and all its messages."""
    success = delete_conversation(conversation_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: str,
    user=Depends(get_current_user),
):
    """Get all messages in a conversation."""
    conv = get_conversation(conversation_id, user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = get_conversation_messages(conversation_id)
    return [
        MessageResponse(
            id=m["id"],
            conversation_id=m["conversation_id"],
            role=m["role"],
            content=m["content"],
            response_data=m["response_data"],
            created_at=m["created_at"] or "",
        )
        for m in msgs
    ]


@router.post("/{conversation_id}/messages")
async def save_message(
    conversation_id: str,
    req: SaveMessageRequest,
    user=Depends(get_current_user),
):
    """Save a message to a conversation."""
    # Auto-create conversation if it doesn't exist
    conv = get_conversation(conversation_id, user["id"])
    if not conv:
        create_conversation(conversation_id, user["id"])

    add_message(
        message_id=req.id,
        conversation_id=conversation_id,
        role=req.role,
        content=req.content,
        response_data=req.response_data,
    )
    return {"status": "saved"}
