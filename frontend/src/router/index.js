import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
    },
    {
        path: '/tools/compare',
        name: 'Compare',
        component: () => import('@/views/tools/Compare.vue'),
        meta: { title: '币种对比' }
    },
    {
        path: '/tools/dca',
        name: 'DCA',
        component: () => import('@/views/tools/DCA.vue'),
        meta: { title: 'DCA模拟' }
    },
    {
        path: '/backtest',
        name: 'Backtest',
        component: () => import('@/views/Backtest.vue'),
    },
    {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
