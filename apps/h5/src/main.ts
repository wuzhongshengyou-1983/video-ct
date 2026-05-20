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

app.mount('#app')
