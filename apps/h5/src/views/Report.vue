<template>
  <div class="page">
    <van-nav-bar title="CT 诊断报告" left-arrow @click-left="router.replace('/diagnose')" :border="false">
      <template #right>
        <van-icon name="share-o" size="20" @click="share" />
      </template>
    </van-nav-bar>

    <div v-if="report" class="report">
      <!-- 总评 -->
      <section class="vct-card glow score-card">
        <div class="grade-badge">{{ report.grade }}</div>
        <div class="overall-num">{{ report.overall_score }}</div>
        <div class="overall-label">综合 CT 分</div>
        <div v-if="report.summary" class="summary">{{ report.summary }}</div>
      </section>

      <!-- 雷达图（简易 SVG） -->
      <section class="vct-card">
        <div class="vct-section-title">📡 6 维雷达图</div>
        <RadarChart :scores="dimScores" />
      </section>

      <!-- 各维度详情 -->
      <section v-for="(d, key) in report.dimensions" :key="key" class="vct-card dim-card">
        <div class="dim-head">
          <span class="dim-name">{{ key }}</span>
          <span class="dim-score" :class="scoreCls(d.score)">{{ d.score }}</span>
        </div>
        <div v-if="d.advantages?.length" class="dim-block">
          <div class="block-title">✓ 优势</div>
          <ul><li v-for="a in d.advantages" :key="a">{{ a }}</li></ul>
        </div>
        <div v-if="d.findings?.length" class="dim-block warning">
          <div class="block-title">⚠ 病灶</div>
          <ul><li v-for="f in d.findings" :key="f">{{ f }}</li></ul>
        </div>
        <div v-if="d.suggestions?.length" class="dim-block primary">
          <div class="block-title">💡 修复建议</div>
          <ul><li v-for="s in d.suggestions" :key="s">{{ s }}</li></ul>
        </div>
      </section>

      <!-- 病灶时间戳 -->
      <section v-if="report.findings?.length" class="vct-card">
        <div class="vct-section-title">⏱ 关键病灶时间戳</div>
        <div v-for="(f, i) in report.findings" :key="i" class="finding-item">
          <div class="ts">{{ f.timestamp }}</div>
          <div class="finding-text">
            <div class="finding-dim"><span class="vct-tag">{{ f.dimension }}</span></div>
            <div class="finding-problem">{{ f.problem }}</div>
            <div class="finding-suggest">💡 {{ f.suggestion }}</div>
          </div>
        </div>
      </section>

      <!-- 修复建议优先级 -->
      <section v-if="report.suggestions?.length" class="vct-card">
        <div class="vct-section-title">🎯 修复优先级</div>
        <div v-for="(s, i) in report.suggestions" :key="i" class="suggest-item">
          <div class="suggest-head">
            <span class="vct-tag" :class="prioCls(s.priority)">{{ s.priority }}</span>
            <span class="suggest-title">{{ s.title }}</span>
          </div>
          <div class="suggest-block"><b>做什么：</b>{{ s.what }}</div>
          <div class="suggest-block"><b>怎么做：</b>{{ s.how }}</div>
          <div class="suggest-block"><b>为什么：</b>{{ s.why }}</div>
        </div>
      </section>

      <!-- 头部差距 -->
      <section v-if="hasGap" class="vct-card">
        <div class="vct-section-title">📊 与赛道头部差距</div>
        <div v-for="(v, k) in report.benchmark_gap" :key="k" class="gap-item">
          <div class="gap-label">{{ k.replace('_gap_pct', '').replace('_', '') }}</div>
          <div class="gap-bar">
            <div
              class="gap-fill"
              :class="(v as number) < 0 ? 'neg' : 'pos'"
              :style="{ width: Math.min(100, Math.abs(v as number)) + '%' }"
            />
          </div>
          <div class="gap-val">{{ v }}%</div>
        </div>
      </section>

      <!-- 反馈 -->
      <section class="vct-card">
        <div class="vct-section-title">📝 报告好不好用？</div>
        <van-rate v-model="rating" size="28" color="#f59e0b" gutter="8" />
        <van-field
          v-model="feedback"
          placeholder="（可选）告诉我们哪里不准 / 哪里有用，AI 会变得更聪明"
          autosize
          type="textarea"
          rows="2"
          class="feedback-input"
        />
        <van-button block type="primary" size="small" @click="submitFeedback" :disabled="rating === 0">
          提交反馈
        </van-button>
      </section>
    </div>

    <van-loading v-else size="24" vertical>加载报告中…</van-loading>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Toast } from 'vant'
