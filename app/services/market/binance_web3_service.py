from __future__ import annotations

from typing import Any

from config import settings

from .binance_api_support import BinanceApiSupport, compact_query


TOKEN_INFO_SKILL_SPEC: dict[str, Any] = {
    "skill_name": "query-token-info",
    "skill_version": "1.1",
    "supported_chains": [
        {"name": "BSC", "chain_id": "56", "platform": "bsc"},
        {"name": "Base", "chain_id": "8453", "platform": "base"},
        {"name": "Solana", "chain_id": "CT_501", "platform": "solana"},
    ],
    "endpoints": {
        "token_info_search": {
            "method": "GET",
            "url": "https://web3.binance.com/bapi/defi/v5/public/wallet-direct/buw/wallet/market/token/search/ai",
            "params": ["keyword", "chainIds", "orderBy"],
            "fields": [
                "chainId",
                "contractAddress",
                "tokenId",
                "name",
                "symbol",
                "icon",
                "price",
                "percentChange24h",
                "volume24h",
                "marketCap",
                "liquidity",
                "tagsInfo",
                "links",
                "createTime",
                "holdersTop10Percent",
                "riskLevel",
            ],
        },
        "token_info_metadata": {
            "method": "GET",
            "url": "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/dex/market/token/meta/info/ai",
            "params": ["chainId", "contractAddress"],
            "fields": [
                "tokenId",
                "name",
                "symbol",
                "chainId",
                "chainName",
                "contractAddress",
                "decimals",
                "icon",
                "links",
                "previewLink",
                "createTime",
                "creatorAddress",
                "auditInfo",
                "description",
            ],
        },
        "token_info_dynamic": {
            "method": "GET",
            "url": "https://web3.binance.com/bapi/defi/v4/public/wallet-direct/buw/wallet/market/token/dynamic/info/ai",
            "params": ["chainId", "contractAddress"],
            "fields": [
                "price",
                "nativeTokenPrice",
                "volume24h",
                "volume24hBuy",
                "volume24hSell",
                "volume4h",
                "volume1h",
                "volume5m",
                "count24h",
                "count24hBuy",
                "count24hSell",
                "percentChange5m",
                "percentChange1h",
                "percentChange4h",
                "percentChange24h",
                "marketCap",
                "fdv",
                "totalSupply",
                "circulatingSupply",
                "priceHigh24h",
                "priceLow24h",
                "holders",
                "liquidity",
                "launchTime",
                "top10HoldersPercentage",
                "kycHolderCount",
                "kolHolders",
                "kolHoldingPercent",
                "proHoldingPercent",
                "smartMoneyHoldingPercent",
            ],
        },
        "token_info_kline": {
            "method": "GET",
            "url": "https://dquery.sintral.io/u-kline/v1/k-line/candles",
            "params": ["address", "platform", "interval", "limit", "from", "to", "pm"],
            "fields": ["open", "high", "low", "close", "volume", "timestamp", "count"],
        },
    },
    "notes": [
        "请求头使用 User-Agent: binance-web3/1.1 (Skill) 和 Accept-Encoding: identity。",
        "图标路径需要补 https://bin.bnbstatic.com 前缀。",
        "大部分数字字段是字符串，落库或计算前统一转成数字。",
        "K 线接口按 platform 查询，不按 chainId 查询；limit 与 from 同时传时优先使用 limit。",
        "K 线返回二维数组，顺序是 [open, high, low, close, volume, timestamp, count]。",
    ],
}


