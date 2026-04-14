import { computed, ref } from 'vue'
import { marketApi } from './api'
import type { MarketSymbolSearchItem } from '@/types'

const fallbackSymbols: MarketSymbolSearchItem[] = [
  { symbol: 'USD', name: 'US Dollar', asset_class: 'cash', market: 'USD', currency: 'USD', exchange: 'USD', aliases: ['美元', '现金', 'stablecoin', '稳定币'], pricing_currency: 'USD' },
  { symbol: 'USDT', name: 'USDT USD equivalent', asset_class: 'cash', market: 'USD', currency: 'USD', exchange: 'USD', aliases: ['Tether', '美元稳定币', 'stablecoin'], pricing_currency: 'USD' },
  { symbol: 'USDC', name: 'USDC USD equivalent', asset_class: 'cash', market: 'USD', currency: 'USD', exchange: 'USD', aliases: ['Circle', '美元稳定币', 'stablecoin'], pricing_currency: 'USD' },
  { symbol: 'FDUSD', name: 'FDUSD USD equivalent', asset_class: 'cash', market: 'USD', currency: 'USD', exchange: 'USD', aliases: ['美元稳定币', 'stablecoin'], pricing_currency: 'USD' },
  { symbol: 'DAI', name: 'DAI USD equivalent', asset_class: 'cash', market: 'USD', currency: 'USD', exchange: 'USD', aliases: ['美元稳定币', 'stablecoin'], pricing_currency: 'USD' },
  { symbol: 'BTC/USDT', name: 'BTC/USDT', asset_class: 'crypto', market: 'CRYPTO', currency: 'USDT', exchange: 'BINANCE', pricing_currency: 'USDT' },
  { symbol: 'ETH/USDT', name: 'ETH/USDT', asset_class: 'crypto', market: 'CRYPTO', currency: 'USDT', exchange: 'BINANCE', pricing_currency: 'USDT' },
  { symbol: 'SOL/USDT', name: 'SOL/USDT', asset_class: 'crypto', market: 'CRYPTO', currency: 'USDT', exchange: 'BINANCE', pricing_currency: 'USDT' },
  { symbol: 'DOGE/USDT', name: 'DOGE/USDT', asset_class: 'crypto', market: 'CRYPTO', currency: 'USDT', exchange: 'BINANCE', pricing_currency: 'USDT' },
  { symbol: 'US_SP500', name: 'S&P 500', asset_class: 'index', market: 'US', currency: 'USD', exchange: 'US', aliases: ['标普', '标普500', 'SP500', 'S&P', 'S&P500', 'SPX'], pricing_symbol: 'SPY', pricing_name: 'SPDR S&P 500 ETF Trust', pricing_currency: 'USD' },
  { symbol: 'US_NASDAQ100', name: 'Nasdaq 100', asset_class: 'index', market: 'US', currency: 'USD', exchange: 'US', aliases: ['纳斯达克100', '纳指100', 'NASDAQ100', 'NDX100', 'NDX'], pricing_symbol: 'QQQ', pricing_name: 'Invesco QQQ Trust', pricing_currency: 'USD' },
  { symbol: 'CN_CSI_A500', name: '中证A500', asset_class: 'index', market: 'CN', currency: 'CNY', exchange: 'CN', aliases: ['中证A500', '中证 A500', 'A500', 'CSI A500', '000510'], pricing_symbol: 'sh560610', pricing_name: 'A500指数ETF', pricing_currency: 'CNY' },
  { symbol: 'CN_STAR50', name: '科创50', asset_class: 'index', market: 'CN', currency: 'CNY', exchange: 'CN', aliases: ['科创50', '科创 50', 'STAR50', '000688'], pricing_symbol: 'sh588000', pricing_name: '科创50ETF', pricing_currency: 'CNY' },
  { symbol: 'HK_HSI', name: '恒生指数', asset_class: 'index', market: 'HK', currency: 'HKD', exchange: 'HK', aliases: ['恒生', '恒生指数', 'HSI'], pricing_symbol: '02800', pricing_name: 'Tracker Fund of Hong Kong', pricing_currency: 'HKD' },
  { symbol: 'HK_HSTECH', name: '恒生科技指数', asset_class: 'index', market: 'HK', currency: 'HKD', exchange: 'HK', aliases: ['恒生科技', '恒生科技指数', '恒科', 'HSTECH'], pricing_symbol: '03033', pricing_name: 'CSOP Hang Seng TECH Index ETF', pricing_currency: 'HKD' },
]

const symbols = ref<MarketSymbolSearchItem[]>(fallbackSymbols)
const loading = ref(false)
let loaded = false

export const isIndexSymbol = (symbol: string) => /^(US|CN|HK)_/.test(String(symbol || '').toUpperCase())

export const USD_EQUIVALENT_SYMBOLS = ['USD', 'USDT', 'USDC', 'FDUSD', 'BUSD', 'DAI', 'TUSD', 'USDP', 'PYUSD', 'USDS']

export const isUsdEquivalentSymbol = (symbol: string) => USD_EQUIVALENT_SYMBOLS.includes(toBaseSymbol(symbol))

export const toBaseSymbol = (symbol: string) => {
  const value = String(symbol || '').trim().toUpperCase()
  return value.includes('/') ? value.split('/')[0] : value
}

export const findSymbolCatalogItem = (symbol: string) => {
  const normalized = String(symbol || '').trim().toUpperCase()
  if (!normalized) return null
  const base = toBaseSymbol(normalized)
  return symbols.value.find((item) => {
    const itemSymbol = String(item.symbol || '').trim().toUpperCase()
    return itemSymbol === normalized || toBaseSymbol(itemSymbol) === base
  }) || null
}

export function useSymbolCatalog() {
  const loadSymbols = async () => {
    if (loaded || loading.value) return
    loading.value = true
    try {
      const response = await marketApi.getSymbols()
      if (Array.isArray(response.data) && response.data.length) {
        symbols.value = response.data
        loaded = true
      }
    } catch (error) {
      console.warn('Symbol catalog load failed', error)
    } finally {
      loading.value = false
    }
  }

  return {
    symbols: computed(() => symbols.value),
    loading,
    loadSymbols,
  }
}
