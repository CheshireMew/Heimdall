from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from app.services.backtest.contracts import (
    BacktestStartCommand,
    CreateIndicatorDefinitionCommand,
    CreateStrategyTemplateCommand,
    CreateStrategyVersionCommand,
)
from app.services.backtest.run_service import BacktestRunService
from app.services.backtest.strategy_library import StrategyLibraryService
from app.services.market.market_data_service import MarketDataService
from utils.logger import logger


class BacktestCommandService:
    def __init__(
        self,
        market_data_service: MarketDataService,
        strategy_library: StrategyLibraryService | None = None,
        run_service: BacktestRunService | None = None,
    ) -> None:
        self.strategy_library = strategy_library or StrategyLibraryService()
        self.run_service = run_service or BacktestRunService(market_data_service=market_data_service)

    async def start_backtest(self, command: BacktestStartCommand) -> dict[str, Any]:
        strategy = self.strategy_library.get_strategy_version(command.strategy_key, command.strategy_version)
        logger.info(
            f"启动 Freqtrade 回测: strategy={command.strategy_key} v{command.strategy_version or 'default'}, "
            f"symbols={','.join(command.portfolio.symbols)}, tf={command.timeframe}, days={command.days}, "
            f"本金={command.initial_cash}, 手续费={command.fee_rate}%"
        )

        end = datetime.now()
        start = end - timedelta(days=command.days)
        loop = asyncio.get_running_loop()
        backtest_id = await loop.run_in_executor(
            None,
            lambda: self.run_service.run_backtest(
                strategy=strategy,
                portfolio=command.portfolio,
                research=command.research,
                start_date=start,
                end_date=end,
                timeframe=command.timeframe,
                initial_cash=command.initial_cash,
                fee_rate=command.fee_rate,
            ),
        )
        if not backtest_id:
            raise RuntimeError("回测执行失败")
        return {"success": True, "backtest_id": backtest_id, "message": "回测已完成"}

    async def create_template(self, command: CreateStrategyTemplateCommand) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.strategy_library.create_template(
                key=command.key,
                name=command.name,
                category=command.category,
                description=command.description,
                indicator_keys=command.indicator_keys,
                default_config=command.default_config,
                default_parameter_space=command.default_parameter_space,
            ),
        )

    async def create_indicator(self, command: CreateIndicatorDefinitionCommand) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.strategy_library.create_indicator(
                key=command.key,
                name=command.name,
                engine_key=command.engine_key,
                description=command.description,
                params=command.params,
            ),
        )

    async def create_strategy_version(self, command: CreateStrategyVersionCommand) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.strategy_library.create_strategy_version(
                key=command.key,
                name=command.name,
                template=command.template,
                category=command.category,
                description=command.description,
                config=command.config,
                parameter_space=command.parameter_space,
                notes=command.notes,
                make_default=command.make_default,
            ),
        )
        return {
            "id": result.id,
            "version": result.version,
            "name": result.version_name or result.strategy_name,
            "notes": result.notes,
            "is_default": result.is_default,
            "config": result.config,
            "parameter_space": result.parameter_space,
        }
