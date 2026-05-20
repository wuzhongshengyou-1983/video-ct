<template>
  <div class="page">
    <van-nav-bar title="人设 IPP" left-arrow @click-left="router.back()" :border="false" />

    <van-loading v-if="loading" size="24" vertical class="loading-center">加载中…</van-loading>

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchData">重试</van-button>
    </div>

    <!-- 无人设档案：输入 + 扫描 -->
    <div v-if="!loading && !networkError && !persona" class="scan-section">
      <div class="vct-card intro-card">
        <div class="intro-icon">🎭</div>
        <div class="intro-title">人设 IPP 分析</div>
        <div class="intro-desc">
          基于 12 原型理论，AI 深度分析你的视频内容，精准定位你的人设定位、病灶和改进建议。
        </div>
      </div>

      <div class="vct-card form-card">
        <van-field
          v-model="description"
          label="账号描述"
          placeholder="简单描述你的账号定位和内容方向"
          type="textarea"
          rows="3"
          autosize
          :error="descError"
          :error-message="descError"
          @update:model-value="descError = ''"
        />
        <div class="vct-divider" />
        <van-field
          v-model="sampleUrls"
          label="视频链接"
          placeholder="选填，粘贴 1-3 条代表性视频链接，换行分隔"
          type="textarea"
          rows="2"
          autosize
        />
        <van-button
          type="primary"
          block
          class="scan-btn"
          :loading="scanning"
          @click="doScan"
        >
          开始扫描
        </van-button>
      </div>

      <!-- 12 原型库 -->
      <div class="vct-card archetypes-card">
        <div class="vct-section-title">📚 12 原型库</div>
        <div class="archetype-grid">
          <div
            v-for="a in archetypes"
            :key="a.name"
            class="archetype-item"
          >
            <div class="arch-emoji">{{ a.emoji || '🎭' }}</div>
            <div class="arch-name">{{ a.name }}</div>
            <div class="arch-desc">{{ a.tagline || '' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 有人设档案 -->
    <template v-if="persona">
      <!-- 6 维评分 -->
      <section class="vct-card glow score-card">
        <div class="match-title">人设匹配结果</div>
        <div class="primary-archetype">{{ persona.primary_archetype || '-' }}</div>
        <div class="match-pct" v-if="persona.match_score">
          匹配度 {{ persona.match_score }}%
        </div>
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
      </section>

      <!-- 人设画布 9 模块 -->
      <section v-if="persona.canvas" class="vct-card">
        <div class="vct-section-title">🎨 人设画布</div>
        <div class="canvas-grid">
          <div
            v-for="(val, key) in persona.canvas"
            :key="key"
            class="canvas-cell"
          >
            <div class="canvas-key">{{ canvasLabels[key] || key }}</div>
            <div class="canvas-val">{{ val }}</div>
          </div>
        </div>
      </section>

      <!-- 病灶 + 建议 -->
      <section v-if="persona.findings?.length" class="vct-card">
        <div class="vct-section-title">⚠ 病灶发现</div>
        <div v-for="(f, i) in persona.findings" :key="i" class="finding-item">
          <div class="finding-dim"><span class="vct-tag">{{ f.dimension || '综合' }}</span></div>
          <div class="finding-problem">{{ f.problem }}</div>
          <div class="finding-suggest">💡 {{ f.suggestion }}</div>
        </div>
      </section>

      <section v-if="persona.suggestions?.length" class="vct-card">
        <div class="vct-section-title">💡 改进建议</div>
        <div v-for="(s, i) in persona.suggestions" :key="i" class="suggest-item">
          <div class="suggest-priority" :class="prioCls(s.priority)">
            {{ s.priority || 'P2' }}
          </div>
          <div class="suggest-content">
            <div class="suggest-title">{{ s.title }}</div>
            <div class="suggest-detail">{{ s.detail }}</div>
          </div>
        </div>
      </section>

      <!-- 重新扫描 -->
      <div class="rescan-section">
        <van-button plain type="primary" size="small" @click="resetScan">
          重新扫描
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Toast } from 'vant'
import { personaApi } from '@/api'

const router = useRouter()

const loading = ref(true)
const networkError = ref(false)
const serverError = ref('')
const scanning = ref(false)
const persona = ref<any | null>(null)
const archetypes = ref<any[]>([])
const description = ref('')
const sampleUrls = ref('')
const descError = ref('')

const dimLabels: Record<string, string> = {
  authenticity: '真实性', consistency: '一致性', uniqueness: '独特性',
  relatability: '共鸣感', professionalism: '专业度', charisma: '魅力值',
}

const canvasLabels: Record<string, string> = {
  role: '人设角色', style: '风格基调', values: '核心价值观',
  audience: '目标受众', pain_point: '用户痛点', solution: '解决方案',
  differentiator: '差异化', content_pillar: '内容支柱', tone: '语调风格',
}

const dimensionScores = computed(() => {
  if (!persona.value?.dimension_scores) return persona.value?.scores || {}
  return persona.value.dimension_scores
})

function scoreColor(v: number) {
  if (v >= 80) return 'linear-gradient(90deg, #10b981, #34d399)'
  if (v >= 60) return 'linear-gradient(90deg, #38bdf8, #60a5fa)'
  if (v >= 40) return 'linear-gradient(90deg, #f59e0b, #fbbf24)'
  return 'linear-gradient(90deg, #ef4444, #f87171)'
}

function prioCls(p: string) {
  return p === 'P0' ? 'p0' : p === 'P1' ? 'p1' : 'p2'
}

// 缓存 key，避免重复请求
const PERSONA_CACHE_KEY = 'vct_persona_cache'

function loadCachedPersona(): any | null {
  try {
    const cached = localStorage.getItem(PERSONA_CACHE_KEY)
    if (cached) return JSON.parse(cached)
  } catch { /* ignore */ }
  return null
}

function saveCachedPersona(data: any) {
  try {
    localStorage.setItem(PERSONA_CACHE_KEY, JSON.stringify(data))
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true
  networkError.value = false
  serverError.value = ''
  try {
    const [p, a] = await Promise.all([
      personaApi.me().catch(() => null),
      personaApi.archetypes().catch(() => []),
    ])
    persona.value = p
    if (p) saveCachedPersona(p)
    archetypes.value = a || []
  } catch (e: any) {
    if (!navigator.onLine) {
      networkError.value = true
      // 尝试读取缓存
      persona.value = loadCachedPersona()
    } else if (e.status && e.status >= 500) {
      serverError.value = '服务繁忙，请稍后重试'
    } else {
      serverError.value = e.message || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

async function doScan() {
  if (!description.value.trim()) {
    descError.value = '请先填写账号描述'
    return
  }
  scanning.value = true
  try {
    const urls = sampleUrls.value
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)
    const result = await personaApi.scan({
      description: description.value,
      sample_video_urls: urls.length > 0 ? urls : undefined,
    })
    persona.value = result
    saveCachedPersona(result)
    Toast.success('扫描完成！')
  } catch (e: any) {
    if (e.status === 429) {
      Toast.fail('本月配额已用完，升级 PRO 解锁')
    } else if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '扫描失败')
    }
  } finally {
    scanning.value = false
  }
}

function resetScan() {
  persona.value = null
  description.value = ''
  sampleUrls.value = ''
  descError.value = ''
  try { localStorage.removeItem(PERSONA_CACHE_KEY) } catch { /* ignore */ }
}

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); min-height: 100vh; }
.loading-center { padding-top: 120px; display: flex; justify-content: center; }

