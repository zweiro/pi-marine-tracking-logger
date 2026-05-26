import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/about'
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('@/views/AboutView.vue'),
    meta: { title: 'About' }
  },
  {
    path: '/monitoring',
    name: 'monitoring',
    component: () => import('@/views/MonitoringView.vue'),
    meta: { title: 'Monitoring' }
  },
  {
    path: '/open-data',
    name: 'open-data',
    component: () => import('@/views/OpenDataView.vue'),
    meta: { title: 'Open Data' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - OceanPulse` : 'OceanPulse - PI MONIT'
  next()
})

export default router
