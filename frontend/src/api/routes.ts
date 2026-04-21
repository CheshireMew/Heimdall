// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

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
  get_api_status: "/status",
  get_backtest: "/backtest/{backtest_id}",
  get_binance_market_breakout_monitor: "/binance/market/breakout_monitor",
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
  get_api_status: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_backtest: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
  get_binance_market_breakout_monitor: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
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
  update_llm_config: {"repeatedKeys": [], "aliases": {}} as EndpointQueryContract,
} as const
