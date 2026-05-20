import { http } from './client'

// 鉴权
export const authApi = {
  sendOtp: (phone: string) => http.post<unknown, { sent: boolean; dev_code: string }>('/api/v1/auth/otp/send', { phone }),
  verifyOtp: (phone: string, code: string, referrer_code?: string) =>
    http.post<unknown, any>('/api/v1/auth/otp/verify', { phone, code, referrer_code }),
  wechatLogin: (code: string, referrer_code?: string) =>
    http.post<unknown, any>('/api/v1/auth/wechat/login', { code, referrer_code }),
  me: () => http.get<unknown, any>('/api/v1/auth/me'),
}

// 用户
export const userApi = {
  updateProfile: (data: any) => http.put('/api/v1/users/me/profile', data),
  uploadAvatar: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post<unknown, { url: string }>('/api/v1/upload/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// 订阅
export const subscriptionApi = {
  products: () => http.get<unknown, any[]>('/api/v1/subscriptions/products'),
  createOrder: (sku: string, opts: { use_deduction?: boolean; coupon_code?: string; referrer_code?: string } = {}) =>
    http.post<unknown, any>('/api/v1/subscriptions/orders', { sku, ...opts }),
  getPayParams: (orderNo: string) => http.get<unknown, any>(`/api/v1/subscriptions/orders/${orderNo}/pay-params`),
  checkPayStatus: (orderNo: string) => http.get<unknown, any>(`/api/v1/subscriptions/orders/${orderNo}/status`),
  mySubscription: () => http.get<unknown, any>('/api/v1/subscriptions/my'),
  myOrders: () => http.get<unknown, any[]>('/api/v1/subscriptions/orders'),
}

// 诊断
export const diagnosisApi = {
  submit: (payload: { video_url: string; track?: string; diagnosis_type?: string }) =>
    http.post<unknown, any>('/api/v1/diagnoses/submit', payload),
  get: (id: number | string) => http.get<unknown, any>(`/api/v1/diagnoses/${id}`),
  list: () => http.get<unknown, any[]>('/api/v1/diagnoses/'),
  report: (id: number | string) => http.get<unknown, any>(`/api/v1/diagnoses/${id}/report`),
  feedback: (id: number | string, rating: number, feedback?: string) =>
    http.post(`/api/v1/diagnoses/${id}/report/feedback`, { rating, feedback }),
}

// 对标
export const benchmarkApi = {
  tracks: () => http.get<unknown, any[]>('/api/v1/benchmarks/tracks'),
  top10: (track: string) => http.get<unknown, any[]>(`/api/v1/benchmarks/top10/${encodeURIComponent(track)}`),
  gap: (track: string, user_metrics: any) =>
    http.post<unknown, any>(`/api/v1/benchmarks/gap?track=${encodeURIComponent(track)}`, user_metrics),
}

// 档案
export const archiveApi = {
  me: () => http.get<unknown, any>('/api/v1/archives/me'),
  curve: () => http.get<unknown, any>('/api/v1/archives/me/curve'),
}

// 人设
export const personaApi = {
  scan: (data: { sample_video_urls?: string[]; description?: string }) =>
    http.post<unknown, any>('/api/v1/personas/scan', data),
  me: () => http.get<unknown, any>('/api/v1/personas/me'),
  archetypes: () => http.get<unknown, any>('/api/v1/personas/archetypes'),
}

// 商业定位
export const positioningApi = {
  scan: (data: { description?: string } = {}) =>
    http.post<unknown, any>('/api/v1/positionings/scan', data),
  me: () => http.get<unknown, any>('/api/v1/positionings/me'),
}

// 分享官
export const referrerApi = {
  me: () => http.get<unknown, any>('/api/v1/referrers/me'),
  link: () => http.get<unknown, any>('/api/v1/referrers/link'),
  records: () => http.get<unknown, any[]>('/api/v1/referrers/records'),
  withdraw: (amount_cny: number) => http.post('/api/v1/referrers/withdraw', { amount_cny }),
  leaderboard: () => http.get<unknown, any[]>('/api/v1/referrers/leaderboard'),
}

// AI
export const aiApi = {
  generate: (topic: string, track?: string) =>
    http.post<unknown, any>('/api/v1/ai/content/generate', { topic, track }),
  agents: () => http.get<unknown, any>('/api/v1/ai/agents'),
}

// 埋点
export const analyticsApi = {
  sendEvents: (events: any[]) =>
    http.post<unknown, void>('/api/v1/analytics/events', { events }, { _noToast: true }),
}

// 微信
export const wechatApi = {
  jsSdkSign: (url: string) =>
    http.get<unknown, {
      app_id: string
      timestamp: number
      nonce_str: string
      signature: string
      js_api_list: string[]
    }>(`/api/v1/wechat/js-sdk-sign?url=${encodeURIComponent(url)}`),
  oauthUrl: (redirect: string = '/home', ref?: string) =>
    http.get<unknown, { url: string }>(
      `/api/v1/wechat/oauth-url?redirect=${encodeURIComponent(redirect)}${ref ? `&ref=${ref}` : ''}`,
    ),
}
