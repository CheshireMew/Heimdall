from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.runtime_refs import MARKET_BINANCE_WEB3_SERVICE
from app.schemas.binance_market import (
    BinanceRwaDynamicResponse,
    BinanceRwaKlineResponse,
    BinanceRwaMarketStatusResponse,
    BinanceRwaMetaResponse,
    BinanceRwaSymbolListResponse,
)

if TYPE_CHECKING:
    from app.services.market.binance_web3_service import BinanceWeb3Service


router = APIRouter(tags=["Market Data"])
binance_web3_dependency = runtime_dependency(MARKET_BINANCE_WEB3_SERVICE)


@router.get("/binance/rwa/symbols", response_model=BinanceRwaSymbolListResponse)
async def get_binance_rwa_symbols(
    platform_type: int | None = Query(1),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    return await service.rwa.list_symbols(platform_type=platform_type)


@router.get("/binance/rwa/meta", response_model=BinanceRwaMetaResponse)
async def get_binance_rwa_meta(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    return await service.rwa.get_meta(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/rwa/market_status", response_model=BinanceRwaMarketStatusResponse)
async def get_binance_rwa_market_status(
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    return await service.rwa.get_market_status()


@router.get("/binance/rwa/asset_market_status", response_model=BinanceRwaMarketStatusResponse)
async def get_binance_rwa_asset_market_status(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    return await service.rwa.get_asset_market_status(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/rwa/dynamic", response_model=BinanceRwaDynamicResponse)
async def get_binance_rwa_dynamic(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    return await service.rwa.get_dynamic(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/rwa/kline", response_model=BinanceRwaKlineResponse)
async def get_binance_rwa_kline(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    interval: str = Query("1d"),
    limit: int = Query(120, ge=1, le=300),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceWeb3Service = Depends(binance_web3_dependency),
):
    return await service.rwa.get_kline(
        chain_id=chain_id,
        contract_address=contract_address,
        interval=interval,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
    )
