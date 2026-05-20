<template>
  <div class="page">
    <div class="not-found">
      <div class="code">404</div>
      <div class="message">页面不存在</div>
      <div class="sub">你访问的页面已离开地球轨道</div>
      <van-button type="primary" round size="large" @click="router.replace('/home')">
        返回首页
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 24px 24px calc(24px + env(safe-area-inset-bottom, 0px));
}
.not-found { text-align: center; }
.code {
  font-size: 100px; font-weight: 900; line-height: 1;
  background: linear-gradient(135deg, #f59e0b, #fbbf24, #38bdf8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.message { font-size: 20px; font-weight: 600; margin: 16px 0 8px; }
.sub { font-size: 13px; color: var(--vct-text-2); margin-bottom: 32px; }
</style>
