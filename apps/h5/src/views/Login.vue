<template>
  <div class="login">
    <van-nav-bar left-arrow @click-left="router.back()" :border="false" />

    <div class="hero">
      <div class="logo">视频 <span>CT</span></div>
      <div class="tag">用医学 CT 方式诊断你的短视频</div>
    </div>

    <div class="vct-card form">
      <van-field
        v-model="phone"
        label="手机号"
        placeholder="请输入手机号"
        maxlength="11"
        type="tel"
        :error="phoneError"
        :error-message="phoneError"
        @update:model-value="phoneError = ''"
      />
      <div class="vct-divider" />
      <van-field
        v-model="code"
        label="验证码"
        placeholder="6 位验证码"
        maxlength="6"
        type="number"
        :error="codeError"
        :error-message="codeError"
        @update:model-value="codeError = ''"
      >
        <template #button>
          <van-button size="small" type="primary" :disabled="cooldown > 0" @click="sendOtp">
            {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
          </van-button>
        </template>
      </van-field>

      <div v-if="referrer" class="referrer-tip">
        🎁 受 <strong>{{ referrer }}</strong> 邀请，注册即享首单 9 折
      </div>

      <van-button type="primary" block class="login-btn" :loading="loading" @click="login">
        登录 / 注册
      </van-button>

      <!-- 微信一键登录（仅微信环境显示） -->
      <div v-if="isWechatEnv" class="wechat-login-section">
        <div class="wechat-divider">
          <span class="divider-line" />
          <span class="divider-text">或</span>
          <span class="divider-line" />
        </div>
        <van-button
          block
          class="wechat-login-btn"
          :loading="wechatLoading"
          @click="doWechatLogin"
        >
          <span class="wechat-icon">💬</span>
          微信一键登录
        </van-button>
      </div>

      <div v-if="isDev" class="dev-tip">
        💡 开发模式：万能验证码 <code>{{ DEV_OTP_CODE }}</code>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Toast } from 'vant'
import { authApi, wechatApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { DEV_OTP_CODE } from '@video-ct/shared'
import { trackPageView, trackConversion } from '@/utils/tracker'
import { isWechat } from '@/utils/wechat'

const isDev = import.meta.env.DEV

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const phone = ref('')
const code = ref('')
const phoneError = ref('')
const codeError = ref('')
const cooldown = ref(0)
const loading = ref(false)
const wechatLoading = ref(false)
const isWechatEnv = ref(false)
const referrer = ref<string | null>(null)

onMounted(() => {
  trackPageView('login')
  isWechatEnv.value = isWechat()
  referrer.value = localStorage.getItem('vct_ref') || (route.query.ref as string) || null
  if (referrer.value && !localStorage.getItem('vct_ref')) {
    localStorage.setItem('vct_ref', referrer.value)
  }
})

async function doWechatLogin() {
  wechatLoading.value = true
  try {
    const redirect = (route.query.redirect as string) || '/home'
    const data = await wechatApi.oauthUrl(redirect, referrer.value || undefined)
    // 跳转到微信授权页面
    window.location.href = data.url
  } catch (e: any) {
    Toast.fail(e.message || '获取微信授权失败')
    wechatLoading.value = false
  }
}

async function sendOtp() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    phoneError.value = '请输入正确的手机号'
    return
  }
  try {
    const r = await authApi.sendOtp(phone.value)
    Toast.success(r.dev_code ? `已发送（dev: ${r.dev_code}）` : '验证码已发送')
    cooldown.value = 60
    const timer = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e: any) {
    if (e.status === 429) {
      Toast.fail('验证码发送太频繁，请稍后重试')
    } else if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '发送失败')
    }
  }
}

async function login() {
  let valid = true
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    phoneError.value = '请输入正确的手机号'
    valid = false
  }
  if (!/^\d{4,6}$/.test(code.value)) {
    codeError.value = '请输入验证码'
    valid = false
  }
  if (!valid) return

  loading.value = true
  try {
    const r = await authApi.verifyOtp(phone.value, code.value, referrer.value || undefined)
    userStore.setToken(r.access_token)
    await userStore.fetchMe()
    trackConversion(r.is_new_user ? 'register' : 'login')
    Toast.success(r.is_new_user ? '注册成功' : '登录成功')
    localStorage.removeItem('vct_ref')
    const redirect = (route.query.redirect as string) || '/home'
    router.replace(redirect)
  } catch (e: any) {
    if (e.status === 429) {
      Toast.fail('验证码验证太频繁，请稍后重试')
    } else if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '登录失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login { min-height: 100vh; padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); }
.hero { text-align: center; padding: 24px 0 32px;
  .logo { font-size: 36px; font-weight: 800;
    span { color: var(--vct-primary); }
  }
  .tag { color: var(--vct-text-2); font-size: 13px; margin-top: 4px; }
}
.form { padding: 24px 16px; scroll-margin-bottom: 40vh; }
.referrer-tip {
  background: rgba(56,189,248,0.12); border: 1px solid rgba(56,189,248,0.3);
  padding: 10px 12px; border-radius: 8px; font-size: 12px;
  color: var(--vct-accent); margin: 16px 0 4px;
  strong { color: var(--vct-primary); }
}
.login-btn { margin-top: 24px; min-height: 48px; font-size: 16px; }
.wechat-login-section { margin-top: 20px; }
.wechat-divider {
  display: flex; align-items: center; margin: 16px 0;
  .divider-line { flex: 1; height: 1px; background: var(--vct-border); }
  .divider-text { padding: 0 12px; font-size: 12px; color: var(--vct-text-3); }
}
.wechat-login-btn {
  background: #07c160 !important; border-color: #07c160 !important;
  color: #fff !important; font-size: 15px; min-height: 48px;
  .wechat-icon { margin-right: 6px; font-size: 18px; }
}
.dev-tip {
  margin-top: 16px; text-align: center; font-size: 11px; color: var(--vct-text-3);
  code { background: var(--vct-surface); padding: 2px 6px; border-radius: 4px; color: var(--vct-primary); }
}
</style>
