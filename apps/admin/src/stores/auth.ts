import { defineStore } from 'pinia'
import { login as apiLogin, getMe } from '@/api/admin'

interface User {
  id: string
  phone: string
  name: string
  role: string
  avatar?: string
}

export const useAuthStore = defineStore('auth', () => {
  const me = ref<User | null>(null)
  const loggedIn = ref(false)

  // 从 localStorage 恢复用户状态
  function restore() {
    const saved = localStorage.getItem('user')
    if (saved) {
      try {
        me.value = JSON.parse(saved)
        loggedIn.value = true
      } catch {
        // ignore
      }
    }
  }

  async function login(payload: { phone: string; password: string }) {
    const res = await apiLogin(payload)
    const { access_token, user } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(user))
    me.value = user
    loggedIn.value = true
    return user
  }

  async function fetchMe() {
    try {
      const res = await getMe()
      me.value = res.data
      loggedIn.value = true
      localStorage.setItem('user', JSON.stringify(res.data))
    } catch {
      me.value = null
      loggedIn.value = false
    }
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    me.value = null
    loggedIn.value = false
  }

  return { me, loggedIn, restore, login, fetchMe, logout }
})
