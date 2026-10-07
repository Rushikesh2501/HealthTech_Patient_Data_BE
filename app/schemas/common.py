"""Common schemas for pagination, standard responses, and error envelopes."""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page: int
    page_size: int = Field(alias="pageSize")
    total: int
    total_pages: int = Field(alias="totalPages")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    data: List[T]
    pagination: PaginationMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None
