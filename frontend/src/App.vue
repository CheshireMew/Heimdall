<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white flex transition-colors duration-300">
    <!-- Sidebar -->
    <aside class="w-56 overflow-y-auto bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 transition-colors duration-300">
      <div class="p-5">
        <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400">
          Heimdall
        </h1>
        <p class="text-xs text-gray-500 mt-1">{{ $t('app.subtitle') }}</p>
      </div>

      <nav class="mt-4 px-3 space-y-1">
        <router-link to="/" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <ChartBarSquareIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.realtime') }}
        </router-link>

        <div class="px-3 py-2 text-xs text-gray-500 font-bold uppercase mt-3">{{ $t('nav.indicators') }}</div>

        <router-link to="/indicators/macro" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <BuildingLibraryIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.macro') }}
        </router-link>
        <router-link to="/indicators/onchain" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <CubeTransparentIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.onchain') }}
        </router-link>
        <router-link to="/indicators/sentiment" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <HeartIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.sentiment') }}
        </router-link>
        <router-link to="/indicators/technical" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <CalculatorIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.tech') }}
        </router-link>
        <router-link to="/indicators/crypto-index" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <CircleStackIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.cryptoIndex') }}
        </router-link>
        <router-link to="/indicators/binance-market" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <ChartBarSquareIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.binanceMarket') }}
        </router-link>
        <router-link to="/indicators/web3-rank" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <CubeTransparentIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.web3Rank') }}
        </router-link>
        <router-link to="/indicators/tokenized-securities" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <BuildingLibraryIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.tokenizedSecurities') }}
        </router-link>

        <div class="px-3 py-2 text-xs text-gray-500 font-bold uppercase mt-3">{{ $t('nav.tools') }}</div>

        <router-link to="/backtest" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <BeakerIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.backtest') }}
        </router-link>
        <router-link to="/tools/compare" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <ScaleIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.compare') }}
        </router-link>
        <router-link to="/tools/factors" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <PresentationChartLineIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.factorResearch') }}
        </router-link>
        <router-link to="/tools/dca" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <BanknotesIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.dca') }}
        </router-link>
        <router-link to="/tools/portfolio-balance" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <ArrowsRightLeftIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.portfolioBalance') }}
        </router-link>
        <router-link to="/tools/halving" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <ClockIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.halving') }}
        </router-link>

        <div class="px-3 py-2 text-xs text-gray-500 font-bold uppercase mt-3">{{ $t('nav.system') }}</div>

        <router-link to="/settings" class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <CogIcon class="w-5 h-5 mr-2.5" /> {{ $t('nav.settings') }}
        </router-link>

        <div class="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4 px-3 space-y-2">
          <button
             @click="toggleTheme"
             class="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm text-gray-600 dark:text-gray-300"
          >
             <span class="flex items-center">
                 <MoonIcon v-if="theme === 'dark'" class="w-5 h-5 mr-2 text-yellow-500" />
                 <SunIcon v-else class="w-5 h-5 mr-2 text-orange-500" />
                 {{ theme === 'dark' ? $t('theme.dark') : $t('theme.light') }}
             </span>
          </button>
          <button
             @click="toggleLocale"
             class="w-full flex items-center justify-center px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm text-gray-600 dark:text-gray-300 font-bold"
          >
             <LanguageIcon class="w-5 h-5 mr-2" />
             {{ $t('lang.switch') }}
          </button>
        </div>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['Dashboard']">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ChartBarSquareIcon,
  BeakerIcon,
  ScaleIcon,
  BanknotesIcon,
  ArrowsRightLeftIcon,
  CogIcon,
  ClockIcon,
  MoonIcon,
  SunIcon,
  BuildingLibraryIcon,
  CubeTransparentIcon,
  HeartIcon,
  CalculatorIcon,
  LanguageIcon,
  CircleStackIcon,
  PresentationChartLineIcon
} from '@heroicons/vue/24/outline'
import { useTheme } from '@/composables/useTheme'
import { useMoney } from '@/composables/useMoney'
import { useSymbolCatalog } from '@/modules/market'
import { setAppLocale, toggleAppLocale } from '@/i18n/config'

const { locale } = useI18n()
const { theme, toggleTheme } = useTheme()
const { loadCurrencyRates } = useMoney()
const { loadSymbols } = useSymbolCatalog()

const toggleLocale = () => {
  setAppLocale(locale, toggleAppLocale(locale.value))
}

onMounted(() => {
    loadSymbols()
    loadCurrencyRates()
})
</script>
