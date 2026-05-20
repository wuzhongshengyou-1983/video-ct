import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    redirect: '/clients',
  },
  {
    path: '/clients',
    name: 'Clients',
    component: () => import('@/views/Clients.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/clients/:id',
    name: 'ClientDetail',
    component: () => import('@/views/ClientDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reviews',
    name: 'Reviews',
    component: () => import('@/views/Reviews.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/meetings',
    name: 'Meetings',
    component: () => import('@/views/Meetings.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tickets',
    name: 'Tickets',
    component: () => import('@/views/Tickets.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if (to.meta.guest && token) {
    return next('/clients')
  }

  next()
})

export default router
