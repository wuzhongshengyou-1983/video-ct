import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { Toast } from 'vant'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export const http = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('vct_token')
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err: AxiosError<{ code?: string; message?: string }>) => {
    const status = err.response?.status
    const data = err.response?.data
    const msg = data?.message || err.message || '请求失败'
    if (status === 401) {
      localStorage.removeItem('vct_token')
      if (location.pathname !== '/login') {
        location.href = `/login?redirect=${encodeURIComponent(location.pathname)}`
      }
    } else if (status === 429) {
      Toast.fail('额度已用完')
    } else if (status === 402) {
      Toast.fail(msg)
    } else if (status && status >= 400) {
      Toast.fail(msg)
    }
    return Promise.reject({ status, code: data?.code, message: msg })
  },
)
