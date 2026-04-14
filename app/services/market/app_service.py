from __future__ import annotations

import asyncio
from typing import Any, Callable

from app.infra.llm_client import LLMClient
from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.symbol_catalog import get_supported_market_symbols
from app.domain.market.trade_setup import TradeSetupEngine, TradeSetupRequest
from app.services.market.binance_market_intel_service import BinanceMarketIntelService
from app.services.market.binance_web3_service import BinanceWeb3Service
from app.services.market.crypto_index_app_service import CryptoIndexAppService
from app.services.market.funding_rate_service import FundingRateService
from app.services.market.history_service import HistoryService
from app.services.market.indicator_service import IndicatorService
from app.services.market.market_data_service import MarketDataService
from app.services.market.realtime_service import RealtimeService
from config import settings
from app.domain.market.constants import Timeframe
from utils.logger import logger


class MarketAppService:
    def __init__(
        self,
        binance_market_intel_service: BinanceMarketIntelService,
        binance_web3_service: BinanceWeb3Service,
        crypto_index_service: CryptoIndexAppService,
        realtime_service: RealtimeService,
        indicator_service: IndicatorService,
        history_service: HistoryService,
        funding_rate_service: FundingRateService,
    ) -> None:
        self.binance_market_intel_service = binance_market_intel_service
        self.binance_web3_service = binance_web3_service
        self.crypto_index_service = crypto_index_service
        self.realtime_service = realtime_service
        self.indicator_service = indicator_service
        self.history_service = history_service
        self.funding_rate_service = funding_rate_service
        self.trade_setup_engine = TradeSetupEngine()
        self.valid_symbols = get_supported_market_symbols()
        self.valid_timeframes = [item.value for item in Timeframe]

    def get_llm_client(self) -> LLMClient | None:
        return LLMClient()

    def validate_market_request(self, symbol: str, timeframe: str) -> None:
        if symbol not in self.valid_symbols:
            raise ValueError(f"无效交易对。可选: {self.valid_symbols}")
        if timeframe not in self.valid_timeframes:
            raise ValueError(f"无效时间周期。可选: {self.valid_timeframes}")

    async def get_realtime(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        resolved_timeframe = timeframe or settings.TIMEFRAME
        self.validate_market_request(symbol, resolved_timeframe)
        resolved_limit = limit or settings.LIMIT

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                resolved_timeframe,
                resolved_limit,
            ),
        )
        if result is None:
            raise RuntimeError("获取数据失败")

        kline_data, indicators = result
        ai_analysis = None
        llm_client = self.get_llm_client()
        if llm_client:
            try:
                ai_analysis = await self.realtime_service.maybe_run_ai(llm_client, symbol, kline_data, indicators)
            except Exception as exc:
                logger.warning(f"AI 分析失败: {exc}")
        return self.realtime_service.build_response_payload(
            symbol,
            resolved_timeframe,
            kline_data,
            indicators,
            ai_analysis=ai_analysis,
        )

    async def get_realtime_ws_payload(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        use_ai: bool,
    ) -> dict[str, Any] | None:
        self.validate_market_request(symbol, timeframe)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                timeframe,
                limit,
            ),
        )
        if not result:
            return None

        kline_data, indicators = result
        ai_analysis = None
        if use_ai:
            llm_client = self.get_llm_client()
            if llm_client:
                try:
                    ai_analysis = await self.realtime_service.maybe_run_ai(llm_client, symbol, kline_data, indicators)
                except Exception as exc:
                    logger.warning(f"WS AI 分析失败: {exc}")
        return self.realtime_service.build_response_payload(
            symbol,
            timeframe,
            kline_data,
            indicators,
            ai_analysis=ai_analysis,
            include_type=True,
        )

    def get_history(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        end_ts: int,
        limit: int,
    ) -> list[list[float]]:
        self.validate_market_request(symbol, timeframe)
        return self.history_service.get_history(market_data_service, symbol, timeframe, end_ts, limit)

    def get_recent_klines(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[list[float]]:
        self.validate_market_request(symbol, timeframe)
        return self.history_service.get_recent_klines(market_data_service, symbol, timeframe, limit)

    async def get_full_history(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        start_date: str,
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> list[list[float]]:
        self.validate_market_request(symbol, timeframe)
        return await self.history_service.get_full_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            persist_klines=persist_klines,
        )

    async def get_full_history_batch(
        self,
        *,
        market_data_service: MarketDataService,
        symbols: list[str],
        timeframe: str,
        start_date: str,
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> dict[str, list[list[float]]]:
        normalized_symbols: list[str] = []
        seen_symbols: set[str] = set()
        for symbol in symbols:
            self.validate_market_request(symbol, timeframe)
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            normalized_symbols.append(symbol)

        return await self.history_service.get_full_history_batch(
            market_data_service=market_data_service,
            symbols=normalized_symbols,
            timeframe=timeframe,
            start_date=start_date,
            persist_klines=persist_klines,
        )

    def get_indicators(self, category: str | None, days: int) -> list[dict[str, Any]]:
        return self.indicator_service.get_indicators(category=category, days=days)

    async def get_crypto_index(self, top_n: int, days: int) -> dict[str, Any]:
        return await self.crypto_index_service.get_index(top_n=top_n, days=days)

    async def get_current_funding_rate(self, symbol: str) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.funding_rate_service.fetch_current_rate(symbol),
        )

    async def sync_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.funding_rate_service.sync_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    async def get_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.funding_rate_service.get_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            ),
        )

    async def get_technical_metrics(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int,
        volatility_period: int,
    ) -> dict[str, Any]:
        self.validate_market_request(symbol, timeframe)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                timeframe,
                limit,
                atr_period=atr_period,
                volatility_period=volatility_period,
            ),
        )
        if not result:
            raise RuntimeError("获取数据失败")

        kline_data, indicators = result
        current_price = kline_data[-1][4]
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "sample_size": len(kline_data),
            "current_price": current_price,
            "atr": indicators.get("atr"),
            "atr_pct": indicators.get("atr_pct") * 100.0 if indicators.get("atr_pct") is not None else None,
            "realized_volatility_pct": indicators.get("realized_volatility") * 100.0
            if indicators.get("realized_volatility") is not None
            else None,
            "annualized_volatility_pct": indicators.get("annualized_volatility") * 100.0
            if indicators.get("annualized_volatility") is not None
            else None,
        }

    async def get_trade_setup(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        account_size: float,
        style: str,
        strategy: str,
        mode: str,
    ) -> dict[str, Any]:
        self.validate_market_request(symbol, timeframe)
        if mode not in {"rules", "ai"}:
            raise ValueError("无效判断方式。可选: rules, ai")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                timeframe,
                limit,
            ),
        )
        if not result:
            raise RuntimeError("获取数据失败")

        kline_data, indicators = result
        request = TradeSetupRequest(
            symbol=symbol,
            timeframe=timeframe,
            account_size=account_size,
            style=style,
            strategy=strategy,
            mode=mode,
        )
        if mode == "rules":
            return self.trade_setup_engine.build_rules(request, kline_data, indicators)

        llm_client = self.get_llm_client()
        if not llm_client:
            return self.trade_setup_engine.build_ai(request, kline_data, None)
        prompt = PromptEngine.build_trade_setup_prompt(
            symbol,
            timeframe,
            kline_data,
            indicators,
            account_size,
            style,
            strategy,
        )
        ai_payload = await llm_client.analyze(prompt)
        return self.trade_setup_engine.build_ai(request, kline_data, ai_payload)

    async def get_binance_spot_exchange_info(
        self,
        *,
        symbols: list[str] | None,
        permissions: list[str] | None,
        symbol_status: str | None,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_exchange_info(
            symbols=symbols,
            permissions=permissions,
            symbol_status=symbol_status,
        )

    async def get_binance_spot_ticker_24hr(self, *, symbols: list[str] | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_ticker_24hr(symbols=symbols)

    async def get_binance_spot_ticker_window(
        self,
        *,
        symbols: list[str] | None,
        window_size: str | None,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_ticker_window(symbols=symbols, window_size=window_size)

    async def get_binance_spot_price(self, *, symbols: list[str] | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_price(symbols=symbols)

    async def get_binance_spot_book_ticker(self, *, symbols: list[str] | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_book_ticker(symbols=symbols)

    async def get_binance_spot_depth(self, *, symbol: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_depth(symbol=symbol, limit=limit)

    async def get_binance_spot_trades(self, *, symbol: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_trades(symbol=symbol, limit=limit)

    async def get_binance_spot_agg_trades(
        self,
        *,
        symbol: str,
        limit: int,
        start_time: int | None,
        end_time: int | None,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_agg_trades(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_binance_spot_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int,
        start_time: int | None,
        end_time: int | None,
        ui_mode: bool,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_spot_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=ui_mode,
        )

    async def get_binance_usdm_exchange_info(self) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_exchange_info()

    async def get_binance_coinm_exchange_info(self) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_exchange_info()

    async def get_binance_usdm_ticker_24hr(self, *, symbol: str | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_ticker_24hr(symbol=symbol)

    async def get_binance_coinm_ticker_24hr(self, *, symbol: str | None, pair: str | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_ticker_24hr(symbol=symbol, pair=pair)

    async def get_binance_usdm_mark_price(self, *, symbol: str | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_mark_price(symbol=symbol)

    async def get_binance_coinm_mark_price(self, *, symbol: str | None, pair: str | None) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_mark_price(symbol=symbol, pair=pair)

    async def get_binance_usdm_funding_info(self) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_funding_info()

    async def get_binance_coinm_funding_info(self) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_funding_info()

    async def get_binance_usdm_funding_history(
        self,
        *,
        symbol: str | None,
        limit: int,
        start_time: int | None,
        end_time: int | None,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_binance_coinm_funding_history(
        self,
        *,
        symbol: str | None,
        limit: int,
        start_time: int | None,
        end_time: int | None,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_binance_usdm_open_interest(self, *, symbol: str) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_open_interest(symbol=symbol)

    async def get_binance_coinm_open_interest(self, *, symbol: str) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_open_interest(symbol=symbol)

    async def get_binance_usdm_open_interest_stats(self, *, symbol: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_open_interest_stats(symbol=symbol, period=period, limit=limit)

    async def get_binance_coinm_open_interest_stats(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_open_interest_stats(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )

    async def get_binance_usdm_long_short_ratio(self, *, symbol: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_long_short_ratio(symbol=symbol, period=period, limit=limit)

    async def get_binance_coinm_long_short_ratio(self, *, pair: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_long_short_ratio(pair=pair, period=period, limit=limit)

    async def get_binance_usdm_top_trader_accounts(self, *, symbol: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_top_trader_accounts(symbol=symbol, period=period, limit=limit)

    async def get_binance_coinm_top_trader_accounts(self, *, symbol: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_top_trader_accounts(symbol=symbol, period=period, limit=limit)

    async def get_binance_usdm_top_trader_positions(self, *, symbol: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_top_trader_positions(symbol=symbol, period=period, limit=limit)

    async def get_binance_coinm_top_trader_positions(self, *, pair: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_top_trader_positions(pair=pair, period=period, limit=limit)

    async def get_binance_usdm_taker_volume(self, *, symbol: str, period: str, limit: int) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_taker_volume(symbol=symbol, period=period, limit=limit)

    async def get_binance_coinm_taker_volume(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_taker_volume(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )

    async def get_binance_usdm_basis(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_usdm_basis(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )

    async def get_binance_coinm_basis(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int,
    ) -> dict[str, Any]:
        return await self.binance_market_intel_service.get_coinm_basis(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )

    async def get_binance_web3_social_hype(
        self,
        *,
        chain_id: str,
        target_language: str,
        time_range: int,
        sentiment: str,
        social_language: str,
    ) -> dict[str, Any]:
        return await self.binance_web3_service.get_social_hype_leaderboard(
            chain_id=chain_id,
            target_language=target_language,
            time_range=time_range,
            sentiment=sentiment,
            social_language=social_language,
        )

    async def get_binance_web3_unified_token_rank(
        self,
        *,
        rank_type: int,
        chain_id: str | None,
        period: int,
        sort_by: int,
        order_asc: bool,
        page: int,
        size: int,
    ) -> dict[str, Any]:
        return await self.binance_web3_service.get_unified_token_rank(
            rank_type=rank_type,
            chain_id=chain_id,
            period=period,
            sort_by=sort_by,
            order_asc=order_asc,
            page=page,
            size=size,
        )

    async def get_binance_web3_smart_money_inflow(self, *, chain_id: str, period: str, tag_type: int) -> dict[str, Any]:
        return await self.binance_web3_service.get_smart_money_inflow_rank(chain_id=chain_id, period=period, tag_type=tag_type)

    async def get_binance_web3_meme_rank(self, *, chain_id: str) -> dict[str, Any]:
        return await self.binance_web3_service.get_meme_rank(chain_id=chain_id)

    async def get_binance_web3_address_pnl_rank(
        self,
        *,
        chain_id: str,
        period: str,
        tag: str,
        page_no: int,
        page_size: int,
    ) -> dict[str, Any]:
        return await self.binance_web3_service.get_address_pnl_rank(
            chain_id=chain_id,
            period=period,
            tag=tag,
            page_no=page_no,
            page_size=page_size,
        )

    async def get_binance_rwa_symbols(self, *, platform_type: int | None) -> dict[str, Any]:
        return await self.binance_web3_service.list_rwa_symbols(platform_type=platform_type)

    async def get_binance_rwa_meta(self, *, chain_id: str, contract_address: str) -> dict[str, Any]:
        return await self.binance_web3_service.get_rwa_meta(chain_id=chain_id, contract_address=contract_address)

    async def get_binance_rwa_market_status(self) -> dict[str, Any]:
        return await self.binance_web3_service.get_rwa_market_status()

    async def get_binance_rwa_asset_market_status(self, *, chain_id: str, contract_address: str) -> dict[str, Any]:
        return await self.binance_web3_service.get_rwa_asset_market_status(chain_id=chain_id, contract_address=contract_address)

    async def get_binance_rwa_dynamic(self, *, chain_id: str, contract_address: str) -> dict[str, Any]:
        return await self.binance_web3_service.get_rwa_dynamic(chain_id=chain_id, contract_address=contract_address)

    async def get_binance_rwa_kline(
        self,
        *,
        chain_id: str,
        contract_address: str,
        interval: str,
        limit: int,
        start_time: int | None,
        end_time: int | None,
    ) -> dict[str, Any]:
        return await self.binance_web3_service.get_rwa_kline(
            chain_id=chain_id,
            contract_address=contract_address,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_reserved_token_search(
        self,
        *,
        keyword: str | None,
        chain_ids: str | None,
        order_by: str | None,
    ) -> dict[str, Any]:
        return await self.binance_web3_service.search_tokens(
            keyword=keyword,
            chain_ids=chain_ids,
            order_by=order_by,
        )

    async def get_reserved_token_metadata(self, *, chain_id: str | None, contract_address: str | None) -> dict[str, Any]:
        return await self.binance_web3_service.get_token_metadata(chain_id=chain_id, contract_address=contract_address)

    async def get_reserved_token_dynamic(self, *, chain_id: str | None, contract_address: str | None) -> dict[str, Any]:
        return await self.binance_web3_service.get_token_dynamic(chain_id=chain_id, contract_address=contract_address)

    async def get_reserved_token_kline(
        self,
        *,
        address: str | None,
        platform: str | None,
        interval: str | None,
        limit: int | None,
        from_time: int | None,
        to_time: int | None,
        pm: str | None,
    ) -> dict[str, Any]:
        return await self.binance_web3_service.get_token_kline(
            address=address,
            platform=platform,
            interval=interval,
            limit=limit,
            from_time=from_time,
            to_time=to_time,
            pm=pm,
        )

    async def get_reserved_token_audit(self, *, binance_chain_id: str | None, contract_address: str | None) -> dict[str, Any]:
        return await self.binance_web3_service.audit_token(
            binance_chain_id=binance_chain_id,
            contract_address=contract_address,
        )
