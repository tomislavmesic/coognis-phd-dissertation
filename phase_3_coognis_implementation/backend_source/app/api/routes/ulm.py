from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.module import ModuleStatusResponse
from app.schemas.ulm import (
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
    UlmRetrieveRequest,
    UlmRetrievedContext,
    UlmGenerateRequest,
    UlmGenerateResponse,
    UlmIngestRequest,
)
from app.services.local_llm import LocalLlmClient
from app.services.ulm import UlmService, get_llm_client

router = APIRouter()


@router.get("", response_model=ModuleStatusResponse, summary="ULM module status")
def get_ulm_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="ULM")


@router.post("/ingest", response_model=KnowledgeSourceResponse)
def ingest_source(
    payload: UlmIngestRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeSourceResponse:
    service = UlmService(db)
    try:
        return service.ingest(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/generate", response_model=UlmGenerateResponse)
def generate_explanation(
    payload: UlmGenerateRequest,
    db: Annotated[Session, Depends(get_db_session)],
    llm_client: Annotated[LocalLlmClient, Depends(get_llm_client)],
) -> UlmGenerateResponse:
    service = UlmService(db)
    return service.generate(payload, llm_client)


@router.post("/retrieve", response_model=UlmRetrievedContext)
def retrieve_context(
    payload: UlmRetrieveRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> UlmRetrievedContext:
    service = UlmService(db)
    return service.retrieve(payload)


@router.get("/sources", response_model=KnowledgeSourceListResponse)
def list_sources(
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeSourceListResponse:
    service = UlmService(db)
    return service.list_sources()
