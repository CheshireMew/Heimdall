"""
路由模块初始化
"""
# 导入所有路由以便在main.py中使用
from app.routers import market, analysis, backtest, tools, config_router

__all__ = ["market", "analysis", "backtest", "tools", "config_router"]