.scan-section { margin-top: 16px; }
.intro-card {
  text-align: center; padding: 24px 16px;
  background: linear-gradient(135deg, rgba(56,189,248,0.08), rgba(245,158,11,0.06));
  .intro-icon { font-size: 48px; }
  .intro-title { font-size: 18px; font-weight: 700; margin: 8px 0; }
  .intro-desc { font-size: 13px; color: var(--vct-text-2); line-height: 1.6; }
}
.form-card { margin-top: 16px; padding: 16px; scroll-margin-bottom: 40vh; }
.scan-btn { margin-top: 16px; min-height: 44px; }

.archetypes-card { margin-top: 16px; }
.archetype-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  .archetype-item {
    background: var(--vct-surface); border-radius: var(--vct-radius);
    padding: 12px 6px; text-align: center; border: 1px solid var(--vct-border);
    .arch-emoji { font-size: 24px; }
    .arch-name { font-size: 12px; font-weight: 600; margin: 4px 0 2px; }
    .arch-desc { font-size: 10px; color: var(--vct-text-3); }
  }
}

.score-card {
  margin: 16px 0; padding: 20px 16px; text-align: center;
  background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(56,189,248,0.05));
  .match-title { font-size: 14px; color: var(--vct-text-2); }
  .primary-archetype { font-size: 24px; font-weight: 700; color: var(--vct-primary); margin: 8px 0; }
  .match-pct { font-size: 13px; color: var(--vct-accent); margin-bottom: 16px; }
  .dim-scores { text-align: left; }
  .dim-score-row {
    display: grid; grid-template-columns: 64px 1fr 32px; align-items: center; gap: 10px; padding: 4px 0;
    .dim-label { font-size: 12px; color: var(--vct-text-2); }
    .dim-val { font-size: 12px; font-weight: 600; text-align: right; }
  }
}

.canvas-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
  .canvas-cell {
    background: var(--vct-surface); border-radius: 8px; padding: 10px 8px;
    border: 1px solid var(--vct-border);
    .canvas-key { font-size: 10px; color: var(--vct-text-3); margin-bottom: 4px; }
    .canvas-val { font-size: 12px; color: var(--vct-text); word-break: break-all; }
  }
}

.finding-item {
  padding: 12px 0; border-bottom: 1px dashed var(--vct-border);
  &:last-child { border-bottom: none; }
  .finding-problem { font-size: 13px; margin-top: 6px; }
  .finding-suggest { font-size: 12px; color: var(--vct-text-2); margin-top: 4px; }
}

.suggest-item {
  display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px dashed var(--vct-border);
  &:last-child { border-bottom: none; }
  .suggest-priority {
    min-width: 32px; height: 24px; border-radius: 4px; text-align: center;
    font-size: 11px; font-weight: 600; line-height: 24px;
    background: var(--vct-surface); color: var(--vct-text-3);
    &.p0 { background: rgba(239,68,68,0.15); color: #ef4444; }
    &.p1 { background: rgba(245,158,11,0.15); color: #f59e0b; }
    &.p2 { background: rgba(107,114,128,0.15); color: #9ca3af; }
  }
  .suggest-content { flex: 1; }
  .suggest-title { font-size: 13px; font-weight: 600; }
  .suggest-detail { font-size: 12px; color: var(--vct-text-2); margin-top: 4px; }
}

.rescan-section { text-align: center; padding: 16px 0; }

.error-box { margin-top: 24px; text-align: center; padding: 24px;
  p { color: var(--vct-danger); font-size: 13px; margin-bottom: 12px; }
}
</style>
