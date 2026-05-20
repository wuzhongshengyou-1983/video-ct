<template>
  <div class="skeleton-card vct-card">
    <div v-for="i in lines" :key="i" class="skeleton-line" :style="{ width: lineWidth(i) }" />
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ lines?: number }>(), { lines: 3 })

function lineWidth(i: number): string {
  if (i === props.lines && props.lines > 1) return '60%'
  if (i === 1) return '80%'
  return '100%'
}
</script>

<style lang="scss" scoped>
.skeleton-card {
  padding: 16px;
  border-color: rgba(255, 255, 255, 0.04);
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  animation: vct-skeleton-pulse 1.6s ease-in-out infinite;

  + .skeleton-line {
    margin-top: 10px;
  }
}

@keyframes vct-skeleton-pulse {
  0%, 100% { opacity: 0.4; }
  50%      { opacity: 0.8; }
}
</style>
