// 视频 CT · 共享包总入口
// @video-ct/shared

// ─── 类型 ──────────────────────────────────────────
export type {
  // 通用
  Page,
  ApiResponse,
  ErrorResponse,
  // 用户
  UserPublic,
  UserProfile,
  UserMe,
  // 鉴权
  TokenResponse,
  PhoneOTPRequest,
  PhoneOTPVerify,
  WechatLoginRequest,
  // 订阅
  ProductOut,
  Subscription,
  OrderCreate,
  Order,
  // 诊断
  DiagnosisSubmit,
  Diagnosis,
  ReportDimension,
  ReportFinding,
  Report,
  ReportFeedback,
  // 人设
  PersonaScanRequest,
  Persona,
  // 商业定位
  PositioningScanRequest,
  Positioning,
  // 分享官
  ReferrerInfo,
  ReferrerLink,
  ReferralRecord,
  WithdrawRequest,
  LeaderboardItem,
  // 成长档案
  Archive,
  ArchiveSnapshot,
  GrowthCurve,
  // 对标
  BenchmarkItem,
  ArchetypesMap,
} from './types/api'

// ─── 常量 ──────────────────────────────────────────
export {
  // 订阅
  TIERS,
  PRICES,
  PRICE_MAP,
  FREE_MONTHLY_SCANS,
  TIER_SCAN_QUOTA,
  // 分享官
  REFERRER_LEVELS,
  REFERRER_LEVEL_LABELS,
  REFERRER_LEVEL_ICONS,
  REFERRER_THRESHOLDS,
  REFERRER_REWARDS,
  REFERRER_REWARD_CNY,
  REFERRER_DEDUCT_COUNT,
  MIN_WITHDRAW_CNY,
  // 诊断
  DIAGNOSIS_TYPES,
  DIAGNOSIS_STATUS,
  METRICS,
  // 支付
  PAYMENT_STATUS,
  // 成长
  GROWTH_LEVELS,
  GRADE_LABELS,
  ARCHIVE_METRIC_LABELS,
  // 计费
  BILLING_CYCLES,
  // 角色
  ROLES,
  // 开发
  DEV_OTP_CODE,
  // 人设
  PERSONA_ARCHETYPES,
  // 变现
  MONETIZATION_ARCHETYPES,
  // 风险
  RISK_LEVELS,
} from './constants/business'

export type {
  Tier,
  ReferrerLevel as ReferrerLevelType,
  DiagnosisType,
  DiagnosisStatus,
  MetricName,
  PaymentStatus,
  GrowthLevel,
  BillingCycle,
  Role,
} from './constants/business'

// ─── 工具函数 ──────────────────────────────────────
export {
  formatFollowerCount,
  formatTime,
  formatDateTime,
  formatDate,
  formatCny,
  formatCnyShort,
  getTierLabel,
  getLevelLabel,
  getStatusLabel,
  getGradeLabel,
  getPaymentStatusLabel,
  formatRelativeTime,
} from './utils/format'

// ─── 设计令牌 ──────────────────────────────────────
export {
  colors,
  spacing,
  fontSize,
  radius,
  effects,
  duration,
  breakpoints,
  tokens,
} from './tokens/design-tokens'

export type { DesignTokens } from './tokens/design-tokens'
