import { createI18n } from 'vue-i18n'
import zh from './zh-CN.json'
import en from './en.json'
import { FALLBACK_LOCALE, resolveInitialLocale } from './config'

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: resolveInitialLocale(),
  fallbackLocale: FALLBACK_LOCALE,
  messages: {
    'zh-CN': zh,
    en
  }
})

export default i18n
