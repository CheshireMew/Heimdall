from __future__ import annotations

from app.services.market.binance_web3_support import (
    SUPPORTED_WEB3_CHAIN_IDS,
    WEB3_ALL_CHAINS_ID,
    asset_url,
    chain_platform,
    normalize_web3_chain_id,
)


def test_web3_supported_chain_catalog_includes_aggregate_and_all_rank_chains():
    assert WEB3_ALL_CHAINS_ID == "all"
    assert SUPPORTED_WEB3_CHAIN_IDS == ("1", "56", "8453", "CT_501")
    assert chain_platform("1") == "ethereum"
    assert chain_platform("56") == "bsc"
    assert chain_platform("8453") == "base"
    assert chain_platform("CT_501") == "solana"


def test_web3_chain_normalization_uses_none_for_aggregate_boundary():
    assert normalize_web3_chain_id(None) is None
    assert normalize_web3_chain_id("") is None
    assert normalize_web3_chain_id("all") is None
    assert normalize_web3_chain_id(" ALL ") is None
    assert normalize_web3_chain_id("8453") == "8453"


def test_asset_url_handles_binance_relative_and_protocol_relative_urls():
    assert asset_url("/images/web3-data/public/token/logos/example.png") == (
        "https://bin.bnbstatic.com/images/web3-data/public/token/logos/example.png"
    )
    assert asset_url("//static.example.com/token.png") == "https://static.example.com/token.png"
    assert asset_url("https://example.com/token.png") == "https://example.com/token.png"
