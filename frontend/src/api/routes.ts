// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

import type * as BacktestTypes from '../modules/backtest/contracts'
import type * as FactorTypes from '../modules/factors/contracts'
import type * as MarketTypes from '../modules/market/contracts'
import type * as ToolsTypes from '../modules/tools/contracts'
import type * as ConfigTypes from '../modules/system/contracts'

export type RouteParams = Record<string, string | number>
export type ApiQueryShape = object
export type EndpointQueryContract = { aliases?: Record<string, string>; repeatedKeys?: readonly string[] }

const fillRoute = (template: string, params: RouteParams = {}) => template.replace(/\{([^}]+)\}/g, (_, key: string) => {
  const value = params[key]
  if (value === undefined || value === null || value === '') throw new Error(`Missing API route param: ${key}`)
  return encodeURIComponent(String(value))
})

const routeTemplates = {
  analyze_factors: "/factor-research/analyze",
  compare_pairs: "/tools/compare_pairs",
  create_indicator: "/backtest/indicators",
  create_strategy_template: "/backtest/templates",
  create_strategy_version: "/backtest/strategies",
  dca_simulate: "/tools/dca_simulate",
  delete_backtest: "/backtest/{backtest_id}",
  delete_paper_run: "/paper/{run_id}",
  evolve_strategy_from_backtest: "/backtest/{backtest_id}/evolve",
  get_api_status: "/status",
  get_backtest: "/backtest/{backtest_id}",
  get_binance_market_contract_detail: "/binance/market/contract_detail",
  get_binance_market_page: "/binance/market/page",
  get_binance_rwa_asset_market_status: "/binance/rwa/asset_market_status",
  get_binance_rwa_dynamic: "/binance/rwa/dynamic",
  get_binance_rwa_kline: "/binance/rwa/kline",
  get_binance_rwa_market_status: "/binance/rwa/market_status",
  get_binance_rwa_meta: "/binance/rwa/meta",
  get_binance_rwa_symbols: "/binance/rwa/symbols",
  get_binance_spot_agg_trades: "/binance/spot/agg_trades",
  get_binance_spot_book_ticker: "/binance/spot/book_ticker",
  get_binance_spot_depth: "/binance/spot/depth",
  get_binance_spot_exchange_info: "/binance/spot/exchange_info",
  get_binance_spot_klines: "/binance/spot/klines",
  get_binance_spot_price: "/binance/spot/price",
  get_binance_spot_ticker_24hr: "/binance/spot/ticker_24hr",
  get_binance_spot_ticker_window: "/binance/spot/ticker_window",
  get_binance_spot_trades: "/binance/spot/trades",
  get_binance_spot_ui_klines: "/binance/spot/ui_klines",
  get_binance_usdm_basis: "/binance/futures/usdm/basis",
  get_binance_usdm_exchange_info: "/binance/futures/usdm/exchange_info",
  get_binance_usdm_funding_history: "/binance/futures/usdm/funding_history",
  get_binance_usdm_funding_info: "/binance/futures/usdm/funding_info",
  get_binance_usdm_long_short_ratio: "/binance/futures/usdm/long_short_ratio",
  get_binance_usdm_mark_price: "/binance/futures/usdm/mark_price",
  get_binance_usdm_open_interest: "/binance/futures/usdm/open_interest",
  get_binance_usdm_open_interest_stats: "/binance/futures/usdm/open_interest_stats",
  get_binance_usdm_taker_volume: "/binance/futures/usdm/taker_volume",
  get_binance_usdm_ticker_24hr: "/binance/futures/usdm/ticker_24hr",
  get_binance_usdm_top_trader_accounts: "/binance/futures/usdm/top_trader_accounts",
  get_binance_usdm_top_trader_positions: "/binance/futures/usdm/top_trader_positions",
  get_binance_web3_address_pnl_rank: "/binance/web3/address_pnl_rank",
  get_binance_web3_heat_rank: "/binance/web3/heat_rank",
  get_binance_web3_heat_rank_boards: "/binance/web3/heat_rank_boards",
  get_binance_web3_meme_rank: "/binance/web3/meme_rank",
  get_binance_web3_smart_money_inflow: "/binance/web3/smart_money_inflow",
  get_binance_web3_social_hype: "/binance/web3/social_hype",
  get_binance_web3_token_audit: "/binance/web3/token_audit",
  get_binance_web3_token_dynamic: "/binance/web3/token_dynamic",
  get_binance_web3_token_kline: "/binance/web3/token_kline",
  get_binance_web3_unified_token_rank: "/binance/web3/unified_token_rank",
  get_config: "/config",
  get_crypto_index: "/crypto_index",
  get_currencies: "/currencies",
  get_current_funding_rate: "/funding-rate/current",
  get_current_price: "/price/current",
  get_current_price_batch: "/price/current/batch",
  get_factor_catalog: "/factor-research/catalog",
  get_factor_contract: "/factor-research/contract",
  get_factor_run: "/factor-research/runs/{run_id}",
  get_fred_api_config: "/fred-api-config",
  get_funding_rate_history: "/funding-rate/history",
  get_index_history: "/indexes/history",
  get_index_pricing_history: "/indexes/pricing/history",
  get_kline_tail: "/klines/tail",
  get_latest_index: "/indexes/latest",
  get_latest_index_pricing: "/indexes/pricing/latest",
  get_latest_klines: "/klines/latest",
  get_llm_config: "/llm-config",
  get_market_full_history: "/full_history",
  get_market_full_history_batch: "/full_history/batch",
  get_market_history: "/history",
  get_market_indicators: "/indicators",
  get_paper_run: "/paper/{run_id}",
  get_realtime_analysis: "/realtime",
  get_strategy_editor_contract: "/backtest/editor-contract",
  get_technical_metrics: "/technical-metrics",
  get_tools_contract: "/tools/contract",
  get_trade_setup: "/trade-setup",
  list_backtests: "/backtest/list",
  list_factor_runs: "/factor-research/runs",
  list_indicator_engines: "/backtest/indicator-engines",
  list_indicators: "/backtest/indicators",
  list_market_indexes: "/indexes",
  list_market_symbols: "/symbols",
  list_paper_runs: "/paper/list",
  list_strategies: "/backtest/strategies",
  list_strategy_templates: "/backtest/templates",
  start_backtest: "/backtest/start",
  start_factor_backtest: "/factor-research/runs/{run_id}/backtest",
  start_factor_paper_run: "/factor-research/runs/{run_id}/paper",
  start_paper_run: "/paper/start",
  stop_paper_run: "/paper/{run_id}/stop",
  sync_funding_rate_history: "/funding-rate/sync",
  update_fred_api_config: "/fred-api-config",
  update_llm_config: "/llm-config",
} as const

