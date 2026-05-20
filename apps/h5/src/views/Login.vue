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
      />
      <div class="vct-divider" />
      <van-field
        v-model="code"
        label="验证码"
        placeholder="6 位验证码"
        maxlength="6"
        type="number"
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

      <div class="dev-tip">
        💡 开发模式：万能验证码 <code>0000</code>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Toast } from 'vant'
import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const phone = ref('')
const code = ref('')
const cooldown = ref(0)
const loading = ref(false)
const referrer = ref<string | null>(null)

onMounted(() => {
  referrer.value = localStorage.getItem('vct_ref') || (route.query.ref as string) || null
  if (referrer.value && !localStorage.getItem('vct_ref')) {
    localStorage.setItem('vct_ref', referrer.value)
  }
})

async function sendOtp() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    Toast.fail('手机号格式错误')
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
    Toast.fail(e.message || '发送失败')
  }
}

async function login() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    Toast.fail('手机号格式错误')
    return
  }
  if (!/^\d{4,6}$/.test(code.value)) {
    Toast.fail('请输入验证码')
    return
  }
  loading.value = true
  try {
    const r = await authApi.verifyOtp(phone.value, code.value, referrer.value || undefined)
    userStore.setToken(r.access_token)
    await userStore.fetchMe()
    Toast.success(r.is_new_user ? '注册成功' : '登录成功')
    localStorage.removeItem('vct_ref')
    const redirect = (route.query.redirect as string) || '/home'
    router.replace(redirect)
  } catch (e: any) {
    Toast.fail(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login { min-height: 100vh; padding: 0 16px 24px; }
.hero { text-align: center; padding: 24px 0 32px;
  .logo { font-size: 36px; font-weight: 800;
    span { color: var(--vct-primary); }
  }
  .tag { color: var(--vct-text-2); font-size: 13px; margin-top: 4px; }
}
.form { padding: 24px 16px; }
.referrer-tip {
  background: rgba(56,189,248,0.12); border: 1px solid rgba(56,189,248,0.3);
  padding: 10px 12px; border-radius: 8px; font-size: 12px;
  color: var(--vct-accent); margin: 16px 0 4px;
  strong { color: var(--vct-primary); }
}
.login-btn { margin-top: 24px; height: 48px; font-size: 16px; }
.dev-tip {
  margin-top: 16px; text-align: center; font-size: 11px; color: var(--vct-text-3);
  code { background: var(--vct-surface); padding: 2px 6px; border-radius: 4px; color: var(--vct-primary); }
}
</style>
