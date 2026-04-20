from __future__ import annotations

import uuid

from app.schemas.binance_market import (
    BinanceWeb3TokenAuditResponse,
    BinanceWeb3TokenDynamicResponse,
    BinanceWeb3TokenKlineResponse,
)

from .binance_api_support import BinanceApiSupport, compact_query
from .binance_numbers import to_float, to_int
from .binance_web3_support import normalize_token_dynamic


class BinanceWeb3TokenService:
    def __init__(self, *, web3_client: BinanceApiSupport, kline_client: BinanceApiSupport) -> None:
        self.web3_client = web3_client
        self.kline_client = kline_client

    async def get_dynamic(self, *, chain_id: str | None = None, contract_address: str | None = None) -> BinanceWeb3TokenDynamicResponse:
        if not chain_id or not contract_address:
            raise ValueError("chain_id 和 contract_address 不能为空")
        payload = await self.web3_client.get_json(
            "/bapi/defi/v4/public/wallet-direct/buw/wallet/market/token/dynamic/info/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=30,
        )
        return BinanceWeb3TokenDynamicResponse.model_validate({
            "source": "binance-web3",
            "chain_id": chain_id,
            "contract_address": contract_address,
            **normalize_token_dynamic(payload.get("data") or {}),
        })

    async def get_kline(
        self,
        *,
        address: str | None = None,
        platform: str | None = None,
        interval: str | None = None,
        limit: int | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        pm: str | None = None,
    ) -> BinanceWeb3TokenKlineResponse:
        if not address or not platform or not interval:
            raise ValueError("address、platform 和 interval 不能为空")
        payload = await self.kline_client.get_json(
            "/u-kline/v1/k-line/candles",
            params=compact_query(
                {
                    "address": address,
                    "platform": platform,
                    "interval": interval,
                    "limit": limit or 240,
                    "from": from_time,
                    "to": to_time,
                    "pm": pm or "p",
                }
            ),
            ttl=30,
        )
        return BinanceWeb3TokenKlineResponse.model_validate({
            "source": "binance-web3",
            "address": address,
            "platform": platform,
            "interval": interval,
            "items": [
                {
                    "open_time": to_int(row[5]) if len(row) > 5 else None,
                    "open": to_float(row[0]) if len(row) > 0 else None,
                    "high": to_float(row[1]) if len(row) > 1 else None,
                    "low": to_float(row[2]) if len(row) > 2 else None,
                    "close": to_float(row[3]) if len(row) > 3 else None,
                    "volume": to_float(row[4]) if len(row) > 4 else None,
                    "trade_count": to_int(row[6]) if len(row) > 6 else None,
                }
                for row in payload.get("data") or []
                if isinstance(row, list)
            ],
        })

    async def get_audit(self, *, binance_chain_id: str | None = None, contract_address: str | None = None) -> BinanceWeb3TokenAuditResponse:
        if not binance_chain_id or not contract_address:
            raise ValueError("binance_chain_id 和 contract_address 不能为空")
        payload = await self.web3_client.post_json(
            "/bapi/defi/v1/public/wallet-direct/security/token/audit",
            body={
                "binanceChainId": binance_chain_id,
                "contractAddress": contract_address,
                "requestId": str(uuid.uuid4()),
            },
            extra_headers={"Content-Type": "application/json", "source": "agent"},
            ttl=30,
        )
        data = payload.get("data") or {}
        return BinanceWeb3TokenAuditResponse.model_validate({
            "source": "binance-web3",
            "binance_chain_id": binance_chain_id,
            "contract_address": contract_address,
            "has_result": bool(data.get("hasResult")),
            "is_supported": bool(data.get("isSupported")),
            "risk_level_enum": data.get("riskLevelEnum"),
            "risk_level": to_int(data.get("riskLevel")),
            "buy_tax": to_float((data.get("extraInfo") or {}).get("buyTax")),
            "sell_tax": to_float((data.get("extraInfo") or {}).get("sellTax")),
            "is_verified": (data.get("extraInfo") or {}).get("isVerified"),
            "risk_items": data.get("riskItems") or [],
        })
