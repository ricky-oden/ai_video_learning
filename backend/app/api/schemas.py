from typing import Any

from pydantic import BaseModel, Field


class ApiFieldError(BaseModel):
    field: str
    message: str
    type: str


class ApiErrorBody(BaseModel):
    code: str
    message: str
    field_errors: list[ApiFieldError] = Field(default_factory=list)
    conflict: dict[str, Any] | None = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorBody
