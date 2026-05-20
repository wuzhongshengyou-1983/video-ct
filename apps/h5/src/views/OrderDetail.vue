<template>
  <div class="page">
    <van-nav-bar title="订单详情" left-arrow @click-left="goBack" :border="false" />

    <van-loading v-if="loading" size="24" vertical class="loading-center">加载订单…</van-loading>

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchOrder">重试</van-button>
    </div>

    <!-- 订单信息 -->
    <div v-if="order && !loading && !networkError" class="order-card vct-card glow">
      <div class="status-badge" :class="order.pay_status">
        {{ getPaymentStatusLabel(order.pay_status) }}
      </div>
      <div class="order-no">订单号：{{ order.order_no }}</div>
      <div class="order-product">{{ order.product_name || order.sku }}</div>
      <div class="order-amount">¥{{ order.amount_cny }}</div>

      <div class="order-details">
        <div class="detail-row">
          <span class="label">创建时间</span>
          <span class="value">{{ formatDateTime(order.created_at) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">支付方式</span>
          <span class="value">{{ order.pay_channel || '-' }}</span>
        </div>
        <div class="detail-row" v-if="order.paid_at">
          <span class="label">支付时间</span>
          <span class="value">{{ formatDateTime(order.paid_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 待支付：真实支付 -->
    <div v-if="order?.pay_status === 'pending'" class="pay-section">
      <!-- 微信内 JSAPI 支付 -->
      <van-button
        v-if="payChannel === 'wechat'"
        type="primary" block size="large" :loading="paying"
        @click="doPay"
      >
        微信支付 ¥{{ order.paid_cny ?? order.amount_cny }}
      </van-button>

      <!-- 微信外 H5 支付 -->
      <div v-if="payChannel === 'h5'" class="h5-pay">
        <p class="h5-tip">请在微信中打开此页面完成支付，或使用下方链接</p>
        <van-button type="primary" block size="large" @click="openH5Pay">
          前往微信支付
        </van-button>
      </div>

      <!-- DEV 模拟支付（仅开发环境） -->
      <div v-if="payChannel === 'dev'" class="dev-pay">
        <van-button type="primary" block size="large" :loading="paying" @click="doMockPay">
          [DEV] 模拟支付 ¥{{ order.paid_cny ?? order.amount_cny }}
        </van-button>
        <p class="dev-tip">开发环境，点击即可完成支付（商户号未配置）</p>
      </div>
    </div>

    <!-- 已支付：成功提示 -->
    <div v-if="order?.pay_status === 'paid'" class="success-section">
      <div class="success-icon">✓</div>
      <div class="success-text">支付成功</div>
      <van-button type="primary" block size="large" @click="goBack">
        返回上页
      </van-button>
    </div>

    <!-- 服务端错误 -->
    <div v-if="!loading && serverError" class="error-box vct-card">
      <p>{{ serverError }}</p>
      <van-button size="small" @click="fetchOrder">重试</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Toast } from 'vant'
import { subscriptionApi } from '@/api'
import { isWechat, wechatPay, openPayUrl } from '@/utils/pay'
import type { WxPayParams } from '@/utils/pay'
import { formatDateTime, getPaymentStatusLabel } from '@video-ct/shared'

const router = useRouter()
const route = useRoute()
const orderNo = route.params.no as string

const loading = ref(true)
const networkError = ref(false)
const serverError = ref('')
const paying = ref(false)
const order = ref<any | null>(null)
const payParams = ref<WxPayParams | null>(null)

// 支付渠道判断：wechat(微信JSAPI) / h5(微信外H5) / dev(开发模拟)
const payChannel = computed(() => {
  if (import.meta.env.DEV) return 'dev'
  if (isWechat()) return 'wechat'
  return 'h5'
})

let pollTimer: ReturnType<typeof setInterval> | null = null
let pollStart = 0
const POLL_MAX_MS = 60_000
const POLL_INTERVAL = 2000

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/home')
  }
}

async function fetchOrder() {
  loading.value = true
  networkError.value = false
  serverError.value = ''
  try {
    const orders = await subscriptionApi.myOrders()
    if (orders === null) {
      networkError.value = true
      return
    }
    const found = orders.find((o: any) => o.order_no === orderNo)
    if (!found) {
      serverError.value = '订单不存在'
      return
    }
    order.value = found
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

function startPolling() {
  if (pollTimer) return
  pollStart = Date.now()
  pollTimer = setInterval(async () => {
    if (Date.now() - pollStart > POLL_MAX_MS) {
      stopPolling()
      Toast.fail('支付超时，请联系客服')
      return
    }
    try {
      const status = await subscriptionApi.checkPayStatus(orderNo)
      if (status) {
        order.value = { ...order.value, ...status }
        if (status.payment_status === 'paid' || status.payment_status === 'cancelled') {
          stopPolling()
          if (status.payment_status === 'paid') {
            Toast.success('支付成功！')
          }
        }
      }
    } catch {
      // 轮询失败不提示，等下一轮
    }
  }, POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// DEV 环境保留模拟支付
async function doMockPay() {
  paying.value = true
  try {
    await subscriptionApi.getPayParams(orderNo) // 即使 mock 也走统一流程
    // DEV 模式直接标记支付成功
    startPolling()
  } catch (e: any) {
    if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '支付失败')
    }
  } finally {
    paying.value = false
  }
}

// 真实支付流程
async function doPay() {
  paying.value = true
  try {
    // 1. 获取支付参数
    const params = await subscriptionApi.getPayParams(orderNo)
    if (!params) {
      Toast.fail('获取支付参数失败')
      return
    }
    payParams.value = params as WxPayParams

    // 2. mock 模式：直接开始轮询
    if (params.mock) {
      Toast.success('[DEV] 模拟支付已触发')
      startPolling()
      return
    }

    // 3. 微信 JSAPI 支付
    if (isWechat() && params.prepay_id) {
      const result = await wechatPay(params as WxPayParams)
      if (result.success) {
        startPolling()
      } else if (result.message === '用户取消支付') {
        Toast.fail('支付已取消')
      } else {
        Toast.fail(result.message || '支付失败')
      }
      return
    }

    // 4. 微信外 H5 支付
    if (params.pay_url) {
      openPayUrl(params.pay_url)
      // 跳转后开始轮询（用户可能在新窗口完成支付）
      startPolling()
      return
    }

    Toast.fail('暂不支持此支付方式')
  } catch (e: any) {
    if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '支付失败')
    }
  } finally {
    paying.value = false
  }
}

// 微信外 H5：复制/打开支付链接
function openH5Pay() {
  if (payParams.value?.pay_url) {
    openPayUrl(payParams.value.pay_url)
  } else {
    Toast.fail('支付链接不可用')
  }
}

onMounted(async () => {
  await fetchOrder()
  if (order.value?.pay_status === 'pending') {
    startPolling()
  }
})

onUnmounted(stopPolling)
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); min-height: 100vh; }
.loading-center { padding-top: 120px; display: flex; justify-content: center; }

