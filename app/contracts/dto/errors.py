from __future__ import annotations

from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    detail: str
