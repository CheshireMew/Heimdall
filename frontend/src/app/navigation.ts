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
    component: () => import('@/views/indicators/CategoryView.vue'),
    meta: { title: '宏观经济', category: 'Macro' },
    nav: { section: 'indicators', labelKey: 'nav.macro', icon: 'BuildingLibraryIcon' },
  },
  {
    path: '/indicators/onchain',
    name: 'IndicatorsOnchain',
    component: () => import('@/views/indicators/CategoryView.vue'),
    meta: { title: '链上数据', category: 'Onchain' },
    nav: { section: 'indicators', labelKey: 'nav.onchain', icon: 'CubeTransparentIcon' },
  },
  {
    path: '/indicators/sentiment',
    name: 'IndicatorsSentiment',
    component: () => import('@/views/indicators/CategoryView.vue'),
    meta: { title: '市场情绪', category: 'Sentiment' },
    nav: { section: 'indicators', labelKey: 'nav.sentiment', icon: 'HeartIcon' },
  },
  {
    path: '/indicators/technical',
    name: 'IndicatorsTech',
    component: () => import('@/views/indicators/CategoryView.vue'),
    meta: { title: '技术指标', category: 'Tech' },
    nav: { section: 'indicators', labelKey: 'nav.tech', icon: 'CalculatorIcon' },
  },
  {
    path: '/indicators/crypto-index',
    name: 'CryptoIndex',
    component: () => import('@/views/indicators/CryptoIndex.vue'),
    meta: { title: '加密指数' },
    nav: { section: 'indicators', labelKey: 'nav.cryptoIndex', icon: 'CircleStackIcon' },
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
    path: '/indicators/tokenized-securities',
    name: 'TokenizedSecurities',
    component: () => import('@/views/indicators/TokenizedSecurities.vue'),
    meta: { title: '代币化美股' },
    nav: {
      section: 'indicators',
      labelKey: 'nav.tokenizedSecurities',
      icon: 'BuildingLibraryIcon',
    },
  },
  {
    path: '/tools/compare',
    name: 'Compare',
    component: () => import('@/views/tools/Compare.vue'),
    meta: { title: '币种对比' },
    nav: { section: 'tools', labelKey: 'nav.compare', icon: 'ScaleIcon' },
  },
  {
    path: '/tools/factors',
    name: 'FactorResearch',
    component: () => import('@/views/tools/FactorResearch.vue'),
    meta: { title: '因子研究' },
    nav: {
      section: 'tools',
      labelKey: 'nav.factorResearch',
      icon: 'PresentationChartLineIcon',
    },
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
    path: '/backtest',
    name: 'Backtest',
    component: () => import('@/views/Backtest.vue'),
    nav: { section: 'tools', labelKey: 'nav.backtest', icon: 'BeakerIcon' },
  },
  {
    path: '/backtest/editor',
    name: 'BacktestEditor',
    component: () => import('@/views/BacktestEditor.vue'),
  },
  {
    path: '/backtest/:mode(runs|paper)/:id(\\d+)',
    name: 'BacktestDetail',
    component: () => import('@/views/BacktestDetail.vue'),
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
