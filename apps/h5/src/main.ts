import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Lazyload, Toast, Dialog, Notify } from 'vant'

import App from './App.vue'
import router from './router'

// Eruda 移动端调试面板 — 仅 DEV 环境加载，生产构建自动 tree-shake
if (import.meta.env.DEV) {
  import('eruda').then(({ default: eruda }) => {
    eruda.init()
    console.log('%c[video-ct] Eruda 已就绪 · 点击右下角按钮打开调试面板', 'color:#4ade80;font-weight:bold')
  })
}

import 'vant/lib/index.css'
import './styles/main.scss'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Lazyload)
app.use(Toast)
app.use(Dialog)
app.use(Notify)

// Service Worker 注册（仅生产环境，避免开发时缓存干扰调试）
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  navigator.serviceWorker.register('/sw.js').catch((err) => {
    console.warn('[sw] register failed:', err.message)
  })
}

// 微信 JS-SDK 初始化（非微信环境静默跳过）
import { initWxConfig } from '@/utils/wechat'
initWxConfig().then((ok) => {
  if (ok) console.log('[main] 微信 JS-SDK 已就绪')
})

app.mount('#app')