TOKEN_AUDIT_SKILL_SPEC: dict[str, Any] = {
    "skill_name": "query-token-audit",
    "skill_version": "1.4",
    "supported_chains": [
        {"name": "BSC", "chain_id": "56"},
        {"name": "Base", "chain_id": "8453"},
        {"name": "Solana", "chain_id": "CT_501"},
        {"name": "Ethereum", "chain_id": "1"},
    ],
    "endpoints": {
        "token_audit": {
            "method": "POST",
            "url": "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/security/token/audit",
            "params": ["binanceChainId", "contractAddress", "requestId"],
            "fields": [
                "requestId",
                "hasResult",
                "isSupported",
                "riskLevelEnum",
                "riskLevel",
                "extraInfo.buyTax",
                "extraInfo.sellTax",
                "extraInfo.isVerified",
                "riskItems[].id",
                "riskItems[].details[].title",
                "riskItems[].details[].description",
                "riskItems[].details[].isHit",
                "riskItems[].details[].riskType",
            ],
        }
    },
    "notes": [
        "请求头使用 User-Agent: binance-web3/1.4 (Skill)、Content-Type: application/json、source: agent。",
        "每次审计请求都要生成 UUID v4 作为 requestId。",
        "只有 hasResult=true 且 isSupported=true 时才展示 riskLevel 和 riskItems。",
        "riskLevel 0-1 低风险但不等于安全，2-3 中风险，4 高风险，5 应阻断交易。",
        "税费阈值：大于 10% 视为严重，5%-10% 视为警告，低于 5% 才相对可接受。",
        "审计只输出安全风险，不输出投资建议。",
    ],
}


