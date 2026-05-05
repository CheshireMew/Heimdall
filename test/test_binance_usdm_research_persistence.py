from __future__ import annotations

import pytest

from app.services.market.binance_usdm_market import BinanceUsdmMarketService
from app.services.market.binance_spot_market import BinanceSpotMarketService
from app.infra.persistence.market.binance_market_research_store import BinanceMarketResearchStore
from app.infra.persistence.market.funding_rate_store import FundingRateStore


class FakeBinanceClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    async def get_json(self, endpoint: str, *, params=None, ttl: int | None = None):
        self.calls.append({"endpoint": endpoint, "params": params, "ttl": ttl})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_service(installed_database_runtime, responses: list[object]) -> tuple[BinanceUsdmMarketService, BinanceMarketResearchStore, FundingRateStore]:
    research_store = BinanceMarketResearchStore(database_runtime=installed_database_runtime)
    funding_rate_store = FundingRateStore(database_runtime=installed_database_runtime)
    return (
        BinanceUsdmMarketService(
            FakeBinanceClient(responses),
            research_store=research_store,
            funding_rate_store=funding_rate_store,
        ),
        research_store,
        funding_rate_store,
    )


def make_spot_service(installed_database_runtime, responses: list[object]) -> tuple[BinanceSpotMarketService, BinanceMarketResearchStore]:
    research_store = BinanceMarketResearchStore(database_runtime=installed_database_runtime)
    return (
        BinanceSpotMarketService(FakeBinanceClient(responses), research_store=research_store),
        research_store,
    )


@pytest.mark.asyncio
async def test_usdm_open_interest_stats_are_persisted_and_read_back(installed_database_runtime):
    service, research_store, _ = make_service(
        installed_database_runtime,
        [
            [
                {
                    "symbol": "BTCUSDT",
                    "sumOpenInterest": "101.25",
                    "sumOpenInterestValue": "4200000",
                    "timestamp": 1717000000000,
                },
                {
                    "symbol": "BTCUSDT",
                    "sumOpenInterest": "102.5",
                    "sumOpenInterestValue": "4300000",
                    "timestamp": 1717003600000,
                },
            ],
            RuntimeError("upstream unavailable"),
        ],
    )

    first = await service.get_open_interest_stats(symbol="btcusdt", period="1h", limit=2)

    stored = research_store.list_items(
        market="usdm",
        series="open_interest_stats",
        symbol="BTCUSDT",
        period="1h",
        limit=10,
    )
    assert [item["timestamp"] for item in stored] == [1717000000000, 1717003600000]
    assert first.items[0].sum_open_interest == 101.25

    second = await service.get_open_interest_stats(symbol="BTCUSDT", period="1h", limit=2)

    assert [item.timestamp for item in second.items] == [1717000000000, 1717003600000]
    assert second.items[1].sum_open_interest_value == 4300000


