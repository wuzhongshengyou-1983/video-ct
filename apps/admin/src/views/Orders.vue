<script setup lang="ts">
import { listOrders, refundOrder, type OrderQuery } from '@/api/admin'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { DollarOutlined } from '@ant-design/icons-vue'

interface OrderRecord {
  id: string
  order_no?: string
  user_id?: string
  user_phone?: string
  product_name?: string
  amount_cny?: number
  amount?: number
  pay_status?: string
  status?: string
  created_at: string
}

const orders = ref<OrderRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const statusFilter = ref<string | undefined>(undefined)
const timeRange = ref<string | undefined>(undefined)
const refundingId = ref<string | null>(null)

const timeRangeOptions = [
  { label: '近 7 天', value: '7d' },
  { label: '近 30 天', value: '30d' },
  { label: '本月', value: 'this_month' },
]

const columns = [
  { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 200, ellipsis: true },
  { title: '用户', dataIndex: 'user_phone', key: 'user_phone', width: 130 },
  { title: '产品', dataIndex: 'product_name', key: 'product_name', width: 160 },
  { title: '金额', dataIndex: 'amount_cny', key: 'amount_cny', width: 100 },
  { title: '支付状态', dataIndex: 'pay_status', key: 'pay_status', width: 100 },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'actions', width: 100, fixed: 'right' as const },
]

const payStatusMap: Record<string, string> = {
  paid: '已支付', unpaid: '未支付', refunded: '已退款', cancelled: '已取消',
}
const payStatusColors: Record<string, string> = {
  paid: 'green', unpaid: 'orange', refunded: 'red', cancelled: 'default',
}

function getTimeRangeParams(): { start?: string; end?: string } {
  if (!timeRange.value) return {}
  const now = dayjs()
  if (timeRange.value === '7d') {
    return { start: now.subtract(7, 'day').format('YYYY-MM-DD'), end: now.format('YYYY-MM-DD') }
  }
  if (timeRange.value === '30d') {
    return { start: now.subtract(30, 'day').format('YYYY-MM-DD'), end: now.format('YYYY-MM-DD') }
  }
  if (timeRange.value === 'this_month') {
    return { start: now.startOf('month').format('YYYY-MM-DD'), end: now.format('YYYY-MM-DD') }
  }
  return {}
}

async function fetchOrders() {
  loading.value = true
  try {
    const timeParams = getTimeRangeParams()
    const params: OrderQuery & { start?: string; end?: string } = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...timeParams,
    }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await listOrders(params)
    orders.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetchOrders()
}

async function handleRefund(record: OrderRecord) {
  refundingId.value = record.id
  try {
    await refundOrder(record.id)
    message.success('退款申请已提交')
    fetchOrders()
  } finally {
    refundingId.value = null
  }
}

function formatAmount(n?: number): string {
  if (n == null) return '¥0'
  if (n >= 1000) return '¥' + n.toLocaleString()
  return '¥' + n.toFixed(2).replace(/\.?0+$/, '')
}

onMounted(fetchOrders)
</script>

<template>
  <div class="orders-page">
    <div class="page-header">
      <h2>订单管理</h2>
      <a-space>
        <a-select
          v-model:value="timeRange"
          placeholder="时间范围"
          allow-clear
          style="width: 130px"
          :options="timeRangeOptions"
          @change="() => { pagination.current = 1; fetchOrders() }"
        />
        <a-select
          v-model:value="statusFilter"
          placeholder="支付状态筛选"
          allow-clear
          style="width: 140px"
          @change="() => { pagination.current = 1; fetchOrders() }"
        >
          <a-select-option value="paid">已支付</a-select-option>
          <a-select-option value="unpaid">未支付</a-select-option>
          <a-select-option value="refunded">已退款</a-select-option>
        </a-select>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="orders"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 1000 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'amount_cny'">
            <span :style="{ color: '#10b981', fontWeight: 500 }">
              {{ formatAmount(record.amount_cny ?? record.amount) }}
            </span>
          </template>
          <template v-if="column.key === 'pay_status'">
            <a-tag :color="payStatusColors[record.pay_status ?? record.status ?? ''] || 'default'">
              {{ payStatusMap[record.pay_status ?? record.status ?? ''] || record.pay_status || record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-popconfirm
              v-if="(record.pay_status ?? record.status) === 'paid'"
              title="确定退款?"
              ok-text="确定"
              cancel-text="取消"
              @confirm="handleRefund(record)"
            >
              <a-button
                size="small"
                danger
                :loading="refundingId === record.id"
              >
                <DollarOutlined /> 退款
              </a-button>
            </a-popconfirm>
            <span v-else style="color: var(--text-muted)">--</span>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && orders.length === 0" description="暂无订单数据" />
    </a-spin>
  </div>
</template>
