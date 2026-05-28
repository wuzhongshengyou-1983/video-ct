import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { Toast } from 'vant'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

const TOKEN_KEY = 'vct_token'
const REFRESH_KEY = 'vct_refresh'

export const http = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

// 单飞 refresh：并发 401 共享同一个 refresh 请求，避免单次轮换被互相作废
let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return null
  try {
    // 裸 axios 调用，绕过本拦截器避免递归
    const { data } = await axios.post(`${baseURL}/api/v1/auth/refresh`, { refresh_token: refresh })
    localStorage.setItem(TOKEN_KEY, data.access_token)
    if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token)
    return data.access_token as string
  } catch {
    return null
  }
}

function clearAuthAndRedirect() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  if (location.pathname !== '/login') {
    location.href = `/login?redirect=${encodeURIComponent(location.pathname)}`
  }
}

http.interceptors.response.use(
  (res) => res.data,
  async (err: AxiosError<{ code?: string; message?: string }>) => {
    const status = err.response?.status
    const data = err.response?.data
    const msg = data?.message || err.message || '请求失败'
    const original = err.config as InternalAxiosRequestConfig | undefined

    // 401：先尝试用 refresh token 换新再重放原请求（每个请求最多一次）
    if (
      status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes('/api/v1/auth/refresh')
    ) {
      original._retry = true
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const newToken = await refreshPromise
      if (newToken) {
        original.headers.set('Authorization', `Bearer ${newToken}`)
        return http(original)
      }
      clearAuthAndRedirect()
      return Promise.reject({ status, code: data?.code, message: '登录已过期，请重新登录' })
    }

    if (status === 429) {
      Toast.fail('本月配额已用完，升级 PRO 解锁')
    } else if (status === 402) {
      Toast.fail(msg)
    } else if (status && status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else if (status && status >= 400 && !original?._noToast) {
      Toast.fail(msg)
    }
    return Promise.reject({ status, code: data?.code, message: msg })
  },
)
