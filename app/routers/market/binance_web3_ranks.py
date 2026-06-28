from __future__ import annotations

from fastapi import Depends, Query

from app.contracts.frontend import FrontendContractRouter
from app.dependencies import get_binance_web3_heat_rank_service, get_binance_web3_rank_gateway
from app.contracts.dto.binance.web3 import (
    BinanceWeb3AddressPnlResponse,
    BinanceWeb3HeatRankBoardsResponse,
)


router = FrontendContractRouter(frontend_contract_target="market", tags=["Market Data"])


@router.get("/binance/web3/address_pnl_rank", response_model=BinanceWeb3AddressPnlResponse)
async def get_binance_web3_address_pnl_rank(
    chain_id: str = Query(...),
    period: str = Query("30d"),
    tag: str = Query("ALL"),
    page_no: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=25),
    service = Depends(get_binance_web3_rank_gateway),
):
    return await service.get_address_pnl_rank(
        chain_id=chain_id,
        period=period,
        tag=tag,
        page_no=page_no,
        page_size=page_size,
    )


@router.get("/binance/web3/heat_rank_boards", response_model=BinanceWeb3HeatRankBoardsResponse)
async def get_binance_web3_heat_rank_boards(
    chain_id: str | None = Query(None),
    size: int = Query(30, ge=1, le=50),
    service = Depends(get_binance_web3_heat_rank_service),
):
    return await service.get_web3_heat_rank_boards(chain_id=chain_id, size=size)
