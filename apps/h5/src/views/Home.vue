<template>
  <div class="home">
    <!-- 顶部：身份/欢迎 -->
    <header class="hero">
      <div class="logo">视频 <span>CT</span></div>
      <div class="tagline">像影像科医生一样诊断短视频</div>
      <div class="hero-stats">
        <div class="stat-pill">
          <div class="num">{{ usedCount }}/{{ quota }}</div>
          <div class="label">本月免费扫描</div>
        </div>
        <div class="stat-pill primary">
          <div class="num">{{ tierLabel }}</div>
          <div class="label">当前档位</div>
        </div>
      </div>
    </header>

    <!-- 主 CTA -->
    <section class="cta">
      <div class="vct-card glow main-cta" @click="router.push('/diagnose/submit')">
        <div class="cta-icon">⚡</div>
        <div class="cta-text">
          <div class="cta-title">给你的视频做一次 CT 扫描</div>
          <div class="cta-sub">6 维 18 点位 · 90 秒出报告</div>
        </div>
        <van-icon name="arrow" />
      </div>
    </section>

    <!-- 三大入口 -->
    <section class="grid-3">
      <div class="grid-item" @click="router.push('/persona')">
        <div class="icon">🎭</div>
        <div class="title">人设 IPP</div>
        <div class="sub">12 原型匹配</div>
      </div>
      <div class="grid-item" @click="router.push('/positioning')">
        <div class="icon">💰</div>
        <div class="title">商业 BPS</div>
        <div class="sub">变现路径推荐</div>
      </div>
      <div class="grid-item" @click="router.push('/archive')">
        <div class="icon">📈</div>
        <div class="title">成长档案</div>
        <div class="sub">头部差距进度</div>
      </div>
    </section>

    <!-- 头部对标榜 -->
    <section>
      <div class="vct-section-title">
        🔥 赛道头部对标
        <van-button size="mini" plain @click="router.push('/diagnose')">查看全部</van-button>
      </div>
      <div class="benchmark-list">
        <div v-for="b in benchmarkTop" :key="b.account_id" class="benchmark-item vct-card">
          <div class="rank">#{{ b.rank }}</div>
          <div class="info">
            <div class="name">{{ b.nickname }}</div>
            <div class="meta">{{ b.platform }} · {{ formatNum(b.follower_count) }} 粉</div>
            <div class="archetype">{{ b.style_archetype }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 分享官入口 -->
    <section>
      <div class="vct-card referrer-banner" @click="router.push('/referrer')">
        <div class="banner-left">
          <div class="banner-title">成为品牌分享官</div>
          <div class="banner-sub">拉 1 个朋友付费 = 18 元 · 拉 6 个抵 PRO 月卡</div>
        </div>
        <div class="banner-right">💎</div>
      </div>
    </section>

    <!-- 8 大 AI 专员介绍 -->
    <section>
      <div class="vct-section-title">🤖 8 大 AI 专员 7×24 守在你账号背后</div>
      <div class="agents">
        <div v-for="a in agents" :key="a.name" class="agent-card vct-card">
          <div class="agent-emoji">{{ a.emoji }}</div>
          <div class="agent-name">{{ a.role }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { benchmarkApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const benchmarkTop = ref<any[]>([])
const agents = ref([
  { name: 'CTRadiologist', role: 'CT 诊断官', emoji: '🩺' },
  { name: 'BenchmarkAnalyst', role: '对标分析师', emoji: '📊' },
  { name: 'PersonaScout', role: '人设观察员', emoji: '🎭' },
  { name: 'BizStrategist', role: '商业策略师', emoji: '💎' },
  { name: 'ContentMaker', role: '内容生成手', emoji: '✍️' },
  { name: 'DataSentinel', role: '数据预警员', emoji: '🚨' },
  { name: 'ConsultantCopilot', role: '顾问助理', emoji: '🤝' },
  { name: 'CSButler', role: '客户成功管家', emoji: '⭐' },
])

const usedCount = computed(() => userStore.me?.monthly_free_scans_used ?? 0)
const quota = computed(() => userStore.me?.monthly_free_scans_quota ?? 3)
const tierLabel = computed(() => ({
  free: '免费', pro: 'PRO', max: 'MAX',
}[userStore.tier] || '免费'))

function formatNum(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return String(n)
}

onMounted(async () => {
  try {
    benchmarkTop.value = await benchmarkApi.top10('职场干货')
  } catch { /* ignore */ }
})
</script>

<style lang="scss" scoped>
.home { padding: 16px; }
.hero {
  text-align: center;
  padding: 24px 0 16px;
  .logo {
    font-size: 32px; font-weight: 800; letter-spacing: 2px;
    span { color: var(--vct-primary); text-shadow: 0 0 20px rgba(245,158,11,0.5); }
  }
  .tagline { color: var(--vct-text-2); margin-top: 4px; font-size: 13px; }
  .hero-stats { display: flex; gap: 12px; margin-top: 20px; justify-content: center; }
  .stat-pill {
    padding: 8px 16px; border-radius: 999px; background: var(--vct-surface);
    border: 1px solid var(--vct-border); min-width: 100px;
    .num { font-size: 18px; font-weight: 700; color: var(--vct-text); }
    .label { font-size: 11px; color: var(--vct-text-3); margin-top: 2px; }
    &.primary { border-color: var(--vct-primary); }
    &.primary .num { color: var(--vct-primary); }
  }
}
.main-cta {
  display: flex; align-items: center; gap: 16px;
  background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(56,189,248,0.08));
  border-color: rgba(245,158,11,0.3);
  .cta-icon { font-size: 36px; }
  .cta-text { flex: 1; }
  .cta-title { font-size: 17px; font-weight: 600; }
  .cta-sub { font-size: 12px; color: var(--vct-text-2); margin-top: 4px; }
}
.grid-3 {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px;
  .grid-item {
    background: var(--vct-surface); border-radius: var(--vct-radius);
    padding: 16px 8px; text-align: center; border: 1px solid var(--vct-border);
    .icon { font-size: 28px; }
    .title { font-size: 13px; font-weight: 600; margin-top: 6px; }
    .sub { font-size: 10px; color: var(--vct-text-3); }
  }
}
.benchmark-list {
  display: flex; gap: 12px; overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  &::-webkit-scrollbar { display: none; }
}
.benchmark-item {
  min-width: 200px; display: flex; gap: 10px; align-items: center;
  .rank {
    font-size: 24px; font-weight: 800; color: var(--vct-primary);
    background: linear-gradient(135deg, #f59e0b, #fb923c); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .info { flex: 1; }
  .name { font-size: 14px; font-weight: 600; }
  .meta { font-size: 11px; color: var(--vct-text-3); }
  .archetype { font-size: 11px; color: var(--vct-accent); margin-top: 2px; }
}
.referrer-banner {
  display: flex; align-items: center; gap: 12px; cursor: pointer;
  background: linear-gradient(135deg, rgba(56,189,248,0.12), rgba(245,158,11,0.08));
  border-color: rgba(56,189,248,0.25);
  .banner-left { flex: 1; }
  .banner-title { font-weight: 600; }
  .banner-sub { font-size: 11px; color: var(--vct-text-2); margin-top: 4px; }
  .banner-right { font-size: 36px; }
}
.agents {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  .agent-card { text-align: center; padding: 12px 4px; }
  .agent-emoji { font-size: 24px; }
  .agent-name { font-size: 11px; color: var(--vct-text-2); margin-top: 4px; }
}
</style>
