from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.router_service_ports import BinanceWeb3TokensPort
from app.runtime_refs import MARKET_BINANCE_WEB3_TOKENS
from app.contracts.dto.binance.web3 import (
    BinanceWeb3TokenAuditResponse,
    BinanceWeb3TokenDynamicResponse,
    BinanceWeb3TokenKlineResponse,
)


router = APIRouter(tags=["Market Data"])
binance_web3_tokens_dependency = runtime_dependency(MARKET_BINANCE_WEB3_TOKENS)


@router.get("/binance/web3/token_dynamic", response_model=BinanceWeb3TokenDynamicResponse)
async def get_binance_web3_token_dynamic(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3TokensPort = Depends(binance_web3_tokens_dependency),
):
    return await service.get_dynamic(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/web3/token_kline", response_model=BinanceWeb3TokenKlineResponse)
async def get_binance_web3_token_kline(
    address: str = Query(...),
    platform: str = Query(...),
    interval: str = Query("15min"),
    limit: int = Query(240, ge=1, le=1000),
    from_time: int | None = Query(None, alias="from"),
    to_time: int | None = Query(None, alias="to"),
    pm: str | None = Query("p"),
    service: BinanceWeb3TokensPort = Depends(binance_web3_tokens_dependency),
):
    return await service.get_kline(
        address=address,
        platform=platform,
        interval=interval,
        limit=limit,
        from_time=from_time,
        to_time=to_time,
        pm=pm,
    )


@router.get("/binance/web3/token_audit", response_model=BinanceWeb3TokenAuditResponse)
async def get_binance_web3_token_audit(
    binance_chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: BinanceWeb3TokensPort = Depends(binance_web3_tokens_dependency),
):
    return await service.get_audit(binance_chain_id=binance_chain_id, contract_address=contract_address)
