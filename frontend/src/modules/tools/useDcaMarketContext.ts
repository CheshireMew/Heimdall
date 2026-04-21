import { reactive } from 'vue'

import { isRecord } from '@/composables/pageSnapshot'
import { ensureSymbolCatalogLoaded, isIndexSymbol, marketApi } from '@/modules/market'
import { resolveSentimentBucket } from '@/modules/market/sentiment'
import { localIsoDateDaysAgo } from '@/utils/localDate'

export interface DcaMarketState {
  rsi: string | null
  sentiment: number | null
  sentimentLabel: string
}

export const createEmptyMarketData = (): DcaMarketState => ({
  rsi: null,
  sentiment: null,
  sentimentLabel: '',
})

export const normalizeMarketData = (value: unknown): DcaMarketState => {
  if (!isRecord(value)) return createEmptyMarketData()
  return {
    rsi: typeof value.rsi === 'string' ? value.rsi : null,
    sentiment: typeof value.sentiment === 'number' ? value.sentiment : null,
    sentimentLabel: typeof value.sentimentLabel === 'string' ? value.sentimentLabel : '',
  }
}

interface UseDcaMarketContextOptions {
  symbol: () => string
  t: (key: string) => string
  initialValue?: DcaMarketState
}

export const useDcaMarketContext = ({
  symbol,
  t,
  initialValue,
}: UseDcaMarketContextOptions) => {
  const marketData = reactive(normalizeMarketData(initialValue))

  const sentimentLabel = (value: number) => {
    const key = resolveSentimentBucket(value)
    return t(`dca.fgLabels.${key}`)
  }

  const fetchMarketIndicators = async () => {
    try {
      await ensureSymbolCatalogLoaded()
      const currentSymbol = symbol()
      const [marketRes, indicatorsRes] = await Promise.all([
        isIndexSymbol(currentSymbol)
          ? marketApi.getIndexPricingHistory({
              symbol: currentSymbol,
              timeframe: '1d',
              start_date: localIsoDateDaysAgo(180),
            })
          : marketApi.getRealtime({ symbol: currentSymbol, timeframe: '1d', limit: 100 }),
        marketApi.getIndicators({ days: 7 }),
      ])

      marketData.rsi = isIndexSymbol(currentSymbol)
        ? '--'
        : ('indicators' in marketRes.data ? marketRes.data.indicators?.rsi?.toFixed(2) : '--') || '--'
      const fearGreed = (indicatorsRes.data || []).find((item) => item.indicator_id === 'FEAR_GREED')
      if (!fearGreed || fearGreed.current_value === null) {
        return
      }

      marketData.sentiment = fearGreed.current_value
      marketData.sentimentLabel = sentimentLabel(fearGreed.current_value)
    } catch (error) {
      console.warn('Failed to fetch market indicators:', error)
    }
  }

  return {
    marketData,
    fetchMarketIndicators,
  }
}
