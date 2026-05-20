import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: '视频 CT · 开发者文档',
  description: '短视频博主 AI 诊断 + 对标 + 陪跑 SaaS · 开放端 API 与 SDK 文档',
  lang: 'zh-CN',
  base: '/',

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['meta', { name: 'theme-color', content: '#f59e0b' }],
    ['meta', { name: 'og:type', content: 'website' }],
    ['meta', { name: 'og:title', content: '视频 CT · 开发者文档' }],
    ['meta', { name: 'og:description', content: '短视频博主 AI 诊断 + 对标 + 陪跑 SaaS · 开放端 API 与 SDK 文档' }],
  ],

  markdown: {
    theme: {
      light: 'github-dark',
      dark: 'github-dark',
    },
  },

  themeConfig: {
    logo: '/logo.svg',

    siteTitle: '视频 CT',

    // 搜索
    search: {
      provider: 'local',
    },

    // 顶部导航
    nav: [
      { text: '指南', link: '/guide/quickstart' },
      { text: 'API 参考', link: '/api/overview' },
      { text: 'SDK', link: '/sdk/js' },
      {
        text: '相关链接',
        items: [
          { text: 'API Spec (OpenAPI)', link: '/api-spec.yaml' },
          { text: '产品主页', link: 'https://video-ct.cn' },
          { text: 'GitHub', link: 'https://github.com/video-ct/video-ct' },
        ],
      },
    ],

    // 侧边栏
    sidebar: {
      '/guide/': [
        {
          text: '入门指南',
          items: [
            { text: '快速开始', link: '/guide/quickstart' },
            { text: '鉴权说明', link: '/guide/authentication' },
          ],
        },
      ],
      '/api/': [
        {
          text: 'API 参考',
          items: [
            { text: '概览', link: '/api/overview' },
            { text: '诊断 API', link: '/api/diagnosis' },
            { text: '订阅 API', link: '/api/subscription' },
            { text: '人设 API', link: '/api/persona' },
            { text: '分享官 API', link: '/api/referrer' },
          ],
        },
      ],
      '/sdk/': [
        {
          text: 'SDK 指南',
          items: [
            { text: 'JavaScript / TypeScript', link: '/sdk/js' },
            { text: 'Python', link: '/sdk/python' },
          ],
        },
      ],
    },

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/video-ct/video-ct' },
    ],

    // 页脚
    footer: {
      message: '视频 CT · 短视频博主 AI 诊断 + 对标 + 陪跑 SaaS',
      copyright: 'Copyright 2025-2026 视频 CT',
    },

    // 编辑链接
    editLink: {
      pattern: 'https://github.com/video-ct/video-ct/edit/main/apps/docs/:path',
      text: '在 GitHub 上编辑此页',
    },

    // 最后更新时间
    lastUpdated: {
      text: '最后更新',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'medium',
      },
    },
  },

  // 深色主题由 CSS 变量驱动（匹配星际深空风）
  appearance: 'dark',
})
