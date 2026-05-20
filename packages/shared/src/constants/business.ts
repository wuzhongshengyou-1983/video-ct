// 视频 CT · 业务常量

/** 订阅等级 */
export const TIERS = {
  FREE: 'free',
  PRO: 'pro',
  MAX: 'max',
} as const

export type Tier = (typeof TIERS)[keyof typeof TIERS]

/** 订阅价格（单位：元） */
export const PRICES = {
  /** PRO 月度订阅 */
  PRO_MONTHLY: 99,
  /** PRO 季度订阅 */
  PRO_QUARTERLY: 249,
  /** PRO 年度订阅 */
  PRO_YEARLY: 899,
  /** MAX 月度订阅 */
  MAX_MONTHLY: 499,
  /** MAX 季度订阅 */
  MAX_QUARTERLY: 1199,
  /** MAX 年度订阅 */
  MAX_YEARLY: 4499,
  /** 单次 CT 诊断 */
  SINGLE_CT: 19,
  /** 单次全维度诊断 */
  SINGLE_FULL: 49,
} as const

/** 订阅价格映射（用于展示） */
export const PRICE_MAP: Record<string, number> = {
  'pro_monthly': PRICES.PRO_MONTHLY,
  'pro_quarterly': PRICES.PRO_QUARTERLY,
  'pro_yearly': PRICES.PRO_YEARLY,
  'max_monthly': PRICES.MAX_MONTHLY,
  'max_quarterly': PRICES.MAX_QUARTERLY,
  'max_yearly': PRICES.MAX_YEARLY,
  'ct_basic': PRICES.SINGLE_CT,
  'ct_full': PRICES.SINGLE_FULL,
}

/** 免费额度：每月免费诊断次数 */
export const FREE_MONTHLY_SCANS = 3

/** 收费额度：按等级每月额外扫描次数 */
export const TIER_SCAN_QUOTA: Record<Tier, number> = {
  free: FREE_MONTHLY_SCANS,
  pro: 20,
  max: 100,
}

/** 分享官等级 */
export const REFERRER_LEVELS = {
  BRONZE: 'bronze',
  SILVER: 'silver',
  GOLD: 'gold',
  DIAMOND: 'diamond',
} as const

export type ReferrerLevel = (typeof REFERRER_LEVELS)[keyof typeof REFERRER_LEVELS]

/** 分享官等级标签 */
export const REFERRER_LEVEL_LABELS: Record<ReferrerLevel, string> = {
  bronze: '铜牌',
  silver: '银牌',
  gold: '金牌',
  diamond: '钻石',
}

/** 分享官等级图标 */
export const REFERRER_LEVEL_ICONS: Record<ReferrerLevel, string> = {
  bronze: '🥉',
  silver: '🥈',
  gold: '🥇',
  diamond: '💎',
}

/** 分享官升级所需有效推荐数 */
export const REFERRER_THRESHOLDS: Record<ReferrerLevel, number> = {
  bronze: 0,
  silver: 11,
  gold: 31,
  diamond: 101,
}

/** 分享奖励（单位：元/有效用户） */
export const REFERRER_REWARDS = {
  /** 被推荐人首次付费奖励 */
  FIRST_PAY: 20,
  /** 被推荐人持续消费分成比例 */
  COMMISSION_RATE: 0.15,
} as const

/** 提现最低金额（元） */
export const MIN_WITHDRAW_CNY = 100

/** 诊断类型 */
export const DIAGNOSIS_TYPES = {
  CT_BASIC: 'ct_basic',
  CT_FULL: 'ct_full',
} as const

export type DiagnosisType = (typeof DIAGNOSIS_TYPES)[keyof typeof DIAGNOSIS_TYPES]

/** 诊断状态 */
export const DIAGNOSIS_STATUS = {
  PENDING: 'pending',
  CRAWLING: 'crawling',
  ANALYZING: 'analyzing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const

export type DiagnosisStatus = (typeof DIAGNOSIS_STATUS)[keyof typeof DIAGNOSIS_STATUS]

/** 诊断维度（六大指标） */
export const METRICS = [
  '曝光率',
  '点赞率',
  '评论率',
  '转发率',
  '收藏率',
  '变现率',
] as const

export type MetricName = (typeof METRICS)[number]

/** 付款状态 */
export const PAYMENT_STATUS = {
  PENDING: 'pending',
  PAID: 'paid',
  CANCELLED: 'cancelled',
  REFUNDED: 'refunded',
} as const

export type PaymentStatus = (typeof PAYMENT_STATUS)[keyof typeof PAYMENT_STATUS]

/** 成长等级（L1-L6） */
export const GROWTH_LEVELS = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6'] as const
export type GrowthLevel = (typeof GROWTH_LEVELS)[number]

/** 计费周期 */
export const BILLING_CYCLES = {
  MONTHLY: 'monthly',
  QUARTERLY: 'quarterly',
  YEARLY: 'yearly',
  ONCE: 'once',
} as const

export type BillingCycle = (typeof BILLING_CYCLES)[keyof typeof BILLING_CYCLES]

/** 角色 */
export const ROLES = {
  USER: 'user',
  CONSULTANT: 'consultant',
  ADMIN: 'admin',
} as const

export type Role = (typeof ROLES)[keyof typeof ROLES]
