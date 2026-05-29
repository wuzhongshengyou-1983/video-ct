<template>
  <div id="vct-root">
    <router-view v-slot="{ Component, route }">
      <transition
        :name="(route.meta.transition as string) || 'fade'"
        mode="out-in"
      >
        <component :is="Component" />
      </transition>
    </router-view>
    <NavBar v-if="$route.meta.showTabbar" />
    <footer class="icp-footer">蜀ICP备2026010386号-1</footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import NavBar from "@/components/NavBar.vue";
import { useWechatShare } from "@/composables/useWechatShare";

// 全局默认分享卡片（各页面可通过路由变更时重新 setWxShare 覆盖）
const { updateShare } = useWechatShare();
onMounted(() => {
  updateShare(
    "给你的短视频做一次 CT 扫描",
    "6 维 18 点位，90 秒出报告，AI 驱动的短视频诊断工具",
  );
});
</script>

<style lang="scss" scoped>
#vct-root {
  min-height: 100vh;
  background: var(--mfc-bg-soft);
  color: var(--mfc-fg);
  padding-bottom: 64px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.icp-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 10px;
  color: var(--mfc-fg-4);
  padding: 4px 0;
  background: transparent;
  pointer-events: none;
  z-index: 10;
}
</style>
