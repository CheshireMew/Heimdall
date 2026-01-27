"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# 导入路由
from app.routers import market, analysis, backtest, tools, config_router

# 创建FastAPI应用
app = FastAPI(
    title="Heimdall",
    description="AI-Powered Crypto Trading Intelligence",
    version="2.0.0"
)

# CORS配置（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_path = Path(__file__).parent.parent / "static"
templates_path = Path(__file__).parent.parent / "templates"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 注册路由
app.include_router(market.router, prefix="/api", tags=["市场数据"])
app.include_router(analysis.router, prefix="/api", tags=["AI分析"])
app.include_router(backtest.router, prefix="/api", tags=["回测"])
app.include_router(tools.router, prefix="/api/tools", tags=["工具"])
app.include_router(config_router.router, prefix="/api", tags=["配置"])

# 首页路由
@app.get("/")
async def root():
    """返回主页面"""
    index_path = templates_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Heimdall API is running", "docs": "/docs"}

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
