import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
    },
    {
        path: '/indicators/macro',
        name: 'IndicatorsMacro',
        component: () => import('@/views/indicators/CategoryView.vue'),
        meta: { title: '宏观经济', category: 'Macro' }
    },
    {
        path: '/indicators/onchain',
        name: 'IndicatorsOnchain',
        component: () => import('@/views/indicators/CategoryView.vue'),
        meta: { title: '链上数据', category: 'Onchain' }
    },
    {
        path: '/indicators/sentiment',
        name: 'IndicatorsSentiment',
        component: () => import('@/views/indicators/CategoryView.vue'),
        meta: { title: '市场情绪', category: 'Sentiment' }
    },
    {
        path: '/indicators/technical',
        name: 'IndicatorsTech',
        component: () => import('@/views/indicators/CategoryView.vue'),
        meta: { title: '技术指标', category: 'Tech' }
    },
    {
        path: '/indicators/crypto-index',
        name: 'CryptoIndex',
        component: () => import('@/views/indicators/CryptoIndex.vue'),
        meta: { title: '加密指数' }
    },
    {
        path: '/indicators/binance-market',
        name: 'BinanceMarket',
        component: () => import('@/views/indicators/BinanceMarket.vue'),
        meta: { title: '币安市场' }
    },
    {
        path: '/indicators/web3-rank',
        name: 'Web3MarketRank',
        component: () => import('@/views/indicators/Web3MarketRank.vue'),
        meta: { title: 'Web3 榜单' }
    },
    {
        path: '/indicators/tokenized-securities',
        name: 'TokenizedSecurities',
        component: () => import('@/views/indicators/TokenizedSecurities.vue'),
        meta: { title: '代币化美股' }
    },
    {
        path: '/tools/compare',
        name: 'Compare',
        component: () => import('@/views/tools/Compare.vue'),
        meta: { title: '币种对比' }
    },
    {
        path: '/tools/factors',
        name: 'FactorResearch',
        component: () => import('@/views/tools/FactorResearch.vue'),
        meta: { title: '因子研究' }
    },
    {
        path: '/tools/dca',
        name: 'DCA',
        component: () => import('@/views/tools/DCA.vue'),
        meta: { title: 'DCA模拟' }
    },
    {
        path: '/tools/portfolio-balance',
        name: 'PortfolioBalance',
        component: () => import('@/views/tools/PortfolioBalance.vue'),
        meta: { title: '组合平衡' }
    },
    {
        path: '/tools/halving',
        name: 'Halving',
        component: () => import('@/views/tools/Halving.vue'),
        meta: { title: '减半周期' }
    },
    {
        path: '/backtest',
        name: 'Backtest',
        component: () => import('@/views/Backtest.vue'),
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
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFound.vue'),
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
