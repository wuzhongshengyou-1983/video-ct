import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

const TOKEN_KEY = 'vct_token'
const REFRESH_KEY = 'vct_refresh'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const me = ref<any | null>(null)

  const tier = computed(() => me.value?.subscription_tier || 'free')
  const isPaid = computed(() => tier.value !== 'free')
  const isMax = computed(() => tier.value === 'max')

  function setToken(t: string | null) {
    token.value = t
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  }

  /** 登录成功后写入 access + refresh 对 */
  function setTokens(access: string, refresh?: string) {
    setToken(access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  }

  async function fetchMe() {
    if (!token.value) return null
    me.value = await authApi.me()
    return me.value
  }

  async function logout() {
    const refresh = localStorage.getItem(REFRESH_KEY) || undefined
    try {
      await authApi.logout(refresh)
    } catch {
      // 登出接口失败不阻断本地清理
    }
    setToken(null)
    localStorage.removeItem(REFRESH_KEY)
    me.value = null
  }

  return { token, me, tier, isPaid, isMax, setToken, setTokens, fetchMe, logout }
})
