<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const form = reactive({ phone: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.phone || !form.password) return
  loading.value = true
  try {
    await authStore.login(form)
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <a-card class="login-card" :bordered="false">
      <div class="login-header">
        <h1>视频 CT</h1>
        <p>管理后台</p>
      </div>
      <a-form
        :model="form"
        name="login"
        layout="vertical"
        @finish="handleLogin"
        autocomplete="off"
      >
        <a-form-item name="phone" :rules="[{ required: true, message: '请输入手机号' }]">
          <a-input v-model:value="form.phone" placeholder="手机号" size="large">
            <template #prefix><UserOutlined /></template>
          </a-input>
        </a-form-item>
        <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
          <a-input-password v-model:value="form.password" placeholder="密码" size="large">
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" block size="large" :loading="loading">
            登录
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<style lang="scss" scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: var(--bg-secondary) !important;

  .login-header {
    text-align: center;
    margin-bottom: 32px;
    h1 {
      font-size: 28px;
      color: var(--color-primary);
      font-weight: 700;
    }
    p {
      color: var(--text-secondary);
      margin-top: 8px;
      font-size: 14px;
    }
  }
}
</style>
