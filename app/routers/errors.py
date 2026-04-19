from __future__ import annotations

from fastapi import HTTPException

from utils.logger import logger


def service_http_error(context: str, exc: Exception, *, value_status: int = 400) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ValueError):
        return HTTPException(status_code=value_status, detail=str(exc))
    logger.error(f"{context}: {exc}", exc_info=True)
    return HTTPException(status_code=500, detail="Internal server error")
