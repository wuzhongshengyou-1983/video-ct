<template>
  <div class="page">
    <van-nav-bar title="品牌分享官" left-arrow @click-left="router.back()" :border="false" />

    <!-- 骨架屏加载 -->
    <SkeletonCard v-if="loading" :lines="4" />

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchData">重试</van-button>
    </div>

    <!-- 下拉刷新包裹内容 -->
    <van-pull-refresh
      v-if="!loading && !networkError && data"
      v-model="refreshing"
      @refresh="onRefresh"
      success-text="刷新成功"
      :head-height="80"
    >
    <template v-if="!loading && !networkError && data">
      <!-- 等级卡片 -->
      <section class="vct-card glow level-card">
        <div class="level-badge" :class="levelCls(data.level)">
          {{ getLevelLabel(data.level) }}
        </div>
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-num">{{ data.total_referrals || data.total_valid_referrals || 0 }}</div>
            <div class="stat-label">推荐人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-num">{{ data.total_reward_cny || data.total_rewards_cny || 0 }}</div>
            <div class="stat-label">累积奖励(元)</div>
          </div>
          <div class="stat-item">
            <div class="stat-num balance">{{ data.balance_cny || data.cash_balance_cny || 0 }}</div>
            <div class="stat-label">可提现余额(元)</div>
          </div>
        </div>
        <div v-if="nextLevel" class="next-level">
          距 {{ nextLevel.name }} 还差 {{ nextLevel.need }} 人
        </div>
      </section>

      <!-- 专属链接 -->
      <section class="vct-card">
        <div class="vct-section-title">🔗 专属邀请链接</div>
        <div class="link-row">
          <div class="link-text">{{ linkUrl }}</div>
          <van-button size="small" type="primary" @click="copyLink">复制</van-button>
        </div>
        <div class="link-tip">每邀请 1 位好友付费，你可得 {{ REFERRER_REWARD_CNY }} 元奖励</div>
      </section>

      <!-- 提现 -->
      <section class="vct-card">
        <div class="vct-section-title">💵 提现</div>
        <div class="withdraw-row">
          <van-field
            v-model="withdrawAmount"
            label="金额"
            placeholder="输入提现金额（最低 {{ MIN_WITHDRAW_CNY }} 元）"
            type="number"
            :error="withdrawError"
            :error-message="withdrawError"
            @update:model-value="withdrawError = ''"
          />
          <van-button
            type="primary"
            size="small"
            :loading="withdrawing"
            :disabled="!withdrawAmount || Number(withdrawAmount) <= 0"
            @click="doWithdraw"
          >
            提现
          </van-button>
        </div>
      </section>

      <!-- 推荐记录（无限滚动） -->
      <section class="vct-card">
        <div class="vct-section-title">📋 推荐记录（{{ allRecords.length }}）</div>
        <div v-if="allRecords.length === 0" class="no-data">暂无推荐记录</div>
        <van-list
          v-else
          v-model:loading="recordsLoading"
          :finished="recordsFinished"
          finished-text="没有更多了"
          @load="onLoadRecords"
        >
          <div v-for="r in records" :key="r.id" class="record-item">
            <div class="record-left">
              <div class="record-name">{{ r.referee_name || r.invitee_nickname || '匿名用户' }}</div>
              <div class="record-meta">
                <span>{{ formatTime(r.created_at) }}</span>
                <span>· {{ r.status_label || r.status }}</span>
              </div>
            </div>
            <div class="record-reward" v-if="r.reward_cny || r.reward_amount_cny">+{{ r.reward_cny || r.reward_amount_cny }}元</div>
          </div>
        </van-list>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Toast } from 'vant'
import { referrerApi } from '@/api'
import {
  formatTime,
  getLevelLabel,
  REFERRER_THRESHOLDS,
  REFERRER_REWARD_CNY,
  MIN_WITHDRAW_CNY,
} from '@video-ct/shared'
import { trackClick } from '@/utils/tracker'
import SkeletonCard from '@/components/SkeletonCard.vue'
import { useWechatShare, SHARE_TEXT } from '@/composables/useWechatShare'

const router = useRouter()
const { updateShare } = useWechatShare()

const loading = ref(true)
const networkError = ref(false)
const serverError = ref('')
const refreshing = ref(false)
const data = ref<any | null>(null)
const allRecords = ref<any[]>([])
const records = ref<any[]>([])
const linkUrl = ref('')
const withdrawAmount = ref('')
const withdrawError = ref('')
const withdrawing = ref(false)

// 分页
const recordsLoading = ref(false)
const recordsFinished = ref(false)
const recordsPage = ref(1)
const RECORDS_PAGE_SIZE = 10

const levelConfig: Record<string, { name: string; min: number }> = {
  bronze: { name: '银牌分享官', min: REFERRER_THRESHOLDS.silver },
  silver: { name: '金牌分享官', min: REFERRER_THRESHOLDS.gold },
  gold: { name: '钻石分享官', min: REFERRER_THRESHOLDS.diamond },
  diamond: { name: '已达最高级', min: Infinity },
}

const nextLevel = computed(() => {
  if (!data.value) return null
  const level = data.value.level || 'bronze'
  const current = data.value.total_referrals || data.value.total_valid_referrals || 0
  const cfg = levelConfig[level]
  if (!cfg || cfg.min === Infinity) return null
  const need = cfg.min - current
  if (need <= 0) return null
  return { name: cfg.name, need }
})

function levelCls(l: string) {
  const map: Record<string, string> = { bronze: 'bronze', silver: 'silver', gold: 'gold', diamond: 'diamond' }
  return map[l] || 'bronze'
}

