import 'axios'

declare module 'axios' {
  interface AxiosRequestConfig {
    /** 跳过全局错误 Toast（埋点等静默请求） */
    _noToast?: boolean
    /** 标记 401 后已尝试过 refresh，防止无限重试 */
    _retry?: boolean
  }
}
