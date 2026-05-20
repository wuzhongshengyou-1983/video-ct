// 视频 CT · 核心 TypeScript 接口定义
// 从 services/api/app/schemas/ 推导而来，保持与后端 Pydantic schema 一致

// ─── 通用泛型 ───────────────────────────────────────

/** 分页响应 */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

/** 统一 API 响应包裹 */
export interface ApiResponse<T = unknown> {
  code: string
  message: string
  data: T | null
}

/** 错误响应 */
export interface ErrorResponse {
  code: string
  message: string
  trace_id?: string
  details?: Record<string, unknown>
}

// ─── 用户 ──────────────────────────────────────────

export interface UserPublic {
  id: number
  nickname: string
  avatar_url: string | null
  role: string
  is_realname: boolean
  created_at: string // ISO-8601 datetime
}

export interface UserProfile {
  nickname?: string
  avatar_url?: string
  track?: string
  platform_main?: string
  follower_count?: number
  bio?: string
  goals?: string
}

export interface UserMe extends UserPublic {
  phone: string | null
  email: string | null
  track: string | null
  platform_main: string | null
  follower_count: number
  subscription_tier: string
  subscription_expires_at: string | null
  monthly_free_scans_used: number
  monthly_free_scans_quota: number
  cash_balance_cny: number
  deduction_balance_cny: number
  ticket_balance: number
}

// ─── 鉴权 ──────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user_id: number
  nickname: string
  role: string
  is_new_user: boolean
}

export interface PhoneOTPRequest {
  phone: string
}

export interface PhoneOTPVerify {
  phone: string
  code: string
  referrer_code?: string
}

export interface WechatLoginRequest {
  code: string
  referrer_code?: string
}

// ─── 订阅 ──────────────────────────────────────────

export interface ProductOut {
  sku: string
  name: string
  tier: string
  billing_cycle: string
  price_cny: number
  description: string | null
  features: string[] | null
}

export interface Subscription {
  id: number
  sku: string
  tier: string
  status: string
  started_at: string
  expires_at: string
  auto_renew: boolean
}

export interface OrderCreate {
  sku: string
  coupon_code?: string
  use_deduction?: boolean
  referrer_code?: string
}

export interface Order {
  id: number
  order_no: string
  sku: string
  total_cny: number
  deduction_cny: number
  paid_cny: number
  payment_status: string
  pay_url: string | null
  created_at: string
}

// ─── 诊断 ──────────────────────────────────────────

export interface DiagnosisSubmit {
  video_url: string
  track?: string
  diagnosis_type?: string // "ct_basic" | "ct_full"
  title?: string
  description?: string
}

export interface Diagnosis {
  id: number
  video_url: string
  video_platform: string | null
  status: string
  diagnosis_type: string
  progress_pct: number
  created_at: string
  completed_at: string | null
}

export interface ReportDimension {
  score: number // 0-100
  advantages: string[]
  findings: string[]
  suggestions: string[]
}

export interface ReportFinding {
  timestamp: string // "0:07"
  dimension: string
  problem: string
  suggestion: string
}

export interface Report {
  id: number
  diagnosis_id: number
  overall_score: number
  grade: string
  dimensions: Record<string, ReportDimension>
  findings: ReportFinding[]
  suggestions: Record<string, unknown>[]
  benchmark_gap: Record<string, unknown> | null
  html_path: string | null
  pdf_path: string | null
  model_used: string | null
  user_rating: number | null
  consultant_reviewed: boolean
  created_at: string
}

export interface ReportFeedback {
  rating: number // 1-5
  feedback?: string
}

// ─── 人设 ──────────────────────────────────────────

export interface PersonaScanRequest {
  sample_video_urls?: string[]
  description?: string
}

export interface Persona {
  id: number
  primary_archetype: string | null
  sub_archetype: string | null
  contrast_point: string | null
  self_tags: Record<string, unknown> | null
  audience_tags: Record<string, unknown> | null
  scores: Record<string, number>
  consistency_score: number
  canvas: Record<string, unknown> | null
  diagnosis: Record<string, unknown> | null
  drift_alert: boolean
  created_at: string
}

// ─── 商业定位 ──────────────────────────────────────

export interface PositioningScanRequest {
  description?: string
}

export interface Positioning {
  id: number
  scores: Record<string, number>
  monetization_paths: Record<string, unknown>
  recommended_archetype: string | null
  recommended_routes: Record<string, unknown> | null
  avoid_routes: Record<string, unknown> | null
  roadmap_12m: Record<string, unknown> | null
  risk_level: number
  canvas_bmc: Record<string, unknown> | null
  created_at: string
}

// ─── 分享官 ────────────────────────────────────────

export interface ReferrerInfo {
  link_code: string
  level: string
  total_valid_referrals: number
  total_rewards_cny: number
  cash_balance_cny: number
  deduction_balance_cny: number
  ticket_balance: number
  next_level_at: number
  next_level_name: string | null
}

export interface ReferrerLink {
  link_code: string
  h5_url: string
  qr_code_url: string
  poster_url: string
}

export interface ReferralRecord {
  invitee_nickname: string
  source: string | null
  first_paid_at: string | null
  reward_amount_cny: number
  reward_status: string
  created_at: string
}

export interface WithdrawRequest {
  amount_cny: number
}

export interface LeaderboardItem {
  rank: number
  nickname: string
  avatar_url: string | null
  level: string
  monthly_referrals: number
  monthly_rewards_cny: number
}

// ─── 成长档案 ──────────────────────────────────────

export interface Archive {
  id: number
  archive_no: string
  track: string | null
  current_level: string // L1-L6
  initial_baseline: Record<string, unknown> | null
  total_diagnoses: number
  created_at: string
}

export interface ArchiveSnapshot {
  snapshot_date: string // YYYY-MM-DD
  metrics: Record<string, number>
  benchmark_gap: Record<string, unknown> | null
  level: string
  overall_score: number | null
  notes: string | null
}

export interface GrowthCurve {
  metrics: Record<string, Array<{ date: string; value: number }>>
  benchmark_gap_curve: Array<{ date: string; gap_pct: number }>
  level_history: Array<{ date: string; level: string }>
  diagnoses_count: number
  days_active: number
}

// ─── 对标 ──────────────────────────────────────────

export interface BenchmarkItem {
  rank: number
  account_id: string
  nickname: string
  platform: string
  follower_count: number
  avatar_url: string | null
  bio: string | null
  style_archetype: string | null
  monetization: string | null
}

// ─── 人设原型 ──────────────────────────────────────

export interface ArchetypesMap {
  气场型: string[]
  干货型: string[]
  共情型: string[]
  趣味型: string[]
}
