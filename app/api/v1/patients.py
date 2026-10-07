"""Anonymized Patient Records API Endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.constants import Gender, PatientStatus, Permission
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardErrorResponse
from app.schemas.patient import (
    PatientCreate,
    PatientFilterParams,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "",
    response_model=PaginatedResponse[PatientResponse],
    summary="List Anonymized Patients",
    description="Retrieve a paginated list of anonymized patient records with filtering by demographics and registration dates.",
    dependencies=[Depends(require_permission(Permission.PATIENTS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires patients.read"},
    },
)
def list_patients(
    search: Optional[str] = Query(
        None, description="Search by anonymized patient code (e.g. PT-0001)"
    ),
    gender: Optional[Gender] = Query(None, description="Filter by gender"),
    age_min: Optional[int] = Query(None, ge=0, le=125, alias="ageMin", description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=125, alias="ageMax", description="Maximum age"),
    status: Optional[PatientStatus] = Query(None, description="Filter by patient status"),
    date_from: Optional[date] = Query(None, alias="dateFrom", description="Registration date from"),
    date_to: Optional[date] = Query(None, alias="dateTo", description="Registration date to"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize", description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PatientResponse]:
    filters = PatientFilterParams(
        search=search,
        gender=gender,
        age_min=age_min,
        age_max=age_max,
        status=status,
        registration_date_from=date_from,
        registration_date_to=date_to,
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    service = PatientService(db)
    return service.get_patients(filters, pagination)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Anonymized Patient",
    description="Create a new anonymized patient profile. Auto-generates PT-xxxx code if not provided.",
    dependencies=[Depends(require_permission(Permission.PATIENTS_CREATE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {
            "model": StandardErrorResponse,
            "description": "Forbidden - requires patients.create",
        },
        409: {"model": StandardErrorResponse, "description": "Patient code already exists"},
    },
)
def create_patient(
    payload: PatientCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = PatientService(db)
    return service.create_patient(
        payload, actor=current_user, ip_address=ip_addr, request_id=req_id
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get Anonymized Patient by ID",
    description="Fetch a single patient record by internal ID.",
    dependencies=[Depends(require_permission(Permission.PATIENTS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "Patient not found"},
    },
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
) -> PatientResponse:
    service = PatientService(db)
    return service.get_patient_by_id(patient_id)


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update Patient Record",
    description="Update non-identifiable demographics (age, gender, status).",
    dependencies=[Depends(require_permission(Permission.PATIENTS_UPDATE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "Patient not found"},
    },
)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = PatientService(db)
    return service.update_patient(
        patient_id, payload, actor=current_user, ip_address=ip_addr, request_id=req_id
    )


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Patient Record",
    description="Permanently delete a patient record and cascaded encounters. Requires admin permission.",
    dependencies=[Depends(require_permission(Permission.PATIENTS_DELETE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {
            "model": StandardErrorResponse,
            "description": "Forbidden - requires patients.delete",
        },
        404: {"model": StandardErrorResponse, "description": "Patient not found"},
    },
)
def delete_patient(
    patient_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = PatientService(db)
    service.delete_patient(patient_id, actor=current_user, ip_address=ip_addr, request_id=req_id)
