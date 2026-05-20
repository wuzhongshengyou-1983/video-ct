<template>
  <div class="skeleton-list">
    <SkeletonCard v-for="i in count" :key="i" :lines="lines" />
  </div>
</template>

<script setup lang="ts">
import SkeletonCard from './SkeletonCard.vue'

withDefaults(defineProps<{ count?: number; lines?: number }>(), { count: 5, lines: 3 })
</script>

<style lang="scss" scoped>
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
