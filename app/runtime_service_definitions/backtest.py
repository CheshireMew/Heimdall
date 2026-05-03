from __future__ import annotations

from app.runtime_definition import RuntimeBuildContext, RuntimeServiceDefinition
from app.runtime_lifecycle import restore_paper_runs, shutdown_service
from app.runtime_refs import (
    BACKTEST_COMMAND_SERVICE,
    BACKTEST_FREQTRADE_SERVICE,
    BACKTEST_PAPER_RUN_MANAGER,
    BACKTEST_QUERY_SERVICE,
    BACKTEST_REPORT_BUILDER,
    BACKTEST_RUN_REPOSITORY,
    BACKTEST_RUN_SERVICE,
    BACKTEST_STRATEGY_QUERY_SERVICE,
    BACKTEST_STRATEGY_WRITE_SERVICE,
    INFRA_DATABASE_RUNTIME,
    MARKET_MARKET_DATA_SERVICE,
)


def _build_backtest_run_repository(ctx: RuntimeBuildContext):
    from app.services.backtest.run_repository import BacktestRunRepository

    return BacktestRunRepository(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_freqtrade_backtest_service(ctx: RuntimeBuildContext):
    from app.services.backtest.freqtrade_service import FreqtradeBacktestService

    return FreqtradeBacktestService(market_data_service=ctx.require(MARKET_MARKET_DATA_SERVICE))


def _build_backtest_run_service(ctx: RuntimeBuildContext):
    from app.services.backtest.run_service import BacktestRunService

    return BacktestRunService(
        execution_engine=ctx.require(BACKTEST_FREQTRADE_SERVICE),
        database_runtime=ctx.require(INFRA_DATABASE_RUNTIME),
    )


def _build_strategy_query_service(ctx: RuntimeBuildContext):
    from app.services.backtest.strategy_query_service import StrategyQueryService

    return StrategyQueryService(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_strategy_write_service(ctx: RuntimeBuildContext):
    from app.services.backtest.strategy_write_service import StrategyWriteService

    return StrategyWriteService(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_freqtrade_report_builder(_ctx: RuntimeBuildContext):
    from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder

    return FreqtradeReportBuilder()


def _build_paper_run_manager(ctx: RuntimeBuildContext):
    from app.services.backtest.paper_manager import PaperRunManager

    return PaperRunManager(
        strategy_query_service=ctx.require(BACKTEST_STRATEGY_QUERY_SERVICE),
        freqtrade_service=ctx.require(BACKTEST_FREQTRADE_SERVICE),
        report_builder=ctx.require(BACKTEST_REPORT_BUILDER),
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        database_runtime=ctx.require(INFRA_DATABASE_RUNTIME),
    )


def _build_backtest_command_service(ctx: RuntimeBuildContext):
    from app.services.backtest.command_service import BacktestCommandService

    return BacktestCommandService(
        run_service=ctx.require(BACKTEST_RUN_SERVICE),
        paper_manager=ctx.require(BACKTEST_PAPER_RUN_MANAGER),
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        strategy_query_service=ctx.require(BACKTEST_STRATEGY_QUERY_SERVICE),
        strategy_write_service=ctx.require(BACKTEST_STRATEGY_WRITE_SERVICE),
    )


def _build_backtest_query_service(ctx: RuntimeBuildContext):
    from app.services.backtest.query_service import BacktestQueryService

    return BacktestQueryService(
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        strategy_query_service=ctx.require(BACKTEST_STRATEGY_QUERY_SERVICE),
    )


BACKTEST_SERVICE_DEFINITIONS: tuple[RuntimeServiceDefinition, ...] = (
    RuntimeServiceDefinition(
        BACKTEST_RUN_REPOSITORY,
        frozenset({"api", "background"}),
        _build_backtest_run_repository,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        BACKTEST_FREQTRADE_SERVICE,
        frozenset({"api", "background"}),
        _build_freqtrade_backtest_service,
        deps=(MARKET_MARKET_DATA_SERVICE,),
    ),
    RuntimeServiceDefinition(
        BACKTEST_RUN_SERVICE,
        frozenset({"api"}),
        _build_backtest_run_service,
        deps=(BACKTEST_FREQTRADE_SERVICE, INFRA_DATABASE_RUNTIME),
    ),
    RuntimeServiceDefinition(
        BACKTEST_STRATEGY_QUERY_SERVICE,
        frozenset({"api", "background"}),
        _build_strategy_query_service,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        BACKTEST_STRATEGY_WRITE_SERVICE,
        frozenset({"api"}),
        _build_strategy_write_service,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(BACKTEST_REPORT_BUILDER, frozenset({"api", "background"}), _build_freqtrade_report_builder),
    RuntimeServiceDefinition(
        BACKTEST_PAPER_RUN_MANAGER,
        frozenset({"api", "background"}),
        _build_paper_run_manager,
        deps=(
            BACKTEST_STRATEGY_QUERY_SERVICE,
            BACKTEST_FREQTRADE_SERVICE,
            BACKTEST_REPORT_BUILDER,
            BACKTEST_RUN_REPOSITORY,
            INFRA_DATABASE_RUNTIME,
        ),
        background_start=restore_paper_runs,
        background_stop=shutdown_service,
        background_start_order=30,
        background_stop_order=30,
    ),
    RuntimeServiceDefinition(
        BACKTEST_COMMAND_SERVICE,
        frozenset({"api"}),
        _build_backtest_command_service,
        deps=(
            BACKTEST_RUN_SERVICE,
            BACKTEST_PAPER_RUN_MANAGER,
            BACKTEST_RUN_REPOSITORY,
            BACKTEST_STRATEGY_QUERY_SERVICE,
            BACKTEST_STRATEGY_WRITE_SERVICE,
        ),
    ),
    RuntimeServiceDefinition(
        BACKTEST_QUERY_SERVICE,
        frozenset({"api"}),
        _build_backtest_query_service,
        deps=(BACKTEST_RUN_REPOSITORY, BACKTEST_STRATEGY_QUERY_SERVICE),
    ),
)
