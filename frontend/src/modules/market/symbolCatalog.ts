import { computed, ref } from 'vue'
import { marketApi } from './api'
import { BASE_SYMBOLS, USD_EQUIVALENT_SYMBOLS } from './baseSymbolCatalog'
import type { MarketSymbolSearchResponse } from './contracts'

const symbols = ref<MarketSymbolSearchResponse[]>([...BASE_SYMBOLS])
const usdEquivalentSymbolSet = new Set<string>(USD_EQUIVALENT_SYMBOLS)
const loading = ref(false)
let loaded = false

const fallbackAssetClass = (symbol: string) => {
  const value = String(symbol || '').trim().toUpperCase()
  if (!value) return null
  if (/^(US|CN|HK)_/.test(value)) return 'index'
  if (usdEquivalentSymbolSet.has(value.split('/')[0])) return 'cash'
  return null
}

const lookupCatalogItem = (symbol: string) => {
  const normalized = String(symbol || '').trim().toUpperCase()
  if (!normalized) return null
  const base = toBaseSymbol(normalized)
  return symbols.value.find((item) => {
    const itemSymbol = String(item.symbol || '').trim().toUpperCase()
    return itemSymbol === normalized || toBaseSymbol(itemSymbol) === base
  }) || null
}

export const isIndexSymbol = (symbol: string) => (
  lookupCatalogItem(symbol)?.asset_class === 'index'
  || fallbackAssetClass(symbol) === 'index'
)

export const isUsdEquivalentSymbol = (symbol: string) => (
  lookupCatalogItem(symbol)?.asset_class === 'cash'
  || fallbackAssetClass(symbol) === 'cash'
)

export const toBaseSymbol = (symbol: string) => {
  const value = String(symbol || '').trim().toUpperCase()
  const [base] = value.split('/')
  const [assetCode] = base.split(':')
  return assetCode.trim()
}

export const toSlashMarketSymbol = (symbol: string, quoteAsset = 'USDT') => {
  const value = String(symbol || '').trim().toUpperCase()
  const normalizedQuote = String(quoteAsset || '').trim().toUpperCase()
  if (!value) return ''
  if (value.includes('/')) return value
  if (normalizedQuote && value.endsWith(normalizedQuote) && value.length > normalizedQuote.length) {
    return `${value.slice(0, -normalizedQuote.length)}/${normalizedQuote}`
  }
  return value
}

export const findSymbolCatalogItem = (symbol: string) => {
  return lookupCatalogItem(symbol)
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