@pytest.mark.parametrize(
    ("method_name", "kwargs", "series", "raw_item", "stored_field"),
    [
        (
            "get_long_short_ratio",
            {"symbol": "BTCUSDT", "period": "1h", "limit": 1},
            "global_long_short_account_ratio",
            {"symbol": "BTCUSDT", "longShortRatio": "1.25", "longAccount": "0.56", "shortAccount": "0.44", "timestamp": 1717000000000},
            "long_short_ratio",
        ),
        (
            "get_top_trader_accounts",
            {"symbol": "BTCUSDT", "period": "1h", "limit": 1},
            "top_trader_account_ratio",
            {"symbol": "BTCUSDT", "longShortRatio": "1.35", "longAccount": "0.58", "shortAccount": "0.42", "timestamp": 1717000000000},
            "long_short_ratio",
        ),
        (
            "get_top_trader_positions",
            {"symbol": "BTCUSDT", "period": "1h", "limit": 1},
            "top_trader_position_ratio",
            {"symbol": "BTCUSDT", "longShortRatio": "1.45", "longPosition": "0.60", "shortPosition": "0.40", "timestamp": 1717000000000},
            "long_short_ratio",
        ),
        (
            "get_taker_volume",
            {"symbol": "BTCUSDT", "period": "1h", "limit": 1},
            "taker_long_short_ratio",
            {"symbol": "BTCUSDT", "buySellRatio": "1.55", "buyVol": "120", "sellVol": "80", "timestamp": 1717000000000},
            "buy_sell_ratio",
        ),
        (
            "get_basis",
            {"pair": "BTCUSDT", "contract_type": "CURRENT_QUARTER", "period": "1h", "limit": 1},
            "basis",
            {"pair": "BTCUSDT", "contractType": "CURRENT_QUARTER", "basis": "12.5", "basisRate": "0.001", "timestamp": 1717000000000},
            "basis",
        ),
    ],
)
@pytest.mark.asyncio
async def test_usdm_derivative_research_series_are_persisted_and_read_back(
    installed_database_runtime,
    method_name,
    kwargs,
    series,
    raw_item,
    stored_field,
):
    service, research_store, _ = make_service(
        installed_database_runtime,
        [[raw_item], RuntimeError("upstream unavailable")],
    )

    first = await getattr(service, method_name)(**kwargs)

    symbol = kwargs.get("symbol") or kwargs["pair"]
    contract_type = kwargs.get("contract_type", "")
    stored = research_store.list_items(
        market="usdm",
        series=series,
        symbol=symbol,
        period=kwargs["period"],
        contract_type=contract_type,
        limit=10,
    )
    assert stored[0][stored_field] == getattr(first.items[0], stored_field)

    second = await getattr(service, method_name)(**kwargs)

    assert getattr(second.items[0], stored_field) == getattr(first.items[0], stored_field)


@pytest.mark.asyncio
async def test_usdm_klines_keep_full_binance_payload_in_research_store(installed_database_runtime):
    service, research_store, _ = make_service(
        installed_database_runtime,
        [
            [
                [
                    1717000000000,
                    "68000.0",
                    "68100.0",
                    "67900.0",
                    "68050.0",
                    "123.45",
                    1717003599999,
                    "8400000.0",
                    876,
                ]
            ],
            RuntimeError("upstream unavailable"),
        ],
    )

    first = await service.get_klines(symbol="btcusdt", interval="1h", limit=1)

    stored = research_store.list_items(market="usdm", series="klines", symbol="BTCUSDT", period="1h", limit=10)
    assert stored[0]["quote_volume"] == 8400000.0
    assert stored[0]["trade_count"] == 876
    assert first.items[0].close == 68050.0

    second = await service.get_klines(symbol="BTCUSDT", interval="1h", limit=1)

    assert second.symbol == "BTCUSDT"
    assert second.interval == "1h"
    assert second.items[0].quote_volume == 8400000.0


@pytest.mark.asyncio
async def test_usdm_contract_research_detail_collects_derivative_series(installed_database_runtime):
    service, _, _ = make_service(
        installed_database_runtime,
        [
            [{"symbol": "BTCUSDT", "sumOpenInterest": "100", "sumOpenInterestValue": "6800000", "timestamp": 1717000000000}],
            [{"pair": "BTCUSDT", "contractType": "PERPETUAL", "basis": "1.2", "basisRate": "0.0002", "timestamp": 1717000000000}],
            [{"buySellRatio": "1.4", "buyVol": "140", "sellVol": "100", "timestamp": 1717000000000}],
            [{"symbol": "BTCUSDT", "side": "SELL", "avgPrice": "68000", "executedQty": "0.5", "cumQuote": "34000", "time": 1717000000000}],
            [{"symbol": "BTCUSDT", "longShortRatio": "1.1", "longAccount": "0.52", "shortAccount": "0.48", "timestamp": 1717000000000}],
            [{"symbol": "BTCUSDT", "longShortRatio": "1.2", "longAccount": "0.55", "shortAccount": "0.45", "timestamp": 1717000000000}],
            [{"symbol": "BTCUSDT", "longShortRatio": "1.3", "longPosition": "0.57", "shortPosition": "0.43", "timestamp": 1717000000000}],
        ],
    )

    detail = await service.get_contract_research_detail(symbol="btcusdt", period="1h", limit=10)

    assert detail.symbol == "BTCUSDT"
    assert detail.open_interest.items[0].sum_open_interest_value == 6800000
    assert detail.basis.items[0].basis_rate == 0.0002
    assert detail.taker_volume.items[0].buy_sell_ratio == 1.4
    assert detail.force_orders.items[0].cum_quote == 34000
    assert detail.long_short_ratio.items[0].long_short_ratio == 1.1
    assert detail.top_trader_accounts.items[0].long_short_ratio == 1.2
    assert detail.top_trader_positions.items[0].long_short_ratio == 1.3


