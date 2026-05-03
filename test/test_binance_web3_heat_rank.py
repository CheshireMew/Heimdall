from __future__ import annotations

from app.services.market.binance_web3_heat_rank import BinanceWeb3HeatRankComposer


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
