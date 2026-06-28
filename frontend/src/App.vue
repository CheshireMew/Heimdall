<template>
  <div class="app-shell flex min-h-screen transition-colors duration-300">
    <!-- Sidebar -->
    <aside class="app-sidebar w-60 flex-shrink-0 overflow-y-auto transition-colors duration-300">
      <div class="app-sidebar-header p-5">
        <h1 class="app-brand text-xl font-semibold tracking-tight">
          Heimdall
        </h1>
        <p class="app-sidebar-subtitle mt-1 text-xs">{{ $t('app.subtitle') }}</p>
      </div>

      <nav class="mt-4 space-y-1 px-3">
        <template v-for="section in navSections" :key="section.key">
          <div v-if="section.titleKey" class="app-nav-section mt-4 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em]">
            {{ $t(section.titleKey) }}
          </div>

          <router-link
            v-for="item in section.items"
            :key="item.path"
            :to="item.path"
            class="app-nav-link flex items-center px-3 py-2 text-sm transition"
            active-class="app-nav-link--active"
          >
            <component :is="iconMap[item.nav.icon]" class="mr-2.5 h-5 w-5" />
            {{ $t(item.nav.labelKey) }}
          </router-link>
        </template>

        <div class="app-sidebar-controls mt-6 space-y-2 px-3 pt-4">
          <button
             @click="toggleTheme"
             class="app-sidebar-button flex w-full items-center justify-between px-3 py-2 text-sm transition"
          >
             <span class="flex items-center">
                 <MoonIcon v-if="theme === 'dark'" class="mr-2 h-5 w-5 text-yellow-500" />
                 <SunIcon v-else class="mr-2 h-5 w-5 text-[#0f6b4f]" />
                 {{ theme === 'dark' ? $t('theme.dark') : $t('theme.light') }}
             </span>
          </button>
          <button
             @click="toggleLocale"
             class="app-sidebar-button flex w-full items-center justify-center px-3 py-2 text-sm font-semibold transition"
          >
             <LanguageIcon class="mr-2 h-5 w-5" />
             {{ $t('lang.switch') }}
          </button>
        </div>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="app-main flex-1 overflow-auto transition-colors duration-300">
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

<style>
.app-shell {
  --app-shell-bg: #f7f4ed;
  --app-shell-text: #1c1917;
  --app-sidebar-bg: #fbfaf7;
  --app-sidebar-border: #e4ded3;
  --app-brand: #10261f;
  --app-muted: #78716c;
  --app-section: #78716c;
  --app-nav: #57534e;
  --app-nav-hover-bg: #f1eee7;
  --app-nav-hover: #10261f;
  --app-nav-active-border: #0f6b4f;
  --app-nav-active-bg: #edf3ee;
  --app-nav-active: #0f4f3c;
  --app-button-bg: #ffffff;
  --app-button-border: #e4ded3;
  --app-button-hover-bg: #f4f1ea;
  --app-button-hover-border: #cfc7ba;
  --app-main-bg: #f7f4ed;
  background: var(--app-shell-bg);
  color: var(--app-shell-text);
}

html.dark .app-shell {
  --app-shell-bg: #111827;
  --app-shell-text: #f9fafb;
  --app-sidebar-bg: #111827;
  --app-sidebar-border: #334155;
  --app-brand: #f9fafb;
  --app-muted: #94a3b8;
  --app-section: #64748b;
  --app-nav: #cbd5e1;
  --app-nav-hover-bg: #1e293b;
  --app-nav-hover: #f8fafc;
  --app-nav-active-border: #34d399;
  --app-nav-active-bg: rgba(6, 78, 59, 0.35);
  --app-nav-active: #a7f3d0;
  --app-button-bg: #0f172a;
  --app-button-border: #334155;
  --app-button-hover-bg: #1e293b;
  --app-button-hover-border: #475569;
  --app-main-bg: #111827;
}

.app-sidebar {
  border-right: 1px solid var(--app-sidebar-border);
  background: var(--app-sidebar-bg);
}

.app-sidebar-header {
  border-bottom: 1px solid var(--app-sidebar-border);
}

.app-brand {
  color: var(--app-brand);
  font-family: Georgia, "Times New Roman", serif;
}

.app-sidebar-subtitle {
  color: var(--app-muted);
}

.app-nav-section {
  color: var(--app-section);
}

.app-nav-link {
  border-left: 2px solid transparent;
  color: var(--app-nav);
}

.app-nav-link:hover {
  background: var(--app-nav-hover-bg);
  color: var(--app-nav-hover);
}

.app-nav-link--active {
  border-left-color: var(--app-nav-active-border);
  background: var(--app-nav-active-bg);
  color: var(--app-nav-active);
  font-weight: 700;
}

.app-sidebar-controls {
  border-top: 1px solid var(--app-sidebar-border);
}

.app-sidebar-button {
  border: 1px solid var(--app-button-border);
  background: var(--app-button-bg);
  color: var(--app-nav);
}

.app-sidebar-button:hover {
  border-color: var(--app-button-hover-border);
  background: var(--app-button-hover-bg);
  color: var(--app-nav-hover);
}

.app-main {
  background: var(--app-main-bg);
}
</style>
