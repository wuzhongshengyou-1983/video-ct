<template>
  <div class="page">
    <van-nav-bar
      title="成长档案"
      left-arrow
      @click-left="router.back()"
      :border="false"
    />

    <!-- 骨架屏加载 -->
    <SkeletonCard v-if="loading" :lines="5" />

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchData">重试</van-button>
    </div>

    <!-- 下拉刷新 -->
    <van-pull-refresh
      v-if="!loading && !networkError && !serverError"
      v-model="refreshing"
      @refresh="onRefresh"
      success-text="刷新成功"
      :head-height="80"
    >
      <!-- 无档案引导 -->
      <div v-if="!archive" class="empty-guide">
        <van-empty image="search" description="还没有成长档案">
          <template #bottom>
            <p class="guide-text">
              先去做一次视频 CT 诊断，系统会自动为你建立成长档案
            </p>
            <van-button
              type="primary"
              round
              @click="router.push('/diagnose/submit')"
            >
              立即诊断
            </van-button>
          </template>
        </van-empty>
      </div>

      <!-- 档案内容 -->
      <template v-if="archive">
        <!-- 基本档案 -->
        <section class="vct-card glow info-card">
          <div class="archive-no">
            档案编号：{{ archive.archive_no || "-" }}
          </div>
          <div class="meta-row">
            <div class="meta-item">
              <div class="meta-value">{{ archive.track || "未设置" }}</div>
              <div class="meta-label">赛道</div>
            </div>
            <div class="meta-item">
              <div
                class="meta-value level-badge"
                :class="levelCls(archive.current_level)"
              >
                {{ archive.current_level || "L1" }}
              </div>
              <div class="meta-label">当前等级</div>
            </div>
            <div class="meta-item">
              <div class="meta-value">{{ archive.total_diagnoses || 0 }}</div>
              <div class="meta-label">总诊断数</div>
            </div>
          </div>
        </section>

        <!-- 成长曲线 -->
        <section v-if="curveData" class="vct-card">
          <div class="vct-section-title">📈 成长曲线</div>

          <!-- 等级历史 -->
          <div class="curve-block">
            <div class="block-label">等级变化</div>
            <div class="level-timeline">
              <div
                v-for="(l, i) in curveData.level_history"
                :key="i"
                class="level-dot-row"
              >
                <div
                  class="dot"
                  :class="{ active: i === curveData.level_history.length - 1 }"
                ></div>
                <div class="level-info">
                  <span class="lv">{{ l.level }}</span>
                  <span class="date">{{ formatDate(l.date) }}</span>
                </div>
              </div>
              <div v-if="!curveData.level_history?.length" class="no-data">
                暂无数据
              </div>
            </div>
          </div>

          <!-- 六维指标变化 -->
          <div class="curve-block">
            <div class="block-label">六维评分趋势</div>
            <div v-if="dimTrends.length" class="dim-trends">
              <div v-for="d in dimTrends" :key="d.name" class="trend-row">
                <div class="trend-name">{{ d.name }}</div>
                <div class="trend-bar-wrap">
                  <div
                    class="trend-bar"
                    :class="trendClass(d.delta)"
                    :style="{ width: Math.min(100, Math.abs(d.latest)) + '%' }"
                  ></div>
                </div>
                <div class="trend-val">{{ d.latest }}</div>
                <div class="trend-delta" :class="trendClass(d.delta)">
                  {{ d.delta >= 0 ? "+" : "" }}{{ d.delta }}
                </div>
              </div>
            </div>
            <div v-else class="no-data">暂无趋势数据</div>
          </div>
        </section>

        <!-- 曲线数据为空 -->
        <section v-else class="vct-card">
          <div class="vct-section-title">📈 成长曲线</div>
          <div class="empty-curve">
            <p class="empty-curve-text">先做一次诊断，这里就会有你的成长曲线</p>
            <van-button
              size="small"
              type="primary"
              @click="router.push('/diagnose/submit')"
            >
              去诊断
            </van-button>
          </div>
        </section>
      </template>
    </van-pull-refresh>

    <!-- 服务端错误 -->
    <div v-if="!loading && serverError" class="error-box vct-card">
      <p>{{ serverError }}</p>
      <van-button size="small" @click="fetchData">重试</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { archiveApi } from "@/api";
import { GRADE_LABELS, ARCHIVE_METRIC_LABELS } from "@video-ct/shared";
import dayjs from "dayjs";
import SkeletonCard from "@/components/SkeletonCard.vue";

const router = useRouter();

const loading = ref(true);
const networkError = ref(false);
const serverError = ref("");
const refreshing = ref(false);
const archive = ref<any | null>(null);
const curveData = ref<any | null>(null);

const dimTrends = computed(() => {
  if (!curveData.value?.dimension_trends) return [];
  return Object.entries(curveData.value.dimension_trends).map(
    ([key, val]: any) => ({
      name: ARCHIVE_METRIC_LABELS[key] || key,
      latest: val.latest ?? 0,
      delta: val.delta ?? 0,
    }),
  );
});

/** 使用共享 GRADE_LABELS，同时兼容 CSS class */
function levelCls(l: string) {
  const lower = (l || "").toLowerCase();
  return lower;
}

