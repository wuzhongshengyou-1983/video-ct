<template>
  <div class="page">
    <van-nav-bar title="诊断中心" :border="false" />

    <!-- 顶部 CTA -->
    <div class="vct-card cta" @click="router.push('/diagnose/submit')">
      <div class="cta-icon">⚡</div>
      <div class="cta-text">
        <div class="cta-title">新建诊断</div>
        <div class="cta-sub">粘贴视频链接，AI 30 秒出报告</div>
      </div>
      <van-icon name="arrow" />
    </div>

    <!-- 历史诊断 -->
    <div class="vct-section-title">📜 历史诊断（{{ list.length }}）</div>
    <div v-if="list.length === 0 && !networkError" class="empty">
      <van-empty description="还没有诊断记录，去发起第一次吧" />
    </div>
    <div v-if="networkError" class="empty">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block size="small" @click="fetchList">重试</van-button>
    </div>
    <div v-else class="diag-list">
      <div
        v-for="d in list"
        :key="d.id"
        class="vct-card diag-item"
        @click="goReport(d)"
      >
        <div class="diag-head">
          <span class="platform">{{ platformLabel(d.video_platform) }}</span>
          <span class="status-pill" :class="d.status">{{ statusLabel(d.status) }}</span>
        </div>
        <div class="diag-url">{{ d.video_url }}</div>
        <div class="diag-meta">
          <span>{{ formatTime(d.created_at) }}</span>
          <span>· 配额：{{ d.quota_source }}</span>
          <span v-if="d.progress_pct < 100">· {{ d.progress_pct }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { diagnosisApi } from '@/api'
import { formatTime } from '@video-ct/shared'

const router = useRouter()
const list = ref<any[]>([])
const networkError = ref(false)

const PLATFORM_LABELS: Record<string, string> = {
  douyin: '抖音', kuaishou: '快手', shipinhao: '视频号', xiaohongshu: '小红书', bilibili: 'B站', unknown: '其他',
}
const STATUS_LABELS: Record<string, string> = {
  queued: '排队中', processing: '诊断中', done: '已完成', failed: '失败',
}

function platformLabel(p: string) { return PLATFORM_LABELS[p] || '其他' }
function statusLabel(s: string) { return STATUS_LABELS[s] || s }

function goReport(d: any) {
  if (d.status === 'done') router.push(`/report/${d.id}`)
  else router.push(`/diagnose/${d.id}`)
}

async function fetchList() {
  networkError.value = false
  try {
    const data = await diagnosisApi.list()
    list.value = data || []
  } catch (e: any) {
    if (!navigator.onLine) networkError.value = true
    else list.value = []
  }
}

onMounted(fetchList)
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); }
.cta {
  display: flex; align-items: center; gap: 14px; padding: 16px;
  background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(56,189,248,0.08));
  border-color: rgba(245,158,11,0.3); cursor: pointer;
  .cta-icon { font-size: 32px; }
  .cta-text { flex: 1; }
  .cta-title { font-weight: 600; }
  .cta-sub { font-size: 12px; color: var(--vct-text-2); margin-top: 4px; }
}
.empty { padding-top: 40px; }
.diag-list { display: flex; flex-direction: column; gap: 10px; }
.diag-item { cursor: pointer; }
.diag-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.platform { font-size: 12px; color: var(--vct-text-2); }
.status-pill {
  font-size: 11px; padding: 2px 8px; border-radius: 999px;
  background: var(--vct-surface);
  &.processing { background: rgba(56,189,248,0.15); color: var(--vct-accent); }
  &.done { background: rgba(16,185,129,0.15); color: var(--vct-success); }
  &.failed { background: rgba(239,68,68,0.15); color: var(--vct-danger); }
  &.queued { color: var(--vct-text-3); }
}
.diag-url {
  font-size: 12px; color: var(--vct-text-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.diag-meta { font-size: 11px; color: var(--vct-text-3); margin-top: 6px; }
</style>
