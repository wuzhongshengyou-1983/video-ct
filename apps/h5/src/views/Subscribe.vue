<template>
  <div class="page">
    <van-nav-bar title="升级订阅" left-arrow @click-left="router.back()" :border="false" />

    <!-- 加载中 -->
    <van-loading v-if="loading" size="24" vertical class="loading-center">加载产品中…</van-loading>

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="fetchData">重试</van-button>
    </div>

    <!-- 当前订阅 -->
    <div v-if="mySub && !loading && !networkError" class="current-sub vct-card glow">
      <div class="sub-header">
        <span class="sub-tier">{{ getTierLabel(mySub.tier) }}</span>
        <span v-if="mySub.expires_at" class="sub-expire">
          {{ mySub.auto_renew ? '自动续费中' : '到期 ' + formatTime(mySub.expires_at) }}
        </span>
      </div>
      <div class="sub-quota">
        本月扫描：{{ mySub.monthly_scans_used || 0 }} / {{ mySub.monthly_scans_quota || 3 }}
      </div>
      <van-button v-if="mySub.tier !== 'free'" size="small" plain type="primary" @click="renewSub" :loading="renewing">
        续费
      </van-button>
    </div>

    <!-- 产品列表 -->
    <div v-if="!loading && !networkError" class="product-list">
      <div
        v-for="p in products"
        :key="p.sku"
        class="product-card vct-card"
        :class="{ recommended: p.recommended }"
      >
        <div v-if="p.recommended" class="rec-badge">推荐</div>
        <div class="prod-name">{{ p.name }}</div>
        <div class="prod-price">
          <span class="currency">¥</span>
          <span class="amount">{{ p.price }}</span>
          <span v-if="p.original_price" class="original">¥{{ p.original_price }}</span>
          <span class="period">/{{ p.period_label || '月' }}</span>
        </div>
        <ul v-if="p.benefits?.length" class="benefits">
          <li v-for="(b, i) in p.benefits" :key="i">{{ b }}</li>
        </ul>
        <van-button
          type="primary"
          block
          :loading="buyingSku === p.sku"
          :disabled="mySub?.tier === p.tier?.toLowerCase() && mySub?.status === 'active'"
          @click="buy(p)"
        >
          {{ mySub?.tier === p.tier?.toLowerCase() && mySub?.status === 'active' ? '当前方案' : '立即购买' }}
        </van-button>
      </div>
    </div>

    <!-- 空状态 -->
    <van-empty v-if="!loading && !networkError && products.length === 0" description="暂无可选产品" />

    <!-- 服务端错误 -->
    <div v-if="!loading && serverError" class="error-box vct-card">
      <p>{{ serverError }}</p>
      <van-button size="small" @click="fetchData">重试</van-button>
    </div>

    <!-- 支付弹窗 -->
    <van-dialog
      v-model:show="showPay"
      title="确认支付"
      :show-cancel-button="false"
      @confirm="confirmPay"
      :confirm-loading="paying"
    >
      <div class="pay-info">
        <p><strong>{{ selectedProduct?.name }}</strong></p>
        <p class="pay-price">¥{{ selectedProduct?.price }}</p>
        <p v-if="orderResult?.order_no" class="pay-order">订单号：{{ orderResult.order_no }}</p>
        <p class="pay-tip">开发环境，使用模拟支付</p>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Toast } from 'vant'
import { subscriptionApi } from '@/api'
import { formatTime, getTierLabel } from '@video-ct/shared'

const router = useRouter()

const loading = ref(true)
const networkError = ref(false)
const serverError = ref('')
const products = ref<any[]>([])
const mySub = ref<any | null>(null)
const buyingSku = ref('')
const renewing = ref(false)
const showPay = ref(false)
const paying = ref(false)
const selectedProduct = ref<any | null>(null)
const orderResult = ref<any | null>(null)

