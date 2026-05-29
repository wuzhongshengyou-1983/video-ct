<template>
  <svg :viewBox="`0 0 ${size} ${size}`" class="radar">
    <!-- 网格 -->
    <polygon
      v-for="(r, i) in [0.25, 0.5, 0.75, 1]"
      :key="i"
      :points="gridPoints(r)"
      fill="none"
      stroke="rgba(0,0,0,0.08)"
      stroke-width="1"
    />
    <!-- 轴 -->
    <line
      v-for="(a, i) in angles"
      :key="`l${i}`"
      :x1="center.x"
      :y1="center.y"
      :x2="center.x + Math.cos(a) * radius"
      :y2="center.y + Math.sin(a) * radius"
      stroke="rgba(0,0,0,0.08)"
      stroke-width="1"
    />
    <!-- 数据多边形 -->
    <polygon
      :points="dataPoints"
      fill="rgba(245,158,11,0.25)"
      stroke="#f59e0b"
      stroke-width="2"
    />
    <!-- 数据点 -->
    <circle
      v-for="(p, i) in dataDots"
      :key="`d${i}`"
      :cx="p.x"
      :cy="p.y"
      r="4"
      fill="#fbbf24"
    />
    <!-- 标签 -->
    <text
      v-for="(label, i) in labels"
      :key="`t${i}`"
      :x="labelPos(i).x"
      :y="labelPos(i).y"
      text-anchor="middle"
      dominant-baseline="middle"
      fill="#9ca3af"
      font-size="11"
    >
      {{ label }}
    </text>
    <!-- 分数 -->
    <text
      v-for="(label, i) in labels"
      :key="`s${i}`"
      :x="scorePos(i).x"
      :y="scorePos(i).y"
      text-anchor="middle"
      dominant-baseline="middle"
      fill="#f59e0b"
      font-size="11"
      font-weight="700"
    >
      {{ scores[label] ?? 0 }}
    </text>
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ scores: Record<string, number> }>();

const size = 280;
const center = { x: size / 2, y: size / 2 };
const radius = 90;

const labels = computed(() => Object.keys(props.scores));
const count = computed(() => labels.value.length || 6);

const angles = computed(() => {
  const arr: number[] = [];
  for (let i = 0; i < count.value; i++) {
    arr.push(-Math.PI / 2 + (i / count.value) * 2 * Math.PI);
  }
  return arr;
});

function gridPoints(r: number) {
  return angles.value
    .map((a) => {
      const x = center.x + Math.cos(a) * radius * r;
      const y = center.y + Math.sin(a) * radius * r;
      return `${x},${y}`;
    })
    .join(" ");
}

const dataPoints = computed(() => {
  return labels.value
    .map((lbl, i) => {
      const score = (props.scores[lbl] ?? 0) / 100;
      const a = angles.value[i];
      const x = center.x + Math.cos(a) * radius * score;
      const y = center.y + Math.sin(a) * radius * score;
      return `${x},${y}`;
    })
    .join(" ");
});
const dataDots = computed(() => {
  return labels.value.map((lbl, i) => {
    const score = (props.scores[lbl] ?? 0) / 100;
    const a = angles.value[i];
    return {
      x: center.x + Math.cos(a) * radius * score,
      y: center.y + Math.sin(a) * radius * score,
    };
  });
});

function labelPos(i: number) {
  const a = angles.value[i];
  return {
    x: center.x + Math.cos(a) * (radius + 28),
    y: center.y + Math.sin(a) * (radius + 28),
  };
}
function scorePos(i: number) {
  const a = angles.value[i];
  return {
    x: center.x + Math.cos(a) * (radius + 16),
    y: center.y + Math.sin(a) * (radius + 16),
  };
}
</script>

<style scoped>
.radar {
  width: 100%;
  height: auto;
}
</style>