function getGradeLabel(l: string) {
  return GRADE_LABELS[l] || l;
}

function trendClass(d: number) {
  if (d > 0) return "up";
  if (d < 0) return "down";
  return "flat";
}

function formatDate(t: string) {
  if (!t) return "-";
  return dayjs(t).format("MM-DD");
}

async function fetchData() {
  loading.value = true;
  networkError.value = false;
  serverError.value = "";
  try {
    const [a, c] = await Promise.all([
      archiveApi.me(),
      archiveApi.curve().catch(() => null),
    ]);
    archive.value = a;
    curveData.value = c;
  } catch (e: any) {
    if (!navigator.onLine) {
      networkError.value = true;
    } else if (e.status && e.status >= 500) {
      serverError.value = "服务繁忙，请稍后重试";
    } else {
      serverError.value = e.message || "加载失败";
    }
  } finally {
    loading.value = false;
  }
}

async function onRefresh() {
  await fetchData();
  refreshing.value = false;
}

onMounted(fetchData);
</script>

<style lang="scss" scoped>
.page {
  padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px));
  min-height: 100vh;
}
.loading-center {
  padding-top: 120px;
  display: flex;
  justify-content: center;
}

.empty-guide {
  padding-top: 60px;
  text-align: center;
  .guide-text {
    font-size: 13px;
    color: var(--mfc-fg-2);
    margin: 12px 0 20px;
    line-height: 1.6;
  }
}

.info-card {
  margin: 16px 0;
  padding: 20px 16px;
  background: linear-gradient(
    135deg,
    rgba(0, 122, 255, 0.12),
    rgba(88, 86, 214, 0.12)
  );
  .archive-no {
    font-size: 12px;
    color: var(--mfc-fg-3);
  }
  .meta-row {
    display: flex;
    justify-content: space-around;
    margin-top: 16px;
  }
  .meta-item {
    text-align: center;
  }
  .meta-value {
    font-size: 20px;
    font-weight: 700;
  }
  .meta-label {
    font-size: 11px;
    color: var(--mfc-fg-3);
    margin-top: 4px;
  }
  .level-badge {
    display: inline-block;
    padding: 2px 12px;
    border-radius: 999px;
    font-size: 16px;
    font-weight: 700;
    &.l1,
    &.l2 {
      background: rgba(107, 114, 128, 0.2);
      color: #9ca3af;
    }
    &.l3,
    &.l4 {
      background: rgba(88, 86, 214, 0.12);
      color: var(--mfc-indigo);
    }
    &.l5,
    &.l6 {
      background: rgba(0, 122, 255, 0.12);
      color: var(--mfc-blue);
    }
  }
}

.curve-block {
  margin-top: 20px;
}
.block-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--mfc-fg-2);
  margin-bottom: 10px;
}
.no-data {
  font-size: 13px;
  color: var(--mfc-fg-3);
  padding: 16px 0;
  text-align: center;
}

.level-timeline {
  padding-left: 16px;
  border-left: 2px solid var(--mfc-hairline);
}
.level-dot-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  position: relative;
  .dot {
    position: absolute;
    left: -21px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--mfc-bg-soft);
    border: 2px solid var(--mfc-hairline);
    &.active {
      background: var(--mfc-blue);
      border-color: var(--mfc-blue);
      box-shadow: 0 0 8px rgba(0, 122, 255, 0.12);
    }
  }
  .level-info {
    display: flex;
    gap: 12px;
  }
  .lv {
    font-size: 14px;
    font-weight: 600;
    color: var(--mfc-blue);
  }
  .date {
    font-size: 12px;
    color: var(--mfc-fg-3);
  }
}

.dim-trends {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.trend-row {
  display: grid;
  grid-template-columns: 60px 1fr 32px 40px;
  align-items: center;
  gap: 8px;
  .trend-name {
    font-size: 12px;
    color: var(--mfc-fg-2);
  }
  .trend-bar-wrap {
    height: 6px;
    background: var(--mfc-bg-soft);
    border-radius: 3px;
    overflow: hidden;
  }
  .trend-bar {
    height: 100%;
    border-radius: 3px;
    background: var(--mfc-indigo);
    &.up {
      background: var(--mfc-color-success);
    }
    &.down {
      background: var(--mfc-color-danger);
    }
    &.flat {
      background: var(--mfc-fg-3);
    }
  }
  .trend-val {
    font-size: 12px;
    font-weight: 600;
    text-align: right;
  }
  .trend-delta {
    font-size: 11px;
    font-weight: 600;
    &.up {
      color: var(--mfc-color-success);
    }
    &.down {
      color: var(--mfc-color-danger);
    }
    &.flat {
      color: var(--mfc-fg-3);
    }
  }
}

.empty-curve {
  text-align: center;
  padding: 24px 0;
}
.empty-curve-text {
  font-size: 13px;
  color: var(--mfc-fg-3);
  margin-bottom: 16px;
}

.error-box {
  margin-top: 24px;
  text-align: center;
  padding: 24px;
  p {
    color: var(--mfc-color-danger);
    font-size: 13px;
    margin-bottom: 12px;
  }
}
</style>
