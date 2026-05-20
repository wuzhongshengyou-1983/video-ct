import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Lazyload, Toast, Dialog, Notify } from 'vant'

import App from './App.vue'
import router from './router'

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
