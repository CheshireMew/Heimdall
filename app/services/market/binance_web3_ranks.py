from __future__ import annotations

import asyncio
from typing import Any

from app.schemas.binance_market import (
    BinanceWeb3AddressPnlResponse,
    BinanceWeb3HeatRankResponse,
    BinanceWeb3MemeRankResponse,
    BinanceWeb3SmartMoneyInflowResponse,
    BinanceWeb3SocialHypeResponse,
    BinanceWeb3UnifiedTokenRankResponse,
)

from .binance_api_support import BinanceApiSupport, compact_query
from .binance_numbers import to_float, to_int
from .binance_web3_heat_rank import BinanceWeb3HeatRankComposer
from .binance_web3_support import asset_url, normalize_rank_token


class BinanceWeb3RankService:
    def __init__(self, client: BinanceApiSupport) -> None:
        self.client = client
        self.heat_rank_composer = BinanceWeb3HeatRankComposer()

    async def get_social_hype_leaderboard(
        self,
        *,
        chain_id: str,
        target_language: str = "zh",
        time_range: int = 1,
        sentiment: str = "All",
        social_language: str = "ALL",
    ) -> BinanceWeb3SocialHypeResponse:
        payload = await self.client.get_json(
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
        return BinanceWeb3SocialHypeResponse.model_validate({
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
        })

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
    ) -> BinanceWeb3UnifiedTokenRankResponse:
        payload = await self.client.post_json(
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
        return BinanceWeb3UnifiedTokenRankResponse.model_validate({
            "source": "binance-web3",
            "leaderboard": "unified_token_rank",
            "rank_type": rank_type,
            "page": data.get("page", page),
            "size": data.get("size", size),
            "total": data.get("total"),
            "items": [normalize_rank_token(item) for item in rows],
        })

    async def get_smart_money_inflow_rank(
        self,
        *,
        chain_id: str,
        period: str = "24h",
        tag_type: int = 2,
    ) -> BinanceWeb3SmartMoneyInflowResponse:
        payload = await self.client.post_json(
            "/bapi/defi/v1/public/wallet-direct/tracker/wallet/token/inflow/rank/query/ai",
            body={"chainId": chain_id, "period": period, "tagType": tag_type},
            extra_headers={"Content-Type": "application/json"},
            ttl=60,
        )
        rows = payload.get("data") or []
        return BinanceWeb3SmartMoneyInflowResponse.model_validate({
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
        })

    async def get_meme_rank(self, *, chain_id: str = "56") -> BinanceWeb3MemeRankResponse:
        payload = await self.client.get_json(
            "/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/exclusive/rank/list/ai",
            params={"chainId": chain_id},
            ttl=60,
        )
        rows = ((payload.get("data") or {}).get("tokens") or [])
        return BinanceWeb3MemeRankResponse.model_validate({
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
        })

    async def get_address_pnl_rank(
        self,
        *,
        chain_id: str,
        period: str = "30d",
        tag: str = "ALL",
        page_no: int = 1,
        page_size: int = 25,
    ) -> BinanceWeb3AddressPnlResponse:
        payload = await self.client.get_json(
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
        return BinanceWeb3AddressPnlResponse.model_validate({
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
        })

    async def get_web3_heat_rank(
        self,
        *,
        chain_id: str = "56",
        size: int = 30,
    ) -> BinanceWeb3HeatRankResponse:
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
        return BinanceWeb3HeatRankResponse.model_validate({
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
        })

    async def _empty_rank(self, leaderboard: str) -> dict[str, Any]:
        return {
            "source": "binance-web3",
            "leaderboard": leaderboard,
            "items": [],
        }

    async def _safe_rank_call(self, awaitable: Any, leaderboard: str) -> dict[str, Any]:
        try:
            response = await asyncio.wait_for(awaitable, timeout=12)
            return response.model_dump() if hasattr(response, "model_dump") else response
        except Exception as exc:
            return {
                "source": "binance-web3",
                "leaderboard": leaderboard,
                "items": [],
                "error": str(exc),
            }