@pytest.mark.asyncio
async def test_usdm_funding_history_uses_funding_rate_store_as_canonical_source(installed_database_runtime):
    service, _, funding_rate_store = make_service(
        installed_database_runtime,
        [
            [
                {
                    "symbol": "BTCUSDT",
                    "fundingRate": "0.0001",
                    "markPrice": "68000.5",
                    "fundingTime": 1717000000000,
                }
            ],
            RuntimeError("upstream unavailable"),
        ],
    )

    first = await service.get_funding_history(symbol="btcusdt", limit=10)

    stored = funding_rate_store.list_history(exchange="binance", market_type="usdm", symbol="BTCUSDT")
    assert len(stored) == 1
    assert first.items[0].funding_rate == 0.0001

    second = await service.get_funding_history(symbol="BTCUSDT", limit=10)

    assert len(second.items) == 1
    assert second.items[0].funding_time == 1717000000000
    assert second.items[0].mark_price == 68000.5


@pytest.mark.asyncio
async def test_spot_klines_keep_full_binance_payload_in_research_store(installed_database_runtime):
    service, research_store = make_spot_service(
        installed_database_runtime,
        [
            [
                [
                    1717000000000,
                    "68000.0",
                    "68100.0",
                    "67900.0",
                    "68050.0",
                    "123.45",
                    1717003599999,
                    "8400000.0",
                    876,
                ]
            ],
            RuntimeError("upstream unavailable"),
        ],
    )

    first = await service.get_klines(symbol="btcusdt", interval="1h", limit=1)

    stored = research_store.list_items(market="spot", series="klines", symbol="BTCUSDT", period="1h", limit=10)
    assert stored[0]["quote_volume"] == 8400000.0
    assert first.items[0].trade_count == 876

    second = await service.get_klines(symbol="BTCUSDT", interval="1h", limit=1)

    assert second.market == "spot"
    assert second.items[0].close_time == 1717003599999


@pytest.mark.parametrize(
    ("method_name", "kwargs", "series", "raw_item"),
    [
        (
            "get_trades",
            {"symbol": "BTCUSDT", "limit": 1},
            "trades",
            {
                "id": 10001,
                "price": "68050.0",
                "qty": "0.25",
                "quoteQty": "17012.5",
                "time": 1717000000123,
                "isBuyerMaker": True,
            },
        ),
        (
            "get_agg_trades",
            {"symbol": "BTCUSDT", "limit": 1, "start_time": 1717000000000, "end_time": 1717000001000},
            "agg_trades",
            {
                "a": 20002,
                "p": "68055.0",
                "q": "0.30",
                "T": 1717000000456,
                "m": False,
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_spot_trade_series_use_trade_id_identity_and_database_readback(
    installed_database_runtime,
    method_name,
    kwargs,
    series,
    raw_item,
):
    service, research_store = make_spot_service(
        installed_database_runtime,
        [[raw_item], RuntimeError("upstream unavailable")],
    )

    first = await getattr(service, method_name)(**kwargs)

    stored = research_store.list_items(
        market="spot",
        series=series,
        symbol="BTCUSDT",
        start_time=kwargs.get("start_time"),
        end_time=kwargs.get("end_time"),
        limit=10,
    )
    assert stored[0]["id"] == first.items[0].id
    assert stored[0]["time"] == first.items[0].time

    second = await getattr(service, method_name)(**kwargs)

    assert second.items[0].id == first.items[0].id
