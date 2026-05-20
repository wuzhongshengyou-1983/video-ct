<template>
  <div id="vct-root">
    <router-view v-slot="{ Component, route }">
      <transition :name="route.meta.transition as string || 'fade'" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <NavBar v-if="$route.meta.showTabbar" />
  </div>
</template>

<script setup lang="ts">
import NavBar from '@/components/NavBar.vue'
</script>

<style lang="scss" scoped>
#vct-root {
  min-height: 100vh;
  background: linear-gradient(180deg, #0a0e1a 0%, #111827 100%);
  color: #e5e7eb;
  padding-bottom: 64px;
}
.fade-enter-active,.fade-leave-active{ transition: opacity .2s; }
.fade-enter-from,.fade-leave-to{ opacity: 0; }
</style>
