<template>
  <div class="page">
    <div class="invite-hero">
      <div class="logo">视频 <span>CT</span></div>
      <div class="tag">用医学 CT 方式诊断你的短视频</div>

      <div v-if="refCode" class="ref-card vct-card glow">
        <div class="ref-icon">🎁</div>
        <div class="ref-text">受 <strong>{{ refCode }}</strong> 邀请</div>
        <div class="ref-benefit">注册即享首单 9 折优惠</div>
      </div>

      <div class="features">
        <div class="feature-item">
          <div class="icon">🩺</div>
          <div class="title">AI 视频诊断</div>
          <div class="desc">6 维 18 点位深度扫描</div>
        </div>
        <div class="feature-item">
          <div class="icon">📊</div>
          <div class="title">赛道对标</div>
          <div class="desc">与头部差距一目了然</div>
        </div>
        <div class="feature-item">
          <div class="icon">🎭</div>
          <div class="title">人设定位</div>
          <div class="desc">12 原型精准匹配</div>
        </div>
      </div>

      <van-button type="primary" block size="large" @click="goLogin">
        登录 / 注册，开始诊断
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const refCode = ref<string | null>(null)

onMounted(() => {
  const code = route.query.ref as string
  if (code) {
    refCode.value = code
    localStorage.setItem('vct_ref', code)
  } else {
    refCode.value = localStorage.getItem('vct_ref')
  }
})

function goLogin() {
  router.push({ path: '/login', query: { ref: refCode.value || undefined } })
}
</script>

<style lang="scss" scoped>
.page { min-height: 100vh; padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); }
.invite-hero { text-align: center; padding: 60px 0 40px; }
.logo {
  font-size: 42px; font-weight: 800; letter-spacing: 3px;
  span { color: var(--vct-primary); text-shadow: 0 0 24px rgba(245,158,11,0.5); }
}
.tag { font-size: 14px; color: var(--vct-text-2); margin-top: 8px; }

.ref-card {
  margin: 32px 0; padding: 20px;
  background: linear-gradient(135deg, rgba(56,189,248,0.12), rgba(245,158,11,0.08));
  border-color: rgba(56,189,248,0.3);
  .ref-icon { font-size: 36px; }
  .ref-text { font-size: 16px; font-weight: 600; margin: 8px 0 4px;
    strong { color: var(--vct-primary); }
  }
  .ref-benefit { font-size: 12px; color: var(--vct-accent); }
}

.features {
  display: flex; justify-content: space-around; margin: 32px 0;
  .feature-item { text-align: center; }
  .icon { font-size: 32px; }
  .title { font-size: 14px; font-weight: 600; margin: 8px 0 4px; }
  .desc { font-size: 11px; color: var(--vct-text-3); }
}
</style>
