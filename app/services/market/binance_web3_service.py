from __future__ import annotations

from app.infra.cache import RedisService
from config import settings

from .binance_api_support import BinanceApiSupport
from .binance_web3_ranks import BinanceWeb3RankService
from .binance_web3_rwa import BinanceRwaService
from .binance_web3_tokens import BinanceWeb3TokenService


class BinanceWeb3Service:
    def __init__(self, cache_service: RedisService | None = None) -> None:
        web3_client = BinanceApiSupport(
            base_url=settings.BINANCE_WEB3_BASE_URL,
            cache_namespace="binance:web3",
            user_agent="binance-web3/2.1 (Skill)",
            cache_service=cache_service,
        )
        www_client = BinanceApiSupport(
            base_url=settings.BINANCE_WWW_BASE_URL,
            cache_namespace="binance:www",
            user_agent="binance-web3/1.1 (Skill)",
            cache_service=cache_service,
        )
        kline_client = BinanceApiSupport(
            base_url="https://dquery.sintral.io",
            cache_namespace="binance:web3:kline",
            user_agent="binance-web3/1.1 (Skill)",
            cache_service=cache_service,
        )
        self.ranks = BinanceWeb3RankService(web3_client)
        self.rwa = BinanceRwaService(www_client)
        self.tokens = BinanceWeb3TokenService(web3_client=web3_client, kline_client=kline_client)
