"""
Conversation Memory Module for AI Knowledge Continuity System.

This module provides conversation memory management for maintaining
context across multiple interactions in a session.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage

from config.settings import get_settings
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    human_message: str
    ai_message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "human": self.human_message,
            "ai": self.ai_message,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary."""
        return cls(
            human_message=data.get("human", ""),
            ai_message=data.get("ai", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConversationSession:
    """Represents a conversation session."""
    session_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(self, human_message: str, ai_message: str, **metadata) -> None:
        """Add a conversation turn."""
        turn = ConversationTurn(
            human_message=human_message,
            ai_message=ai_message,
            metadata=metadata,
        )
        self.turns.append(turn)
        self.last_active = datetime.now().isoformat()
    
    def get_history(self, max_turns: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history."""
        turns = self.turns
        if max_turns:
            turns = turns[-max_turns:]
        return [turn.to_dict() for turn in turns]
    
    def clear(self) -> None:
        """Clear conversation history."""
        self.turns = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "turns": [turn.to_dict() for turn in self.turns],
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        """Create from dictionary."""
        session = cls(
            session_id=data.get("session_id", "default"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_active=data.get("last_active", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )
        session.turns = [
            ConversationTurn.from_dict(turn)
            for turn in data.get("turns", [])
        ]
        return session


class ConversationMemoryManager:
    """
    Production-grade conversation memory manager.
    
    Features:
    - Multi-session support
    - Configurable history limits
    - Persistence to disk (optional)
    - LangChain memory integration
    - Session management
    
    Example:
        >>> manager = ConversationMemoryManager()
        >>> manager.add_exchange("session1", "Hello", "Hi there!")
        >>> history = manager.get_history("session1")
    """
    
    def __init__(
        self,
        max_turns: Optional[int] = None,
        persist_path: Optional[str] = None,
    ):
        """
        Initialize the conversation memory manager.
        
        Args:
            max_turns: Maximum conversation turns to remember per session.
            persist_path: Path to persist conversation history.
        """
        self.settings = get_settings()
        self.max_turns = max_turns or self.settings.MAX_CONVERSATION_HISTORY
        self.persist_path = Path(persist_path) if persist_path else None
        
        # Session storage
        self._sessions: Dict[str, ConversationSession] = {}
        
        # Load persisted sessions if available
        if self.persist_path:
            self._load_sessions()
        
        logger.info(f"ConversationMemoryManager initialized (max_turns={self.max_turns})")
    
    def _get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(session_id=session_id)
            logger.debug(f"Created new session: {session_id}")
        return self._sessions[session_id]
    
    def add_exchange(
        self,
        session_id: str,
        human_message: str,
        ai_message: str,
        **metadata,
    ) -> None:
        """
        Add a conversation exchange to a session.
        
        Args:
            session_id: Session identifier.
            human_message: The human's message.
            ai_message: The AI's response.
            **metadata: Additional metadata for the turn.
        """
        session = self._get_or_create_session(session_id)
        session.add_turn(human_message, ai_message, **metadata)
        
        # Trim to max turns if needed
        if self.max_turns and len(session.turns) > self.max_turns:
            session.turns = session.turns[-self.max_turns:]
        
        # Persist if enabled
        if self.persist_path:
            self._save_sessions()
        
        logger.debug(f"Added exchange to session {session_id}")
    
    def get_history(
        self,
        session_id: str,
        max_turns: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier.
            max_turns: Maximum turns to return.
            
        Returns:
            List of conversation turns.
        """
        if session_id not in self._sessions:
            return []
        
        session = self._sessions[session_id]
        return session.get_history(max_turns or self.max_turns)
    
    def clear_history(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            
            if self.persist_path:
                self._save_sessions()
            
            logger.info(f"Cleared history for session: {session_id}")
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session completely."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            
            if self.persist_path:
                self._save_sessions()
            
            logger.info(f"Deleted session: {session_id}")
    
    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        return {
            "session_id": session.session_id,
            "num_turns": len(session.turns),
            "created_at": session.created_at,
            "last_active": session.last_active,
        }
    
    def get_langchain_memory(
        self,
        session_id: str = "default",
        window_size: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Get conversation history in a dictionary format.
        
        Args:
            session_id: Session identifier.
            window_size: Number of recent turns to include.
            
        Returns:
            Dictionary with chat history.
        """
        k = window_size or self.max_turns
        history = self.get_history(session_id, max_turns=k)
        
        return {"chat_history": history}
    
    def format_history_as_string(
        self,
        session_id: str,
        max_turns: Optional[int] = None,
    ) -> str:
        """
        Format conversation history as a string.
        
        Args:
            session_id: Session identifier.
            max_turns: Maximum turns to include.
            
        Returns:
            Formatted conversation string.
        """
        history = self.get_history(session_id, max_turns)
        if not history:
            return ""
        
        formatted = []
        for turn in history:
            formatted.append(f"Human: {turn.get('human', '')}")
            formatted.append(f"Assistant: {turn.get('ai', '')}")
        
        return "\n".join(formatted)
    
    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        if not self.persist_path:
            return
        
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                session_id: session.to_dict()
                for session_id, session in self._sessions.items()
            }
            
            with open(self.persist_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._sessions)} sessions to {self.persist_path}")
            
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return
        
        try:
            with open(self.persist_path, 'r') as f:
                data = json.load(f)
            
            self._sessions = {
                session_id: ConversationSession.from_dict(session_data)
                for session_id, session_data in data.items()
            }
            
            logger.info(f"Loaded {len(self._sessions)} sessions from {self.persist_path}")
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self._sessions = {}


# Global memory manager instance
_memory_manager: Optional[ConversationMemoryManager] = None


def get_memory_manager() -> ConversationMemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ConversationMemoryManager()
    return _memory_manager


def create_memory() -> Dict[str, List]:
    """
    Create a simple conversation memory dictionary.
    
    This is a convenience function for backward compatibility.
    For production use, prefer the ConversationMemoryManager class.
    
    Returns:
        Dictionary with empty chat history.
    """
    return {"chat_history": [], "return_messages": True}
