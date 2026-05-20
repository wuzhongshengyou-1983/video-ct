<template>
  <div class="page">
    <van-nav-bar title="诊断进行中" left-arrow @click-left="router.replace('/diagnose')" :border="false" />

    <div class="status vct-card">
      <div class="circle" :class="statusClass">
        <div class="progress-text">{{ diag?.progress_pct ?? 0 }}%</div>
      </div>
      <div class="status-text">
        <div class="status-title">{{ statusTitle }}</div>
        <div class="status-sub">{{ statusSub }}</div>
      </div>
    </div>

    <div class="steps">
      <div v-for="(s, i) in steps" :key="i" class="step" :class="stepCls(i)">
        <div class="step-dot">{{ i + 1 }}</div>
        <div class="step-text">
          <div class="step-title">{{ s.title }}</div>
          <div class="step-sub">{{ s.sub }}</div>
        </div>
      </div>
    </div>

    <div v-if="diag?.status === 'done'" class="action">
      <van-button type="primary" block @click="router.replace(`/report/${id}`)">
        查看完整 CT 报告
      </van-button>
    </div>
    <div v-else-if="diag?.status === 'failed'" class="action">
      <van-empty image="error" description="诊断失败" />
      <div class="err">{{ diag?.error }}</div>
      <van-button block @click="router.replace('/diagnose/submit')">重新提交</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { diagnosisApi } from '@/api'
import { DIAGNOSIS_STATUS } from '@video-ct/shared'

const router = useRouter()
const route = useRoute()
const id = computed(() => route.params.id as string)
const diag = ref<any | null>(null)
let timer: ReturnType<typeof setInterval> | null = null

const steps = [
  { title: '抓取视频元数据', sub: '标题、时长、播放数、互动数' },
  { title: 'OCR + ASR 解析', sub: '封面/字幕识别 + 语音转写' },
  { title: '调用 CT 诊断官 Agent', sub: '6 维 18 点位扫描' },
  { title: '生成完整报告', sub: '病灶定位 + 修复建议 + 头部差距' },
]

const statusTitle = computed(() => ({
  queued: '已排队，等待启动',
  processing: 'AI 正在 CT 扫描你的视频',
  done: '✅ 诊断完成',
  failed: '❌ 诊断失败',
}[diag.value?.status as string] || '加载中…'))

const statusSub = computed(() => {
  if (!diag.value) return ''
  if (diag.value.status === 'processing') return '通常 60-180 秒，请耐心等待'
  if (diag.value.status === 'done') return '点击下方按钮查看完整 6 维报告'
  if (diag.value.status === 'failed') return diag.value.error || '请重试'
  return ''
})

const statusClass = computed(() => ({
  queued: 'idle',
  processing: 'busy',
  done: 'ok',
  failed: 'err',
}[diag.value?.status as string] || 'idle'))

function stepCls(i: number) {
  const p = diag.value?.progress_pct ?? 0
  if (p >= (i + 1) * 25) return 'done'
  if (p >= i * 25) return 'active'
  return ''
}

async function poll() {
  try {
    const data = await diagnosisApi.get(id.value)
    diag.value = data
    if ([DIAGNOSIS_STATUS.COMPLETED, DIAGNOSIS_STATUS.FAILED].includes(data.status)) {
      timer && clearInterval(timer)
      timer = null
    }
  } catch { /* ignore */ }
}

onMounted(async () => {
  await poll()
  if (!['done', 'failed'].includes(diag.value?.status)) {
    timer = setInterval(poll, 3000)
  }
})
onUnmounted(() => { timer && clearInterval(timer) })
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); }
.status {
  display: flex; gap: 20px; align-items: center; padding: 24px 16px; margin-top: 12px;
}
.circle {
  width: 96px; height: 96px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 22px;
  background: conic-gradient(var(--vct-primary) 0deg, var(--vct-surface) 0deg);
  &.idle { color: var(--vct-text-3); }
  &.busy { animation: spin 8s linear infinite; color: var(--vct-primary); }
  &.ok { background: var(--vct-success); color: #fff; }
  &.err { background: var(--vct-danger); color: #fff; }
  .progress-text {
    background: var(--vct-bg); width: 70px; height: 70px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
  }
}
@keyframes spin { to { transform: rotate(360deg); } }

.status-text { flex: 1; }
.status-title { font-size: 16px; font-weight: 600; }
.status-sub { font-size: 12px; color: var(--vct-text-2); margin-top: 4px; }

.steps { padding: 20px 16px; }
.step {
  display: flex; gap: 12px; padding: 14px 0;
  border-bottom: 1px dashed var(--vct-border);
  opacity: 0.5;
  &.active { opacity: 1; }
  &.done { opacity: 1;
    .step-dot { background: var(--vct-success); }
  }
  &:last-child { border-bottom: none; }
}
.step-dot {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--vct-surface); border: 1px solid var(--vct-border);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600;
}
.step-title { font-size: 14px; }
.step-sub { font-size: 11px; color: var(--vct-text-3); margin-top: 2px; }

.action { padding: 24px 16px; }
.err { color: var(--vct-danger); margin: 12px 0; text-align: center; font-size: 12px; }
</style>
