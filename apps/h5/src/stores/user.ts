import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('vct_token'))
  const me = ref<any | null>(null)

  const tier = computed(() => me.value?.subscription_tier || 'free')
  const isPaid = computed(() => tier.value !== 'free')
  const isMax = computed(() => tier.value === 'max')

  function setToken(t: string | null) {
    token.value = t
    if (t) localStorage.setItem('vct_token', t)
    else localStorage.removeItem('vct_token')
  }

  async function fetchMe() {
    if (!token.value) return null
    me.value = await authApi.me()
    return me.value
  }

  function logout() {
    setToken(null)
    me.value = null
  }

  return { token, me, tier, isPaid, isMax, setToken, fetchMe, logout }
})
