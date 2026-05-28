# JavaScript / TypeScript SDK

视频 CT 提供轻量级的 JS/TS SDK，基于 axios 封装了鉴权、错误处理、类型定义。

## 安装

```bash
npm install @video-ct/sdk
# 或
pnpm add @video-ct/sdk
```

::: tip 内网使用
如果你的项目在 video-ct monorepo 内，可以直接引用共享包的类型：

```ts
import type { Diagnosis, Report, UserMe } from '@video-ct/shared'
```
:::

## 快速上手

### 基础封装（axios）

以下的 SDK 示例展示了一个完整的客户端封装。你可以直接复制到项目中，或根据需求调整。

```typescript
// sdk.ts
import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

// 从 @video-ct/shared 导入类型
import type {
  ApiResponse,
  TokenResponse,
  UserMe,
  Diagnosis,
  DiagnosisSubmit,
  Report,
  ProductOut,
  Order,
  OrderCreate,
  Persona,
  PersonaScanRequest,
  Positioning,
  PositioningScanRequest,
  ReferrerInfo,
  ReferrerLink,
  ReferralRecord,
  LeaderboardItem,
  BenchmarkItem,
} from '@video-ct/shared'

// ─── 配置 ──────────────────────────────────────────

export interface VideoCTConfig {
  baseURL: string      // 如 "https://api.video-ct.cn"
  apiPrefix?: string   // 默认 "/api/v1"
  timeout?: number     // 默认 30_000
}

// ─── 客户端类 ──────────────────────────────────────

export class VideoCTClient {
  private http: AxiosInstance
  private token: string | null = null

  constructor(config: VideoCTConfig) {
    const baseURL = `${config.baseURL}${config.apiPrefix ?? '/api/v1'}`
    this.http = axios.create({
      baseURL,
      timeout: config.timeout ?? 30_000,
      headers: { 'Content-Type': 'application/json' },
    })

    // 请求拦截：自动注入 token
    this.http.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
      if (this.token) {
        cfg.headers.set('Authorization', `Bearer ${this.token}`)
      }
      return cfg
    })

    // 响应拦截：统一解包 ApiResponse
    this.http.interceptors.response.use(
      (res) => res.data,
      (err: AxiosError<ApiResponse>) => {
        const data = err.response?.data
        const msg = data?.message ?? err.message
        const code = data?.code ?? 'UNKNOWN'
        throw new VideoCTError(code, msg, err.response?.status)
      },
    )
  }

  /** 设置 token（登录后调用） */
  setToken(token: string): void {
    this.token = token
  }

  /** 清除 token（登出时调用） */
  clearToken(): void {
    this.token = null
  }

  // ─── 鉴权 ────────────────────────────────────────

  /** 发送手机验证码 */
  async sendOTP(phone: string): Promise<ApiResponse<{ sent: boolean; dev_code: string }>> {
    return this.http.post('/auth/otp/send', { phone })
  }

  /** 验证码登录 */
  async verifyOTP(phone: string, code: string, referrerCode?: string): Promise<ApiResponse<TokenResponse>> {
    return this.http.post('/auth/otp/verify', { phone, code, referrer_code: referrerCode })
  }

  /** 微信登录 */
  async wechatLogin(code: string, referrerCode?: string): Promise<ApiResponse<TokenResponse>> {
    return this.http.post('/auth/wechat/login', { code, referrer_code: referrerCode })
  }

  /** 获取当前用户信息 */
  async getMe(): Promise<ApiResponse<UserMe>> {
    return this.http.get('/auth/me')
  }

  // ─── 诊断 ────────────────────────────────────────

  /** 提交诊断 */
  async submitDiagnosis(payload: DiagnosisSubmit): Promise<ApiResponse<Diagnosis>> {
    return this.http.post('/diagnoses/submit', payload)
  }

  /** 诊断历史 */
  async listDiagnoses(limit = 20): Promise<ApiResponse<Diagnosis[]>> {
    return this.http.get('/diagnoses', { params: { limit } })
  }

  /** 诊断详情 */
  async getDiagnosis(id: number): Promise<ApiResponse<Diagnosis>> {
    return this.http.get(`/diagnoses/${id}`)
  }

  /** 获取报告 */
  async getReport(diagnosisId: number): Promise<ApiResponse<Report>> {
    return this.http.get(`/diagnoses/${diagnosisId}/report`)
  }

  /** 报告反馈 */
  async submitFeedback(diagnosisId: number, rating: number, feedback?: string): Promise<ApiResponse<{ ok: boolean }>> {
    return this.http.post(`/diagnoses/${diagnosisId}/report/feedback`, { rating, feedback })
  }

  // ─── 对标 ────────────────────────────────────────

  /** 所有赛道 */
  async listTracks(): Promise<ApiResponse<Array<{ track: string }>>> {
    return this.http.get('/benchmarks/tracks')
  }

  /** 赛道 Top10 */
  async getTop10(track: string): Promise<ApiResponse<BenchmarkItem[]>> {
    return this.http.get(`/benchmarks/top10/${encodeURIComponent(track)}`)
  }

  /** 计算对标差距 */
  async computeGap(track: string, userMetrics: Record<string, number>): Promise<ApiResponse<Record<string, unknown>>> {
    return this.http.post('/benchmarks/gap', null, { params: { track, user_metrics: userMetrics } })
  }

  // ─── 人设 ────────────────────────────────────────

  /** 人设扫描 */
  async scanPersona(payload: PersonaScanRequest): Promise<ApiResponse<Persona>> {
    return this.http.post('/personas/scan', payload)
  }

  /** 我的人设 */
  async getMyPersona(): Promise<ApiResponse<Persona | null>> {
    return this.http.get('/personas/me')
  }

  /** 人设原型列表 */
  async getArchetypes(): Promise<ApiResponse<Record<string, string[]>>> {
    return this.http.get('/personas/archetypes')
  }

  // ─── 商业定位 ────────────────────────────────────

  /** 商业定位扫描 */
  async scanPositioning(payload: PositioningScanRequest): Promise<ApiResponse<Positioning>> {
    return this.http.post('/positionings/scan', payload)
  }

  /** 我的定位 */
  async getMyPositioning(): Promise<ApiResponse<Positioning | null>> {
    return this.http.get('/positionings/me')
  }

  // ─── 订阅 ────────────────────────────────────────

  /** 获取产品列表 */
  async listProducts(): Promise<ApiResponse<ProductOut[]>> {
    return this.http.get('/subscriptions/products')
  }

  /** 创建订单 */
  async createOrder(payload: OrderCreate): Promise<ApiResponse<Order>> {
    return this.http.post('/subscriptions/orders', payload)
  }

  /** 模拟支付（仅开发） */
  async mockPay(orderNo: string): Promise<ApiResponse<{ ok: boolean; order_no: string }>> {
    return this.http.post(`/subscriptions/orders/${orderNo}/mock-pay`)
  }

  /** 我的订阅 */
  async getMySubscription(): Promise<ApiResponse<Subscription | null>> {
    return this.http.get('/subscriptions/my')
  }

  /** 我的订单 */
  async getMyOrders(): Promise<ApiResponse<Order[]>> {
    return this.http.get('/subscriptions/orders')
  }

  // ─── 分享官 ──────────────────────────────────────

  /** 我的分享官信息 */
  async getMyReferrer(): Promise<ApiResponse<ReferrerInfo>> {
    return this.http.get('/referrers/me')
  }

  /** 获取分享链接 */
  async getReferrerLink(): Promise<ApiResponse<ReferrerLink>> {
    return this.http.get('/referrers/link')
  }

  /** 分享记录 */
  async getReferralRecords(): Promise<ApiResponse<ReferralRecord[]>> {
    return this.http.get('/referrers/records')
  }

  /** 分享榜 */
  async getLeaderboard(limit = 30): Promise<ApiResponse<LeaderboardItem[]>> {
    return this.http.get('/referrers/leaderboard', { params: { limit } })
  }

  // ─── 成长档案 ────────────────────────────────────

  /** 我的档案 */
  async getMyArchive(): Promise<ApiResponse<Archive | null>> {
    return this.http.get('/archives/me')
  }

  /** 成长曲线 */
  async getGrowthCurve(): Promise<ApiResponse<GrowthCurve>> {
    return this.http.get('/archives/me/curve')
  }
}

// ─── 错误类 ────────────────────────────────────────

export class VideoCTError extends Error {
  constructor(
    public code: string,
    message: string,
    public status?: number,
  ) {
    super(message)
    this.name = 'VideoCTError'
  }
}
```

