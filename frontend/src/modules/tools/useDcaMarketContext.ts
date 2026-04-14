import { reactive } from 'vue'

import { isIndexSymbol, marketApi } from '@/modules/market'
import { resolveSentimentBucket } from '@/modules/market/sentiment'

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
  if (!value || typeof value !== 'object') return createEmptyMarketData()
  const payload = value as Record<string, unknown>
  return {
    rsi: typeof payload.rsi === 'string' ? payload.rsi : null,
    sentiment: typeof payload.sentiment === 'number' ? payload.sentiment : null,
    sentimentLabel: typeof payload.sentimentLabel === 'string' ? payload.sentimentLabel : '',
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
      const currentSymbol = symbol()
      const [marketRes, indicatorsRes] = await Promise.all([
        isIndexSymbol(currentSymbol)
          ? marketApi.getIndexPricingHistory({
              symbol: currentSymbol,
              timeframe: '1d',
              start_date: new Date(Date.now() - 180 * 86400000).toISOString().slice(0, 10),
            })
          : marketApi.getRealtime({ symbol: currentSymbol, timeframe: '1d', limit: 100 }),
        marketApi.getIndicators({ days: 7 }),
      ])

      marketData.rsi = isIndexSymbol(currentSymbol)
        ? '--'
        : marketRes.data?.indicators?.rsi?.toFixed(2) || '--'
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
