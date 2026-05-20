/** 支付工具 · 微信 JSAPI / H5 支付 */

// 微信 JSAPI 支付参数（后端返回）
export interface WxPayParams {
  order_no: string
  app_id: string
  time_stamp: string
  nonce_str: string
  package: string // "prepay_id=wx..."
  sign_type: string
  pay_sign: string
  pay_url?: string // H5 支付跳转链接（非 JSAPI 环境使用）
  mock: boolean
}

// 支付结果
export interface PayResult {
  success: boolean
  message?: string
}

/** 检测是否在微信内置浏览器中 */
export function isWechat(): boolean {
  return /MicroMessenger/i.test(navigator.userAgent)
}

/** 微信 JSAPI 支付 · 调起 WeixinJSBridge */
export function wechatPay(params: WxPayParams): Promise<PayResult> {
  return new Promise((resolve) => {
    const doPay = () => {
      const bridge = (window as any).WeixinJSBridge
      if (!bridge) {
        resolve({ success: false, message: 'WeixinJSBridge 不可用' })
        return
      }
      bridge.invoke(
        'getBrandWCPayRequest',
        {
          appId: params.app_id,
          timeStamp: params.time_stamp,
          nonceStr: params.nonce_str,
          package: params.package,
          signType: params.sign_type,
          paySign: params.pay_sign,
        },
        (res: any) => {
          if (res.err_msg === 'get_brand_wcpay_request:ok') {
            resolve({ success: true })
          } else if (res.err_msg === 'get_brand_wcpay_request:cancel') {
            resolve({ success: false, message: '用户取消支付' })
          } else {
            resolve({ success: false, message: res.err_msg || '支付失败' })
          }
        },
      )
    }

    if (typeof (window as any).WeixinJSBridge === 'undefined') {
      document.addEventListener('WeixinJSBridgeReady', doPay, { once: true })
    } else {
      doPay()
    }
  })
}

/** 微信外支付 · 打开 H5 支付链接 */
export function openPayUrl(payUrl: string): void {
  window.open(payUrl, '_blank')
}
