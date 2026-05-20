/**
 * 微信 JS-SDK 工具
 * - wx.config 初始化
 * - 分享卡片设置
 * - 微信支付
 * - 图片选择
 *
 * 所有 API 调用前判断 isWechat()，非微信环境静默跳过。
 */

import { http } from '@/api/client'

// ---- 类型定义 ----

interface WxConfigParams {
  appId: string
  timestamp: number
  nonceStr: string
  signature: string
  jsApiList: string[]
}

interface WxShareParams {
  title: string
  desc: string
  link: string
  imgUrl: string
}

interface WxPayParams {
  timestamp: string
  nonceStr: string
  package: string
  signType: string
  paySign: string
}

// 微信 JS-SDK 挂载在 window.wx 上
declare global {
  interface Window {
    wx?: {
      config: (params: WxConfigParams) => void
      ready: (cb: () => void) => void
      error: (cb: (err: any) => void) => void
      checkJsApi: (opts: {
        jsApiList: string[]
        success: (res: { checkResult: Record<string, boolean> }) => void
      }) => void
      updateAppMessageShareData: (params: WxShareParams) => void
      updateTimelineShareData: (params: WxShareParams) => void
      onMenuShareAppMessage: (params: WxShareParams) => void
      onMenuShareTimeline: (params: WxShareParams) => void
      chooseImage: (opts: {
        count: number
        sizeType: string[]
        sourceType: string[]
        success: (res: { localIds: string[] }) => void
        fail?: (err: any) => void
      }) => void
      previewImage: (opts: { current: string; urls: string[] }) => void
      getLocalImgData: (opts: {
        localId: string
        success: (res: { localData: string }) => void
        fail?: (err: any) => void
      }) => void
      chooseWXPay: (opts: WxPayParams & {
        success: (res: { errMsg: string }) => void
        fail?: (err: any) => void
        cancel?: (res: { errMsg: string }) => void
      }) => void
      requestSubscribeMessage: (opts: {
        tmplIds: string[]
        success: (res: any) => void
        fail?: (err: any) => void
        complete?: (res: any) => void
      }) => void
    }
  }
}

// ---- 环境检测 ----

/** 判断是否微信环境 */
export function isWechat(): boolean {
  return /MicroMessenger/i.test(navigator.userAgent)
}

// ---- wx.config 初始化 ----

let wxReady = false
let wxReadyPromise: Promise<boolean> | null = null

/**
 * 初始化 wx.config（从后端获取签名）
 * 非微信环境直接 resolve(false)
 */
export async function initWxConfig(): Promise<boolean> {
  // 复用已有的 ready promise
  if (wxReadyPromise) return wxReadyPromise

  wxReadyPromise = _doInit()
  return wxReadyPromise
}

async function _doInit(): Promise<boolean> {
  if (!isWechat()) {
    console.log('[wechat] 非微信环境，跳过 wx.config')
    return false
  }

  if (!window.wx) {
    console.warn('[wechat] window.wx 未载入，请先引入 //res.wx.qq.com/open/js/jweixin-1.6.0.js')
    return false
  }

  try {
    // 从后端获取签名（URL 用当前页面不含 # 的部分）
    const url = encodeURIComponent(location.href.split('#')[0])
    const signData: any = await http.get(`/api/v1/wechat/js-sdk-sign?url=${url}`)

    window.wx.config({
      appId: signData.app_id,
      timestamp: signData.timestamp,
      nonceStr: signData.nonce_str,
      signature: signData.signature,
      jsApiList: signData.js_api_list || [],
    })

    return new Promise((resolve) => {
      window.wx!.ready(() => {
        wxReady = true
        console.log('[wechat] wx.config ready')
        resolve(true)
      })
      window.wx!.error((err: any) => {
        console.error('[wechat] wx.config error:', err)
        resolve(false)
      })
      // 超时 10 秒也算失败
      setTimeout(() => {
        if (!wxReady) {
          console.warn('[wechat] wx.config timeout')
          resolve(false)
        }
      }, 10000)
    })
  } catch (e) {
    console.error('[wechat] 获取签名失败:', e)
    return false
  }
}

// ---- 分享卡片 ----

/**
 * 设置分享卡片（同时设置好友 + 朋友圈）
 * 会自动判断使用新 API 还是旧 API
 */
export function setWxShare(params: WxShareParams): void {
  if (!isWechat() || !window.wx) return

  const doShare = () => {
    try {
      // 优先使用新 API
      window.wx!.updateAppMessageShareData?.(params)
      window.wx!.updateTimelineShareData?.(params)
    } catch {
      // 降级旧 API
      try {
        window.wx!.onMenuShareAppMessage?.(params)
        window.wx!.onMenuShareTimeline?.(params)
      } catch (e) {
        console.warn('[wechat] 分享设置失败:', e)
      }
    }
  }

  if (wxReady) {
    doShare()
  } else {
    // 如果尚未 ready，等待 ready 后设置
    if (window.wx.ready) {
      window.wx.ready(doShare)
    }
  }
}

// ---- 微信支付 ----

/**
 * 调起微信支付 JSAPI
 * 仅微信环境有效
 */
export function wxRequestPayment(params: WxPayParams): Promise<{ errMsg: string }> {
  return new Promise((resolve, reject) => {
    if (!isWechat() || !window.wx) {
      reject(new Error('非微信环境，无法使用微信支付'))
      return
    }

    const doPay = () => {
      window.wx!.chooseWXPay({
        ...params,
        success: (res) => {
          resolve(res)
        },
        cancel: (res) => {
          reject(new Error('用户取消支付'))
        },
        fail: (err) => {
          reject(new Error(err.errMsg || '支付失败'))
        },
      })
    }

    if (wxReady) {
      doPay()
    } else {
      initWxConfig().then((ok) => {
        if (ok) doPay()
        else reject(new Error('微信 JS-SDK 初始化失败'))
      })
    }
  })
}

// ---- 选择图片 ----

/**
 * 从相册/相机选择图片，返回 base64 data URL
 * 用于头像上传等场景
 */
export function wxChooseImage(): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!isWechat() || !window.wx) {
      reject(new Error('非微信环境，请使用 file input'))
      return
    }

    const doChoose = () => {
      window.wx!.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const localId = res.localIds[0]
          if (!localId) {
            reject(new Error('未选择图片'))
            return
          }
          // 获取 base64 数据
          window.wx!.getLocalImgData({
            localId,
            success: (imgRes) => {
              resolve(imgRes.localData)
            },
            fail: (err) => {
              reject(new Error(err.errMsg || '获取图片数据失败'))
            },
          })
        },
        fail: (err) => {
          reject(new Error(err.errMsg || '选择图片失败'))
        },
      })
    }

    if (wxReady) {
      doChoose()
    } else {
      initWxConfig().then((ok) => {
        if (ok) doChoose()
        else reject(new Error('微信 JS-SDK 初始化失败'))
      })
    }
  })
}
