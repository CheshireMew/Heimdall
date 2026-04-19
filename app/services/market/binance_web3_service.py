from __future__ import annotations

import asyncio
import uuid
from typing import Any

from config import settings

from .binance_api_support import BinanceApiSupport, compact_query
from .binance_numbers import to_float, to_int
from .binance_web3_heat_rank import BinanceWeb3HeatRankComposer
from .binance_web3_support import (
    asset_url,
    normalize_rank_token,
    normalize_token_dynamic,
)


class BinanceWeb3Service:
    def __init__(self) -> None:
        self.heat_rank_composer = BinanceWeb3HeatRankComposer()
        self.web3 = BinanceApiSupport(
            base_url=settings.BINANCE_WEB3_BASE_URL,
            cache_namespace="binance:web3",
            user_agent="binance-web3/2.1 (Skill)",
        )
        self.www = BinanceApiSupport(
            base_url=settings.BINANCE_WWW_BASE_URL,
            cache_namespace="binance:www",
            user_agent="binance-web3/1.1 (Skill)",
        )
        self.kline = BinanceApiSupport(
            base_url="https://dquery.sintral.io",
            cache_namespace="binance:web3:kline",
            user_agent="binance-web3/1.1 (Skill)",
        )

    async def get_social_hype_leaderboard(
        self,
        *,
        chain_id: str,
        target_language: str = "zh",
        time_range: int = 1,
        sentiment: str = "All",
        social_language: str = "ALL",
    ) -> dict[str, Any]:
        payload = await self.web3.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/social/hype/rank/leaderboard/ai",
            params={
                "chainId": chain_id,
                "targetLanguage": target_language,
                "timeRange": time_range,
                "sentiment": sentiment,
                "socialLanguage": social_language,
            },
            ttl=60,
        )
        rows = ((payload.get("data") or {}).get("leaderBoardList") or [])
        return {
            "source": "binance-web3",
            "leaderboard": "social_hype",
            "items": [
                {
                    "symbol": (item.get("metaInfo") or {}).get("symbol"),
                    "chain_id": (item.get("metaInfo") or {}).get("chainId"),
                    "contract_address": (item.get("metaInfo") or {}).get("contractAddress"),
                    "logo_url": asset_url((item.get("metaInfo") or {}).get("logo")),
                    "market_cap": to_float((item.get("marketInfo") or {}).get("marketCap")),
                    "price_change_pct": to_float((item.get("marketInfo") or {}).get("priceChange")),
                    "social_hype": to_float((item.get("socialHypeInfo") or {}).get("socialHype")),
                    "sentiment": (item.get("socialHypeInfo") or {}).get("sentiment"),
                    "summary": (item.get("socialHypeInfo") or {}).get("socialSummaryBriefTranslated")
                    or (item.get("socialHypeInfo") or {}).get("socialSummaryBrief"),
                }
                for item in rows
            ],
        }

    async def get_unified_token_rank(
        self,
        *,
        rank_type: int = 10,
        chain_id: str | None = None,
        period: int = 50,
        sort_by: int = 0,
        order_asc: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        payload = await self.web3.post_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/unified/rank/list/ai",
            body=compact_query(
                {
                    "rankType": rank_type,
                    "chainId": chain_id,
                    "period": period,
                    "sortBy": sort_by,
                    "orderAsc": order_asc,
                    "page": page,
                    "size": size,
                }
            ),
            extra_headers={"Content-Type": "application/json"},
            ttl=60,
        )
        data = payload.get("data") or {}
        rows = data.get("tokens") or []
        return {
            "source": "binance-web3",
            "leaderboard": "unified_token_rank",
            "rank_type": rank_type,
            "page": data.get("page", page),
            "size": data.get("size", size),
            "total": data.get("total"),
            "items": [normalize_rank_token(item) for item in rows],
        }

    async def get_smart_money_inflow_rank(
        self,
        *,
        chain_id: str,
        period: str = "24h",
        tag_type: int = 2,
    ) -> dict[str, Any]:
        payload = await self.web3.post_json(
            "/bapi/defi/v1/public/wallet-direct/tracker/wallet/token/inflow/rank/query/ai",
            body={"chainId": chain_id, "period": period, "tagType": tag_type},
            extra_headers={"Content-Type": "application/json"},
            ttl=60,
        )
        rows = payload.get("data") or []
        return {
            "source": "binance-web3",
            "leaderboard": "smart_money_inflow",
            "items": [
                {
                    "symbol": item.get("tokenName"),
                    "chain_id": chain_id,
                    "contract_address": item.get("ca"),
                    "logo_url": asset_url(item.get("tokenIconUrl")),
                    "price": to_float(item.get("price")),
                    "market_cap": to_float(item.get("marketCap")),
                    "liquidity": to_float(item.get("liquidity")),
                    "volume": to_float(item.get("volume")),
                    "price_change_pct": to_float(item.get("priceChangeRate")),
                    "holders": to_int(item.get("holders")),
                    "traders": to_int(item.get("traders")),
                    "inflow": to_float(item.get("inflow")),
                    "risk_level": to_int(item.get("tokenRiskLevel")),
                }
                for item in rows
            ],
        }

    async def get_meme_rank(self, *, chain_id: str = "56") -> dict[str, Any]:
        payload = await self.web3.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/exclusive/rank/list/ai",
            params={"chainId": chain_id},
            ttl=60,
        )
        rows = ((payload.get("data") or {}).get("tokens") or [])
        return {
            "source": "binance-web3",
            "leaderboard": "meme_rank",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "chain_id": item.get("chainId"),
                    "contract_address": item.get("contractAddress"),
                    "rank": to_int(item.get("rank")),
                    "score": to_float(item.get("score")),
                    "logo_url": asset_url(((item.get("metaInfo") or {}).get("icon"))),
                    "price": to_float(item.get("price")),
                    "price_change_pct": to_float(item.get("percentChange")),
                    "market_cap": to_float(item.get("marketCap")),
                    "liquidity": to_float(item.get("liquidity")),
                    "volume": to_float(item.get("volume")),
                    "holders": to_int(item.get("holders")),
                    "unique_trader_bn": to_int(item.get("uniqueTraderBn")),
                }
                for item in rows
            ],
        }

    async def get_address_pnl_rank(
        self,
        *,
        chain_id: str,
        period: str = "30d",
        tag: str = "ALL",
        page_no: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        payload = await self.web3.get_json(
            "/bapi/defi/v1/public/wallet-direct/market/leaderboard/query/ai",
            params={
                "chainId": chain_id,
                "period": period,
                "tag": tag,
                "pageNo": page_no,
                "pageSize": page_size,
                "sortBy": 0,
                "orderBy": 0,
            },
            ttl=60,
        )
        data = payload.get("data") or {}
        rows = data.get("data") or []
        return {
            "source": "binance-web3",
            "leaderboard": "address_pnl_rank",
            "page": data.get("current", page_no),
            "size": data.get("size", page_size),
            "pages": data.get("pages"),
            "items": [
                {
                    "address": item.get("address"),
                    "address_label": item.get("addressLabel"),
                    "address_logo": item.get("addressLogo"),
                    "tags": list(item.get("tags") or []),
                    "realized_pnl": to_float(item.get("realizedPnl")),
                    "realized_pnl_pct": to_float(item.get("realizedPnlPercent")),
                    "win_rate": to_float(item.get("winRate")),
                    "total_volume": to_float(item.get("totalVolume")),
                    "total_tx_cnt": to_int(item.get("totalTxCnt")),
                    "total_traded_tokens": to_int(item.get("totalTradedTokens")),
                    "last_activity": to_int(item.get("lastActivity")),
                }
                for item in rows
            ],
        }

    async def get_web3_heat_rank(
        self,
        *,
        chain_id: str = "56",
        size: int = 30,
    ) -> dict[str, Any]:
        source_size = min(100, max(50, size * 2))
        (
            top_search,
            trending,
            volume_rank,
            tx_rank,
            unique_rank,
            social_hype,
            smart_money,
        ) = await asyncio.gather(
            self._safe_rank_call(
                self.get_unified_token_rank(rank_type=11, chain_id=chain_id, period=50, sort_by=2, size=source_size),
                "top_search",
            ),
            self._safe_rank_call(
                self.get_unified_token_rank(rank_type=10, chain_id=chain_id, period=50, sort_by=0, size=source_size),
                "trending",
            ),
            self._safe_rank_call(
                self.get_unified_token_rank(rank_type=10, chain_id=chain_id, period=50, sort_by=70, size=source_size),
                "volume_rank",
            ),
            self._safe_rank_call(
                self.get_unified_token_rank(rank_type=10, chain_id=chain_id, period=50, sort_by=60, size=source_size),
                "transaction_rank",
            ),
            self._safe_rank_call(
                self.get_unified_token_rank(rank_type=10, chain_id=chain_id, period=50, sort_by=100, size=source_size),
                "unique_trader_rank",
            ),
            self._safe_rank_call(
                self.get_social_hype_leaderboard(chain_id=chain_id, target_language="zh"),
                "social_hype",
            ),
            self._safe_rank_call(
                self.get_smart_money_inflow_rank(chain_id=chain_id, period="24h")
                if chain_id in {"56", "CT_501"}
                else self._empty_rank("smart_money_inflow"),
                "smart_money_inflow",
            ),
        )
        items = self.heat_rank_composer.compose(
            chain_id=chain_id,
            top_search=top_search.get("items") or [],
            trending=trending.get("items") or [],
            volume_rank=volume_rank.get("items") or [],
            tx_rank=tx_rank.get("items") or [],
            unique_rank=unique_rank.get("items") or [],
            social_hype=social_hype.get("items") or [],
            smart_money=smart_money.get("items") or [],
        )
        return {
            "source": "binance-web3",
            "leaderboard": "web3_heat_rank",
            "chain_id": chain_id,
            "size": size,
            "items": items[:size],
            "formula": {
                "positive": [
                    "top_search_rank",
                    "trending_rank",
                    "social_hype",
                    "volume_growth",
                    "transaction_growth",
                    "unique_traders",
                    "smart_money_inflow",
                ],
                "penalty": ["low_liquidity", "contract_risk"],
            },
        }

    async def list_rwa_symbols(self, *, platform_type: int | None = 1) -> dict[str, Any]:
        payload = await self.www.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/stock/detail/list/ai",
            params=compact_query({"type": platform_type}),
            ttl=300,
        )
        rows = payload.get("data") or []
        return {
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
        }

    async def get_rwa_meta(self, *, chain_id: str, contract_address: str) -> dict[str, Any]:
        payload = await self.www.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/meta/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=300,
        )
        data = payload.get("data") or {}
        return {
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
        }

    async def get_rwa_market_status(self) -> dict[str, Any]:
        payload = await self.www.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/market/status/ai",
            ttl=30,
        )
        return {"source": "binance-rwa", **(payload.get("data") or {})}

    async def get_rwa_asset_market_status(self, *, chain_id: str, contract_address: str) -> dict[str, Any]:
        payload = await self.www.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/rwa/asset/market/status/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=30,
        )
        return {"source": "binance-rwa", **(payload.get("data") or {})}

    async def get_rwa_dynamic(self, *, chain_id: str, contract_address: str) -> dict[str, Any]:
        payload = await self.www.get_json(
            "/bapi/defi/v2/public/wallet-direct/buw/wallet/market/token/rwa/dynamic/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=30,
        )
        data = payload.get("data") or {}
        return {
            "source": "binance-rwa",
            "symbol": data.get("symbol"),
            "ticker": data.get("ticker"),
            "token_info": data.get("tokenInfo") or {},
            "stock_info": data.get("stockInfo") or {},
            "status_info": data.get("statusInfo") or {},
            "limit_info": data.get("limitInfo") or {},
        }

    async def get_rwa_kline(
        self,
        *,
        chain_id: str,
        contract_address: str,
        interval: str,
        limit: int = 120,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        payload = await self.www.get_json(
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
        return {
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
        }

    async def get_token_dynamic(self, *, chain_id: str | None = None, contract_address: str | None = None) -> dict[str, Any]:
        if not chain_id or not contract_address:
            raise ValueError("chain_id 和 contract_address 不能为空")
        payload = await self.web3.get_json(
            "/bapi/defi/v4/public/wallet-direct/buw/wallet/market/token/dynamic/info/ai",
            params={"chainId": chain_id, "contractAddress": contract_address},
            ttl=30,
        )
        return {
            "source": "binance-web3",
            "chain_id": chain_id,
            "contract_address": contract_address,
            **normalize_token_dynamic(payload.get("data") or {}),
        }

    async def get_token_kline(
        self,
        *,
        address: str | None = None,
        platform: str | None = None,
        interval: str | None = None,
        limit: int | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        pm: str | None = None,
    ) -> dict[str, Any]:
        if not address or not platform or not interval:
            raise ValueError("address、platform 和 interval 不能为空")
        payload = await self.kline.get_json(
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
        return {
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
        }

    async def get_token_audit(self, *, binance_chain_id: str | None = None, contract_address: str | None = None) -> dict[str, Any]:
        if not binance_chain_id or not contract_address:
            raise ValueError("binance_chain_id 和 contract_address 不能为空")
        payload = await self.web3.post_json(
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
        return {
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
        }

    async def _empty_rank(self, leaderboard: str) -> dict[str, Any]:
        return {
            "source": "binance-web3",
            "leaderboard": leaderboard,
            "items": [],
        }

    async def _safe_rank_call(self, awaitable: Any, leaderboard: str) -> dict[str, Any]:
        try:
            return await asyncio.wait_for(awaitable, timeout=12)
        except Exception as exc:
            return {
                "source": "binance-web3",
                "leaderboard": leaderboard,
                "items": [],
                "error": str(exc),
            }
