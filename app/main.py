"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.exceptions import AppError, app_error_handler, unhandled_exception_handler, value_error_handler
from app.lifecycle import lifespan, wait_for_background_services
from app.rate_limit import limiter
from app.web import register_app_routes
from config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Heimdall",
        description="AI-Powered Crypto Trading Intelligence",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_app_routes(app)

    @app.middleware("http")
    async def _wait_for_background_services(request, call_next):
        return await wait_for_background_services(request, call_next)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        reload_dirs=["app", "config", "utils"],
        reload_excludes=["data/*", "logs/*", "frontend/dist/*"],
    )
