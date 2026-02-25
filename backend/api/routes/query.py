"""
Query route handlers.

Implements the main query endpoint for the RAG system.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.deps import (
    get_rag_service,
    get_validation,
    RAGServiceDep,
    ValidationServiceDep,
)
from backend.core.logging import APILogger, get_logger
from backend.schemas.query import (
    QueryRequest,
    QueryResponse,
    QueryErrorResponse,
)
from backend.supabase_client import get_current_user

# Import DB for gap logging
try:
    from backend.db import log_knowledge_gap
except ImportError:
    log_knowledge_gap = None


router = APIRouter(prefix="/query", tags=["query"])
logger = get_logger(__name__)
api_logger = APILogger(__name__)


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Successful query response",
            "model": QueryResponse,
        },
        400: {
            "description": "Validation error",
            "model": QueryErrorResponse,
        },
        500: {
            "description": "Internal server error",
            "model": QueryErrorResponse,
        },
        503: {
            "description": "Service unavailable",
            "model": QueryErrorResponse,
        },
    },
    summary="Query the knowledge system",
    description="""
    Execute a query against the RAG-based knowledge continuity system.
    
    This endpoint supports three advanced knowledge features:
    
    1. **Tacit Knowledge Extraction**: Identifies and surfaces experiential 
       knowledge from lessons learned, retrospectives, and exit interviews.
    
    2. **Decision Traceability**: When decision documents are used in the 
       response, provides full context including rationale, alternatives 
       considered, and trade-offs.
    
    3. **Knowledge Gap Detection**: Automatically detects when the system 
       cannot provide a confident answer and flags potential gaps in the 
       knowledge base.
    
    The response includes source documents, confidence scores, and detailed 
    metadata about the knowledge features used.
    """,
)
async def query(
    request: QueryRequest,
    rag_service: Annotated[RAGServiceDep, Depends(get_rag_service)],
    validation: Annotated[ValidationServiceDep, Depends(get_validation)],
    user=Depends(get_current_user),
) -> QueryResponse:
    """
    Query the RAG knowledge system.
    
    Args:
        request: Query request with question and options
        rag_service: Injected RAG service
        validation: Injected validation service
        user: Authenticated user (used for per-user retrieval)
        
    Returns:
        QueryResponse with answer and knowledge features
    """
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())[:8]
    
    # Log request
    api_logger.request(
        method="POST",
        path="/api/query",
        request_id=request_id,
        body={"question": request.question[:100] + "..." if len(request.question) > 100 else request.question},
    )
    
    # Validate question
    validated_question = validation.validate_question(request.question)
    validated_conversation_id = validation.validate_conversation_id(request.conversation_id)
    validated_department = validation.validate_department(request.department)
    
    # Update request with validated values
    request.question = validated_question
    request.conversation_id = validated_conversation_id
    request.department = validated_department
    
    # Execute query (pass user_id for per-user vector filtering)
    response = await rag_service.query(request, user_id=user["id"])
    
    # Log knowledge gap if detected
    if response.knowledge_gap.detected:
        api_logger.knowledge_gap(
            query=request.question,
            confidence_score=response.knowledge_gap.confidence_score,
            severity=response.knowledge_gap.severity,
        )
        # Persist gap to database for dashboard tracking
        if log_knowledge_gap:
            try:
                log_knowledge_gap(
                    query=request.question,
                    confidence_score=response.knowledge_gap.confidence_score,
                    severity=response.knowledge_gap.severity or "medium",
                )
            except Exception:
                pass
    
    # Log response
    api_logger.response(
        status_code=200,
        request_id=request_id,
        body={"answer_length": len(response.answer), "confidence": response.confidence},
    )
    
    return response


@router.post(
    "/batch",
    response_model=list[QueryResponse],
    status_code=status.HTTP_200_OK,
    summary="Batch query the knowledge system",
    description="Execute multiple queries in a single request.",
)
async def batch_query(
    requests: list[QueryRequest],
    rag_service: Annotated[RAGServiceDep, Depends(get_rag_service)],
    validation: Annotated[ValidationServiceDep, Depends(get_validation)],
) -> list[QueryResponse]:
    """
    Execute multiple queries.
    
    Args:
        requests: List of query requests
        rag_service: Injected RAG service
        validation: Injected validation service
        
    Returns:
        List of QueryResponse objects
    """
    if len(requests) > 10:
        from backend.core.exceptions import ValidationError
        raise ValidationError(
            message="Maximum 10 queries per batch",
            field="requests"
        )
    
    responses = []
    for request in requests:
        # Validate
        request.question = validation.validate_question(request.question)
        request.conversation_id = validation.validate_conversation_id(request.conversation_id)
        request.department = validation.validate_department(request.department)
        
        # Execute
        response = await rag_service.query(request)
        responses.append(response)
    
    return responses
