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

    <!-- 历史诊断（下拉刷新 + 无限滚动） -->
    <div class="vct-section-title">📜 历史诊断（{{ total }}）</div>

    <!-- 骨架屏首次加载态 -->
    <SkeletonList v-if="firstLoad" :count="4" />

    <!-- 网络异常 -->
    <div v-if="!firstLoad && networkError" class="empty">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block size="small" @click="onRefresh"
        >重试</van-button
      >
    </div>

    <!-- 列表区域（下拉刷新包裹） -->
    <van-pull-refresh
      v-if="!firstLoad && !networkError"
      v-model="refreshing"
      @refresh="onRefresh"
      success-text="刷新成功"
      :head-height="80"
    >
      <div v-if="list.length === 0" class="empty">
        <van-empty description="还没有诊断记录，去发起第一次吧" />
      </div>
      <van-list
        v-else
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <div class="diag-list">
          <div
            v-for="d in list"
            :key="d.id"
            class="vct-card diag-item"
            @click="goReport(d)"
          >
            <div class="diag-head">
              <span class="platform">{{
                platformLabel(d.video_platform)
              }}</span>
              <span class="status-pill" :class="d.status">{{
                statusLabel(d.status)
              }}</span>
            </div>
            <div class="diag-url">{{ d.video_url }}</div>
            <div class="diag-meta">
              <span>{{ formatTime(d.created_at) }}</span>
              <span>· 配额：{{ d.quota_source }}</span>
              <span v-if="d.progress_pct < 100">· {{ d.progress_pct }}%</span>
            </div>
          </div>
        </div>
      </van-list>
    </van-pull-refresh>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { diagnosisApi } from "@/api";
import { formatTime } from "@video-ct/shared";
import SkeletonList from "@/components/SkeletonList.vue";

const router = useRouter();
const allItems = ref<any[]>([]);
const list = ref<any[]>([]);
const total = ref(0);
const firstLoad = ref(true);
const networkError = ref(false);
const refreshing = ref(false);
const loading = ref(false);
const finished = ref(false);
const page = ref(1);
const PAGE_SIZE = 10;

const PLATFORM_LABELS: Record<string, string> = {
  douyin: "抖音",
  kuaishou: "快手",
  shipinhao: "视频号",
  xiaohongshu: "小红书",
  bilibili: "B站",
  unknown: "其他",
};
const STATUS_LABELS: Record<string, string> = {
  queued: "排队中",
  processing: "诊断中",
  done: "已完成",
  failed: "失败",
};

function platformLabel(p: string) {
  return PLATFORM_LABELS[p] || "其他";
}
function statusLabel(s: string) {
  return STATUS_LABELS[s] || s;
}

function goReport(d: any) {
  if (d.status === "done") router.push(`/report/${d.id}`);
  else router.push(`/diagnose/${d.id}`);
}

/** 全量获取数据，由前端分页展示 */
async function fetchAllItems() {
  networkError.value = false;
  try {
    const data = await diagnosisApi.list();
    allItems.value = data || [];
    total.value = allItems.value.length;
  } catch (e: any) {
    if (!navigator.onLine) networkError.value = true;
    else allItems.value = [];
  }
}

/** 前端分页加载：每次追加 PAGE_SIZE 条 */
function onLoad() {
  const start = (page.value - 1) * PAGE_SIZE;
  const chunk = allItems.value.slice(start, start + PAGE_SIZE);
  if (chunk.length > 0) {
    list.value.push(...chunk);
    page.value++;
  }
  loading.value = false;
  if (list.value.length >= allItems.value.length) {
    finished.value = true;
  }
}

/** 下拉刷新：重新全量获取 + 重置分页 */
async function onRefresh() {
  await fetchAllItems();
  list.value = [];
  page.value = 1;
  finished.value = false;
  // 立即加载第一页
  onLoad();
  refreshing.value = false;
}

onMounted(async () => {
  await fetchAllItems();
  firstLoad.value = false;
  onLoad();
});
</script>

<style lang="scss" scoped>
.page {
  padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px));
}
.cta {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: linear-gradient(
    135deg,
    rgba(0, 122, 255, 0.12),
    rgba(88, 86, 214, 0.12)
  );
  border-color: rgba(0, 122, 255, 0.12);
  cursor: pointer;
  .cta-icon {
    font-size: 32px;
  }
  .cta-text {
    flex: 1;
  }
  .cta-title {
    font-weight: 600;
  }
  .cta-sub {
    font-size: 12px;
    color: var(--mfc-fg-2);
    margin-top: 4px;
  }
}
.empty {
  padding-top: 40px;
}
.diag-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.diag-item {
  cursor: pointer;
}
.diag-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.platform {
  font-size: 12px;
  color: var(--mfc-fg-2);
}
.status-pill {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--mfc-bg-soft);
  &.processing {
    background: rgba(88, 86, 214, 0.12);
    color: var(--mfc-indigo);
  }
  &.done {
    background: rgba(52, 199, 89, 0.12);
    color: var(--mfc-color-success);
  }
  &.failed {
    background: rgba(255, 59, 48, 0.12);
    color: var(--mfc-color-danger);
  }
  &.queued {
    color: var(--mfc-fg-3);
  }
}
.diag-url {
  font-size: 12px;
  color: var(--mfc-fg-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.diag-meta {
  font-size: 11px;
  color: var(--mfc-fg-3);
  margin-top: 6px;
}
</style>
