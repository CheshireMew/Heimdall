import { createI18n } from 'vue-i18n'
import zh from './zh-CN.json'
import en from './en.json'

const savedLocale = localStorage.getItem('locale') || 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages: {
    'zh-CN': zh,
    en
  }
})

export default i18n
