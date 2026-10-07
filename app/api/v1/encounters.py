"""Clinical Encounters API Endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.constants import EncounterStatus, Permission
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardErrorResponse
from app.schemas.encounter import (
    EncounterCreate,
    EncounterFilterParams,
    EncounterResponse,
    EncounterUpdate,
)
from app.services.encounter_service import EncounterService

router = APIRouter(prefix="/encounters", tags=["Encounters"])


@router.get(
    "",
    response_model=PaginatedResponse[EncounterResponse],
    summary="List Encounters",
    description="Retrieve a paginated list of clinical encounters with filters for patient, diagnosis, status, and dates.",
    dependencies=[Depends(require_permission(Permission.ENCOUNTERS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {
            "model": StandardErrorResponse,
            "description": "Forbidden - requires encounters.read",
        },
    },
)
def list_encounters(
    search: Optional[str] = Query(None, description="Search by diagnosis, symptoms, or codes"),
    patient_id: Optional[int] = Query(None, alias="patientId", description="Filter by patient ID"),
    clinician_id: Optional[int] = Query(
        None, alias="clinicianId", description="Filter by clinician ID"
    ),
    diagnosis: Optional[str] = Query(None, description="Filter by specific diagnosis name"),
    status: Optional[EncounterStatus] = Query(None, description="Filter by encounter status"),
    date_from: Optional[datetime] = Query(
        None, alias="dateFrom", description="Encounter timestamp from"
    ),
    date_to: Optional[datetime] = Query(None, alias="dateTo", description="Encounter timestamp to"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize", description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EncounterResponse]:
    filters = EncounterFilterParams(
        search=search,
        patient_id=patient_id,
        clinician_id=clinician_id,
        diagnosis=diagnosis,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    service = EncounterService(db)
    return service.get_encounters(filters, pagination)


@router.post(
    "",
    response_model=EncounterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Clinical Encounter",
    description="Log a new consultation encounter including symptoms, diagnosis, vitals, and prescribed treatment.",
    dependencies=[Depends(require_permission(Permission.ENCOUNTERS_CREATE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {
            "model": StandardErrorResponse,
            "description": "Forbidden - requires encounters.create",
        },
        404: {"model": StandardErrorResponse, "description": "Patient not found"},
    },
)
def create_encounter(
    payload: EncounterCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EncounterResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = EncounterService(db)
    return service.create_encounter(
        payload, actor=current_user, ip_address=ip_addr, request_id=req_id
    )


@router.get(
    "/{encounter_id}",
    response_model=EncounterResponse,
    summary="Get Encounter Details",
    description="Fetch a single clinical encounter record by ID.",
    dependencies=[Depends(require_permission(Permission.ENCOUNTERS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "Encounter not found"},
    },
)
def get_encounter(
    encounter_id: int,
    db: Session = Depends(get_db),
) -> EncounterResponse:
    service = EncounterService(db)
    return service.get_encounter_by_id(encounter_id)


@router.patch(
    "/{encounter_id}",
    response_model=EncounterResponse,
    summary="Update Encounter",
    description="Update encounter symptoms, diagnosis, treatment, or vitals.",
    dependencies=[Depends(require_permission(Permission.ENCOUNTERS_UPDATE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "Encounter not found"},
    },
)
def update_encounter(
    encounter_id: int,
    payload: EncounterUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EncounterResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = EncounterService(db)
    return service.update_encounter(
        encounter_id, payload, actor=current_user, ip_address=ip_addr, request_id=req_id
    )


@router.delete(
    "/{encounter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Encounter",
    description="Permanently delete an encounter. Requires admin permission.",
    dependencies=[Depends(require_permission(Permission.ENCOUNTERS_DELETE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {
            "model": StandardErrorResponse,
            "description": "Forbidden - requires encounters.delete",
        },
        404: {"model": StandardErrorResponse, "description": "Encounter not found"},
    },
)
def delete_encounter(
    encounter_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = EncounterService(db)
    service.delete_encounter(
        encounter_id, actor=current_user, ip_address=ip_addr, request_id=req_id
    )
