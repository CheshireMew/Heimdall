from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.contracts.dto.binance.web3 import (
    BinanceWeb3AddressPnlResponse,
    BinanceWeb3HeatRankBoardsResponse,
)


router = APIRouter(tags=["Market Data"])
binance_web3_ranks_dependency = runtime_dependency("binance_web3_ranks")
binance_web3_heat_ranks_dependency = runtime_dependency("binance_web3_heat_ranks")


@router.get("/binance/web3/address_pnl_rank", response_model=BinanceWeb3AddressPnlResponse)
async def get_binance_web3_address_pnl_rank(
    chain_id: str = Query(...),
    period: str = Query("30d"),
    tag: str = Query("ALL"),
    page_no: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=25),
    service = Depends(binance_web3_ranks_dependency),
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
    service = Depends(binance_web3_heat_ranks_dependency),
):
    return await service.get_web3_heat_rank_boards(chain_id=chain_id, size=size)
