/**
 * 微信小程序订阅消息工具
 * 用于在 H5 中调起订阅消息授权（通过 JS-SDK）
 */

import { isWechat } from './wechat'

// ---- 类型 ----

interface SubscribeResult {
  /** 模板 ID → 是否接受 */
  [templateId: string]: 'accept' | 'reject' | 'ban'
}

// ---- 便捷订阅 ----

/** 诊断完成通知模板 ID（从配置获取或默认空） */
const TEMPLATE_DIAGNOSIS_DONE = ''

/**
 * 请求订阅消息授权
 * @param templateIds 要订阅的模板 ID 列表（最多 3 个）
 * @returns 用户接受至少一个模板则返回 true
 */
export function requestSubscribeMessage(templateIds: string[]): Promise<boolean> {
  return new Promise((resolve) => {
    if (!isWechat()) {
      console.log('[subscribe-msg] 非微信环境，跳过订阅')
      resolve(false)
      return
    }

    if (!window.wx || !window.wx.requestSubscribeMessage) {
      console.warn('[subscribe-msg] 当前环境不支持 wx.requestSubscribeMessage')
      resolve(false)
      return
    }

    // 过滤空模板 ID
    const validIds = templateIds.filter(Boolean)
    if (validIds.length === 0) {
      console.log('[subscribe-msg] 无有效模板 ID，跳过')
      resolve(false)
      return
    }

    window.wx.requestSubscribeMessage({
      tmplIds: validIds.slice(0, 3), // 最多 3 个
      success: (res: SubscribeResult) => {
        // 至少有一个接受就算成功
        const accepted = Object.values(res).some((v) => v === 'accept')
        console.log('[subscribe-msg] 订阅结果:', res, 'accepted:', accepted)
        resolve(accepted)
      },
      fail: (err: any) => {
        console.warn('[subscribe-msg] 订阅失败:', err)
        resolve(false)
      },
      complete: () => {
        // noop
      },
    })
  })
}

/**
 * 订阅「诊断完成」通知
 * 便捷方法，hardcoded 模板 ID
 */
export function subscribeDiagnosisComplete(): Promise<boolean> {
  if (!TEMPLATE_DIAGNOSIS_DONE) {
    console.log('[subscribe-msg] 诊断完成模板 ID 未配置，跳过')
    return Promise.resolve(false)
  }
  return requestSubscribeMessage([TEMPLATE_DIAGNOSIS_DONE])
}
