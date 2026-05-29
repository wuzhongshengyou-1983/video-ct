<template>
  <!-- 骨架屏 -->
  <div v-if="loading" class="dna-skeleton">
    <van-skeleton title :row="3" row-width="100%" />
    <van-skeleton title :row="5" row-width="100%" style="margin-top: 16px" />
    <van-skeleton title :row="4" row-width="100%" style="margin-top: 16px" />
  </div>

  <!-- 无数据 -->
  <div v-else-if="!data" class="dna-empty">
    <van-empty description="暂无爆火 DNA 数据" />
  </div>

  <!-- 正式内容 -->
  <div v-else class="dna-wrap">
    <!-- 1. 竞品信息头部 -->
    <section class="vct-card dna-hero">
      <div class="hero-left">
        <div class="avatar-placeholder">
          {{ data.competitor.nickname.slice(0, 1) }}
        </div>
        <div class="hero-info">
          <div class="hero-name">{{ data.competitor.nickname }}</div>
          <div class="hero-meta">
            <span class="hero-fans"
              >{{ formatFans(data.competitor.follower_count) }} 粉丝</span
            >
            <span class="platform-tag">{{ data.competitor.platform }}</span>
          </div>
        </div>
      </div>
      <div class="viral-score-box">
        <div class="viral-score-num">{{ Math.round(data.viral_score) }}</div>
        <div class="viral-score-label">综合爆火力</div>
      </div>
    </section>

    <!-- 2. 7 维评分条 -->
    <section class="vct-card">
      <div class="vct-section-title">🧬 爆火 DNA 7 维</div>
      <div v-for="dim in data.dimensions" :key="dim.name" class="dim-bar-row">
        <div class="dim-bar-label">
          <span class="dim-bar-name">{{ dim.name }}</span>
          <span class="dim-bar-score" :class="scoreCls(dim.score)">{{
            dim.score
          }}</span>
        </div>
        <div class="dim-bar-track">
          <div
            class="dim-bar-fill"
            :class="scoreCls(dim.score)"
            :style="{ width: dim.score + '%' }"
          />
        </div>
        <div class="dim-bar-evidence">{{ dim.evidence }}</div>
      </div>
    </section>

    <!-- 3. Top 3 贡献因子 -->
    <section class="vct-card">
      <div class="vct-section-title">🏆 Top 3 爆火因子</div>
      <div
        v-for="(factor, i) in data.top_factors"
        :key="factor.name"
        class="factor-item"
      >
        <div class="factor-head" @click="toggleFactor(i)">
          <div class="factor-left">
            <span class="factor-rank">{{ i + 1 }}</span>
            <span class="factor-name">{{ factor.name }}</span>
          </div>
          <div class="factor-right">
            <span class="factor-pct">贡献 {{ factor.contribution_pct }}%</span>
            <van-icon
              :name="expandedFactors[i] ? 'arrow-up' : 'arrow-down'"
              size="14"
            />
          </div>
        </div>
        <div v-show="expandedFactors[i]" class="factor-evidence">
          {{ factor.evidence }}
        </div>
      </div>
    </section>

    <!-- 4. F-Frame 时间轴 -->
    <section class="vct-card">
      <div class="vct-section-title">🎬 F-Frame 时间轴</div>
      <div class="fframe-track">
        <div v-for="frame in data.fframe" :key="frame.range" class="fframe-seg">
          <div class="fframe-range">{{ frame.range }}</div>
          <div class="fframe-score-badge" :class="scoreCls(frame.score)">
            {{ frame.score }}
          </div>
          <div class="fframe-label">{{ frame.label }}</div>
          <div class="fframe-tactic">{{ frame.tactic }}</div>
        </div>
      </div>
    </section>

    <!-- 5. 策略建议三列 -->
    <section class="vct-card">
      <div class="vct-section-title">🎯 策略建议</div>
      <div class="strategy-grid">
        <div class="strategy-col can-copy">
          <div class="strategy-col-title">✅ 能抄</div>
          <ul>
            <li v-for="item in data.can_copy" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="strategy-col avoid">
          <div class="strategy-col-title">❌ 别抄</div>
          <ul>
            <li v-for="item in data.avoid" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="strategy-col transform">
          <div class="strategy-col-title">🔄 改造</div>
          <ul>
            <li v-for="item in data.transform" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 6. 生成复刻方案 -->
    <section class="vct-card remix-section">
      <van-button
        block
        type="primary"
        :loading="remixLoading"
        :disabled="remixLoading"
        @click="generateRemix"
        class="remix-btn"
      >
        🎬 生成我的复刻方案
      </van-button>

      <!-- 复刻结果折叠卡片 -->
      <div v-if="remixSegments.length" class="remix-result">
        <div class="remix-result-title">🎞️ 复刻剧本</div>
        <div v-for="(seg, i) in remixSegments" :key="i" class="remix-seg-item">
          <div class="remix-seg-head" @click="toggleRemixSeg(i)">
            <div class="remix-seg-left">
              <span class="remix-stage-tag">{{ seg.stage }}</span>
              <span class="remix-duration">{{ seg.duration }}</span>
              <span class="remix-function">{{ seg.function }}</span>
            </div>
            <van-icon
              :name="expandedRemix[i] ? 'arrow-up' : 'arrow-down'"
              size="14"
            />
          </div>
          <div v-show="expandedRemix[i]" class="remix-seg-body">
            <div class="remix-field">
              <span class="remix-field-label">台词</span>
              <span class="remix-field-val">{{ seg.script }}</span>
            </div>
            <div class="remix-field">
              <span class="remix-field-label">镜头</span>
              <span class="remix-field-val">{{ seg.shot }}</span>
            </div>
            <div class="remix-field why">
              <span class="remix-field-label">为什么</span>
              <span class="remix-field-val">{{ seg.why }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Toast } from "vant";
