<template>
  <van-tabbar v-model="active" route active-color="#f59e0b" inactive-color="#6b7280" class="vct-tabbar">
    <van-tabbar-item to="/home" icon="home-o">首页</van-tabbar-item>
    <van-tabbar-item to="/diagnose" icon="bulb-o">诊断</van-tabbar-item>
    <van-tabbar-item to="/subscribe" icon="diamond-o">订阅</van-tabbar-item>
    <van-tabbar-item to="/me" icon="user-o">我的</van-tabbar-item>
  </van-tabbar>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const active = ref(0)
</script>

<style scoped>
.vct-tabbar { backdrop-filter: blur(20px); background: rgba(10,14,26,0.92) !important; border-top: 1px solid var(--vct-border); }
</style>
