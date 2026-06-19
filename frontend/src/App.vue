<template>
  <div class="app-shell flex min-h-screen text-gray-900 transition-colors duration-300 dark:bg-gray-900 dark:text-white">
    <!-- Sidebar -->
    <aside class="app-sidebar w-60 flex-shrink-0 overflow-y-auto transition-colors duration-300 dark:border-gray-700 dark:bg-gray-800">
      <div class="border-b border-stone-200/80 p-5 dark:border-gray-700">
        <h1 class="app-brand text-xl font-semibold tracking-tight dark:text-white">
          Heimdall
        </h1>
        <p class="mt-1 text-xs text-stone-500 dark:text-gray-400">{{ $t('app.subtitle') }}</p>
      </div>

      <nav class="mt-4 space-y-1 px-3">
        <template v-for="section in navSections" :key="section.key">
          <div v-if="section.titleKey" class="mt-4 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-400 dark:text-gray-500">
            {{ $t(section.titleKey) }}
          </div>

          <router-link
            v-for="item in section.items"
            :key="item.path"
            :to="item.path"
            class="app-nav-link flex items-center px-3 py-2 text-sm transition dark:text-gray-300 dark:hover:bg-gray-700"
            active-class="app-nav-link--active"
          >
            <component :is="iconMap[item.nav.icon]" class="mr-2.5 h-5 w-5" />
            {{ $t(item.nav.labelKey) }}
          </router-link>
        </template>

        <div class="mt-6 space-y-2 border-t border-stone-200/80 px-3 pt-4 dark:border-gray-700">
          <button
             @click="toggleTheme"
             class="app-sidebar-button flex w-full items-center justify-between px-3 py-2 text-sm transition dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
          >
             <span class="flex items-center">
                 <MoonIcon v-if="theme === 'dark'" class="mr-2 h-5 w-5 text-yellow-500" />
                 <SunIcon v-else class="mr-2 h-5 w-5 text-[#0f6b4f]" />
                 {{ theme === 'dark' ? $t('theme.dark') : $t('theme.light') }}
             </span>
          </button>
          <button
             @click="toggleLocale"
             class="app-sidebar-button flex w-full items-center justify-center px-3 py-2 text-sm font-semibold transition dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
          >
             <LanguageIcon class="mr-2 h-5 w-5" />
             {{ $t('lang.switch') }}
          </button>
        </div>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="app-main flex-1 overflow-auto transition-colors duration-300 dark:bg-gray-900">
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
  ScaleIcon,
  BanknotesIcon,
  ArrowsRightLeftIcon,
  CogIcon,
  ClockIcon,
  MoonIcon,
  SunIcon,
  BuildingLibraryIcon,
  CubeTransparentIcon,
  LanguageIcon,
  CircleStackIcon,
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
  ScaleIcon,
  BanknotesIcon,
  ArrowsRightLeftIcon,
  CogIcon,
  ClockIcon,
  BuildingLibraryIcon,
  CubeTransparentIcon,
  CircleStackIcon,
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

<style scoped>
.app-shell {
  background: #f7f4ed;
}

.app-sidebar {
  border-right: 1px solid #e4ded3;
  background: #fbfaf7;
}

.app-brand {
  color: #10261f;
  font-family: Georgia, "Times New Roman", serif;
}

.app-nav-link {
  border-left: 2px solid transparent;
  color: #57534e;
}

.app-nav-link:hover {
  background: #f1eee7;
  color: #10261f;
}

.app-nav-link--active {
  border-left-color: #0f6b4f;
  background: #edf3ee;
  color: #0f4f3c;
  font-weight: 700;
}

.app-sidebar-button {
  border: 1px solid #e4ded3;
  background: #ffffff;
  color: #57534e;
}

.app-sidebar-button:hover {
  border-color: #cfc7ba;
  background: #f4f1ea;
  color: #10261f;
}

.app-main {
  background: #f7f4ed;
}

:global(.dark) .app-shell {
  background: #111827;
}

:global(.dark) .app-sidebar {
  border-right-color: #374151;
  background: #1f2937;
}

:global(.dark) .app-nav-link:hover {
  background: #374151;
  color: #f9fafb;
}

:global(.dark) .app-nav-link--active {
  border-left-color: #60a5fa;
  background: rgba(30, 64, 175, 0.3);
  color: #60a5fa;
}

:global(.dark) .app-sidebar-button {
  border-color: #374151;
  background: #374151;
}

:global(.dark) .app-sidebar-button:hover {
  background: #4b5563;
}

:global(.dark) .app-main {
  background: #111827;
}
</style>