.order-card {
  margin: 16px 0; padding: 24px 16px; text-align: center;
  background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(56,189,248,0.06));
  .status-badge {
    display: inline-block; padding: 4px 14px; border-radius: 999px; font-size: 12px; font-weight: 600;
    background: var(--vct-surface); color: var(--vct-text-2);
    &.pending { background: rgba(245,158,11,0.15); color: var(--vct-warning); }
    &.paid { background: rgba(16,185,129,0.15); color: var(--vct-success); }
    &.cancelled { background: rgba(239,68,68,0.15); color: var(--vct-danger); }
    &.refunded { background: rgba(107,114,128,0.15); color: var(--vct-text-3); }
  }
  .order-no { font-size: 12px; color: var(--vct-text-3); margin-top: 12px; word-break: break-all; }
  .order-product { font-size: 16px; font-weight: 600; margin: 8px 0; }
  .order-amount { font-size: 40px; font-weight: 800; color: var(--vct-primary); }
  .order-details { margin-top: 16px; text-align: left; }
  .detail-row {
    display: flex; justify-content: space-between; padding: 8px 0;
    border-bottom: 1px dashed var(--vct-border);
    .label { font-size: 12px; color: var(--vct-text-3); }
    .value { font-size: 13px; color: var(--vct-text); }
  }
}

.pay-section { margin-top: 24px; text-align: center; }
.dev-tip { font-size: 11px; color: var(--vct-text-3); margin-top: 12px; }
.h5-pay { margin-top: 12px; }
.h5-tip { font-size: 13px; color: var(--vct-text-3); margin-bottom: 16px; line-height: 1.6; }
.dev-pay { margin-top: 8px; }

.success-section { margin-top: 24px; text-align: center; }
.success-icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #34d399);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 32px; color: #fff; margin-bottom: 12px;
}
.success-text { font-size: 18px; font-weight: 600; margin-bottom: 24px; }

.error-box { margin-top: 24px; text-align: center; padding: 24px;
  p { color: var(--vct-danger); font-size: 13px; margin-bottom: 12px; }
}
</style>
