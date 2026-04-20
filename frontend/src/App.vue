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
        <template v-for="section in navSections" :key="section.key">
          <div v-if="section.titleKey" class="px-3 py-2 text-xs text-gray-500 font-bold uppercase mt-3">
            {{ $t(section.titleKey) }}
          </div>

          <router-link
            v-for="item in section.items"
            :key="item.path"
            :to="item.path"
            class="block px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center text-sm"
            active-class="bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
          >
            <component :is="iconMap[item.nav.icon]" class="w-5 h-5 mr-2.5" />
            {{ $t(item.nav.labelKey) }}
          </router-link>
        </template>

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
        <keep-alive :include="keepAliveRoutes">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, type Component } from 'vue'
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
import {
  APP_KEEP_ALIVE_ROUTE_NAMES,
  APP_NAV_ITEMS,
  APP_NAV_SECTIONS,
  type AppNavIconName,
} from '@/app/navigation'
import { useTheme } from '@/composables/useTheme'
import { useMoney } from '@/composables/useMoney'
import { useSymbolCatalog } from '@/modules/market'
import { setAppLocale, toggleAppLocale } from '@/i18n/config'

const { locale } = useI18n()
const { theme, toggleTheme } = useTheme()
const { loadCurrencyRates } = useMoney()
const { loadSymbols } = useSymbolCatalog()
const keepAliveRoutes = APP_KEEP_ALIVE_ROUTE_NAMES
const iconMap: Record<AppNavIconName, Component> = {
  ChartBarSquareIcon,
  BeakerIcon,
  ScaleIcon,
  BanknotesIcon,
  ArrowsRightLeftIcon,
  CogIcon,
  ClockIcon,
  BuildingLibraryIcon,
  CubeTransparentIcon,
  HeartIcon,
  CalculatorIcon,
  CircleStackIcon,
  PresentationChartLineIcon,
}
const navSections = APP_NAV_SECTIONS.map((section) => ({
  ...section,
  items: APP_NAV_ITEMS.filter((item) => item.nav.section === section.key),
})).filter((section) => section.items.length > 0)

const toggleLocale = () => {
  setAppLocale(locale, toggleAppLocale(locale.value))
}

onMounted(() => {
    loadSymbols()
    loadCurrencyRates()
})
</script>
