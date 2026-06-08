from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.module import ModuleStatusResponse
from app.schemas.synapse import (
    SynapseInferRequest,
    SynapseProfileUpdateRequest,
    SynapseRunResponse,
)
from app.services.synapse import SynapseService, get_synapse_service
from app.services.synapse.profile import SynapseProfileService

router = APIRouter()


@router.get("", response_model=ModuleStatusResponse, summary="SYNAPSE module status")
def get_synapse_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="SYNAPSE")


@router.post(
    "/profile/infer",
    response_model=SynapseRunResponse,
    summary="Run SYNAPSE inference and persist the run",
)
def infer_synapse(
    payload: SynapseInferRequest,
    synapse_service: Annotated[SynapseService, Depends(get_synapse_service)],
    db: Annotated[Session, Depends(get_db_session)],
) -> SynapseRunResponse:
    try:
        inference_result = synapse_service.infer(payload.content)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SYNAPSE model files are not available.",
        ) from exc
    profile_service = SynapseProfileService(db)
    return profile_service.create_inference_run(payload, inference_result)


@router.post(
    "/profile/update",
    response_model=SynapseRunResponse,
    summary="Update a stored SYNAPSE profile with a persisted run",
)
def update_synapse_profile(
    payload: SynapseProfileUpdateRequest,
    synapse_service: Annotated[SynapseService, Depends(get_synapse_service)],
    db: Annotated[Session, Depends(get_db_session)],
) -> SynapseRunResponse:
    try:
        inference_result = synapse_service.infer(payload.content)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SYNAPSE model files are not available.",
        ) from exc
    profile_service = SynapseProfileService(db)
    return profile_service.create_inference_run(payload, inference_result)


@router.get(
    "/profile/user/{id}",
    response_model=SynapseRunResponse,
    summary="Get the latest SYNAPSE profile for a user",
)
def get_user_profile(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
) -> SynapseRunResponse:
    profile_service = SynapseProfileService(db)
    run = profile_service.get_latest_profile("user", id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return run


@router.get(
    "/profile/expert/{id}",
    response_model=SynapseRunResponse,
    summary="Get the latest SYNAPSE profile for an expert",
)
def get_expert_profile(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
) -> SynapseRunResponse:
    profile_service = SynapseProfileService(db)
    run = profile_service.get_latest_profile("expert", id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return run


@router.get(
    "/runs/{id}",
    response_model=SynapseRunResponse,
    summary="Get a persisted SYNAPSE inference run",
)
def get_synapse_run(
    id: int,
    db: Annotated[Session, Depends(get_db_session)],
) -> SynapseRunResponse:
    profile_service = SynapseProfileService(db)
    run = profile_service.get_run(id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return run