import { benchmarkApi } from "@/api";

// ---- 类型定义 ----
export interface ViralDnaDimension {
  name: string;
  score: number;
  weight: number;
  evidence: string;
}

export interface ViralDnaTopFactor {
  name: string;
  contribution_pct: number;
  evidence: string;
}

export interface ViralDnaFrame {
  range: string;
  label: string;
  score: number;
  tactic: string;
}

export interface ViralDnaCompetitor {
  nickname: string;
  follower_count: number;
  platform: string;
}

export interface ViralDnaResult {
  competitor: ViralDnaCompetitor;
  viral_score: number;
  dimensions: ViralDnaDimension[];
  top_factors: ViralDnaTopFactor[];
  fframe: ViralDnaFrame[];
  can_copy: string[];
  avoid: string[];
  transform: string[];
}

interface RemixSegment {
  stage: string;
  duration: string;
  function: string;
  script: string;
  shot: string;
  why: string;
}

interface Props {
  data: ViralDnaResult | null;
  loading: boolean;
  track?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: "remix-request", payload: { track: string; viral_dna: any }): void;
}>();

// ---- 因子折叠状态 ----
const expandedFactors = ref<boolean[]>([true, false, false]);

function toggleFactor(i: number) {
  expandedFactors.value[i] = !expandedFactors.value[i];
}

// ---- 复刻方案状态 ----
const remixLoading = ref(false);
const remixSegments = ref<RemixSegment[]>([]);
const expandedRemix = ref<boolean[]>([]);

function toggleRemixSeg(i: number) {
  expandedRemix.value[i] = !expandedRemix.value[i];
}

async function generateRemix() {
  if (!props.data) return;
  const track = props.track || props.data.competitor.platform || "通用";
  const viral_dna = {
    competitor_nickname: props.data.competitor.nickname,
    viral_score: props.data.viral_score,
    top_factors: props.data.top_factors,
    dimensions: props.data.dimensions,
  };

  emit("remix-request", { track, viral_dna });

  remixLoading.value = true;
  try {
    const result = await benchmarkApi.remix(track, viral_dna);
    remixSegments.value = result.segments ?? [];
    expandedRemix.value = remixSegments.value.map((_, i) => i === 0);
    if (!remixSegments.value.length) {
      Toast.fail("暂时没有生成到剧本，请稍后重试");
    }
  } catch (e: any) {
    Toast.fail(e.message || "复刻方案生成失败，请稍后重试");
  } finally {
    remixLoading.value = false;
  }
}

// ---- 工具函数 ----
function formatFans(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + " 百万";
  if (n >= 10_000) return (n / 10_000).toFixed(1) + " 万";
  return n.toString();
}

function scoreCls(score: number): string {
  if (score >= 85) return "excellent";
  if (score >= 70) return "good";
  if (score >= 50) return "fair";
  return "poor";
}
</script>

<style lang="scss" scoped>
/* ---- 骨架 / 空态 ---- */
.dna-skeleton {
  padding: 0 16px;
}
.dna-empty {
  padding: 32px 0;
}

/* ---- 竞品头部 ---- */
.dna-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--mfc-bg-soft);
  border: 2px solid var(--mfc-hairline);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: var(--mfc-blue);
  flex-shrink: 0;
}

.hero-name {
  font-size: 16px;
  font-weight: 700;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.hero-fans {
  font-size: 12px;
  color: var(--mfc-fg-2);
}

.platform-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(0, 122, 255, 0.1);
  color: var(--mfc-blue);
  font-weight: 600;
}

.viral-score-box {
  text-align: center;
}

.viral-score-num {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #007aff, #0070f3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.viral-score-label {
  font-size: 11px;
  color: var(--mfc-fg-2);
  margin-top: 4px;
}

