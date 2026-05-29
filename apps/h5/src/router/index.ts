import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { trackPageView } from '@/utils/tracker'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/home' },
  { path: '/home', component: () => import('@/views/Home.vue'), meta: { showTabbar: true, title: '首页' } },
  { path: '/diagnose', component: () => import('@/views/Diagnose.vue'), meta: { showTabbar: true, title: '诊断' } },
  { path: '/diagnose/submit', component: () => import('@/views/DiagnoseSubmit.vue'), meta: { title: '提交视频' } },
  { path: '/diagnose/resubmit/:id', component: () => import('@/views/DiagnoseResubmit.vue'), meta: { title: '复诊' } },
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
    const wechatRefresh = to.query.wechat_refresh as string | undefined
    userStore.setTokens(wechatToken, wechatRefresh)
    await userStore.fetchMe()
    // 移除 token 参数，清理 URL
    const cleanQuery = { ...to.query }
    delete cleanQuery.wechat_token
    delete cleanQuery.wechat_refresh
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

// 路径 → 埋点页面名映射（统一全局 page_view，无需每个组件单独调用）
const PAGE_NAMES: Record<string, string> = {
  '/home': 'home',
  '/diagnose': 'diagnose',
  '/diagnose/submit': 'diagnose_submit',
  '/diagnose/resubmit': 'diagnose_resubmit',
  '/archive': 'archive',
  '/persona': 'persona',
  '/positioning': 'positioning',
  '/subscribe': 'subscribe',
  '/referrer': 'referrer',
  '/leaderboard': 'leaderboard',
  '/me': 'me',
  '/me/profile': 'profile',
  '/login': 'login',
  '/invite': 'invite',
}

router.afterEach((to) => {
  // 动态路由取前缀匹配（如 /diagnose/:id → diagnose_detail）
  const path = to.path
  let pageName =
    PAGE_NAMES[path] ??
    (path.startsWith('/diagnose/') ? 'diagnose_detail' :
     path.startsWith('/order/') ? 'order_detail' :
     path.startsWith('/report/') ? 'report' : undefined)
  if (pageName) trackPageView(pageName)
})

export default router
