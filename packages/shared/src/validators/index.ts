// 四端共享校验规则（骨架，待实现）
//
// 设计目标：H5 / 小程序 / Admin / Consultant 用同一套校验，避免各端规则漂移

// 手机号：中国大陆 11 位
export const isPhone = (v: string) => /^1[3-9]\d{9}$/.test(v)

// 视频链接：抖音 / 快手 / B站
export const isVideoUrl = (v: string) =>
  /douyin\.com|kuaishou\.com|bilibili\.com|v\.qq\.com/.test(v)

// OTP 验证码：6 位数字
export const isOtp = (v: string) => /^\d{6}$/.test(v)

// TODO: 补充更多共享校验规则
// - 用户名长度 / 特殊字符
// - 优惠券码格式
// - 文件大小上限（MAX_UPLOAD_SIZE_MB=200）
