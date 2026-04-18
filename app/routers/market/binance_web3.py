from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_binance_web3_service
from app.routers.market.common import internal_error
from app.schemas.binance_market import (
    BinanceReservedFeatureResponse,
    BinanceRwaDynamicResponse,
    BinanceRwaKlineResponse,
    BinanceRwaMarketStatusResponse,
    BinanceRwaMetaResponse,
    BinanceRwaSymbolListResponse,
    BinanceWeb3AddressPnlResponse,
    BinanceWeb3MemeRankResponse,
    BinanceWeb3SmartMoneyInflowResponse,
    BinanceWeb3SocialHypeResponse,
    BinanceWeb3UnifiedTokenRankResponse,
)

if TYPE_CHECKING:
    from app.services.market.binance_web3_service import BinanceWeb3Service


router = APIRouter(tags=["Market Data"])


@router.get("/binance/web3/social_hype", response_model=BinanceWeb3SocialHypeResponse)
async def get_binance_web3_social_hype(
    chain_id: str = Query(...),
    target_language: str = Query("zh"),
    time_range: int = Query(1, ge=1, le=30),
    sentiment: str = Query("All"),
    social_language: str = Query("ALL"),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_social_hype_leaderboard(
            chain_id=chain_id,
            target_language=target_language,
            time_range=time_range,
            sentiment=sentiment,
            social_language=social_language,
        )
    except Exception as exc:
        raise internal_error("API /binance/web3/social_hype 错误", exc)


@router.get("/binance/web3/unified_token_rank", response_model=BinanceWeb3UnifiedTokenRankResponse)
async def get_binance_web3_unified_token_rank(
    rank_type: int = Query(10),
    chain_id: str | None = Query(None),
    period: int = Query(50),
    sort_by: int = Query(0),
    order_asc: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_unified_token_rank(
            rank_type=rank_type,
            chain_id=chain_id,
            period=period,
            sort_by=sort_by,
            order_asc=order_asc,
            page=page,
            size=size,
        )
    except Exception as exc:
        raise internal_error("API /binance/web3/unified_token_rank 错误", exc)


@router.get("/binance/web3/smart_money_inflow", response_model=BinanceWeb3SmartMoneyInflowResponse)
async def get_binance_web3_smart_money_inflow(
    chain_id: str = Query(...),
    period: str = Query("24h"),
    tag_type: int = Query(2),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_smart_money_inflow_rank(chain_id=chain_id, period=period, tag_type=tag_type)
    except Exception as exc:
        raise internal_error("API /binance/web3/smart_money_inflow 错误", exc)


@router.get("/binance/web3/meme_rank", response_model=BinanceWeb3MemeRankResponse)
async def get_binance_web3_meme_rank(
    chain_id: str = Query("56"),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_meme_rank(chain_id=chain_id)
    except Exception as exc:
        raise internal_error("API /binance/web3/meme_rank 错误", exc)


@router.get("/binance/web3/address_pnl_rank", response_model=BinanceWeb3AddressPnlResponse)
async def get_binance_web3_address_pnl_rank(
    chain_id: str = Query(...),
    period: str = Query("30d"),
    tag: str = Query("ALL"),
    page_no: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=25),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_address_pnl_rank(
            chain_id=chain_id,
            period=period,
            tag=tag,
            page_no=page_no,
            page_size=page_size,
        )
    except Exception as exc:
        raise internal_error("API /binance/web3/address_pnl_rank 错误", exc)


@router.get("/binance/rwa/symbols", response_model=BinanceRwaSymbolListResponse)
async def get_binance_rwa_symbols(
    platform_type: int | None = Query(1),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.list_rwa_symbols(platform_type=platform_type)
    except Exception as exc:
        raise internal_error("API /binance/rwa/symbols 错误", exc)


@router.get("/binance/rwa/meta", response_model=BinanceRwaMetaResponse)
async def get_binance_rwa_meta(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_rwa_meta(chain_id=chain_id, contract_address=contract_address)
    except Exception as exc:
        raise internal_error("API /binance/rwa/meta 错误", exc)


@router.get("/binance/rwa/market_status", response_model=BinanceRwaMarketStatusResponse)
async def get_binance_rwa_market_status(
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_rwa_market_status()
    except Exception as exc:
        raise internal_error("API /binance/rwa/market_status 错误", exc)


@router.get("/binance/rwa/asset_market_status", response_model=BinanceRwaMarketStatusResponse)
async def get_binance_rwa_asset_market_status(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_rwa_asset_market_status(chain_id=chain_id, contract_address=contract_address)
    except Exception as exc:
        raise internal_error("API /binance/rwa/asset_market_status 错误", exc)


@router.get("/binance/rwa/dynamic", response_model=BinanceRwaDynamicResponse)
async def get_binance_rwa_dynamic(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_rwa_dynamic(chain_id=chain_id, contract_address=contract_address)
    except Exception as exc:
        raise internal_error("API /binance/rwa/dynamic 错误", exc)


@router.get("/binance/rwa/kline", response_model=BinanceRwaKlineResponse)
async def get_binance_rwa_kline(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    interval: str = Query("1d"),
    limit: int = Query(120, ge=1, le=300),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    try:
        return await service.get_rwa_kline(
            chain_id=chain_id,
            contract_address=contract_address,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise internal_error("API /binance/rwa/kline 错误", exc)


@router.get("/binance/web3/token_info/search", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_search(
    keyword: str | None = Query(None),
    chain_ids: str | None = Query(None, alias="chainIds"),
    order_by: str | None = Query(None, alias="orderBy"),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    return await service.search_tokens(keyword=keyword, chain_ids=chain_ids, order_by=order_by)


@router.get("/binance/web3/token_info/metadata", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_metadata(
    chain_id: str | None = Query(None, alias="chainId"),
    contract_address: str | None = Query(None, alias="contractAddress"),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    return await service.get_token_metadata(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/web3/token_info/dynamic", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_dynamic(
    chain_id: str | None = Query(None, alias="chainId"),
    contract_address: str | None = Query(None, alias="contractAddress"),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    return await service.get_token_dynamic(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/web3/token_info/kline", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_kline(
    address: str | None = Query(None),
    platform: str | None = Query(None),
    interval: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=1000),
    from_time: int | None = Query(None, alias="from"),
    to_time: int | None = Query(None, alias="to"),
    pm: str | None = Query(None),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    return await service.get_token_kline(
        address=address,
        platform=platform,
        interval=interval,
        limit=limit,
        from_time=from_time,
        to_time=to_time,
        pm=pm,
    )


@router.get("/binance/web3/token_audit", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_audit(
    binance_chain_id: str | None = Query(None, alias="binanceChainId"),
    contract_address: str | None = Query(None, alias="contractAddress"),
    service: BinanceWeb3Service = Depends(get_binance_web3_service),
):
    return await service.audit_token(
        binance_chain_id=binance_chain_id,
        contract_address=contract_address,
    )
