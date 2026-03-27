"""
FastAPI应用主入口
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from contextlib import asynccontextmanager

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.dependencies import get_backtest_query_service, get_factor_paper_run_manager, get_paper_run_manager
from app.rate_limit import limiter
from app.services.market_cron import start_scheduler, scheduler
from utils.logger import logger

# 导入路由
from app.routers import market, backtest, tools, config_router, factor
from config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"

# 定义应用生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动定时任务调度器
    start_scheduler()
    repaired_runs = await get_backtest_query_service().repair_run_storage()
    if repaired_runs:
        logger.info(f"已修复/归档 {repaired_runs} 条旧版回测记录")
    await get_paper_run_manager().restore_active_runs()
    await get_factor_paper_run_manager().restore_active_runs()
    yield
    # 停止定时任务调度器
    await get_factor_paper_run_manager().shutdown()
    await get_paper_run_manager().shutdown()
    if scheduler.running:
        scheduler.shutdown()

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
