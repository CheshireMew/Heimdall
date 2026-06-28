from __future__ import annotations

import pytest

from app.services.market.binance_web3_heat_rank import BinanceWeb3HeatRankComposer
from app.services.market.binance_web3_heat_rank_service import sort_heat_rank_items
from app.services.market.binance_web3_tokens import BinanceWeb3TokenService
import app.services.market.binance_web3_tokens as web3_tokens_module


def test_web3_heat_rank_composer_folds_meme_rank_into_heat_signals():
    items = BinanceWeb3HeatRankComposer().compose(
        chain_id="56",
        top_search=[],
        trending=[],
        volume_rank=[],
        tx_rank=[],
        unique_rank=[],
        social_hype=[],
        smart_money=[],
        meme_rank=[
            {
                "symbol": "MEME",
                "chain_id": "56",
                "contract_address": "0xmemecoin",
                "rank": 3,
                "score": 88,
                "liquidity": 500_000,
            }
        ],
    )

    assert len(items) == 1
    assert items[0]["symbol"] == "MEME"
    assert items[0]["ranks"]["meme"] == 3
    assert items[0]["metrics"]["meme_score"] == 88
    assert items[0]["components"]["meme"] == 8
    assert items[0]["heat_score"] == 8


def test_web3_heat_rank_service_sorts_prebuilt_boards_by_requested_metric():
    items = [
        {"symbol": "A", "rank": 1, "heat_score": 80, "metrics": {"market_cap": 100, "liquidity": 5}},
        {"symbol": "B", "rank": 2, "heat_score": 70, "metrics": {"market_cap": 300, "liquidity": 2}},
        {"symbol": "C", "rank": 3, "heat_score": 90, "metrics": {"market_cap": 200, "liquidity": 8}},
    ]

    assert [item["symbol"] for item in sort_heat_rank_items(items, "market_cap", "desc")] == ["B", "C", "A"]
    assert [item["symbol"] for item in sort_heat_rank_items(items, "liquidity", "asc")] == ["B", "A", "C"]


class FakeWeb3Client:
    async def get_json(self, *args, **kwargs):
        return {"data": {}}

    async def post_json(self, *args, **kwargs):
        return {"data": {}}


class FakeKlineClient:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def get_json(self, path, *, params=None, **kwargs):
        self.calls.append({"path": path, "params": params, **kwargs})
        return {"data": self.rows}


class FakeKlineStore:
    def __init__(self):
        self.rows_by_key = {}
        self.saved = []

    def get_range(self, symbol, timeframe, start_ts, end_ts):
        rows = self.rows_by_key.get((symbol, timeframe), [])
        return [row for row in rows if start_ts <= row[0] <= end_ts]

    def save(self, symbol, timeframe, klines):
        self.saved.append((symbol, timeframe, list(klines)))
        self.rows_by_key.setdefault((symbol, timeframe), []).extend(klines)


@pytest.mark.asyncio
async def test_web3_token_kline_persists_to_kline_store_before_reusing_network(monkeypatch):
    fixed_now = 1_777_800_000_000
    interval_ms = 15 * 60 * 1000
    monkeypatch.setattr(web3_tokens_module.time, "time", lambda: fixed_now / 1000)
    rows = [
        ["0.00012", "0.00013", "0.00011", "0.000129", "1200", fixed_now - (2 * interval_ms), 12],
        ["0.000129", "0.000131", "0.000128", "0.0001297", "1300", fixed_now - interval_ms, 18],
    ]
    kline_client = FakeKlineClient(rows)
    kline_store = FakeKlineStore()
    service = BinanceWeb3TokenService(
        web3_client=FakeWeb3Client(),
        kline_client=kline_client,
        kline_store=kline_store,
    )

    first = (await service.get_kline(address="0xToken", platform="bsc", interval="15min", limit=2)).model_dump()
    second = (await service.get_kline(address="0xToken", platform="bsc", interval="15min", limit=2)).model_dump()

    assert [item["close"] for item in first["items"]] == [0.000129, 0.0001297]
    assert [item["close"] for item in second["items"]] == [0.000129, 0.0001297]
    assert len(kline_client.calls) == 1
    assert kline_store.saved[0][0] == "WEB3:bsc:0xtoken"
    assert kline_store.saved[0][1] == "15min"
