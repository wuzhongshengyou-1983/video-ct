// 视频 CT · 设计令牌
// 基于 apps/h5/src/styles/main.scss 的 CSS 变量导出，供 TypeScript 端使用

export const colors = {
  /** 主背景色 — 深空黑 */
  bg: '#0a0e1a',
  /** 次背景色 */
  bg2: '#111827',
  /** 表面/卡片背景 */
  surface: 'rgba(255,255,255,0.04)',
  /** 表面 hover */
  surfaceHover: 'rgba(255,255,255,0.08)',
  /** 主文字 */
  text: '#e5e7eb',
  /** 辅助文字 */
  text2: '#9ca3af',
  /** 三级文字（弱提示） */
  text3: '#6b7280',
  /** 主色 — 琥珀暖光 */
  primary: '#f59e0b',
  /** 主色 hover */
  primaryHover: '#fbbf24',
  /** 强调色 — 天蓝色 */
  accent: '#38bdf8',
  /** 成功色 */
  success: '#10b981',
  /** 警告色 */
  warning: '#f59e0b',
  /** 危险色 */
  danger: '#ef4444',
  /** 边框色 */
  border: 'rgba(255,255,255,0.08)',
} as const

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const

export const fontSize = {
  /** 11px — 标签/角标 */
  sm: 11,
  /** 13px — 正文 */
  base: 13,
  /** 16px — 正文增强 */
  lg: 16,
  /** 18px — 段落标题 */
  xl: 18,
  /** 24px — 卡片标题/大数字 */
  xxl: 24,
  /** 32px — Hero 数字 */
  hero: 32,
} as const

export const radius = {
  /** 8px — 小元素（按钮/标签） */
  sm: 8,
  /** 12px — 卡片/面板 */
  md: 12,
  /** 16px — 大卡片/弹窗 */
  lg: 16,
} as const

/** 阴影与光晕 */
export const effects = {
  shadow: '0 4px 24px rgba(0,0,0,0.4)',
  glow: '0 0 32px rgba(245,158,11,0.25)',
} as const

/** 动画时长（ms） */
export const duration = {
  fast: 150,
  normal: 300,
  slow: 500,
} as const

/** 断点（px） */
export const breakpoints = {
  xs: 375,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const

/**
 * 设计令牌汇总导出（兼容 CSS-in-JS 场景）
 * 使用方式：
 *   import { tokens } from '@video-ct/shared/tokens'
 *   tokens.colors.primary  // '#f59e0b'
 */
export const tokens = {
  colors,
  spacing,
  fontSize,
  radius,
  effects,
  duration,
  breakpoints,
} as const

export type DesignTokens = typeof tokens
