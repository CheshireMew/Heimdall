import { apiErrorMessage } from '@/api/request'

export const toPortfolioUserError = (error: unknown, fallback: string) => {
  const message = apiErrorMessage(error, fallback).trim()
  if (!message) return fallback
  if (message.includes('Background on this error at:') || message.includes('sqlalche.me/e/')) {
    return '历史数据处理失败，请稍后重试。'
  }
  if (message.length > 240) {
    return `${message.slice(0, 240)}...`
  }
  return message
}

