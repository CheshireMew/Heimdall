from __future__ import annotations

from app.services.market.binance_web3_heat_rank import BinanceWeb3HeatRankComposer
from app.services.market.binance_web3_ranks import BinanceWeb3RankService


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
    service = BinanceWeb3RankService(client=object())
    items = [
        {"symbol": "A", "rank": 1, "heat_score": 80, "metrics": {"market_cap": 100, "liquidity": 5}},
        {"symbol": "B", "rank": 2, "heat_score": 70, "metrics": {"market_cap": 300, "liquidity": 2}},
        {"symbol": "C", "rank": 3, "heat_score": 90, "metrics": {"market_cap": 200, "liquidity": 8}},
    ]

    assert [item["symbol"] for item in service._sort_heat_rank_items(items, "market_cap", "desc")] == ["B", "C", "A"]
    assert [item["symbol"] for item in service._sort_heat_rank_items(items, "liquidity", "asc")] == ["B", "A", "C"]
