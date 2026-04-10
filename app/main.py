"""
FastAPI应用主入口
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.dependencies import get_factor_paper_run_manager, get_paper_run_manager
from app.infra.db.database import init_db
from app.rate_limit import limiter
from app.services.market_cron import scheduler, start_scheduler
from utils.logger import logger

# 导入路由
from app.routers import market, backtest, tools, config_router, factor
from config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"


async def _start_background_services(app: FastAPI) -> None:
    try:
        start_scheduler()
        await get_paper_run_manager().restore_active_runs()
        await get_factor_paper_run_manager().restore_active_runs()

        app.state.paper_run_manager = get_paper_run_manager()
        app.state.factor_paper_run_manager = get_factor_paper_run_manager()
        app.state.market_scheduler = scheduler
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.error(f"后台服务启动失败: {exc}", exc_info=True)


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
    init_db()
    await _start_background_services(app)
    yield
    await _shutdown_background_services(app)

# 创建FastAPI应用
app = FastAPI(
    title="Heimdall",
    description="AI-Powered Crypto Trading Intelligence",
    version="2.0.0",
    lifespan=lifespan
)

# 挂载速率限制器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS配置（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {request.method} {request.url} - {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# 注册路由 (API v1)
app.include_router(market.router, prefix="/api/v1", tags=["市场数据"])
app.include_router(factor.router, prefix="/api/v1", tags=["因子研究"])
app.include_router(backtest.router, prefix="/api/v1", tags=["回测"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["工具"])
app.include_router(config_router.router, prefix="/api/v1", tags=["配置"])

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
        "frontend_dev": f"http://localhost:{settings.FRONTEND_DEV_PORT}",
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


@app.get("/{full_path:path}", include_in_schema=False)
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
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        reload_dirs=["app", "config", "utils"],
        reload_excludes=["data/*", "logs/*", "frontend/dist/*"],
    )
