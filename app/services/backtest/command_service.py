from __future__ import annotations

import asyncio
from typing import Any

from app.contracts.backtest import (
    BacktestStartCommand,
    CreateIndicatorDefinitionCommand,
    CreateStrategyTemplateCommand,
    CreateStrategyVersionCommand,
    PaperStartCommand,
)
from app.services.backtest.paper_manager import PaperRunManager
from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.run_service import BacktestRunService
from app.services.backtest.scripted_template_runtime import template_supports_paper
from app.services.backtest.strategy_catalog import get_template_runtime_contract
from app.services.backtest.strategy_query_service import StrategyQueryService
from app.services.backtest.strategy_write_service import StrategyWriteService
from utils.logger import logger


class BacktestCommandService:
    def __init__(
        self,
        *,
        run_service: BacktestRunService,
        paper_manager: PaperRunManager,
        run_repository: BacktestRunRepository,
        strategy_query_service: StrategyQueryService,
        strategy_write_service: StrategyWriteService,
    ) -> None:
        self.strategy_query_service = strategy_query_service
        self.strategy_write_service = strategy_write_service
        self.run_service = run_service
        self.paper_manager = paper_manager
        self.run_repository = run_repository

    async def start_backtest(self, command: BacktestStartCommand) -> dict[str, Any]:
        strategy = self.strategy_query_service.get_strategy_version(command.strategy_key, command.strategy_version)
        logger.info(
            f"启动回测: strategy={command.strategy_key} v{command.strategy_version or 'default'}, "
            f"symbols={','.join(command.portfolio.symbols)}, tf={command.timeframe}, "
            f"range=({command.start_date} - {command.end_date}), "
            f"本金={command.initial_cash}, 手续费={command.fee_rate}%"
        )

        loop = asyncio.get_running_loop()
        backtest_id = await loop.run_in_executor(
            None,
            lambda: self.run_service.run_backtest(
                strategy=strategy,
                portfolio=command.portfolio,
                research=command.research,
                start_date=command.start_date,
                end_date=command.end_date,
                timeframe=command.timeframe,
                initial_cash=command.initial_cash,
                fee_rate=command.fee_rate,
            ),
        )
        if not backtest_id:
            raise RuntimeError("回测执行失败")
        return {"success": True, "backtest_id": backtest_id, "message": "回测已完成"}

    async def start_paper_run(self, command: PaperStartCommand) -> dict[str, Any]:
        strategy = self.strategy_query_service.get_strategy_version(command.strategy_key, command.strategy_version)
        runtime_contract = get_template_runtime_contract(strategy.template)
        if not template_supports_paper(runtime_contract):
            raise ValueError("该策略当前只支持回测，不支持模拟盘")
        logger.info(
            f"启动模拟盘: strategy={strategy.strategy_key} v{strategy.version}, "
            f"symbols={','.join(command.portfolio.symbols)}, tf={command.timeframe}, "
            f"本金={command.initial_cash}, 手续费={command.fee_rate}%"
        )
        return await self.paper_manager.start_run(command)

    async def stop_paper_run(self, run_id: int) -> dict[str, Any]:
        logger.info(f"停止模拟盘: run_id={run_id}")
        return await self.paper_manager.stop_run(run_id)

    async def delete_backtest(self, backtest_id: int) -> dict[str, Any]:
        logger.info(f"删除回测记录: backtest_id={backtest_id}")
        loop = asyncio.get_running_loop()
        deleted = await loop.run_in_executor(
            None,
            lambda: self.run_repository.delete_run(backtest_id, "backtest"),
        )
        if not deleted:
            raise ValueError(f"回测记录不存在: {backtest_id}")
        return {"success": True, "run_id": backtest_id, "message": "回测记录已删除"}

    async def delete_paper_run(self, run_id: int) -> dict[str, Any]:
        logger.info(f"删除模拟盘记录: run_id={run_id}")
        return await self.paper_manager.delete_run(run_id)

    async def create_template(self, command: CreateStrategyTemplateCommand) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.strategy_write_service.create_template(
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
            lambda: self.strategy_write_service.create_indicator(
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
            lambda: self.strategy_write_service.create_strategy_version(
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
