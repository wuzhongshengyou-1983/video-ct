<template>
  <div class="page">
    <van-nav-bar title="个人资料" left-arrow @click-left="router.back()" :border="false" />

    <van-loading v-if="loading" size="24" vertical class="loading-center">加载中…</van-loading>

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="loadProfile">重试</van-button>
    </div>

    <template v-if="!loading && !networkError">
      <div class="form-section">
        <van-field
          v-model="form.nickname"
          label="昵称"
          placeholder="你的昵称"
          maxlength="20"
          :error="errors.nickname"
          :error-message="errors.nickname"
          @update:model-value="errors.nickname = ''"
        />
        <van-field
          v-model="form.track"
          label="赛道"
          placeholder="如：职场干货、美妆教程"
        />
        <van-field
          v-model="form.platform"
          label="主平台"
          placeholder="如：抖音、B站"
        />
        <van-field
          v-model="form.follower_count"
          label="粉丝数"
          placeholder="输入数字"
          type="number"
          :error="errors.follower_count"
          :error-message="errors.follower_count"
          @update:model-value="errors.follower_count = ''"
        />
        <van-field
          v-model="form.bio"
          label="简介"
          placeholder="简单介绍你的账号定位"
          type="textarea"
          rows="3"
          autosize
        />
        <van-field
          v-model="form.goal"
          label="目标"
          placeholder="你的短视频目标（如：百万粉、月入5万）"
          type="textarea"
          rows="2"
          autosize
        />
      </div>

      <div class="save-section">
        <van-button type="primary" block size="large" :loading="saving" @click="save">
          保存
        </van-button>
      </div>
    </template>

    <!-- 服务端错误 -->
    <div v-if="!loading && serverError" class="error-box vct-card">
      <p>{{ serverError }}</p>
      <van-button size="small" @click="loadProfile">重试</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Toast } from 'vant'
import { userApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { formatFollowerCount } from '@video-ct/shared'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const networkError = ref(false)
const serverError = ref('')
const saving = ref(false)

const form = reactive({
  nickname: '',
  track: '',
  platform: '',
  follower_count: '',
  bio: '',
  goal: '',
})

const errors = reactive({
  nickname: '',
  follower_count: '',
})

function loadProfile() {
  loading.value = true
  networkError.value = false
  serverError.value = ''
  try {
    const me = userStore.me
    if (me) {
      form.nickname = me.nickname || ''
      form.track = me.track || ''
      form.platform = me.platform || me.platform_main || ''
      form.follower_count = me.follower_count ? String(me.follower_count) : ''
      form.bio = me.bio || ''
      form.goal = me.goal || me.goals || ''
    } else {
      // no user data yet, not a network error
    }
  } catch {
    networkError.value = true
  } finally {
    loading.value = false
  }
}

function validate(): boolean {
  let valid = true

  if (!form.nickname.trim()) {
    errors.nickname = '请输入昵称'
    valid = false
  }

  if (form.follower_count) {
    const n = Number(form.follower_count)
    if (isNaN(n) || n < 0) {
      errors.follower_count = '请输入有效的粉丝数'
      valid = false
    } else if (n > 999_999_999) {
      errors.follower_count = '粉丝数不能超过 10 亿'
      valid = false
    }
  }

  return valid
}

async function save() {
  if (!validate()) return

  saving.value = true
  try {
    const payload: Record<string, any> = {}
    if (form.nickname) payload.nickname = form.nickname.trim()
    if (form.track) payload.track = form.track.trim()
    if (form.platform) payload.platform = form.platform.trim()
    if (form.follower_count) payload.follower_count = Number(form.follower_count)
    if (form.bio) payload.bio = form.bio.trim()
    if (form.goal) payload.goal = form.goal.trim()

    await userApi.updateProfile(payload)
    Toast.success('保存成功')
    await userStore.fetchMe()
    router.back()
  } catch (e: any) {
    if (!navigator.onLine) {
      Toast.fail('网络异常，请检查网络后重试')
    } else if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<style lang="scss" scoped>
.page { padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px)); min-height: 100vh; }
.loading-center { padding-top: 120px; display: flex; justify-content: center; }

.form-section {
  margin: 0; scroll-margin-bottom: 40vh;
  :deep(.van-cell) {
    padding: 14px 16px;
  }
}

.save-section { padding: 24px 16px; }

.error-box { margin: 24px 16px; text-align: center; padding: 24px;
  p { color: var(--vct-danger); font-size: 13px; margin-bottom: 12px; }
}
</style>