## 使用示例

```typescript
import { VideoCTClient } from './sdk'

const client = new VideoCTClient({
  baseURL: 'https://api.video-ct.cn',
})

// 1. 登录
const { data: loginResult } = await client.verifyOTP('13800138000', '123456')
client.setToken(loginResult.access_token)

// 2. 提交诊断
const { data: diagnosis } = await client.submitDiagnosis({
  video_url: 'https://v.douyin.com/xxxxx/',
  track: '美食',
  diagnosis_type: 'ct_basic',
})

// 3. 轮询报告（简易版）
async function waitForReport(diagnosisId: number, maxRetries = 30): Promise<Report> {
  for (let i = 0; i < maxRetries; i++) {
    const { data } = await client.getReport(diagnosisId)
    if (data) return data
    await new Promise(r => setTimeout(r, 2000)) // 等 2 秒
  }
  throw new Error('诊断超时')
}

const report = await waitForReport(diagnosis.id)
console.log('综合评分:', report.overall_score)
console.log('评级:', report.grade)

// 4. 查看对标差距
const { data: top10 } = await client.getTop10('美食')
console.log('赛道 Top1:', top10[0].nickname)

// 5. 人设扫描
const { data: persona } = await client.scanPersona({
  description: '我想做一个有态度的美食测评博主'
})
console.log('你的主原型:', persona.primary_archetype)
```

## Node.js 环境

在 Node.js 后端使用时，相同代码可以直接运行（axios 同时支持浏览器和 Node.js）。

```typescript
// server.ts
import { VideoCTClient } from './sdk'

const client = new VideoCTClient({
  baseURL: process.env.VCT_API_BASE_URL!,
})

// 使用 API Key 而不是 JWT（服务端到服务端）
// 在请求头中注入 API Key
const apiKey = process.env.VCT_API_KEY

// 自定义请求拦截
// 你可以在自己的 axios 实例上添加 API Key 拦截器
```

## React 集成

```tsx
import { createContext, useContext, useState, useEffect } from 'react'
import { VideoCTClient } from './sdk'

const client = new VideoCTClient({ baseURL: 'https://api.video-ct.cn' })
const VideoCTContext = createContext(client)

export function VideoCTProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('vct_token')
    if (token) {
      client.setToken(token)
    }
    setReady(true)
  }, [])

  return (
    <VideoCTContext.Provider value={client}>
      {ready ? children : <div>Loading...</div>}
    </VideoCTContext.Provider>
  )
}

export function useVideoCT() {
  return useContext(VideoCTContext)
}
```
