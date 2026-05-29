<template>
  <van-tabbar
    v-model="active"
    route
    active-color="var(--mfc-blue)"
    inactive-color="var(--mfc-fg-3)"
    class="vct-tabbar"
  >
    <van-tabbar-item to="/home" icon="home-o">首页</van-tabbar-item>
    <van-tabbar-item to="/diagnose" icon="bulb-o">诊断</van-tabbar-item>
    <van-tabbar-item to="/subscribe" icon="diamond-o">订阅</van-tabbar-item>
    <van-tabbar-item to="/me" icon="user-o">我的</van-tabbar-item>
  </van-tabbar>
</template>

<script setup lang="ts">
import { ref } from "vue";
const active = ref(0);
</script>

<style scoped>
.vct-tabbar {
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  background: rgba(255, 255, 255, 0.85) !important;
  border-top: 0.5px solid var(--mfc-hairline);
}
</style>
