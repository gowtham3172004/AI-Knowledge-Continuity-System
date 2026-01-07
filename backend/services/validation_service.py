"""
Validation Service - Input validation and sanitization.

Provides centralized validation logic for API inputs,
including query sanitization and rate limiting support.
"""

import re
from typing import Any, Dict, List, Optional, Set

from backend.core.config import api_settings
from backend.core.exceptions import ValidationError
from backend.core.logging import get_logger


logger = get_logger(__name__)


# Patterns for detecting potential injection attempts
SUSPICIOUS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"on\w+\s*=",
    r"\{\{.*\}\}",  # Template injection
    r"\$\{.*\}",    # Expression injection
]

# Maximum lengths
MAX_QUESTION_LENGTH = 2000
MAX_CONVERSATION_ID_LENGTH = 50
MAX_DEPARTMENT_LENGTH = 100


class ValidationService:
    """
    Service for input validation and sanitization.
    
    Provides centralized validation logic to ensure
    API inputs are safe and well-formed.
    """
    
    def __init__(self):
        """Initialize validation service."""
        self._suspicious_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in SUSPICIOUS_PATTERNS
        ]
        logger.info("Validation Service initialized")
    
    def validate_question(self, question: str) -> str:
        """
        Validate and sanitize a question.
        
        Args:
            question: Raw question input
            
        Returns:
            Sanitized question
            
        Raises:
            ValidationError: If question is invalid
        """
        if not question:
            raise ValidationError(
                message="Question is required",
                field="question"
            )
        
        # Strip whitespace
        question = question.strip()
        
        if len(question) < 3:
            raise ValidationError(
                message="Question must be at least 3 characters",
                field="question"
            )
        
        if len(question) > MAX_QUESTION_LENGTH:
            raise ValidationError(
                message=f"Question exceeds maximum length of {MAX_QUESTION_LENGTH}",
                field="question"
            )
        
        # Check for suspicious patterns
        for pattern in self._suspicious_patterns:
            if pattern.search(question):
                logger.warning(
                    "Suspicious pattern detected in question",
                    extra={"pattern": pattern.pattern}
                )
                raise ValidationError(
                    message="Question contains invalid content",
                    field="question"
                )
        
        return question
    
    def validate_conversation_id(
        self,
        conversation_id: Optional[str],
    ) -> Optional[str]:
        """
        Validate conversation ID.
        
        Args:
            conversation_id: Optional conversation ID
            
        Returns:
            Validated conversation ID or None
            
        Raises:
            ValidationError: If conversation ID is invalid
        """
        if not conversation_id:
            return None
        
        conversation_id = conversation_id.strip()
        
        if len(conversation_id) > MAX_CONVERSATION_ID_LENGTH:
            raise ValidationError(
                message=f"Conversation ID exceeds maximum length of {MAX_CONVERSATION_ID_LENGTH}",
                field="conversation_id"
            )
        
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
            raise ValidationError(
                message="Conversation ID contains invalid characters",
                field="conversation_id"
            )
        
        return conversation_id
    
    def validate_department(
        self,
        department: Optional[str],
    ) -> Optional[str]:
        """
        Validate department name.
        
        Args:
            department: Optional department name
            
        Returns:
            Validated department or None
            
        Raises:
            ValidationError: If department is invalid
        """
        if not department:
            return None
        
        department = department.strip()
        
        if len(department) > MAX_DEPARTMENT_LENGTH:
            raise ValidationError(
                message=f"Department exceeds maximum length of {MAX_DEPARTMENT_LENGTH}",
                field="department"
            )
        
        # Only allow alphanumeric, spaces, and common punctuation
        if not re.match(r"^[a-zA-Z0-9\s\-_&]+$", department):
            raise ValidationError(
                message="Department contains invalid characters",
                field="department"
            )
        
        return department
    
    def validate_file_path(self, path: str) -> str:
        """
        Validate file path for security.
        
        Args:
            path: File path to validate
            
        Returns:
            Validated path
            
        Raises:
            ValidationError: If path is invalid or unsafe
        """
        if not path:
            raise ValidationError(
                message="File path is required",
                field="path"
            )
        
        # Prevent directory traversal
        if ".." in path:
            raise ValidationError(
                message="Path traversal not allowed",
                field="path"
            )
        
        # Prevent absolute paths outside data directory
        # (This should be customized based on your security requirements)
        if path.startswith("/") and not path.startswith(api_settings.DATA_DIR):
            logger.warning(
                "Attempt to access path outside data directory",
                extra={"path": path}
            )
            raise ValidationError(
                message="Path outside allowed directory",
                field="path"
            )
        
        return path
    
    def validate_api_key(
        self,
        api_key: Optional[str],
        required: bool = False,
    ) -> bool:
        """
        Validate API key for admin operations.
        
        Args:
            api_key: API key to validate
            required: Whether API key is required
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If required and missing/invalid
        """
        if not api_key:
            if required:
                raise ValidationError(
                    message="API key is required",
                    field="api_key"
                )
            return False
        
        # Compare with configured admin key
        # Use constant-time comparison for security
        import hmac
        
        expected_key = api_settings.ADMIN_API_KEY
        if not expected_key:
            logger.warning("Admin API key not configured")
            if required:
                raise ValidationError(
                    message="Admin operations not configured",
                    field="api_key"
                )
            return False
        
        return hmac.compare_digest(api_key, expected_key)
    
    def sanitize_output(self, text: str) -> str:
        """
        Sanitize output text.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove any potential HTML/script content
        text = re.sub(r"<[^>]+>", "", text)
        
        return text.strip()


# Global instance
_validation_service: Optional[ValidationService] = None


def get_validation_service() -> ValidationService:
    """
    Get global validation service instance.
    
    Returns:
        ValidationService instance
    """
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service
