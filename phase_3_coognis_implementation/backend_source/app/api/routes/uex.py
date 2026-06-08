from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.module import ModuleStatusResponse
from app.schemas.uex import (
    ExpertAnalysisResponse,
    ExpertCreateRequest,
    ExpertMatchRequest,
    ExpertMatchResponse,
    ExpertResponse,
    KnowledgeItemCreateRequest,
    KnowledgeItemListResponse,
    KnowledgeItemResponse,
    KnowledgeItemUpdateRequest,
)
from app.services.synapse import get_synapse_inference_service
from app.services.synapse.inference import SynapseInferenceService
from app.services.uex import UexService

router = APIRouter()


@router.get("", response_model=ModuleStatusResponse, summary="UEX module status")
def get_uex_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="UEX")


@router.post("/experts", response_model=ExpertResponse, status_code=status.HTTP_201_CREATED)
def create_expert(
    payload: ExpertCreateRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertResponse:
    service = UexService(db)
    return service.create_expert(payload)


@router.post("/experts/match", response_model=ExpertMatchResponse)
def match_experts(
    payload: ExpertMatchRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertMatchResponse:
    service = UexService(db)
    return service.match_experts(payload)


@router.get("/experts/{id}", response_model=ExpertResponse)
def get_expert(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertResponse:
    service = UexService(db)
    try:
        return service.get_expert(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/experts/{id}/analyze", response_model=ExpertAnalysisResponse)
def analyze_expert(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
    synapse_inference_service: Annotated[
        SynapseInferenceService,
        Depends(get_synapse_inference_service),
    ],
) -> ExpertAnalysisResponse:
    service = UexService(db)
    try:
        return service.analyze_expert(id, synapse_inference_service)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/knowledge", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_item(
    payload: KnowledgeItemCreateRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeItemResponse:
    service = UexService(db)
    return service.create_knowledge_item(payload)


@router.get("/knowledge", response_model=KnowledgeItemListResponse)
def list_knowledge_items(
    db: Annotated[Session, Depends(get_db_session)],
    domain: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> KnowledgeItemListResponse:
    service = UexService(db)
    return service.list_knowledge_items(
        domain=domain,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/knowledge/{id}", response_model=KnowledgeItemResponse)
def get_knowledge_item(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeItemResponse:
    service = UexService(db)
    try:
        return service.get_knowledge_item(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/knowledge/{id}", response_model=KnowledgeItemResponse)
def update_knowledge_item(
    id: int,
    payload: KnowledgeItemUpdateRequest,
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeItemResponse:
    service = UexService(db)
    try:
        return service.update_knowledge_item(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/knowledge/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_knowledge_item(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    service = UexService(db)
    try:
        service.delete_knowledge_item(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
