/**
 * 微信分享 composable
 *
 * 用法：
 *   const { updateShare } = useWechatShare()
 *   updateShare('标题', '描述', '/report/123', 'https://...thumb.jpg')
 */

import { setWxShare, isWechat, initWxConfig } from '@/utils/wechat'

/** 默认分享图标（需上传到 CDN） */
const DEFAULT_SHARE_IMG = 'https://video-ct.oss-cn-hangzhou.aliyuncs.com/share-default.png'

export function useWechatShare() {
  /**
   * 更新当前页面分享卡片
   * @param title  分享标题
   * @param desc   分享描述
   * @param link   分享链接（相对路径即可，会自动补全域名）
   * @param imgUrl 分享图标（可选，默认使用 logo）
   */
  function updateShare(
    title: string,
    desc: string,
    link: string = location.href,
    imgUrl: string = DEFAULT_SHARE_IMG,
  ): void {
    if (!isWechat()) {
      console.log('[useWechatShare] 非微信环境，跳过分享设置')
      return
    }

    // 补全链接为完整 URL
    let fullLink = link
    if (!/^https?:\/\//i.test(link)) {
      fullLink = location.origin + (link.startsWith('/') ? '' : '/') + link
    }

    setWxShare({
      title,
      desc,
      link: fullLink,
      imgUrl,
    })
  }

  return { updateShare }
}

/** 各页面的默认分享文案 */
export const SHARE_TEXT = {
  home: {
    title: '给你的短视频做一次 CT 扫描',
    desc: '6 维 18 点位，90 秒出报告，像影像科医生一样诊断你的短视频',
  },
  report: (score: number, grade: string) => ({
    title: `我的视频 CT 报告：综合分 ${score}，等级 ${grade}`,
    desc: '你也来给你的短视频做个诊断？',
  }),
  referrer: {
    title: '我正在用视频 CT 诊断短视频，邀请你免费体验',
    desc: 'AI 驱动的短视频诊断工具，6 维 CT 扫描 + 修复建议',
  },
  invite: {
    title: '我正在用视频 CT 诊断短视频，邀请你免费体验',
    desc: 'AI 驱动的短视频诊断工具，注册即享首单优惠',
  },
}
