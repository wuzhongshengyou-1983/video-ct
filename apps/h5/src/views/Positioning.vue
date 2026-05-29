<template>
  <div class="page">
    <van-nav-bar
      title="商业定位 BPS"
      left-arrow
      @click-left="router.back()"
      :border="false"
    />

    <van-loading v-if="loading" size="24" vertical class="loading-center"
      >加载中…</van-loading
    >

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchData">重试</van-button>
    </div>

    <!-- 无定位档案：输入 + 扫描 -->
    <div v-if="!loading && !networkError && !positioning" class="scan-section">
      <div class="vct-card intro-card">
        <div class="intro-icon">💰</div>
        <div class="intro-title">商业定位分析</div>
        <div class="intro-desc">
          AI 分析你的变现潜力，推荐最合适的商业模式和成长路径，提供 12
          个月路线图。
        </div>
      </div>

      <div class="vct-card form-card">
        <van-field
          v-model="description"
          label="业务描述"
          placeholder="描述你的账号定位、变现方向和目标"
          type="textarea"
          rows="4"
          autosize
          :error="!!descError"
          :error-message="descError"
          @update:model-value="descError = ''"
        />
        <van-button
          type="primary"
          block
          class="scan-btn"
          :loading="scanning"
          @click="doScan"
        >
          开始分析
        </van-button>
      </div>
    </div>

    <!-- 有定位档案 -->
    <template v-if="positioning">
      <!-- 6 维评分 -->
      <section class="vct-card glow score-card">
        <div class="match-title">商业定位分析</div>
        <div class="dim-scores">
          <div v-for="(v, k) in dimensionScores" :key="k" class="dim-score-row">
            <div class="dim-label">{{ dimLabels[k] || k }}</div>
            <van-progress
              :percentage="v"
              :color="scoreColor(v)"
              stroke-width="6"
              :show-pivot="false"
            />
            <div class="dim-val">{{ v }}</div>
          </div>
        </div>

        <!-- 风险等级 -->
        <div
          v-if="positioning.risk_level"
          class="risk-tag"
          :class="riskCls(positioning.risk_level)"
        >
          风险等级：{{
            RISK_LEVELS[positioning.risk_level] || positioning.risk_level
          }}
        </div>
      </section>

      <!-- 5 变现原型推荐 -->
      <section
        v-if="positioning.monetization_archetypes?.length"
        class="vct-card"
      >
        <div class="vct-section-title">💎 变现原型推荐</div>
        <div class="monet-list">
          <div
            v-for="(m, i) in positioning.monetization_archetypes"
            :key="i"
            class="monet-item"
          >
            <div class="monet-rank">#{{ i + 1 }}</div>
            <div class="monet-info">
              <div class="monet-name">{{ m.name }}</div>
              <div class="monet-desc">{{ m.description }}</div>
              <div class="monet-fit" :class="fitCls(m.fit_score)">
                匹配度 {{ m.fit_score }}%
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- TOP3 路径 -->
      <section v-if="positioning.top_paths?.length" class="vct-card">
        <div class="vct-section-title">🚀 TOP3 增长路径</div>
        <div class="path-list">
          <div
            v-for="(p, i) in positioning.top_paths"
            :key="i"
            class="path-item"
          >
            <div class="path-num">{{ i + 1 }}</div>
            <div class="path-info">
              <div class="path-name">{{ p.name }}</div>
              <div class="path-desc">{{ p.description }}</div>
              <div v-if="p.estimated_revenue" class="path-revenue">
                预估收入：{{ p.estimated_revenue }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 12 月路线图 -->
      <section v-if="positioning.roadmap?.length" class="vct-card">
        <div class="vct-section-title">📅 12 月路线图</div>
        <div class="roadmap-timeline">
          <div
            v-for="(r, i) in positioning.roadmap"
            :key="i"
            class="roadmap-item"
          >
            <div class="roadmap-month">第{{ r.month || i + 1 }}月</div>
            <div class="roadmap-content">
              <div class="roadmap-goal">{{ r.goal }}</div>
              <div class="roadmap-actions">{{ r.actions }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 商业模式九宫格 -->
      <section v-if="positioning.canvas_bmc" class="vct-card">
        <div class="vct-section-title">🧩 商业模式九宫格</div>
        <div class="bmc-grid">
          <div
            v-for="(val, key) in positioning.canvas_bmc"
            :key="key"
            class="bmc-cell"
          >
            <div class="bmc-key">{{ bmcLabels[key] || key }}</div>
            <div class="bmc-val">{{ val }}</div>
          </div>
        </div>
      </section>

      <!-- 重新扫描 -->
      <div class="rescan-section">
        <van-button plain type="primary" size="small" @click="resetScan">
          重新分析
        </van-button>
      </div>
    </template>

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
import { Toast } from "vant";
import { positioningApi } from "@/api";
import { RISK_LEVELS, MONETIZATION_ARCHETYPES } from "@video-ct/shared";

const router = useRouter();

const loading = ref(true);
const networkError = ref(false);
const serverError = ref("");
const scanning = ref(false);
const positioning = ref<any | null>(null);
const description = ref("");
const descError = ref("");

const dimLabels: Record<string, string> = {
  market_size: "市场规模",
  competition: "竞争强度",
  monetization: "变现力",
  scalability: "扩展性",
  moat: "护城河",
  profitability: "盈利性",
};

const bmcLabels: Record<string, string> = {
  customer_segments: "客户细分",
  value_proposition: "价值主张",
  channels: "渠道通路",
  customer_relationships: "客户关系",
  revenue_streams: "收入来源",
  key_resources: "核心资源",
  key_activities: "关键业务",
  key_partners: "关键伙伴",
  cost_structure: "成本结构",
};

const dimensionScores = computed(() => {
  if (!positioning.value?.dimension_scores)
    return positioning.value?.scores || {};
  return positioning.value.dimension_scores;
});

function scoreColor(v: number) {
  if (v >= 80) return "linear-gradient(90deg, #10b981, #34d399)";
  if (v >= 60) return "linear-gradient(90deg, #38bdf8, #60a5fa)";
  if (v >= 40) return "linear-gradient(90deg, #f59e0b, #fbbf24)";
  return "linear-gradient(90deg, #ef4444, #f87171)";
}

function fitCls(s: number) {
  if (s >= 80) return "high";
  if (s >= 60) return "mid";
  return "low";
}

function riskCls(r: string) {
  const map: Record<string, string> = {
    low: "risk-low",
    medium: "risk-mid",
    high: "risk-high",
  };
  return map[r] || "risk-low";
}

// 缓存 key
const POSITIONING_CACHE_KEY = "vct_positioning_cache";

function loadCachedPositioning(): any | null {
  try {
    const cached = localStorage.getItem(POSITIONING_CACHE_KEY);
    if (cached) return JSON.parse(cached);
  } catch {
    /* ignore */
  }
  return null;
}

function saveCachedPositioning(data: any) {
  try {
    localStorage.setItem(POSITIONING_CACHE_KEY, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

async function fetchData() {
  loading.value = true;
  networkError.value = false;
  serverError.value = "";
  try {
    const p = await positioningApi.me().catch(() => null);
    positioning.value = p;
    if (p) saveCachedPositioning(p);
  } catch (e: any) {
    if (!navigator.onLine) {
      networkError.value = true;
      positioning.value = loadCachedPositioning();
    } else if (e.status && e.status >= 500) {
      serverError.value = "服务繁忙，请稍后重试";
    } else {
      serverError.value = e.message || "加载失败";
    }
  } finally {
    loading.value = false;
  }
}

async function doScan() {
  if (!description.value.trim()) {
    descError.value = "请先填写业务描述";
    return;
  }
  scanning.value = true;
  try {
    const result = await positioningApi.scan({
      description: description.value,
    });
    positioning.value = result;
    saveCachedPositioning(result);
    Toast.success("分析完成！");
  } catch (e: any) {
    if (e.status === 429) {
      Toast.fail("本月配额已用完，升级 PRO 解锁");
    } else if (e.status && e.status >= 500) {
      Toast.fail("服务繁忙，请稍后重试");
    } else {
      Toast.fail(e.message || "分析失败");
    }
  } finally {
    scanning.value = false;
  }
}

function resetScan() {
  positioning.value = null;
  description.value = "";
  descError.value = "";
  try {
    localStorage.removeItem(POSITIONING_CACHE_KEY);
  } catch {
    /* ignore */
  }
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

.scan-section {
  margin-top: 16px;
}
.intro-card {
  text-align: center;
  padding: 24px 16px;
  background: linear-gradient(
    135deg,
    rgba(245, 158, 11, 0.08),
    rgba(56, 189, 248, 0.06)
  );
  .intro-icon {
    font-size: 48px;
  }
  .intro-title {
    font-size: 18px;
    font-weight: 700;
    margin: 8px 0;
  }
  .intro-desc {
    font-size: 13px;
    color: var(--vct-text-2);
    line-height: 1.6;
  }
}
.form-card {
  margin-top: 16px;
  padding: 16px;
  scroll-margin-bottom: 40vh;
}
.scan-btn {
  margin-top: 16px;
  min-height: 44px;
}

.score-card {
  margin: 16px 0;
  padding: 20px 16px;
  text-align: center;
  background: linear-gradient(
    135deg,
    rgba(245, 158, 11, 0.1),
    rgba(56, 189, 248, 0.05)
  );
  .match-title {
    font-size: 14px;
    color: var(--vct-text-2);
    margin-bottom: 16px;
  }
  .dim-scores {
    text-align: left;
  }
  .dim-score-row {
    display: grid;
    grid-template-columns: 64px 1fr 32px;
    align-items: center;
    gap: 10px;
    padding: 4px 0;
    .dim-label {
      font-size: 12px;
      color: var(--vct-text-2);
    }
    .dim-val {
      font-size: 12px;
      font-weight: 600;
      text-align: right;
    }
  }
  .risk-tag {
    display: inline-block;
    margin-top: 16px;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    &.risk-low {
      background: rgba(16, 185, 129, 0.15);
      color: var(--vct-success);
    }
    &.risk-mid {
      background: rgba(245, 158, 11, 0.15);
      color: var(--vct-warning);
    }
    &.risk-high {
      background: rgba(239, 68, 68, 0.15);
      color: var(--vct-danger);
    }
  }
}

.monet-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.monet-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.monet-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 800;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.monet-info {
  flex: 1;
}
.monet-name {
  font-size: 14px;
  font-weight: 600;
}
.monet-desc {
  font-size: 12px;
  color: var(--vct-text-2);
  margin-top: 2px;
}
.monet-fit {
  font-size: 11px;
  margin-top: 4px;
  &.high {
    color: var(--vct-success);
  }
  &.mid {
    color: var(--vct-warning);
  }
  &.low {
    color: var(--vct-text-3);
  }
}

.path-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.path-item {
  display: flex;
  gap: 12px;
}
.path-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 800;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.path-info {
  flex: 1;
}
.path-name {
  font-size: 14px;
  font-weight: 600;
}
.path-desc {
  font-size: 12px;
  color: var(--vct-text-2);
  margin-top: 2px;
}
.path-revenue {
  font-size: 11px;
  color: var(--vct-success);
  margin-top: 4px;
}

.roadmap-timeline {
  padding-left: 16px;
  border-left: 2px solid var(--vct-primary);
}
.roadmap-item {
  padding: 10px 0;
  position: relative;
}
.roadmap-month {
  font-size: 12px;
  font-weight: 600;
  color: var(--vct-primary);
  margin-bottom: 4px;
  &::before {
    content: "";
    position: absolute;
    left: -21px;
    top: 14px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--vct-primary);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
  }
}
.roadmap-goal {
  font-size: 13px;
  font-weight: 600;
}
.roadmap-actions {
  font-size: 12px;
  color: var(--vct-text-2);
  margin-top: 2px;
}

.bmc-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  .bmc-cell {
    background: var(--vct-surface);
    border-radius: 8px;
    padding: 10px 8px;
    border: 1px solid var(--vct-border);
    .bmc-key {
      font-size: 10px;
      color: var(--vct-primary);
      font-weight: 600;
      margin-bottom: 4px;
    }
    .bmc-val {
      font-size: 11px;
      color: var(--vct-text-2);
      word-break: break-all;
    }
  }
}

.rescan-section {
  text-align: center;
  padding: 16px 0;
}

.error-box {
  margin-top: 24px;
  text-align: center;
  padding: 24px;
  p {
    color: var(--vct-danger);
    font-size: 13px;
    margin-bottom: 12px;
  }
}
</style>
