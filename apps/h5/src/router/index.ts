import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: () => import('@/views/Home.vue'), meta: { showTabbar: true, title: '首页' } },
  { path: '/diagnose', component: () => import('@/views/Diagnose.vue'), meta: { showTabbar: true, title: '诊断' } },
  { path: '/diagnose/submit', component: () => import('@/views/DiagnoseSubmit.vue'), meta: { title: '提交视频' } },
  { path: '/diagnose/:id', component: () => import('@/views/DiagnoseDetail.vue'), meta: { title: '诊断中' } },
  { path: '/report/:id', component: () => import('@/views/Report.vue'), meta: { title: 'CT 报告' } },
  { path: '/archive', component: () => import('@/views/Archive.vue'), meta: { title: '成长档案' } },
  { path: '/persona', component: () => import('@/views/Persona.vue'), meta: { title: '人设 IPP' } },
  { path: '/positioning', component: () => import('@/views/Positioning.vue'), meta: { title: '商业定位 BPS' } },
  { path: '/subscribe', component: () => import('@/views/Subscribe.vue'), meta: { showTabbar: true, title: '订阅' } },
  { path: '/order/:no', component: () => import('@/views/OrderDetail.vue'), meta: { title: '订单' } },
  { path: '/referrer', component: () => import('@/views/Referrer.vue'), meta: { title: '品牌分享官' } },
  { path: '/leaderboard', component: () => import('@/views/Leaderboard.vue'), meta: { title: '分享榜单' } },
  { path: '/me', component: () => import('@/views/Me.vue'), meta: { showTabbar: true, title: '我的' } },
  { path: '/me/profile', component: () => import('@/views/Profile.vue'), meta: { title: '个人资料' } },
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  { path: '/invite', component: () => import('@/views/Invite.vue'), meta: { title: '邀请落地页' } },
  { path: '/:pathMatch(.*)*', component: () => import('@/views/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const NO_AUTH = new Set(['/login', '/invite', '/home'])
router.beforeEach(async (to) => {
  if (typeof to.meta.title === 'string') {
    document.title = `${to.meta.title} · 视频 CT`
  }
  const userStore = useUserStore()

  // 微信 OAuth 回调：URL 中有 wechat_token → 自动登录
  const wechatToken = to.query.wechat_token as string | undefined
  if (wechatToken) {
    userStore.setToken(wechatToken)
    await userStore.fetchMe()
    // 移除 wechat_token 参数，清理 URL
    const cleanQuery = { ...to.query }
    delete cleanQuery.wechat_token
    return { path: to.path, query: cleanQuery, replace: true }
  }

  if (NO_AUTH.has(to.path)) return true
  if (!userStore.token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (!userStore.me) {
    try { await userStore.fetchMe() } catch { /* ignore */ }
  }
  return true
})

export default router
