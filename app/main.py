"""
FastAPI应用主入口
"""
import asyncio
import importlib
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.dependencies import get_factor_paper_run_manager, get_paper_run_manager
from app.rate_limit import limiter
from app.routers import backtest, config_router, factor, market, tools
from config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"


def _logger():
    from utils.logger import logger

    return logger


def _init_db() -> None:
    from app.infra.db.database import init_db

    init_db()


def _import_market_cron_module():
    return importlib.import_module("app.services.market_cron")


def _resolve_frontend_asset(path: str) -> Path | None:
    if not FRONTEND_DIST_DIR.exists():
        return None

    candidate = (FRONTEND_DIST_DIR / path).resolve()
    frontend_root = FRONTEND_DIST_DIR.resolve()
    if frontend_root not in candidate.parents and candidate != frontend_root:
        return None
    if candidate.is_file():
        return candidate
    return None


def _frontend_not_ready_payload() -> dict[str, str]:
    return {
        "message": "Heimdall API is running",
        "docs": "/docs",
        "frontend_dev": f"http://127.0.0.1:{settings.FRONTEND_DEV_PORT}",
    }


async def root():
    """返回前端入口或 API 状态。"""
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(str(FRONTEND_INDEX_FILE))
    return _frontend_not_ready_payload()


async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "2.0.0"}


async def frontend_fallback(full_path: str):
    """Serve the built SPA and let the client router handle non-API paths."""
    reserved_paths = {"api", "docs", "redoc", "openapi.json", "health"}
    if full_path in reserved_paths or any(full_path.startswith(f"{prefix}/") for prefix in reserved_paths):
        raise HTTPException(status_code=404, detail="Not found")

    if not FRONTEND_INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found")

    asset = _resolve_frontend_asset(full_path)
    if asset:
        return FileResponse(str(asset))
    return FileResponse(str(FRONTEND_INDEX_FILE))


async def global_exception_handler(request: Request, exc: Exception):
    _logger().error(f"Unhandled: {request.method} {request.url} - {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def _register_routes(app: FastAPI) -> None:
    app.include_router(market.router, prefix="/api/v1", tags=["市场数据"])
    app.include_router(factor.router, prefix="/api/v1", tags=["因子研究"])
    app.include_router(backtest.router, prefix="/api/v1", tags=["回测"])
    app.include_router(tools.router, prefix="/api/v1/tools", tags=["工具"])
    app.include_router(config_router.router, prefix="/api/v1", tags=["配置"])
    app.add_api_route("/", root, methods=["GET"], include_in_schema=False)
    app.add_api_route("/health", health_check, methods=["GET"])
    app.add_api_route("/{full_path:path}", frontend_fallback, methods=["GET"], include_in_schema=False)


async def _init_db_async(app: FastAPI) -> None:
    try:
        await asyncio.to_thread(_init_db)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        app.state.database_error = exc
        _logger().error(f"数据库初始化失败: {exc}", exc_info=True)


async def _start_background_services(app: FastAPI) -> None:
    try:
        database_task = getattr(app.state, "database_task", None)
        if database_task is not None:
            await database_task
        if getattr(app.state, "database_error", None) is not None:
            return

        market_cron = await asyncio.to_thread(_import_market_cron_module)
        market_cron.start_scheduler()
        paper_manager = get_paper_run_manager()
        factor_paper_manager = get_factor_paper_run_manager()
        await paper_manager.restore_active_runs()
        await factor_paper_manager.restore_active_runs()

        app.state.paper_run_manager = paper_manager
        app.state.factor_paper_run_manager = factor_paper_manager
        app.state.market_scheduler = market_cron.scheduler
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        app.state.background_services_error = exc
        _logger().error(f"后台服务启动失败: {exc}", exc_info=True)


async def _shutdown_background_services(app: FastAPI) -> None:
    factor_manager = getattr(app.state, "factor_paper_run_manager", None)
    paper_manager = getattr(app.state, "paper_run_manager", None)
    scheduler = getattr(app.state, "market_scheduler", None)

    if factor_manager is not None:
        await factor_manager.shutdown()
    if paper_manager is not None:
        await paper_manager.shutdown()
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()


async def _cancel_task(task: asyncio.Task | None) -> None:
    if task is None or task.done():
        return
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.database_error = None
    app.state.background_services_error = None
    app.state.paper_run_manager = None
    app.state.factor_paper_run_manager = None
    app.state.market_scheduler = None
    app.state.database_task = asyncio.create_task(_init_db_async(app))
    app.state.background_services_task = asyncio.create_task(_start_background_services(app))
    yield
    await _cancel_task(getattr(app.state, "background_services_task", None))
    await _cancel_task(getattr(app.state, "database_task", None))
    await _shutdown_background_services(app)


def _requires_database_initialization(path: str) -> bool:
    return path.startswith("/api/") and path != "/api/v1/status"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Heimdall",
        description="AI-Powered Crypto Trading Intelligence",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _register_routes(app)
    return app


app = create_app()


@app.middleware("http")
async def wait_for_background_services(request: Request, call_next):
    if _requires_database_initialization(request.url.path):
        database_task = getattr(request.app.state, "database_task", None)
        if database_task is not None and not database_task.done():
            await database_task
        if getattr(request.app.state, "database_error", None) is not None:
            return JSONResponse(status_code=503, content={"detail": "Database initialization failed"})
    return await call_next(request)


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
