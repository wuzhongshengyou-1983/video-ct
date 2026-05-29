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
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

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

interface Props {
  data: ViralDnaResult | null;
  loading: boolean;
}

defineProps<Props>();

// ---- 因子折叠状态 ----
const expandedFactors = ref<boolean[]>([true, false, false]);

function toggleFactor(i: number) {
  expandedFactors.value[i] = !expandedFactors.value[i];
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
  background: var(--vct-surface, #2a2a3c);
  border: 2px solid var(--vct-border, #3a3a4c);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: var(--vct-primary, #f59e0b);
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
  color: var(--vct-text-2, #9ca3af);
}

.platform-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.15);
  color: var(--vct-primary, #f59e0b);
  font-weight: 600;
}

.viral-score-box {
  text-align: center;
}

.viral-score-num {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.viral-score-label {
  font-size: 11px;
  color: var(--vct-text-2, #9ca3af);
  margin-top: 4px;
}

/* ---- 7 维评分条 ---- */
.dim-bar-row {
  padding: 8px 0;
  border-bottom: 1px dashed var(--vct-border, #3a3a4c);

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
    color: #10b981;
  }
  &.good {
    color: #38bdf8;
  }
  &.fair {
    color: #f59e0b;
  }
  &.poor {
    color: #ef4444;
  }
}

.dim-bar-track {
  height: 6px;
  background: var(--vct-surface, #2a2a3c);
  border-radius: 3px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;

  &.excellent {
    background: #10b981;
  }
  &.good {
    background: #38bdf8;
  }
  &.fair {
    background: #f59e0b;
  }
  &.poor {
    background: #ef4444;
  }
}

.dim-bar-evidence {
  font-size: 11px;
  color: var(--vct-text-2, #9ca3af);
  margin-top: 5px;
  line-height: 1.5;
}

/* ---- Top 3 贡献因子 ---- */
.factor-item {
  border-bottom: 1px dashed var(--vct-border, #3a3a4c);

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
  background: var(--vct-primary, #f59e0b);
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
  color: var(--vct-primary, #f59e0b);
  font-weight: 700;
}

.factor-evidence {
  font-size: 12px;
  color: var(--vct-text-2, #9ca3af);
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
  background: var(--vct-surface, #2a2a3c);
  border: 1px solid var(--vct-border, #3a3a4c);
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
  color: var(--vct-text-2, #9ca3af);
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
    background: #10b981;
  }
  &.good {
    background: #38bdf8;
  }
  &.fair {
    background: #f59e0b;
  }
  &.poor {
    background: #ef4444;
  }
}

.fframe-label {
  font-size: 12px;
  font-weight: 600;
}

.fframe-tactic {
  font-size: 10px;
  color: var(--vct-text-2, #9ca3af);
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
  background: var(--vct-surface, #2a2a3c);
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
      color: var(--vct-text-2, #9ca3af);
      line-height: 1.5;
      padding: 3px 0;
      border-bottom: 1px dashed var(--vct-border, #3a3a4c);

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
</style>
