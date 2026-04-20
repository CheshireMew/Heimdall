import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { APP_ROUTE_DEFINITIONS } from '@/app/navigation'

const routes: RouteRecordRaw[] = APP_ROUTE_DEFINITIONS.map((route) => {
  const routeRecord: RouteRecordRaw = {
    path: route.path,
    name: route.name,
    component: route.component,
  }
  if ('meta' in route) {
    routeRecord.meta = route.meta
  }
  return routeRecord
})

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