export type ApiRouteName = keyof typeof routeTemplates

export const apiRoute = (name: ApiRouteName, params?: RouteParams) => fillRoute(routeTemplates[name], params)

export const apiEndpoint = (name: ApiRouteName, params?: RouteParams) => ({
  name,
  url: apiRoute(name, params),
  query: endpointQueryContracts[name],
})

export const serializeEndpointQuery = (name: ApiRouteName, params: ApiQueryShape = {}) => {
  const contract = endpointQueryContracts[name]
  const query = new URLSearchParams()
  Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return
    const resolvedKey = contract?.aliases?.[key] ?? key
    const repeatedKeys = contract?.repeatedKeys ?? []
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== null && item !== undefined && item !== '') query.append(resolvedKey, String(item))
      })
      return
    }
    if (repeatedKeys.includes(key)) {
      query.append(resolvedKey, String(value))
      return
    }
    query.set(resolvedKey, String(value))
  })
  return query.toString()
}

const endpointQueryContracts = {
  analyze_factors: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  compare_pairs: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  create_indicator: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  create_strategy_template: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  create_strategy_version: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  dca_simulate: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  delete_backtest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  delete_paper_run: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  evolve_strategy_from_backtest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_api_status: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_backtest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_market_contract_detail: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_market_page: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_rwa_asset_market_status: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_rwa_dynamic: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_rwa_kline: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_rwa_market_status: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_rwa_meta: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_rwa_symbols: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_agg_trades: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_book_ticker: {"repeatedKeys": ["symbols"], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_depth: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_exchange_info: {"repeatedKeys": ["symbols", "permissions"], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_klines: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_price: {"repeatedKeys": ["symbols"], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_ticker_24hr: {"repeatedKeys": ["symbols"], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_ticker_window: {"repeatedKeys": ["symbols"], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_trades: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_spot_ui_klines: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_basis: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_exchange_info: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_funding_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_funding_info: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_long_short_ratio: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_mark_price: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_open_interest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_open_interest_stats: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_taker_volume: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_ticker_24hr: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_top_trader_accounts: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_usdm_top_trader_positions: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_address_pnl_rank: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_heat_rank: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_heat_rank_boards: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_meme_rank: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_smart_money_inflow: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_social_hype: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_token_audit: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_token_dynamic: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_web3_token_kline: {"repeatedKeys": [], "aliases": {"from_time": "from", "to_time": "to"}} as EndpointQueryContract,
  get_binance_web3_unified_token_rank: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_config: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_crypto_index: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_currencies: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_current_funding_rate: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_current_price: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_current_price_batch: {"repeatedKeys": ["symbols"], "aliases": {}} as EndpointQueryContract,
  get_factor_catalog: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_factor_contract: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_factor_run: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_fred_api_config: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_funding_rate_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_index_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_index_pricing_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_kline_tail: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_latest_index: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_latest_index_pricing: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_latest_klines: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_llm_config: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_market_full_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_market_full_history_batch: {"repeatedKeys": ["symbols"], "aliases": {}} as EndpointQueryContract,
  get_market_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_market_indicators: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_paper_run: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_realtime_analysis: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_strategy_editor_contract: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_technical_metrics: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_tools_contract: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_trade_setup: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_backtests: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_factor_runs: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_indicator_engines: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_indicators: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_market_indexes: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_market_symbols: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_paper_runs: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_strategies: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  list_strategy_templates: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  start_backtest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  start_factor_backtest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  start_factor_paper_run: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  start_paper_run: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  stop_paper_run: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  sync_funding_rate_history: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  update_fred_api_config: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  update_llm_config: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
} as const

export type ApiRouteResponseMap = {
  analyze_factors: FactorTypes.FactorResearchResponse
  compare_pairs: ToolsTypes.PairCompareToolResponse
  create_indicator: BacktestTypes.StrategyIndicatorRegistryResponse
  create_strategy_template: BacktestTypes.StrategyTemplateResponse
  create_strategy_version: BacktestTypes.StrategyVersionResponse
  dca_simulate: ToolsTypes.DCAResponse
  delete_backtest: BacktestTypes.BacktestDeleteResponse
  delete_paper_run: BacktestTypes.BacktestDeleteResponse
  evolve_strategy_from_backtest: BacktestTypes.StrategyEvolutionResponse
  get_api_status: MarketTypes.ApiStatusResponse
  get_backtest: BacktestTypes.BacktestDetailResponse
  get_binance_market_contract_detail: MarketTypes.BinanceContractResearchDetailResponse
  get_binance_market_page: MarketTypes.BinanceMarketPageResponse
  get_binance_rwa_asset_market_status: MarketTypes.BinanceRwaMarketStatusResponse
  get_binance_rwa_dynamic: MarketTypes.BinanceRwaDynamicResponse
  get_binance_rwa_kline: MarketTypes.BinanceRwaKlineResponse
  get_binance_rwa_market_status: MarketTypes.BinanceRwaMarketStatusResponse
  get_binance_rwa_meta: MarketTypes.BinanceRwaMetaResponse
  get_binance_rwa_symbols: MarketTypes.BinanceRwaSymbolListResponse
  get_binance_spot_agg_trades: MarketTypes.BinanceTradeListResponse
  get_binance_spot_book_ticker: MarketTypes.BinanceBookTickerResponse
  get_binance_spot_depth: MarketTypes.BinanceOrderBookResponse
  get_binance_spot_exchange_info: MarketTypes.BinanceExchangeInfoResponse
  get_binance_spot_klines: MarketTypes.BinanceKlineResponse
  get_binance_spot_price: MarketTypes.BinancePriceTickerResponse
  get_binance_spot_ticker_24hr: MarketTypes.BinanceTickerStatsResponse
  get_binance_spot_ticker_window: MarketTypes.BinanceTickerStatsResponse
  get_binance_spot_trades: MarketTypes.BinanceTradeListResponse
  get_binance_spot_ui_klines: MarketTypes.BinanceKlineResponse
  get_binance_usdm_basis: MarketTypes.BinanceBasisResponse
  get_binance_usdm_exchange_info: MarketTypes.BinanceExchangeInfoResponse
  get_binance_usdm_funding_history: MarketTypes.BinanceFundingHistoryListResponse
  get_binance_usdm_funding_info: MarketTypes.BinanceFundingInfoResponse
  get_binance_usdm_long_short_ratio: MarketTypes.BinanceRatioSeriesResponse
  get_binance_usdm_mark_price: MarketTypes.BinanceMarkPriceResponse
  get_binance_usdm_open_interest: MarketTypes.BinanceOpenInterestSnapshotResponse
  get_binance_usdm_open_interest_stats: MarketTypes.BinanceOpenInterestStatsResponse
  get_binance_usdm_taker_volume: MarketTypes.BinanceTakerVolumeResponse
  get_binance_usdm_ticker_24hr: MarketTypes.BinanceTickerStatsResponse
  get_binance_usdm_top_trader_accounts: MarketTypes.BinanceRatioSeriesResponse
  get_binance_usdm_top_trader_positions: MarketTypes.BinanceRatioSeriesResponse
  get_binance_web3_address_pnl_rank: MarketTypes.BinanceWeb3AddressPnlResponse
  get_binance_web3_heat_rank: MarketTypes.BinanceWeb3HeatRankResponse
  get_binance_web3_heat_rank_boards: MarketTypes.BinanceWeb3HeatRankBoardsResponse
  get_binance_web3_meme_rank: MarketTypes.BinanceWeb3MemeRankResponse
  get_binance_web3_smart_money_inflow: MarketTypes.BinanceWeb3SmartMoneyInflowResponse
  get_binance_web3_social_hype: MarketTypes.BinanceWeb3SocialHypeResponse
  get_binance_web3_token_audit: MarketTypes.BinanceWeb3TokenAuditResponse
  get_binance_web3_token_dynamic: MarketTypes.BinanceWeb3TokenDynamicResponse
  get_binance_web3_token_kline: MarketTypes.BinanceWeb3TokenKlineResponse
  get_binance_web3_unified_token_rank: MarketTypes.BinanceWeb3UnifiedTokenRankResponse
  get_config: ConfigTypes.SystemConfigResponse
  get_crypto_index: MarketTypes.CryptoIndexResponse
  get_currencies: ConfigTypes.CurrencyRatesResponse
  get_current_funding_rate: MarketTypes.FundingRateSnapshotResponse
  get_current_price: MarketTypes.CurrentPriceResponse
  get_current_price_batch: MarketTypes.CurrentPriceBatchResponse
  get_factor_catalog: FactorTypes.FactorCatalogResponse
  get_factor_contract: FactorTypes.FactorResearchContractResponse
  get_factor_run: FactorTypes.FactorResearchRunDetailResponse
  get_fred_api_config: ConfigTypes.FredApiConfigResponse
  get_funding_rate_history: MarketTypes.FundingRateHistoryResponse
  get_index_history: MarketTypes.MarketIndexHistoryResponse
  get_index_pricing_history: MarketTypes.MarketIndexHistoryResponse
  get_kline_tail: MarketTypes.KlineTailResponse
  get_latest_index: MarketTypes.MarketIndexHistoryResponse
  get_latest_index_pricing: MarketTypes.MarketIndexHistoryResponse
  get_latest_klines: MarketTypes.MarketHistoryResponse
  get_llm_config: ConfigTypes.LlmProviderConfigResponse
  get_market_full_history: MarketTypes.MarketHistoryResponse
  get_market_full_history_batch: MarketTypes.MarketHistoryBatchResponse
  get_market_history: MarketTypes.MarketHistoryResponse
  get_market_indicators: Array<MarketTypes.MarketIndicatorResponse>
  get_paper_run: BacktestTypes.BacktestDetailResponse
  get_realtime_analysis: MarketTypes.RealtimeResponse
  get_strategy_editor_contract: BacktestTypes.StrategyEditorContractResponse
  get_technical_metrics: MarketTypes.TechnicalMetricsResponse
  get_tools_contract: ToolsTypes.ToolsPageContractResponse
  get_trade_setup: MarketTypes.TradeSetupResponse
  list_backtests: Array<BacktestTypes.BacktestRunResponse>
  list_factor_runs: Array<FactorTypes.FactorResearchRunListItemResponse>
  list_indicator_engines: Array<BacktestTypes.StrategyIndicatorEngineResponse>
  list_indicators: Array<BacktestTypes.StrategyIndicatorRegistryResponse>
  list_market_indexes: Array<MarketTypes.MarketIndexResponse>
  list_market_symbols: Array<MarketTypes.MarketSymbolSearchResponse>
  list_paper_runs: Array<BacktestTypes.BacktestRunResponse>
  list_strategies: Array<BacktestTypes.StrategyDefinitionResponse>
  list_strategy_templates: Array<BacktestTypes.StrategyTemplateResponse>
  start_backtest: BacktestTypes.BacktestStartResponse
  start_factor_backtest: FactorTypes.FactorExecutionResponse
  start_factor_paper_run: FactorTypes.FactorExecutionResponse
  start_paper_run: BacktestTypes.PaperStartResponse
  stop_paper_run: BacktestTypes.PaperStopResponse
  sync_funding_rate_history: MarketTypes.FundingRateSyncResponse
  update_fred_api_config: ConfigTypes.FredApiConfigResponse
  update_llm_config: ConfigTypes.LlmProviderConfigResponse
}

export type ApiRouteBodyMap = {
  analyze_factors: FactorTypes.FactorResearchRequest
  compare_pairs: ToolsTypes.PairCompareRequestSchema
  create_indicator: BacktestTypes.IndicatorDefinitionCreateRequest
  create_strategy_template: BacktestTypes.StrategyTemplateCreateRequest
  create_strategy_version: BacktestTypes.StrategyVersionCreateRequest
  dca_simulate: ToolsTypes.DCARequestSchema
  delete_backtest: never
  delete_paper_run: never
  evolve_strategy_from_backtest: BacktestTypes.StrategyEvolutionRequest
  get_api_status: never
  get_backtest: never
  get_binance_market_contract_detail: never
  get_binance_market_page: never
  get_binance_rwa_asset_market_status: never
  get_binance_rwa_dynamic: never
  get_binance_rwa_kline: never
  get_binance_rwa_market_status: never
  get_binance_rwa_meta: never
  get_binance_rwa_symbols: never
  get_binance_spot_agg_trades: never
  get_binance_spot_book_ticker: never
  get_binance_spot_depth: never
  get_binance_spot_exchange_info: never
  get_binance_spot_klines: never
  get_binance_spot_price: never
  get_binance_spot_ticker_24hr: never
  get_binance_spot_ticker_window: never
  get_binance_spot_trades: never
  get_binance_spot_ui_klines: never
  get_binance_usdm_basis: never
  get_binance_usdm_exchange_info: never
  get_binance_usdm_funding_history: never
  get_binance_usdm_funding_info: never
  get_binance_usdm_long_short_ratio: never
  get_binance_usdm_mark_price: never
  get_binance_usdm_open_interest: never
  get_binance_usdm_open_interest_stats: never
  get_binance_usdm_taker_volume: never
  get_binance_usdm_ticker_24hr: never
  get_binance_usdm_top_trader_accounts: never
  get_binance_usdm_top_trader_positions: never
  get_binance_web3_address_pnl_rank: never
  get_binance_web3_heat_rank: never
  get_binance_web3_heat_rank_boards: never
  get_binance_web3_meme_rank: never
  get_binance_web3_smart_money_inflow: never
  get_binance_web3_social_hype: never
  get_binance_web3_token_audit: never
  get_binance_web3_token_dynamic: never
  get_binance_web3_token_kline: never
  get_binance_web3_unified_token_rank: never
  get_config: never
  get_crypto_index: never
  get_currencies: never
  get_current_funding_rate: never
  get_current_price: never
  get_current_price_batch: never
  get_factor_catalog: never
  get_factor_contract: never
  get_factor_run: never
  get_fred_api_config: never
  get_funding_rate_history: never
  get_index_history: never
  get_index_pricing_history: never
  get_kline_tail: never
  get_latest_index: never
  get_latest_index_pricing: never
  get_latest_klines: never
  get_llm_config: never
  get_market_full_history: never
  get_market_full_history_batch: never
  get_market_history: never
  get_market_indicators: never
  get_paper_run: never
  get_realtime_analysis: never
  get_strategy_editor_contract: never
  get_technical_metrics: never
  get_tools_contract: never
  get_trade_setup: never
  list_backtests: never
  list_factor_runs: never
  list_indicator_engines: never
  list_indicators: never
  list_market_indexes: never
  list_market_symbols: never
  list_paper_runs: never
  list_strategies: never
  list_strategy_templates: never
  start_backtest: BacktestTypes.BacktestStartRequest
  start_factor_backtest: FactorTypes.FactorExecutionRequest
  start_factor_paper_run: FactorTypes.FactorExecutionRequest
  start_paper_run: BacktestTypes.PaperStartRequest
  stop_paper_run: never
  sync_funding_rate_history: never
  update_fred_api_config: ConfigTypes.FredApiConfigUpdateRequest
  update_llm_config: ConfigTypes.LlmProviderConfigUpdateRequest
}

export type ApiRouteQueryMap = {
  analyze_factors: never
  compare_pairs: never
  create_indicator: never
  create_strategy_template: never
  create_strategy_version: never
  dca_simulate: never
  delete_backtest: never
  delete_paper_run: never
  evolve_strategy_from_backtest: never
  get_api_status: never
  get_backtest: BacktestTypes.GetBacktestQueryParams
  get_binance_market_contract_detail: MarketTypes.GetBinanceMarketContractDetailQueryParams
  get_binance_market_page: MarketTypes.GetBinanceMarketPageQueryParams
  get_binance_rwa_asset_market_status: MarketTypes.GetBinanceRwaAssetMarketStatusQueryParams
  get_binance_rwa_dynamic: MarketTypes.GetBinanceRwaDynamicQueryParams
  get_binance_rwa_kline: MarketTypes.GetBinanceRwaKlineQueryParams
  get_binance_rwa_market_status: never
  get_binance_rwa_meta: MarketTypes.GetBinanceRwaMetaQueryParams
  get_binance_rwa_symbols: MarketTypes.GetBinanceRwaSymbolsQueryParams
  get_binance_spot_agg_trades: MarketTypes.GetBinanceSpotAggTradesQueryParams
  get_binance_spot_book_ticker: MarketTypes.GetBinanceSpotBookTickerQueryParams
  get_binance_spot_depth: MarketTypes.GetBinanceSpotDepthQueryParams
  get_binance_spot_exchange_info: MarketTypes.GetBinanceSpotExchangeInfoQueryParams
  get_binance_spot_klines: MarketTypes.GetBinanceSpotKlinesQueryParams
  get_binance_spot_price: MarketTypes.GetBinanceSpotPriceQueryParams
  get_binance_spot_ticker_24hr: MarketTypes.GetBinanceSpotTicker24hrQueryParams
  get_binance_spot_ticker_window: MarketTypes.GetBinanceSpotTickerWindowQueryParams
  get_binance_spot_trades: MarketTypes.GetBinanceSpotTradesQueryParams
  get_binance_spot_ui_klines: MarketTypes.GetBinanceSpotUiKlinesQueryParams
  get_binance_usdm_basis: MarketTypes.GetBinanceUsdmBasisQueryParams
  get_binance_usdm_exchange_info: never
  get_binance_usdm_funding_history: MarketTypes.GetBinanceUsdmFundingHistoryQueryParams
  get_binance_usdm_funding_info: never
  get_binance_usdm_long_short_ratio: MarketTypes.GetBinanceUsdmLongShortRatioQueryParams
  get_binance_usdm_mark_price: MarketTypes.GetBinanceUsdmMarkPriceQueryParams
  get_binance_usdm_open_interest: MarketTypes.GetBinanceUsdmOpenInterestQueryParams
  get_binance_usdm_open_interest_stats: MarketTypes.GetBinanceUsdmOpenInterestStatsQueryParams
  get_binance_usdm_taker_volume: MarketTypes.GetBinanceUsdmTakerVolumeQueryParams
  get_binance_usdm_ticker_24hr: MarketTypes.GetBinanceUsdmTicker24hrQueryParams
  get_binance_usdm_top_trader_accounts: MarketTypes.GetBinanceUsdmTopTraderAccountsQueryParams
  get_binance_usdm_top_trader_positions: MarketTypes.GetBinanceUsdmTopTraderPositionsQueryParams
  get_binance_web3_address_pnl_rank: MarketTypes.GetBinanceWeb3AddressPnlRankQueryParams
  get_binance_web3_heat_rank: MarketTypes.GetBinanceWeb3HeatRankQueryParams
  get_binance_web3_heat_rank_boards: MarketTypes.GetBinanceWeb3HeatRankBoardsQueryParams
  get_binance_web3_meme_rank: MarketTypes.GetBinanceWeb3MemeRankQueryParams
  get_binance_web3_smart_money_inflow: MarketTypes.GetBinanceWeb3SmartMoneyInflowQueryParams
  get_binance_web3_social_hype: MarketTypes.GetBinanceWeb3SocialHypeQueryParams
  get_binance_web3_token_audit: MarketTypes.GetBinanceWeb3TokenAuditQueryParams
  get_binance_web3_token_dynamic: MarketTypes.GetBinanceWeb3TokenDynamicQueryParams
  get_binance_web3_token_kline: MarketTypes.GetBinanceWeb3TokenKlineQueryParams
  get_binance_web3_unified_token_rank: MarketTypes.GetBinanceWeb3UnifiedTokenRankQueryParams
  get_config: never
  get_crypto_index: MarketTypes.GetCryptoIndexQueryParams
  get_currencies: never
  get_current_funding_rate: MarketTypes.GetCurrentFundingRateQueryParams
  get_current_price: MarketTypes.GetCurrentPriceQueryParams
  get_current_price_batch: MarketTypes.GetCurrentPriceBatchQueryParams
  get_factor_catalog: never
  get_factor_contract: never
  get_factor_run: never
  get_fred_api_config: never
  get_funding_rate_history: MarketTypes.GetFundingRateHistoryQueryParams
  get_index_history: MarketTypes.GetIndexHistoryQueryParams
  get_index_pricing_history: MarketTypes.GetIndexPricingHistoryQueryParams
  get_kline_tail: MarketTypes.GetKlineTailQueryParams
  get_latest_index: MarketTypes.GetLatestIndexQueryParams
  get_latest_index_pricing: MarketTypes.GetLatestIndexPricingQueryParams
  get_latest_klines: MarketTypes.GetLatestKlinesQueryParams
  get_llm_config: never
  get_market_full_history: MarketTypes.GetMarketFullHistoryQueryParams
  get_market_full_history_batch: MarketTypes.GetMarketFullHistoryBatchQueryParams
  get_market_history: MarketTypes.GetMarketHistoryQueryParams
  get_market_indicators: MarketTypes.GetMarketIndicatorsQueryParams
  get_paper_run: BacktestTypes.GetPaperRunQueryParams
  get_realtime_analysis: MarketTypes.GetRealtimeAnalysisQueryParams
  get_strategy_editor_contract: never
  get_technical_metrics: MarketTypes.GetTechnicalMetricsQueryParams
  get_tools_contract: never
  get_trade_setup: MarketTypes.GetTradeSetupQueryParams
  list_backtests: never
  list_factor_runs: FactorTypes.ListFactorRunsQueryParams
  list_indicator_engines: never
  list_indicators: never
  list_market_indexes: never
  list_market_symbols: never
  list_paper_runs: never
  list_strategies: never
  list_strategy_templates: never
  start_backtest: never
  start_factor_backtest: never
  start_factor_paper_run: never
  start_paper_run: never
  stop_paper_run: never
  sync_funding_rate_history: MarketTypes.SyncFundingRateHistoryQueryParams
  update_fred_api_config: never
  update_llm_config: never
}

export type ApiRouteResponse<N extends ApiRouteName> = ApiRouteResponseMap[N]
export type ApiRouteBody<N extends ApiRouteName> = ApiRouteBodyMap[N]
export type ApiRouteQuery<N extends ApiRouteName> = ApiRouteQueryMap[N]
