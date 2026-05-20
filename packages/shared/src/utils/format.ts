// 视频 CT · 格式化工具函数

/**
 * 格式化粉丝/关注数
 * - < 10,000 原样显示
 * - >= 10,000 转为 "x.xw" 格式
 * - >= 100,000,000 转为 "x.x亿"
 *
 * @example formatFollowerCount(12300) // "1.2w"
 * @example formatFollowerCount(100000000) // "1.0亿"
 */
export function formatFollowerCount(n: number): string {
  if (n < 0) return '0'
  if (n >= 100_000_000) {
    return (n / 100_000_000).toFixed(1) + '亿'
  }
  if (n >= 10_000) {
    return (n / 10_000).toFixed(1) + 'w'
  }
  return String(n)
}

/**
 * 格式化 ISO 时间字符串为「MM-DD HH:mm」
 * @param iso ISO-8601 格式的时间字符串
 * @returns "05-20 10:30"
 */
export function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return iso
  }
}

/**
 * 格式化 ISO 时间字符串为「YYYY-MM-DD HH:mm:ss」
 */
export function formatDateTime(iso: string): string {
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  } catch {
    return iso
  }
}

/**
 * 格式化金额（单位：分 → 元 显示）
 * @param cents 金额（分）
 * @returns "¥99.00"
 */
export function formatCny(cents: number): string {
  const yuan = cents / 100
  return '¥' + yuan.toFixed(2)
}

/**
 * 格式化金额（单位：分 → 元 显示，去掉无用小数位）
 * @param cents 金额（分）
 * @returns "¥99" / "¥99.5" / "¥99.99"
 */
export function formatCnyShort(cents: number): string {
  const yuan = cents / 100
  const s = yuan.toFixed(2)
  // 去掉末尾的 .00
  if (s.endsWith('.00')) return '¥' + s.slice(0, -3)
  // 去掉末尾的 0
  if (s.endsWith('0')) return '¥' + s.slice(0, -1)
  return '¥' + s
}

/**
 * 获取订阅等级对应的中文标签
 */
export function getTierLabel(tier: string): string {
  const map: Record<string, string> = {
    free: '免费版',
    pro: 'Pro 版',
    max: 'Max 版',
  }
  return map[tier] ?? tier
}

/**
 * 获取分享官等级对应的中文标签（带图标）
 */
export function getLevelLabel(level: string): string {
  const map: Record<string, string> = {
    bronze: '🥉 铜牌分享官',
    silver: '🥈 银牌分享官',
    gold: '🥇 金牌分享官',
    diamond: '💎 钻石分享官',
  }
  return map[level] ?? level
}

/**
 * 获取诊断状态对应的中文标签
 */
export function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '排队中',
    crawling: '数据采集',
    analyzing: 'AI 诊断中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] ?? status
}

/**
 * 获取诊断评分对应的等级（S/A/B/C/D）
 */
export function getGradeLabel(grade: string): string {
  const map: Record<string, string> = {
    S: '卓越 (S)',
    A: '优秀 (A)',
    B: '良好 (B)',
    C: '一般 (C)',
    D: '待提升 (D)',
  }
  return map[grade] ?? grade
}

/**
 * 获取付款状态中文标签
 */
export function getPaymentStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    cancelled: '已取消',
    refunded: '已退款',
  }
  return map[status] ?? status
}

/**
 * 格式化 ISO 时间字符串为「YYYY-MM-DD」
 * @param iso ISO-8601 格式的时间字符串
 * @returns "2026-05-20"
 */
export function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  } catch {
    return iso
  }
}

/**
 * 相对时间（简易版）：刚刚 / x 分钟前 / x 小时前 / x 天前
 */
export function formatRelativeTime(iso: string): string {
  try {
    const now = Date.now()
    const then = new Date(iso).getTime()
    if (isNaN(then)) return iso
    const diff = now - then
    const seconds = Math.floor(diff / 1000)
    if (seconds < 60) return '刚刚'
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes} 分钟前`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} 小时前`
    const days = Math.floor(hours / 24)
    if (days < 30) return `${days} 天前`
    const months = Math.floor(days / 30)
    if (months < 12) return `${months} 个月前`
    const years = Math.floor(months / 12)
    return `${years} 年前`
  } catch {
    return iso
  }
}
