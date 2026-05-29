<template>
  <div class="page">
    <van-nav-bar
      title="数据仪表盘"
      left-arrow
      @click-left="router.back()"
      :border="false"
    />

    <SkeletonCard v-if="loading" :lines="6" />

    <template v-if="!loading">
      <!-- Phase1 状态条 -->
      <section class="vct-card phase-bar">
        <div class="phase-row">
          <div class="phase-info">
            <div class="phase-label">Phase1 门槛</div>
            <div
              class="phase-value"
              :class="trend?.phase1_met ? 'met' : 'unmet'"
            >
              {{ trend?.phase1_met ? "✅ 已达成" : `🕐 积累中` }}
            </div>
          </div>
          <div class="phase-count">
            <div class="count-num">{{ todayTotal }}</div>
            <div class="count-label">
              今日事件 / {{ trend?.phase1_threshold || 500 }}
            </div>
          </div>
        </div>
        <van-progress
          :percentage="
            Math.min(100, (todayTotal / (trend?.phase1_threshold || 500)) * 100)
          "
          :color="trend?.phase1_met ? 'var(--mfc-green)' : 'var(--mfc-blue)'"
          stroke-width="6"
          :show-pivot="false"
          style="margin-top: 10px"
        />
      </section>

      <!-- 事件趋势折线图 -->
      <section class="vct-card chart-card">
        <div class="vct-section-title">📈 event_logs 7 日趋势</div>
        <div v-if="chartPoints.length >= 2" class="chart-wrap">
          <svg
            :viewBox="`0 0 ${SVG_W} ${SVG_H}`"
            class="trend-svg"
            preserveAspectRatio="none"
          >
            <!-- 网格线 -->
            <line
              v-for="y in gridYs"
              :key="y"
              :x1="PAD_L"
              :y1="y"
              :x2="SVG_W - PAD_R"
              :y2="y"
              stroke="var(--mfc-hairline)"
              stroke-width="1"
            />
            <!-- 折线填充 -->
            <path :d="areaPath" fill="rgba(0,122,255,0.08)" />
            <!-- 折线 -->
            <polyline
              :points="linePoints"
              fill="none"
              stroke="var(--mfc-blue)"
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <!-- 数据点 -->
            <circle
              v-for="(p, i) in chartPoints"
              :key="i"
              :cx="p.x"
              :cy="p.y"
              r="3"
              fill="var(--mfc-blue)"
            />
          </svg>
          <!-- X 轴日期 -->
          <div class="x-labels">
            <span v-for="(d, i) in chartDates" :key="i" class="x-label">{{
              d
            }}</span>
          </div>
        </div>
        <van-empty
          v-else
          image="search"
          description="暂无数据"
          style="padding: 20px 0"
        />

        <!-- 按类型明细 -->
        <div v-if="latestByType" class="type-breakdown">
          <div class="breakdown-title">今日类型分布</div>
          <div class="breakdown-list">
            <div
              v-for="(cnt, type) in latestByType"
              :key="type"
              class="breakdown-item"
            >
              <span class="type-name">{{ type }}</span>
              <span class="type-count">{{ cnt }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 账号健康分（用户自己的账号） -->
      <section v-if="myAccounts.length > 0">
        <div class="vct-section-title">🏥 账号健康分</div>
        <div
          v-for="acc in myAccounts"
          :key="acc.id"
          class="vct-card health-card"
        >
          <div class="health-header">
            <span class="platform-badge">{{
              PLATFORM_LABELS[acc.platform] || acc.platform
            }}</span>
            <span class="acc-name">{{ acc.nickname || "未命名" }}</span>
          </div>
          <div v-if="healthMap[acc.id]" class="health-body">
            <div class="score-row">
              <div
                class="score-num"
                :style="{ color: scoreColor(healthMap[acc.id].health_score) }"
              >
                {{ healthMap[acc.id].health_score.toFixed(1) }}
              </div>
              <div class="score-label">综合健康分</div>
            </div>
            <div class="health-meta">
              <span
                >趋势：{{
                  TREND_LABELS[healthMap[acc.id].trend] ||
                  healthMap[acc.id].trend
                }}</span
              >
              <span v-if="healthMap[acc.id].benchmark_percentile">
                · 赛道 Top
                {{ Math.round(100 - healthMap[acc.id].benchmark_percentile) }}%
              </span>
            </div>
            <div class="health-note">{{ healthMap[acc.id].notes }}</div>
          </div>
          <van-loading v-else size="20px" style="margin: 12px 0" />
        </div>
      </section>

      <!-- 无账号引导 -->
      <section v-else class="vct-card bind-hint">
        <div class="hint-text">先在首页绑定账号，即可查看健康分</div>
        <van-button size="small" type="primary" @click="router.push('/home')"
          >去绑定</van-button
        >
      </section>

      <!-- CEO 总览（admin 专属） -->
      <section v-if="ceo" class="vct-card ceo-card">
        <div class="vct-section-title">🏢 运营总览</div>
        <div class="ceo-grid">
          <div class="ceo-item">
            <div class="ceo-num">{{ ceo.total_users }}</div>
            <div class="ceo-label">总用户</div>
          </div>
          <div class="ceo-item">
            <div class="ceo-num">{{ ceo.today_new_users }}</div>
            <div class="ceo-label">今日新增</div>
          </div>
          <div class="ceo-item">
            <div class="ceo-num">{{ ceo.total_diagnoses }}</div>
            <div class="ceo-label">总诊断数</div>
          </div>
          <div class="ceo-item">
            <div class="ceo-num">
              ¥{{ ceo.month_revenue_cny?.toFixed(0) || 0 }}
            </div>
            <div class="ceo-label">本月收入</div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { adminApi, accountsApi } from "@/api";
import { http } from "@/api/client";
import SkeletonCard from "@/components/SkeletonCard.vue";

const router = useRouter();
const loading = ref(true);
const trend = ref<any>(null);
const myAccounts = ref<any[]>([]);
const healthMap = ref<Record<number, any>>({});
const ceo = ref<any>(null);

const SVG_W = 300;
const SVG_H = 120;
const PAD_L = 8;
const PAD_R = 8;
const PAD_T = 12;
const PAD_B = 8;

const PLATFORM_LABELS: Record<string, string> = {
  douyin: "抖音",
  bilibili: "B站",
  xiaohongshu: "小红书",
};
const TREND_LABELS: Record<string, string> = {
  up: "↑ 上升",
  down: "↓ 下降",
  stable: "→ 稳定",
};

const todayTotal = computed(() => {
  if (!trend.value?.trend?.length) return 0;
  const today = new Date().toISOString().slice(0, 10);
  const item = trend.value.trend.find((d: any) => d.date === today);
  return item?.total ?? 0;
});

const latestByType = computed(() => {
  if (!trend.value?.trend?.length) return null;
  const today = new Date().toISOString().slice(0, 10);
  const item = trend.value.trend.find((d: any) => d.date === today);
  return item?.by_type && Object.keys(item.by_type).length
    ? item.by_type
    : null;
});

const chartPoints = computed(() => {
  const items: any[] = trend.value?.trend ?? [];
  if (items.length < 2) return [];
  const maxVal = Math.max(...items.map((d: any) => d.total), 1);
  const w = SVG_W - PAD_L - PAD_R;
  const h = SVG_H - PAD_T - PAD_B;
  return items.map((d: any, i: number) => ({
    x: PAD_L + (i / (items.length - 1)) * w,
    y: PAD_T + h - (d.total / maxVal) * h,
    total: d.total,
  }));
});

const linePoints = computed(() =>
  chartPoints.value.map((p) => `${p.x},${p.y}`).join(" "),
);

const areaPath = computed(() => {
  const pts = chartPoints.value;
  if (!pts.length) return "";
  const bottom = SVG_H - PAD_B;
  return (
    `M${pts[0].x},${bottom} ` +
    pts.map((p) => `L${p.x},${p.y}`).join(" ") +
    ` L${pts[pts.length - 1].x},${bottom} Z`
  );
});

const gridYs = computed(() => {
  const h = SVG_H - PAD_T - PAD_B;
  return [0, 1, 2].map((i) => PAD_T + (i / 2) * h);
});

const chartDates = computed(() => {
  const items: any[] = trend.value?.trend ?? [];
  if (items.length === 0) return [];
  const indices = [0, Math.floor(items.length / 2), items.length - 1];
  return [...new Set(indices)].map((i) => items[i]?.date?.slice(5) ?? "");
});

function scoreColor(score: number) {
  if (score >= 70) return "var(--mfc-green)";
  if (score >= 40) return "var(--mfc-blue)";
  return "var(--mfc-red)";
}

onMounted(async () => {
  const [trendRes, accountsRes, ceoRes] = await Promise.allSettled([
    adminApi.eventsTrend(7),
    accountsApi.mine(),
    adminApi.dashboard(),
  ]);
  if (trendRes.status === "fulfilled") trend.value = trendRes.value;
  if (accountsRes.status === "fulfilled") myAccounts.value = accountsRes.value;
  if (ceoRes.status === "fulfilled") ceo.value = ceoRes.value;
  loading.value = false;

  // 并行拉取每个账号健康分
  myAccounts.value.forEach(async (acc) => {
    try {
      const h = await http.get<unknown, any>(
        `/api/v1/accounts/${acc.id}/health`,
      );
      healthMap.value = { ...healthMap.value, [acc.id]: h };
    } catch {}
  });
});
</script>

<style lang="scss" scoped>
.page {
  padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px));
  min-height: 100vh;
}
.phase-bar {
  margin-bottom: 12px;
  .phase-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .phase-label {
    font-size: 12px;
    color: var(--mfc-fg-3);
  }
  .phase-value {
    font-size: 15px;
    font-weight: 600;
    margin-top: 2px;
    &.met {
      color: var(--mfc-green);
    }
    &.unmet {
      color: var(--mfc-blue);
    }
  }
  .count-num {
    font-size: 24px;
    font-weight: 700;
    text-align: right;
    color: var(--mfc-fg);
  }
  .count-label {
    font-size: 11px;
    color: var(--mfc-fg-3);
    text-align: right;
  }
}
.chart-card {
  margin-bottom: 12px;
  .chart-wrap {
    margin-top: 12px;
  }
  .trend-svg {
    width: 100%;
    height: 120px;
    display: block;
  }
  .x-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    .x-label {
      font-size: 10px;
      color: var(--mfc-fg-3);
    }
  }
}
.type-breakdown {
  margin-top: 14px;
  border-top: 1px solid var(--mfc-hairline);
  padding-top: 12px;
  .breakdown-title {
    font-size: 12px;
    color: var(--mfc-fg-3);
    margin-bottom: 8px;
  }
  .breakdown-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .breakdown-item {
    display: flex;
    align-items: center;
    gap: 4px;
    background: var(--mfc-bg-soft);
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 12px;
    .type-name {
      color: var(--mfc-fg-2);
    }
    .type-count {
      font-weight: 600;
      color: var(--mfc-blue);
    }
  }
}
.health-card {
  margin-bottom: 10px;
  .health-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    .platform-badge {
      font-size: 11px;
      font-weight: 600;
      color: var(--mfc-blue);
      background: rgba(0, 122, 255, 0.1);
      padding: 2px 8px;
      border-radius: 999px;
    }
    .acc-name {
      font-size: 14px;
      font-weight: 500;
    }
  }
  .score-row {
    display: flex;
    align-items: baseline;
    gap: 6px;
    .score-num {
      font-size: 40px;
      font-weight: 700;
      line-height: 1;
    }
    .score-label {
      font-size: 12px;
      color: var(--mfc-fg-3);
    }
  }
  .health-meta {
    font-size: 12px;
    color: var(--mfc-fg-2);
    margin-top: 6px;
  }
  .health-note {
    font-size: 12px;
    color: var(--mfc-fg-3);
    margin-top: 4px;
    font-style: italic;
  }
}
.bind-hint {
  text-align: center;
  padding: 20px;
  .hint-text {
    font-size: 13px;
    color: var(--mfc-fg-2);
    margin-bottom: 12px;
  }
}
.ceo-card {
  margin-top: 12px;
  .ceo-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-top: 12px;
  }
  .ceo-item {
    text-align: center;
  }
  .ceo-num {
    font-size: 28px;
    font-weight: 700;
    color: var(--mfc-fg);
  }
  .ceo-label {
    font-size: 11px;
    color: var(--mfc-fg-3);
    margin-top: 2px;
  }
}
</style>
