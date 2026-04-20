from __future__ import annotations

from app.schemas.binance_market import (
    BinanceRwaDynamicResponse,
    BinanceRwaKlineResponse,
    BinanceRwaMarketStatusResponse,
    BinanceRwaMetaResponse,
    BinanceRwaSymbolListResponse,
)

from .binance_api_support import BinanceApiSupport, compact_query
from .binance_numbers import to_float, to_int
from .binance_web3_support import asset_url


class BinanceRwaService:
    def __init__(self, client: BinanceApiSupport) -> None:
        self.client = client

    async def list_symbols(self, *, platform_type: int | None = 1) -> BinanceRwaSymbolListResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/stock/detail/list/ai",
            params=compact_query({"type": platform_type}),
            ttl=300,
        )
        rows = payload.get("data") or []
        return BinanceRwaSymbolListResponse.model_validate({
            "source": "binance-rwa",
            "items": [
                {
                    "chain_id": item.get("chainId"),
                    "contract_address": item.get("contractAddress"),
                    "symbol": item.get("symbol"),
                    "ticker": item.get("ticker"),
                    "type": to_int(item.get("type")),
                    "multiplier": to_float(item.get("multiplier")),
                }
                for item in rows
            ],
        })

    async def get_meta(self, *, chain_id: str, contract_address: str) -> BinanceRwaMetaResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/meta/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=300,
        )
        data = payload.get("data") or {}
        return BinanceRwaMetaResponse.model_validate({
            "source": "binance-rwa",
            "token_id": data.get("tokenId"),
            "name": data.get("name"),
            "symbol": data.get("symbol"),
            "ticker": data.get("ticker"),
            "chain_id": data.get("chainId"),
            "chain_name": data.get("chainName"),
            "contract_address": data.get("contractAddress"),
            "decimals": to_int(data.get("decimals")),
            "icon_url": asset_url(data.get("icon")),
            "daily_attestation_report_url": asset_url(data.get("dailyAttestationReports")),
            "monthly_attestation_report_url": asset_url(data.get("monthlyAttestationReports")),
            "company_info": data.get("companyInfo") or {},
            "description": data.get("description"),
        })

    async def get_market_status(self) -> BinanceRwaMarketStatusResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/market/status/ai",
            ttl=30,
        )
        return BinanceRwaMarketStatusResponse.model_validate({"source": "binance-rwa", **(payload.get("data") or {})})

    async def get_asset_market_status(self, *, chain_id: str, contract_address: str) -> BinanceRwaMarketStatusResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/asset/market/status/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=30,
        )
        return BinanceRwaMarketStatusResponse.model_validate({"source": "binance-rwa", **(payload.get("data") or {})})

    async def get_dynamic(self, *, chain_id: str, contract_address: str) -> BinanceRwaDynamicResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v2/public/wallet-direct/buw/wallet/market/token/rwa/dynamic/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=30,
        )
        data = payload.get("data") or {}
        return BinanceRwaDynamicResponse.model_validate({
            "source": "binance-rwa",
            "symbol": data.get("symbol"),
            "ticker": data.get("ticker"),
            "token_info": data.get("tokenInfo") or {},
            "stock_info": data.get("stockInfo") or {},
            "status_info": data.get("statusInfo") or {},
            "limit_info": data.get("limitInfo") or {},
        })

    async def get_kline(
        self,
        *,
        chain_id: str,
        contract_address: str,
        interval: str,
        limit: int = 120,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> BinanceRwaKlineResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/dex/market/token/kline/ai",
            params=compact_query(
                {
                    "chainId": chain_id,
                    "contractAddress": contract_address,
                    "interval": interval,
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            ttl=30,
        )
        data = payload.get("data") or {}
        return BinanceRwaKlineResponse.model_validate({
            "source": "binance-rwa",
            "chain_id": chain_id,
            "contract_address": contract_address,
            "interval": interval,
            "decimals": to_int(data.get("decimals")),
            "items": [
                {
                    "open_time": to_int(row[0]),
                    "open": to_float(row[1]),
                    "high": to_float(row[2]),
                    "low": to_float(row[3]),
                    "close": to_float(row[4]),
                    "close_time": to_int(row[6]),
                }
                for row in data.get("klineInfos") or []
            ],
        })
