from __future__ import annotations

from app.runtime_definition import RuntimeBuildContext, RuntimeServiceDefinition
from app.runtime_lifecycle import shutdown_service, start_market_scheduler
from app.runtime_refs import INFRA_DATABASE_RUNTIME, SYSTEM_CURRENCY_RATE_SERVICE, SYSTEM_MARKET_SCHEDULER_RUNTIME


def _build_currency_rate_service(_ctx: RuntimeBuildContext):
    from app.services.currency_service import CurrencyRateService

    return CurrencyRateService()


def _build_market_scheduler_runtime(ctx: RuntimeBuildContext):
    from app.services.market_scheduler_runtime import MarketSchedulerRuntime

    return MarketSchedulerRuntime(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


SYSTEM_SERVICE_DEFINITIONS: tuple[RuntimeServiceDefinition, ...] = (
    RuntimeServiceDefinition(SYSTEM_CURRENCY_RATE_SERVICE, frozenset({"api"}), _build_currency_rate_service),
    RuntimeServiceDefinition(
        SYSTEM_MARKET_SCHEDULER_RUNTIME,
        frozenset({"background"}),
        _build_market_scheduler_runtime,
        deps=(INFRA_DATABASE_RUNTIME,),
        background_start=start_market_scheduler,
        background_stop=shutdown_service,
        background_start_order=10,
        background_stop_order=40,
    ),
)
