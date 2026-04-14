"""
FastAPI应用主入口
"""
import asyncio
import importlib
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"
STARTUP_WARMUP_DELAY_SECONDS = 2.0
DEFAULT_CORS_ORIGINS = [
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def _setting_value(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is not None:
        return value

    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return default
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw_value = stripped.split("=", 1)
            if key.strip() == name:
                return raw_value.strip().strip("'\"")
    except OSError:
        return default
    return default


def _cors_origins() -> list[str]:
    raw = _setting_value("CORS_ORIGINS", "")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return DEFAULT_CORS_ORIGINS


def _frontend_dev_port() -> int:
    return int(_setting_value("FRONTEND_DEV_PORT", "4173"))


def _logger():
    from utils.logger import logger

    return logger


def _init_db() -> None:
    from app.infra.db.database import init_db

    init_db()


def _import_market_cron_module():
    return importlib.import_module("app.services.market_cron")


def _get_paper_run_manager():
    from app.dependencies import get_paper_run_manager

    return get_paper_run_manager()


def _get_factor_paper_run_manager():
    from app.dependencies import get_factor_paper_run_manager

    return get_factor_paper_run_manager()


def _import_runtime_route_modules():
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    from app.rate_limit import limiter
    from app.routers import backtest, config_router, factor, market, tools

    return {
        "backtest": backtest,
        "config_router": config_router,
        "factor": factor,
        "market": market,
        "tools": tools,
        "limiter": limiter,
        "rate_limit_exceeded": RateLimitExceeded,
        "rate_limit_handler": _rate_limit_exceeded_handler,
    }


def _register_runtime_routes(app: FastAPI, modules=None) -> None:
    if getattr(app.state, "runtime_routes_registered", False):
        return

    modules = modules or _import_runtime_route_modules()
    market = modules["market"]
    factor = modules["factor"]
    backtest = modules["backtest"]
    tools = modules["tools"]
    config_router = modules["config_router"]

    app.state.limiter = modules["limiter"]
    app.add_exception_handler(modules["rate_limit_exceeded"], modules["rate_limit_handler"])
    app.include_router(market.router, prefix="/api/v1", tags=["市场数据"])
    app.include_router(factor.router, prefix="/api/v1", tags=["因子研究"])
    app.include_router(backtest.router, prefix="/api/v1", tags=["回测"])
    app.include_router(tools.router, prefix="/api/v1/tools", tags=["工具"])
    app.include_router(config_router.router, prefix="/api/v1", tags=["配置"])
    app.add_api_route("/{full_path:path}", frontend_fallback, methods=["GET"], include_in_schema=False)
    app.state.runtime_routes_registered = True


async def _register_runtime_routes_async(app: FastAPI) -> None:
    try:
        runtime_route_modules = await asyncio.to_thread(_import_runtime_route_modules)
        _register_runtime_routes(app, runtime_route_modules)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        app.state.runtime_routes_error = exc
        _logger().error(f"路由注册失败: {exc}", exc_info=True)


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
        await _get_paper_run_manager().restore_active_runs()
        await _get_factor_paper_run_manager().restore_active_runs()

        app.state.paper_run_manager = _get_paper_run_manager()
        app.state.factor_paper_run_manager = _get_factor_paper_run_manager()
        app.state.market_scheduler = market_cron.scheduler
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        app.state.background_services_error = exc
        _logger().error(f"后台服务启动失败: {exc}", exc_info=True)


def _ensure_startup_tasks(app: FastAPI) -> None:
    if getattr(app.state, "startup_tasks_started", False):
        return

    app.state.startup_tasks_started = True
    app.state.runtime_routes_task = asyncio.create_task(_register_runtime_routes_async(app))
    app.state.database_task = asyncio.create_task(_init_db_async(app))
    app.state.background_services_task = asyncio.create_task(_start_background_services(app))


async def _delayed_startup_warmup(app: FastAPI) -> None:
    try:
        await asyncio.sleep(STARTUP_WARMUP_DELAY_SECONDS)
        _ensure_startup_tasks(app)
    except asyncio.CancelledError:
        raise


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


# 定义应用生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runtime_routes_error = None
    app.state.database_error = None
    app.state.background_services_error = None
    app.state.startup_tasks_started = False
    app.state.startup_warmup_task = asyncio.create_task(_delayed_startup_warmup(app))
    yield
    startup_warmup_task = getattr(app.state, "startup_warmup_task", None)
    if startup_warmup_task is not None and not startup_warmup_task.done():
        startup_warmup_task.cancel()
        await asyncio.gather(startup_warmup_task, return_exceptions=True)
    runtime_routes_task = getattr(app.state, "runtime_routes_task", None)
    if runtime_routes_task is not None and not runtime_routes_task.done():
        runtime_routes_task.cancel()
        await asyncio.gather(runtime_routes_task, return_exceptions=True)
    database_task = getattr(app.state, "database_task", None)
    if database_task is not None and not database_task.done():
        database_task.cancel()
        await asyncio.gather(database_task, return_exceptions=True)
    background_services_task = getattr(app.state, "background_services_task", None)
    if background_services_task is not None and not background_services_task.done():
        background_services_task.cancel()
        await asyncio.gather(background_services_task, return_exceptions=True)
    await _shutdown_background_services(app)

# 创建FastAPI应用
app = FastAPI(
    title="Heimdall",
    description="AI-Powered Crypto Trading Intelligence",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def wait_for_background_services(request: Request, call_next):
    if request.url.path != "/health":
        _ensure_startup_tasks(request.app)
        runtime_routes_task = getattr(request.app.state, "runtime_routes_task", None)
        if runtime_routes_task is not None and not runtime_routes_task.done():
            await runtime_routes_task
        if getattr(request.app.state, "runtime_routes_error", None) is not None:
            return JSONResponse(status_code=503, content={"detail": "Route initialization failed"})

    if _requires_background_services(request.url.path):
        database_task = getattr(request.app.state, "database_task", None)
        if database_task is not None and not database_task.done():
            await database_task
        if getattr(request.app.state, "database_error", None) is not None:
            return JSONResponse(status_code=503, content={"detail": "Database initialization failed"})
    return await call_next(request)


def _requires_background_services(path: str) -> bool:
    if path == "/api/v1/status":
        return False
    return path.startswith("/api/")

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _logger().error(f"Unhandled: {request.method} {request.url} - {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

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
        "frontend_dev": f"http://localhost:{_frontend_dev_port()}",
    }


@app.get("/", include_in_schema=False)
async def root():
    """返回前端入口或 API 状态。"""
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(str(FRONTEND_INDEX_FILE))
    return _frontend_not_ready_payload()

# 健康检查
@app.get("/health")
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

if __name__ == "__main__":
    import uvicorn
    from config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        reload_dirs=["app", "config", "utils"],
        reload_excludes=["data/*", "logs/*", "frontend/dist/*"],
    )
