from __future__ import annotations

from fastapi import HTTPException

from utils.logger import logger


def internal_error(detail: str, exc: Exception) -> HTTPException:
    logger.error(f"{detail}: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")
