from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.routers.errors import service_http_error
from app.schemas.binance_market import (
    BinanceWeb3AddressPnlResponse,
    BinanceWeb3HeatRankResponse,
    BinanceWeb3MemeRankResponse,
    BinanceWeb3SmartMoneyInflowResponse,
    BinanceWeb3SocialHypeResponse,
    BinanceWeb3UnifiedTokenRankResponse,
)

if TYPE_CHECKING:
    from app.services.market.binance_web3_service import BinanceWeb3Service


router = APIRouter(tags=["Market Data"])
binance_web3_dependency = runtime_dependency("market.binance_web3_service")


@router.get("/binance/web3/social_hype", response_model=BinanceWeb3SocialHypeResponse)
async def get_binance_web3_social_hype(
    chain_id: str = Query(...),
    target_language: str = Query("zh"),
    time_range: int = Query(1, ge=1, le=30),
    sentiment: str = Query("All"),
    social_language: str = Query("ALL"),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    try:
        return await service.ranks.get_social_hype_leaderboard(
            chain_id=chain_id,
            target_language=target_language,
            time_range=time_range,
            sentiment=sentiment,
            social_language=social_language,
        )
    except Exception as exc:
        raise service_http_error("API /binance/web3/social_hype 错误", exc)


@router.get("/binance/web3/unified_token_rank", response_model=BinanceWeb3UnifiedTokenRankResponse)
async def get_binance_web3_unified_token_rank(
    rank_type: int = Query(10),
    chain_id: str | None = Query(None),
    period: int = Query(50),
    sort_by: int = Query(0),
    order_asc: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    try:
        return await service.ranks.get_unified_token_rank(
            rank_type=rank_type,
            chain_id=chain_id,
            period=period,
            sort_by=sort_by,
            order_asc=order_asc,
            page=page,
            size=size,
        )
    except Exception as exc:
        raise service_http_error("API /binance/web3/unified_token_rank 错误", exc)


@router.get("/binance/web3/smart_money_inflow", response_model=BinanceWeb3SmartMoneyInflowResponse)
async def get_binance_web3_smart_money_inflow(
    chain_id: str = Query(...),
    period: str = Query("24h"),
    tag_type: int = Query(2),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    try:
        return await service.ranks.get_smart_money_inflow_rank(chain_id=chain_id, period=period, tag_type=tag_type)
    except Exception as exc:
        raise service_http_error("API /binance/web3/smart_money_inflow 错误", exc)


@router.get("/binance/web3/meme_rank", response_model=BinanceWeb3MemeRankResponse)
async def get_binance_web3_meme_rank(
    chain_id: str = Query("56"),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    try:
        return await service.ranks.get_meme_rank(chain_id=chain_id)
    except Exception as exc:
        raise service_http_error("API /binance/web3/meme_rank 错误", exc)


@router.get("/binance/web3/address_pnl_rank", response_model=BinanceWeb3AddressPnlResponse)
async def get_binance_web3_address_pnl_rank(
    chain_id: str = Query(...),
    period: str = Query("30d"),
    tag: str = Query("ALL"),
    page_no: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=25),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    try:
        return await service.ranks.get_address_pnl_rank(
            chain_id=chain_id,
            period=period,
            tag=tag,
            page_no=page_no,
            page_size=page_size,
        )
    except Exception as exc:
        raise service_http_error("API /binance/web3/address_pnl_rank 错误", exc)


@router.get("/binance/web3/heat_rank", response_model=BinanceWeb3HeatRankResponse)
async def get_binance_web3_heat_rank(
    chain_id: str = Query("56"),
    size: int = Query(30, ge=1, le=50),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    try:
        return await service.ranks.get_web3_heat_rank(chain_id=chain_id, size=size)
    except Exception as exc:
        raise service_http_error("API /binance/web3/heat_rank 错误", exc)