function getBalance(): number {
  return data.value?.balance_cny || data.value?.cash_balance_cny || 0
}

async function fetchData() {
  loading.value = true
  networkError.value = false
  serverError.value = ''
  try {
    const [d, recs, link] = await Promise.all([
      referrerApi.me(),
      referrerApi.records().catch(() => []),
      referrerApi.link().catch(() => ({ url: '' })),
    ])
    data.value = d
    allRecords.value = recs || []
    records.value = []
    recordsPage.value = 1
    recordsFinished.value = false
    linkUrl.value = link?.url || link?.link || link?.h5_url || ''
    onLoadRecords()
  } catch (e: any) {
    if (!navigator.onLine) {
      networkError.value = true
    } else if (e.status && e.status >= 500) {
      serverError.value = '服务繁忙，请稍后重试'
    } else {
      serverError.value = e.message || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

function onLoadRecords() {
  const start = (recordsPage.value - 1) * RECORDS_PAGE_SIZE
  const chunk = allRecords.value.slice(start, start + RECORDS_PAGE_SIZE)
  if (chunk.length > 0) {
    records.value.push(...chunk)
    recordsPage.value++
  }
  recordsLoading.value = false
  if (records.value.length >= allRecords.value.length) {
    recordsFinished.value = true
  }
}

async function onRefresh() {
  await fetchData()
  refreshing.value = false
}

async function copyLink() {
  trackClick('copy_link')
  try {
    await navigator.clipboard.writeText(linkUrl.value)
    Toast.success('已复制，分享给朋友吧')
  } catch {
    // clipboard API 不可用时降级
    const ta = document.createElement('textarea')
    ta.value = linkUrl.value
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try {
      document.execCommand('copy')
      Toast.success('已复制，分享给朋友吧')
    } catch {
      Toast.fail('复制失败，请长按手动复制')
    }
    document.body.removeChild(ta)
  }
}

async function doWithdraw() {
  const amount = Number(withdrawAmount.value)
  if (!amount || amount <= 0) {
    withdrawError.value = '请输入有效金额'
    return
  }
  if (amount < MIN_WITHDRAW_CNY) {
    withdrawError.value = `最低提现金额为 ${MIN_WITHDRAW_CNY} 元`
    return
  }
  const balance = getBalance()
  if (amount > balance) {
    withdrawError.value = '余额不足'
    return
  }
  withdrawing.value = true
  try {
    await referrerApi.withdraw(amount)
    Toast.success('提现申请已提交')
    withdrawAmount.value = ''
    withdrawError.value = ''
    // 更新本地余额
    if (data.value) {
      const key = data.value.balance_cny !== undefined ? 'balance_cny' : 'cash_balance_cny'
      data.value[key] = balance - amount
    }
  } catch (e: any) {
    if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '提现失败')
    }
  } finally {
    withdrawing.value = false
  }
}

onMounted(() => {
  updateShare(SHARE_TEXT.referrer.title, SHARE_TEXT.referrer.desc)
  fetchData()
})
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); min-height: 100vh; }
.loading-center { padding-top: 120px; display: flex; justify-content: center; }

.level-card {
  margin: 16px 0; padding: 20px 16px; text-align: center;
  background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(56,189,248,0.06));
  border-color: rgba(245,158,11,0.3);
  .level-badge {
    display: inline-block; padding: 4px 16px; border-radius: 999px; font-size: 13px; font-weight: 700;
    background: var(--vct-surface); color: var(--vct-text-2);
    &.silver { background: rgba(192,192,192,0.2); color: #c0c0c0; }
    &.gold { background: rgba(245,158,11,0.2); color: var(--vct-primary); }
    &.diamond { background: rgba(56,189,248,0.2); color: var(--vct-accent); }
  }
  .stats-row { display: flex; justify-content: space-around; margin: 16px 0 12px; }
  .stat-item { text-align: center; }
  .stat-num { font-size: 24px; font-weight: 800; color: var(--vct-text);
    &.balance { color: var(--vct-primary); }
  }
  .stat-label { font-size: 11px; color: var(--vct-text-3); margin-top: 2px; }
  .next-level {
    font-size: 12px; color: var(--vct-accent);
    background: rgba(56,189,248,0.1); display: inline-block;
    padding: 2px 12px; border-radius: 999px;
  }
}

.link-row {
  display: flex; gap: 8px; align-items: center;
  .link-text {
    flex: 1; font-size: 12px; color: var(--vct-text-2); word-break: break-all;
    background: var(--vct-surface); padding: 8px 10px; border-radius: 8px;
    border: 1px solid var(--vct-border);
  }
}
.link-tip { font-size: 11px; color: var(--vct-text-3); margin-top: 10px; }

.withdraw-row { display: flex; align-items: center; gap: 8px; scroll-margin-bottom: 40vh; }
.no-data { font-size: 13px; color: var(--vct-text-3); padding: 16px 0; text-align: center; }

.record-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; border-bottom: 1px dashed var(--vct-border);
  &:last-child { border-bottom: none; }
  .record-name { font-size: 14px; font-weight: 500; }
  .record-meta { font-size: 11px; color: var(--vct-text-3); margin-top: 2px; }
  .record-reward { font-size: 14px; font-weight: 600; color: var(--vct-primary); }
}

.error-box { margin-top: 24px; text-align: center; padding: 24px;
  p { color: var(--vct-danger); font-size: 13px; margin-bottom: 12px; }
}
</style>
