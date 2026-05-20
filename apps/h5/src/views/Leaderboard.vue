<template>
  <div class="page">
    <van-nav-bar title="分享榜单" left-arrow @click-left="router.back()" :border="false" />

    <van-loading v-if="loading" size="24" vertical class="loading-center">加载榜单…</van-loading>

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchData">重试</van-button>
    </div>

    <template v-if="!loading && !networkError && list.length > 0">
      <div class="board-header">
        <div class="board-title">🏆 本月分享官 TOP 榜</div>
        <div class="board-sub">按本月推荐人数排名</div>
      </div>

      <div class="board-list">
        <div
          v-for="(item, index) in list"
          :key="item.user_id || index"
          class="board-item vct-card"
          :class="topCls(index)"
        >
          <div class="rank-num" :class="rankCls(index)">
            <template v-if="index === 0">🥇</template>
            <template v-else-if="index === 1">🥈</template>
            <template v-else-if="index === 2">🥉</template>
            <template v-else>#{{ index + 1 }}</template>
          </div>
          <div class="avatar-placeholder">{{ avatarText(item.nickname) }}</div>
          <div class="user-info">
            <div class="nickname">{{ item.nickname || '匿名用户' }}</div>
            <div class="user-level">{{ REFERRER_LEVEL_LABELS[item.level] || item.level || 'Lv.1' }}</div>
          </div>
          <div class="user-stats">
            <div class="stat-referrals">{{ item.monthly_referrals || 0 }}人</div>
            <div class="stat-reward">{{ item.monthly_reward_cny || item.monthly_rewards_cny || 0 }}元</div>
          </div>
        </div>
      </div>
    </template>

    <!-- 空状态 -->
    <van-empty v-if="!loading && !networkError && list.length === 0" description="本月暂无排行数据" />

    <!-- 错误 -->
    <div v-if="errorMsg" class="error-box vct-card">
      <p>{{ errorMsg }}</p>
      <van-button size="small" @click="fetchData">重试</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { referrerApi } from '@/api'
import { REFERRER_LEVEL_LABELS } from '@video-ct/shared'

const router = useRouter()

const loading = ref(true)
const errorMsg = ref('')
const networkError = ref(false)
const list = ref<any[]>([])

function topCls(index: number) {
  if (index === 0) return 'top-1'
  if (index === 1) return 'top-2'
  if (index === 2) return 'top-3'
  return ''
}

function rankCls(index: number) {
  if (index < 3) return 'medal'
  return 'normal'
}

function avatarText(name: string) {
  return (name || '?').charAt(0).toUpperCase()
}

async function fetchData() {
  loading.value = true
  errorMsg.value = ''
  networkError.value = false
  try {
    list.value = await referrerApi.leaderboard()
  } catch (e: any) {
    if (!navigator.onLine) {
      networkError.value = true
    } else if (e.status && e.status >= 500) {
      errorMsg.value = '服务繁忙，请稍后重试'
    } else {
      errorMsg.value = e.message || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); min-height: 100vh; }
.loading-center { padding-top: 120px; display: flex; justify-content: center; }

.board-header {
  text-align: center; padding: 20px 0 16px;
  .board-title { font-size: 18px; font-weight: 700; }
  .board-sub { font-size: 12px; color: var(--vct-text-3); margin-top: 4px; }
}

.board-list { display: flex; flex-direction: column; gap: 8px; }
.board-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  &.top-1 { border-color: rgba(245,158,11,0.5); background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.03)); }
  &.top-2 { border-color: rgba(192,192,192,0.4); background: linear-gradient(135deg, rgba(192,192,192,0.08), rgba(192,192,192,0.02)); }
  &.top-3 { border-color: rgba(205,127,50,0.35); background: linear-gradient(135deg, rgba(205,127,50,0.08), rgba(205,127,50,0.02)); }
}

.rank-num {
  width: 32px; text-align: center; font-size: 18px;
  &.medal { font-size: 24px; }
  &.normal { font-size: 14px; font-weight: 700; color: var(--vct-text-3); }
}

.avatar-placeholder {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, var(--vct-primary), var(--vct-accent));
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #fff; flex-shrink: 0;
}

.user-info { flex: 1; }
.nickname { font-size: 14px; font-weight: 500; }
.user-level { font-size: 11px; color: var(--vct-text-3); margin-top: 2px; }

.user-stats { text-align: right; }
.stat-referrals { font-size: 14px; font-weight: 600; color: var(--vct-primary); }
.stat-reward { font-size: 11px; color: var(--vct-text-3); }

.error-box { margin-top: 24px; text-align: center; padding: 24px;
  p { color: var(--vct-danger); font-size: 13px; margin-bottom: 12px; }
}
</style>
