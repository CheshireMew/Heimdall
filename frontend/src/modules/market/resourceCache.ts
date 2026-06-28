import { isCacheFresh, writeCacheEntry, type CacheEntry } from './cacheTypes'

type ResourceCacheOptions<TData> = {
  cache: Record<string, CacheEntry<TData>>
  key: string
  pendingKey?: string
  ttlMs: number
  force?: boolean
  load: () => Promise<TData | null>
  onLoadStart?: () => void
  onLoadEnd?: () => void
  onLoadError?: (error: unknown) => void
  onWrite?: (data: TData) => void
}

export const createResourceCache = () => {
  const pending = new Map<string, Promise<unknown>>()

  const read = <TData>(
    cache: Record<string, CacheEntry<TData>>,
    key: string,
    ttlMs: number,
    force = false,
  ): TData | null => {
    const entry = cache[key]
    if (!force && isCacheFresh(entry, ttlMs)) return entry.data
    return null
  }

  const load = async <TData>(options: ResourceCacheOptions<TData>): Promise<TData | null> => {
    const cached = read(options.cache, options.key, options.ttlMs, Boolean(options.force))
    if (cached !== null) return cached

    const pendingKey = options.pendingKey ?? options.key
    const active = pending.get(pendingKey) as Promise<TData | null> | undefined
    if (active) return active

    options.onLoadStart?.()
    const request = (async () => {
      try {
        const data = await options.load()
        if (data !== null) {
          writeCacheEntry(options.cache, options.key, data)
          options.onWrite?.(data)
          return data
        }
      } catch (error) {
        options.onLoadError?.(error)
      } finally {
        pending.delete(pendingKey)
        options.onLoadEnd?.()
      }
      return options.cache[options.key]?.data ?? null
    })()

    pending.set(pendingKey, request)
    return request
  }

  return { read, load }
}