import { diagnosisApi } from '@/api'
import RadarChart from '@/components/RadarChart.vue'

const router = useRouter()
const route = useRoute()
const id = route.params.id as string

const report = ref<any | null>(null)
const rating = ref(0)
const feedback = ref('')

const dimScores = computed(() => {
  if (!report.value) return {}
  return Object.fromEntries(
    Object.entries(report.value.dimensions).map(([k, v]: any) => [k, v.score])
  )
})
const hasGap = computed(() => report.value?.benchmark_gap && Object.keys(report.value.benchmark_gap).length > 0)

function scoreCls(n: number) {
  if (n >= 85) return 'excellent'
  if (n >= 70) return 'good'
  if (n >= 50) return 'fair'
  return 'poor'
}
function prioCls(p: string) {
  return p === 'P0' ? 'p0' : p === 'P1' ? 'p1' : 'p2'
}

async function submitFeedback() {
  try {
    await diagnosisApi.feedback(id, rating.value, feedback.value)
    Toast.success('谢谢反馈！AI 会更聪明')
  } catch (e: any) {
    Toast.fail(e.message || '提交失败')
  }
}

function share() {
  Toast('长按截图分享，或复制邀请链接到朋友圈')
}

onMounted(async () => {
  try {
    report.value = await diagnosisApi.report(id)
  } catch (e: any) {
    Toast.fail(e.message || '报告未生成')
    router.replace(`/diagnose/${id}`)
  }
})
</script>

<style lang="scss" scoped>
.page { padding-bottom: 24px; }
.report > section { margin: 12px 16px; }
.score-card {
  text-align: center; padding: 32px 16px;
  background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(56,189,248,0.08));
}
.grade-badge {
  display: inline-block; padding: 4px 12px; background: var(--vct-primary);
  color: #fff; border-radius: 999px; font-size: 12px; font-weight: 600;
}
.overall-num {
  font-size: 72px; font-weight: 800; line-height: 1; margin: 12px 0 4px;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.overall-label { color: var(--vct-text-2); font-size: 13px; }
.summary { margin-top: 16px; font-size: 13px; color: var(--vct-text); line-height: 1.6; }

.dim-card { padding: 16px; }
.dim-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.dim-name { font-size: 16px; font-weight: 600; }
.dim-score {
  font-size: 28px; font-weight: 800;
  &.excellent { color: #10b981; }
  &.good { color: #38bdf8; }
  &.fair { color: #f59e0b; }
  &.poor { color: #ef4444; }
}
.dim-block { margin-top: 12px;
  .block-title { font-size: 12px; color: var(--vct-text-2); margin-bottom: 6px; }
  ul { margin: 0; padding-left: 18px; font-size: 13px; color: var(--vct-text); line-height: 1.7; }
  &.warning .block-title { color: var(--vct-warning); }
  &.primary .block-title { color: var(--vct-primary); }
}

.finding-item {
  display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px dashed var(--vct-border);
  &:last-child { border-bottom: none; }
  .ts {
    font-family: monospace; font-weight: 600; color: var(--vct-accent);
    min-width: 50px;
  }
  .finding-problem { font-size: 13px; margin-top: 6px; }
  .finding-suggest { font-size: 12px; color: var(--vct-text-2); margin-top: 4px; }
}

.suggest-item {
  padding: 14px 0; border-bottom: 1px dashed var(--vct-border);
  &:last-child { border-bottom: none; }
  .suggest-head { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
  .vct-tag.p0 { background: rgba(239,68,68,0.15); color: #ef4444; }
  .vct-tag.p1 { background: rgba(245,158,11,0.15); color: #f59e0b; }
  .vct-tag.p2 { background: rgba(107,114,128,0.15); color: #9ca3af; }
  .suggest-title { font-weight: 600; }
  .suggest-block { font-size: 12px; color: var(--vct-text-2); margin: 4px 0;
    b { color: var(--vct-text); }
  }
}

.gap-item {
  display: grid; grid-template-columns: 80px 1fr 50px; align-items: center; gap: 8px; padding: 6px 0;
  .gap-label { font-size: 12px; color: var(--vct-text-2); }
  .gap-bar { height: 8px; background: var(--vct-surface); border-radius: 4px; overflow: hidden; }
  .gap-fill.neg { background: var(--vct-danger); margin-left: auto; }
  .gap-fill.pos { background: var(--vct-success); }
  .gap-val { font-size: 12px; font-weight: 600; text-align: right; }
}

.feedback-input { margin: 12px 0; }
</style>
