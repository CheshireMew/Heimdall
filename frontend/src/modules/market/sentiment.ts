export type SentimentBucket =
  | 'extremeFear'
  | 'fear'
  | 'neutral'
  | 'greed'
  | 'extremeGreed'

export const resolveSentimentBucket = (value: number): SentimentBucket => {
  if (value <= 25) return 'extremeFear'
  if (value <= 45) return 'fear'
  if (value <= 55) return 'neutral'
  if (value <= 75) return 'greed'
  return 'extremeGreed'
}
