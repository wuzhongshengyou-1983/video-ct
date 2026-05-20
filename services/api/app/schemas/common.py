"""通用 schemas."""
from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20


class ApiResponse(BaseModel, Generic[T]):
    code: str = "OK"
    message: str = "success"
    data: T | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    trace_id: str | None = None
    details: dict | None = None
