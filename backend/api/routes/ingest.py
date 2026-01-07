"""
Ingestion route handlers.

Implements endpoints for document ingestion and indexing.
These are admin-protected endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.deps import (
    get_ingest_service,
    verify_admin_api_key,
    IngestServiceDep,
    AdminKeyDep,
)
from backend.core.logging import get_logger
from backend.schemas.ingest import (
    IngestRequest,
    IngestResponse,
    IngestStatusResponse,
)


router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest documents",
    description="""
    Ingest documents into the knowledge base.
    
    This endpoint supports multiple ingestion modes:
    - **directory_scan**: Scan a directory for documents
    - **file_upload**: Ingest specific files
    - **text**: Ingest raw text content
    
    Documents are automatically:
    1. Classified by knowledge type (tacit, explicit, decision)
    2. Parsed for decision metadata if applicable
    3. Chunked with appropriate overlap
    4. Indexed in the vector store
    
    **Requires admin API key.**
    """,
    dependencies=[Depends(verify_admin_api_key)],
)
async def ingest_documents(
    request: IngestRequest,
    ingest_service: Annotated[IngestServiceDep, Depends(get_ingest_service)],
    _admin: Annotated[AdminKeyDep, Depends(verify_admin_api_key)],
) -> IngestResponse:
    """
    Ingest documents into the knowledge base.
    
    Args:
        request: Ingestion request
        ingest_service: Injected ingestion service
        _admin: Admin verification (dependency)
        
    Returns:
        IngestResponse with ingestion results
    """
    logger.info(
        "Ingestion request received",
        extra={
            "source": request.source.value,
            "force_reindex": request.force_reindex,
        }
    )
    
    return await ingest_service.ingest(request)


@router.get(
    "/status",
    response_model=IngestStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ingestion status",
    description="Check the status of ongoing ingestion operations.",
)
async def get_ingest_status(
    ingest_service: Annotated[IngestServiceDep, Depends(get_ingest_service)],
) -> IngestStatusResponse:
    """
    Get current ingestion status.
    
    Args:
        ingest_service: Injected ingestion service
        
    Returns:
        IngestStatusResponse with current status
    """
    status_data = ingest_service.get_status()
    
    return IngestStatusResponse(
        is_indexing=status_data["is_indexing"],
        current_document=status_data["current_document"],
        progress=status_data["progress"],
        documents_processed=status_data["documents_processed"],
        documents_total=status_data["documents_total"],
    )


@router.post(
    "/reindex",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Reindex all documents",
    description="""
    Reindex all documents in the data directory.
    
    This will:
    1. Clear the existing vector store
    2. Reload all documents from the data directory
    3. Reclassify and reindex everything
    
    **Use with caution - this is a long-running operation.**
    
    **Requires admin API key.**
    """,
    dependencies=[Depends(verify_admin_api_key)],
)
async def reindex_all(
    ingest_service: Annotated[IngestServiceDep, Depends(get_ingest_service)],
    _admin: Annotated[AdminKeyDep, Depends(verify_admin_api_key)],
) -> IngestResponse:
    """
    Reindex all documents.
    
    Args:
        ingest_service: Injected ingestion service
        _admin: Admin verification (dependency)
        
    Returns:
        IngestResponse with reindexing results
    """
    from backend.core.config import api_settings
    
    logger.info("Full reindex requested")
    
    request = IngestRequest(
        source="directory_scan",
        directory_path=api_settings.DATA_DIR,
        force_reindex=True,
    )
    
    return await ingest_service.ingest(request)
