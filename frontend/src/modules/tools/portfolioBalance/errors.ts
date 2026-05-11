export type RequestError = {
  message?: string
  response?: {
    data?: {
      detail?: string
    }
  }
}

export const toPortfolioUserError = (error: unknown, fallback: string) => {
  const requestError = error as RequestError
  const message = String(requestError.response?.data?.detail || requestError.message || '').trim()
  if (!message) return fallback
  if (message.includes('Background on this error at:') || message.includes('sqlalche.me/e/')) {
    return '历史数据处理失败，请稍后重试。'
  }
  if (message.length > 240) {
    return `${message.slice(0, 240)}...`
  }
  return message
}

