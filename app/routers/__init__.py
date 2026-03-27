"""
路由模块初始化
"""
# 导入所有路由以便在main.py中使用
from app.routers import market, backtest, tools, config_router, factor

__all__ = ["market", "backtest", "tools", "config_router", "factor"]