/* ---- 7 维评分条 ---- */
.dim-bar-row {
  padding: 8px 0;
  border-bottom: 1px dashed var(--mfc-hairline);

  &:last-child {
    border-bottom: none;
  }
}

.dim-bar-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.dim-bar-name {
  font-size: 13px;
  font-weight: 600;
}

.dim-bar-score {
  font-size: 18px;
  font-weight: 800;

  &.excellent {
    color: var(--mfc-green);
  }
  &.good {
    color: var(--mfc-teal);
  }
  &.fair {
    color: #007aff;
  }
  &.poor {
    color: var(--mfc-red);
  }
}

.dim-bar-track {
  height: 6px;
  background: var(--mfc-bg-soft);
  border-radius: 3px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;

  &.excellent {
    background: var(--mfc-green);
  }
  &.good {
    background: var(--mfc-teal);
  }
  &.fair {
    background: #007aff;
  }
  &.poor {
    background: var(--mfc-red);
  }
}

.dim-bar-evidence {
  font-size: 11px;
  color: var(--mfc-fg-2);
  margin-top: 5px;
  line-height: 1.5;
}

/* ---- Top 3 贡献因子 ---- */
.factor-item {
  border-bottom: 1px dashed var(--mfc-hairline);

  &:last-child {
    border-bottom: none;
  }
}

.factor-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  cursor: pointer;
  user-select: none;
}

.factor-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.factor-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--mfc-blue);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.factor-name {
  font-size: 14px;
  font-weight: 600;
}

.factor-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.factor-pct {
  font-size: 13px;
  color: var(--mfc-blue);
  font-weight: 700;
}

.factor-evidence {
  font-size: 12px;
  color: var(--mfc-fg-2);
  line-height: 1.6;
  padding-bottom: 12px;
}

/* ---- F-Frame 时间轴 ---- */
.fframe-track {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;

  /* 隐藏滚动条 */
  &::-webkit-scrollbar {
    display: none;
  }
  scrollbar-width: none;
}

.fframe-seg {
  flex: 0 0 auto;
  min-width: 72px;
  background: var(--mfc-bg-soft);
  border: 1px solid var(--mfc-hairline);
  border-radius: 10px;
  padding: 10px 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.fframe-range {
  font-size: 10px;
  color: var(--mfc-fg-2);
  white-space: nowrap;
}

.fframe-score-badge {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  color: #fff;

  &.excellent {
    background: var(--mfc-green);
  }
  &.good {
    background: var(--mfc-teal);
  }
  &.fair {
    background: #007aff;
  }
  &.poor {
    background: var(--mfc-red);
  }
}

.fframe-label {
  font-size: 12px;
  font-weight: 600;
}

.fframe-tactic {
  font-size: 10px;
  color: var(--mfc-fg-2);
  line-height: 1.4;
  text-align: center;
  word-break: break-all;
}

/* ---- 策略建议三列 ---- */
.strategy-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.strategy-col {
  background: var(--mfc-bg-soft);
  border-radius: 8px;
  padding: 10px 8px;

  .strategy-col-title {
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
    text-align: center;
  }

  ul {
    margin: 0;
    padding: 0;
    list-style: none;

    li {
      font-size: 11px;
      color: var(--mfc-fg-2);
      line-height: 1.5;
      padding: 3px 0;
      border-bottom: 1px dashed var(--mfc-hairline);

      &:last-child {
        border-bottom: none;
      }
    }
  }

  &.can-copy {
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  &.avoid {
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  &.transform {
    border: 1px solid rgba(56, 189, 248, 0.3);
  }
}

/* ---- 复刻方案 ---- */
.remix-section {
  padding: 16px;
}

.remix-btn {
  background: linear-gradient(135deg, #007aff, #0070f3);
  border: none;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.remix-result {
  margin-top: 16px;
}

.remix-result-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--mfc-blue);
}

.remix-seg-item {
  border: 1px solid var(--mfc-hairline);
  border-radius: 8px;
  margin-bottom: 8px;
  overflow: hidden;
}

.remix-seg-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--mfc-bg-soft);
  cursor: pointer;
  user-select: none;
}

.remix-seg-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.remix-stage-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 122, 255, 0.12);
  color: var(--mfc-blue);
  flex-shrink: 0;
}

.remix-duration {
  font-size: 11px;
  color: var(--mfc-fg-2);
  font-family: monospace;
  flex-shrink: 0;
}

.remix-function {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.remix-seg-body {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.remix-field {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.5;

  &.why {
    padding-top: 6px;
    border-top: 1px dashed var(--mfc-hairline);
  }
}

.remix-field-label {
  color: var(--mfc-fg-2);
  flex-shrink: 0;
  min-width: 28px;
}

.remix-field-val {
  color: var(--mfc-fg);
}
</style>