class BinanceWeb3Service:
    def __init__(self) -> None:
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
                    "logo_url": self._asset_url((item.get("metaInfo") or {}).get("logo")),
                    "market_cap": self._to_float((item.get("marketInfo") or {}).get("marketCap")),
                    "price_change_pct": self._to_float((item.get("marketInfo") or {}).get("priceChange")),
                    "social_hype": self._to_float((item.get("socialHypeInfo") or {}).get("socialHype")),
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
            "items": [self._normalize_rank_token(item) for item in rows],
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
                    "logo_url": self._asset_url(item.get("tokenIconUrl")),
                    "price": self._to_float(item.get("price")),
                    "market_cap": self._to_float(item.get("marketCap")),
                    "liquidity": self._to_float(item.get("liquidity")),
                    "volume": self._to_float(item.get("volume")),
                    "price_change_pct": self._to_float(item.get("priceChangeRate")),
                    "holders": self._to_int(item.get("holders")),
                    "traders": self._to_int(item.get("traders")),
                    "inflow": self._to_float(item.get("inflow")),
                    "risk_level": self._to_int(item.get("tokenRiskLevel")),
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
                    "rank": self._to_int(item.get("rank")),
                    "score": self._to_float(item.get("score")),
                    "logo_url": self._asset_url(((item.get("metaInfo") or {}).get("icon"))),
                    "price": self._to_float(item.get("price")),
                    "price_change_pct": self._to_float(item.get("percentChange")),
                    "market_cap": self._to_float(item.get("marketCap")),
                    "liquidity": self._to_float(item.get("liquidity")),
                    "volume": self._to_float(item.get("volume")),
                    "holders": self._to_int(item.get("holders")),
                    "unique_trader_bn": self._to_int(item.get("uniqueTraderBn")),
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
                    "realized_pnl": self._to_float(item.get("realizedPnl")),
                    "realized_pnl_pct": self._to_float(item.get("realizedPnlPercent")),
                    "win_rate": self._to_float(item.get("winRate")),
                    "total_volume": self._to_float(item.get("totalVolume")),
                    "total_tx_cnt": self._to_int(item.get("totalTxCnt")),
                    "total_traded_tokens": self._to_int(item.get("totalTradedTokens")),
                    "last_activity": self._to_int(item.get("lastActivity")),
                }
                for item in rows
            ],
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
                    "type": self._to_int(item.get("type")),
                    "multiplier": self._to_float(item.get("multiplier")),
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
            "decimals": self._to_int(data.get("decimals")),
            "icon_url": self._asset_url(data.get("icon")),
            "daily_attestation_report_url": self._asset_url(data.get("dailyAttestationReports")),
            "monthly_attestation_report_url": self._asset_url(data.get("monthlyAttestationReports")),
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
            "decimals": self._to_int(data.get("decimals")),
            "items": [
                {
                    "open_time": self._to_int(row[0]),
                    "open": self._to_float(row[1]),
                    "high": self._to_float(row[2]),
                    "low": self._to_float(row[3]),
                    "close": self._to_float(row[4]),
                    "close_time": self._to_int(row[6]),
                }
                for row in data.get("klineInfos") or []
            ],
        }

    async def search_tokens(
        self,
        *,
        keyword: str | None = None,
        chain_ids: str | None = None,
        order_by: str | None = None,
    ) -> dict[str, Any]:
        # Reserved from skill 7. This keeps the future search contract close to Binance's
        # documented keyword / chainIds / orderBy API before we turn on live token lookup.
        return self._reserved_feature(
            spec=TOKEN_INFO_SKILL_SPEC,
            feature="token_info_search",
            message="Token search is reserved. Future implementation will search by name, symbol, or contract address.",
            received_params={"keyword": keyword, "chain_ids": chain_ids, "order_by": order_by},
        )

    async def get_token_metadata(self, *, chain_id: str | None = None, contract_address: str | None = None) -> dict[str, Any]:
        # Reserved from skill 7. Metadata must carry static token identity, social links,
        # creator address, description, and basic audit flags.
        return self._reserved_feature(
            spec=TOKEN_INFO_SKILL_SPEC,
            feature="token_info_metadata",
            message="Token metadata is reserved. Future implementation will return identity, links, creator, and description.",
            received_params={"chain_id": chain_id, "contract_address": contract_address},
        )

    async def get_token_dynamic(self, *, chain_id: str | None = None, contract_address: str | None = None) -> dict[str, Any]:
        # Reserved from skill 7. Dynamic data is the source for price, volume, holder,
        # liquidity, market-cap, FDV, and short-window change fields.
        return self._reserved_feature(
            spec=TOKEN_INFO_SKILL_SPEC,
            feature="token_info_dynamic",
            message="Token dynamic data is reserved. Future implementation will return live price, volume, holders, liquidity, and supply fields.",
            received_params={"chain_id": chain_id, "contract_address": contract_address},
        )

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
        # Reserved from skill 7. Binance's token chart provider returns array candles,
        # so the implementation must normalize indexes before feeding TradingView charts.
        return self._reserved_feature(
            spec=TOKEN_INFO_SKILL_SPEC,
            feature="token_info_kline",
            message="Token K-line is reserved. Future implementation will normalize array candles into OHLCV rows.",
            received_params={
                "address": address,
                "platform": platform,
                "interval": interval,
                "limit": limit,
                "from": from_time,
                "to": to_time,
                "pm": pm,
            },
        )

    async def audit_token(self, *, binance_chain_id: str | None = None, contract_address: str | None = None) -> dict[str, Any]:
        # Reserved from skill 8. Audit has stricter display rules: risk output is valid
        # only when both hasResult and isSupported are true.
        return self._reserved_feature(
            spec=TOKEN_AUDIT_SKILL_SPEC,
            feature="token_audit",
            message="Token audit is reserved. Future implementation will run Binance's security audit and apply the supported/result gating rules.",
            received_params={"binance_chain_id": binance_chain_id, "contract_address": contract_address},
        )

    def _normalize_rank_token(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": item.get("symbol"),
            "chain_id": item.get("chainId"),
            "contract_address": item.get("contractAddress"),
            "icon_url": self._asset_url(item.get("icon")),
            "price": self._to_float(item.get("price")),
            "market_cap": self._to_float(item.get("marketCap")),
            "liquidity": self._to_float(item.get("liquidity")),
            "holders": self._to_int(item.get("holders")),
            "launch_time": self._to_int(item.get("launchTime")),
            "percent_change_1h": self._to_float(item.get("percentChange1h")),
            "percent_change_24h": self._to_float(item.get("percentChange24h")),
            "volume_24h": self._to_float(item.get("volume24h")),
            "unique_trader_24h": self._to_int(item.get("uniqueTrader24h")),
            "kyc_holders": self._to_int(item.get("kycHolders")),
        }

    def _reserved_feature(
        self,
        *,
        spec: dict[str, Any],
        feature: str,
        message: str,
        received_params: dict[str, Any],
    ) -> dict[str, Any]:
        endpoint = spec["endpoints"][feature]
        return {
            "source": "binance-web3",
            "feature": feature,
            "status": "reserved",
            "message": message,
            "skill_name": spec["skill_name"],
            "skill_version": spec["skill_version"],
            "supported_chains": spec["supported_chains"],
            "reserved_endpoints": [{**endpoint, "feature": feature, "receivedParams": compact_query(received_params)}],
            "response_fields": endpoint["fields"],
            "notes": spec["notes"],
        }

    def _asset_url(self, path: Any) -> str | None:
        if path in (None, ""):
            return None
        value = str(path)
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return f"https://bin.bnbstatic.com{value}"

    def _to_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def _to_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(float(value))
