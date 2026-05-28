// 四端统一 HTTP 请求客户端（骨架，待实现）
//
// 设计目标：H5 / 小程序 / Admin / Consultant 共用同一套请求逻辑
// - 统一 baseURL 注入
// - 统一 JWT token 注入
// - 统一错误码处理（401 跳登录、429 限流提示等）
// - 小程序适配层：wx.request 替换 fetch

export interface ApiClientConfig {
  baseURL: string
  getToken: () => string | null
  onUnauthorized?: () => void
}

// TODO: 实现通用 request 方法
// 参考 apps/h5/src/api/ 中现有的请求封装，提炼到这里

export type { ApiClientConfig as default }