async function fetchData() {
  loading.value = true
  networkError.value = false
  serverError.value = ''
  try {
    const [prods, sub] = await Promise.all([
      subscriptionApi.products().catch(() => null),
      subscriptionApi.mySubscription().catch(() => null),
    ])
    if (prods === null) {
      networkError.value = true
      return
    }
    products.value = prods || []
    mySub.value = sub
  } catch (e: any) {
    if (e.status && e.status >= 500) {
      serverError.value = '服务繁忙，请稍后重试'
    } else {
      serverError.value = e.message || '加载失败'
    }
    products.value = []
  } finally {
    loading.value = false
  }
}

async function buy(p: any) {
  selectedProduct.value = p
  buyingSku.value = p.sku
  try {
    orderResult.value = await subscriptionApi.createOrder(p.sku)
    showPay.value = true
  } catch (e: any) {
    if (e.status === 402) {
      Toast.fail('套餐已是最新，无需重复购买')
    } else if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '下单失败')
    }
  } finally {
    buyingSku.value = ''
  }
}

async function confirmPay() {
  if (!orderResult.value?.order_no) return
  paying.value = true
  try {
    await subscriptionApi.mockPay(orderResult.value.order_no)
    Toast.success('支付成功！')
    showPay.value = false
    router.push(`/order/${orderResult.value.order_no}`)
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

async function renewSub() {
  if (!mySub.value?.sku) {
    Toast.fail('未找到当前套餐信息')
    return
  }
  renewing.value = true
  try {
    const order = await subscriptionApi.createOrder(mySub.value.sku)
    router.push(`/order/${order.order_no}`)
  } catch (e: any) {
    if (e.status && e.status >= 500) {
      Toast.fail('服务繁忙，请稍后重试')
    } else {
      Toast.fail(e.message || '续费下单失败')
    }
  } finally {
    renewing.value = false
  }
}

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.page { padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px)); min-height: 100vh; }
.loading-center { padding-top: 120px; display: flex; justify-content: center; }

.current-sub {
  margin: 16px 0; padding: 16px;
  background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(56,189,248,0.06));
  border-color: rgba(245,158,11,0.25);
  .sub-header { display: flex; justify-content: space-between; align-items: center; }
  .sub-tier { font-size: 18px; font-weight: 700; color: var(--vct-primary); }
  .sub-expire { font-size: 12px; color: var(--vct-text-3); }
  .sub-quota { font-size: 13px; color: var(--vct-text-2); margin: 8px 0 12px; }
}

.product-list { display: flex; flex-direction: column; gap: 14px; margin-top: 16px; }
.product-card {
  padding: 20px 16px; position: relative;
  &.recommended { border-color: rgba(245,158,11,0.4); box-shadow: var(--vct-glow); }
  .rec-badge {
    position: absolute; top: -8px; right: 16px;
    padding: 2px 12px; background: var(--vct-primary); color: #000;
    font-size: 11px; font-weight: 600; border-radius: 999px;
  }
  .prod-name { font-size: 17px; font-weight: 600; }
  .prod-price { margin: 8px 0 12px; }
  .currency { font-size: 14px; color: var(--vct-primary); }
  .amount { font-size: 36px; font-weight: 800; color: var(--vct-primary); }
  .original { font-size: 14px; color: var(--vct-text-3); text-decoration: line-through; margin-left: 8px; }
  .period { font-size: 12px; color: var(--vct-text-3); }
  .benefits {
    margin: 0 0 16px; padding-left: 18px;
    li { font-size: 12px; color: var(--vct-text-2); line-height: 1.8; }
  }
}

.error-box {
  margin-top: 24px; text-align: center; padding: 24px;
  p { color: var(--vct-danger); font-size: 13px; margin-bottom: 12px; }
}

.pay-info {
  padding: 16px 24px 8px; text-align: center;
  .pay-price { font-size: 32px; font-weight: 800; color: var(--vct-primary); margin: 8px 0; }
  .pay-order { font-size: 12px; color: var(--vct-text-2); }
  .pay-tip { font-size: 11px; color: var(--vct-text-3); margin-top: 8px; }
}
</style>
