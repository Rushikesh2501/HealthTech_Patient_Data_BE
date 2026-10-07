"""User Management API Endpoints (Admin RBAC Protected)."""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.constants import Permission
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardErrorResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List System Users",
    description="Retrieve a paginated list of registered staff and administrative accounts.",
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires users.read"},
    },
)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize", description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    service = UserService(db)
    return service.get_users(pagination)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User Account",
    description="Create a new clinician, nurse, or admin account.",
    dependencies=[Depends(require_permission(Permission.USERS_CREATE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires users.create"},
        409: {"model": StandardErrorResponse, "description": "Email already exists"},
    },
)
def create_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = UserService(db)
    return service.create_user(payload, actor=current_user, ip_address=ip_addr, request_id=req_id)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User Details",
    description="Retrieve a specific user profile by numeric ID.",
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "User not found"},
    },
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    return service.get_user_by_id(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User Profile",
    description="Update a user's name, role, active status, or password.",
    dependencies=[Depends(require_permission(Permission.USERS_UPDATE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "User not found"},
    },
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = UserService(db)
    return service.update_user(
        user_id, payload, actor=current_user, ip_address=ip_addr, request_id=req_id
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User Account",
    description="Permanently delete a user account. Cannot delete one's own account.",
    dependencies=[Depends(require_permission(Permission.USERS_DELETE))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
        404: {"model": StandardErrorResponse, "description": "User not found"},
        409: {"model": StandardErrorResponse, "description": "Self-deletion forbidden"},
    },
)
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = UserService(db)
    service.delete_user(user_id, actor=current_user, ip_address=ip_addr, request_id=req_id)
