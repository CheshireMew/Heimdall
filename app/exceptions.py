from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse

from utils.logger import logger


@dataclass(slots=True)
class AppError(Exception):
    detail: str
    status_code: int = 400


class BadRequestError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=400)


class NotFoundError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=404)


class ServiceUnavailableError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=503)


async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {request.method} {request.url} - {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
