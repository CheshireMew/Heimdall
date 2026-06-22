export const APP_ROUTE_DEFINITIONS = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    keepAlive: true,
    nav: {
      section: 'primary',
      labelKey: 'nav.realtime',
      icon: 'ChartBarSquareIcon',
    },
  },
  {
    path: '/indicators/macro',
    name: 'IndicatorsMacro',
    component: () => import('@/views/indicators/MacroLiquidity.vue'),
    meta: { title: '宏观经济', category: 'Macro' },
    nav: { section: 'indicators', labelKey: 'nav.macro', icon: 'BuildingLibraryIcon' },
  },
  {
    path: '/indicators/macro/history',
    name: 'IndicatorsMacroHistory',
    component: () => import('@/views/indicators/MacroLiquidityHistory.vue'),
    meta: { title: 'DLI 历史走势', category: 'Macro' },
  },
  {
    path: '/indicators/macro/methodology',
    name: 'IndicatorsMacroMethodology',
    component: () => import('@/views/indicators/MacroLiquidityMethodology.vue'),
    meta: { title: 'DLI 计算原理', category: 'Macro' },
  },
  {
    path: '/indicators/market-signals',
    name: 'IndicatorsMarketSignals',
    component: () => import('@/views/indicators/MarketSignals.vue'),
    meta: { title: '市场信号' },
    nav: { section: 'indicators', labelKey: 'nav.marketSignals', icon: 'CubeTransparentIcon' },
  },
  {
    path: '/indicators/binance-market',
    name: 'BinanceMarket',
    component: () => import('@/views/indicators/BinanceMarket.vue'),
    meta: { title: '币安市场' },
    nav: { section: 'indicators', labelKey: 'nav.binanceMarket', icon: 'ChartBarSquareIcon' },
  },
  {
    path: '/indicators/web3-rank',
    name: 'Web3MarketRank',
    component: () => import('@/views/indicators/Web3MarketRank.vue'),
    meta: { title: 'Web3 榜单' },
    nav: { section: 'indicators', labelKey: 'nav.web3Rank', icon: 'CubeTransparentIcon' },
  },
  {
    path: '/tools/compare',
    name: 'Compare',
    component: () => import('@/views/tools/Compare.vue'),
    meta: { title: '币种对比' },
    nav: { section: 'tools', labelKey: 'nav.compare', icon: 'ScaleIcon' },
  },
  {
    path: '/tools/dca',
    name: 'DCA',
    component: () => import('@/views/tools/DCA.vue'),
    meta: { title: 'DCA模拟' },
    nav: { section: 'tools', labelKey: 'nav.dca', icon: 'BanknotesIcon' },
  },
  {
    path: '/tools/portfolio-balance',
    name: 'PortfolioBalance',
    component: () => import('@/views/tools/PortfolioBalance.vue'),
    meta: { title: '组合平衡' },
    nav: {
      section: 'tools',
      labelKey: 'nav.portfolioBalance',
      icon: 'ArrowsRightLeftIcon',
    },
  },
  {
    path: '/tools/halving',
    name: 'Halving',
    component: () => import('@/views/tools/Halving.vue'),
    meta: { title: '减半周期' },
    nav: { section: 'tools', labelKey: 'nav.halving', icon: 'ClockIcon' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/settings/Settings.vue'),
    nav: { section: 'system', labelKey: 'nav.settings', icon: 'CogIcon' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
] as const

export const APP_NAV_SECTIONS = [
  { key: 'primary', titleKey: null },
  { key: 'indicators', titleKey: 'nav.indicators' },
  { key: 'tools', titleKey: 'nav.tools' },
  { key: 'system', titleKey: 'nav.system' },
] as const

const hasNav = (
  route: (typeof APP_ROUTE_DEFINITIONS)[number],
): route is Extract<(typeof APP_ROUTE_DEFINITIONS)[number], { nav: object }> => (
  'nav' in route
)

const hasKeepAlive = (
  route: (typeof APP_ROUTE_DEFINITIONS)[number],
): route is Extract<(typeof APP_ROUTE_DEFINITIONS)[number], { keepAlive: true }> => (
  'keepAlive' in route && route.keepAlive === true
)

export const APP_NAV_ITEMS = APP_ROUTE_DEFINITIONS.filter(hasNav)
export const APP_KEEP_ALIVE_ROUTE_NAMES = APP_ROUTE_DEFINITIONS
  .filter(hasKeepAlive)
  .map((route) => route.name)

export type AppNavItem = (typeof APP_NAV_ITEMS)[number]
export type AppNavSectionKey = (typeof APP_NAV_SECTIONS)[number]['key']
export type AppNavIconName = AppNavItem['nav']['icon']
