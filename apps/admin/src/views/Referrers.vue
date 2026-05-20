<script setup lang="ts">
import {
  listReferrers,
  flagReferrer,
  freezeReferrer,
  unfreezeReferrer,
} from '@/api/admin'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  WarningOutlined,
  LockOutlined,
  UnlockOutlined,
} from '@ant-design/icons-vue'

interface ReferrerRecord {
  id: string
  user_id?: string
  name?: string
  phone?: string
  code?: string
  tier?: string
  total_referrals?: number
  total_revenue_cny?: number
  total_commission_cny?: number
  status?: string
  flagged?: boolean
  created_at: string
}

const referrers = ref<ReferrerRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })

// 标记异常弹窗
const flagVisible = ref(false)
const flagTarget = ref<ReferrerRecord | null>(null)
const flagReason = ref('')
const flagLoading = ref(false)

// 冻结中
const freezingId = ref<string | null>(null)

const columns = [
  { title: '分享官', dataIndex: 'name', key: 'name', width: 120 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 130 },
  { title: '邀请码', dataIndex: 'code', key: 'code', width: 110 },
  { title: '等级', dataIndex: 'tier', key: 'tier', width: 80 },
  { title: '推荐人数', dataIndex: 'total_referrals', key: 'total_referrals', width: 90 },
  { title: '累计奖励', dataIndex: 'total_commission_cny', key: 'total_commission_cny', width: 110 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '注册时间', dataIndex: 'created_at', key: 'created_at', width: 140 },
  { title: '操作', key: 'actions', width: 180, fixed: 'right' as const },
]

const statusMap: Record<string, string> = {
  active: '正常', inactive: '未激活', banned: '已冻结', frozen: '已冻结',
}
const statusColors: Record<string, string> = {
  active: 'green', inactive: 'default', banned: 'red', frozen: 'red',
}

const tierMap: Record<string, string> = {
  bronze: '铜牌', silver: '银牌', gold: '金牌', platinum: '铂金', diamond: '钻石',
}
const tierColors: Record<string, string> = {
  bronze: '#cd7f32', silver: '#9ca3af', gold: '#f59e0b', platinum: '#3b82f6', diamond: '#8b5cf6',
}

async function fetch() {
  loading.value = true
  try {
    const res = await listReferrers({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    referrers.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetch()
}

// 标记异常
function openFlag(record: ReferrerRecord) {
  flagTarget.value = record
  flagReason.value = ''
  flagVisible.value = true
}

async function handleFlag() {
  if (!flagTarget.value) return
  flagLoading.value = true
  try {
    await flagReferrer(flagTarget.value.id, { reason: flagReason.value })
    message.success('已标记异常')
    flagVisible.value = false
    fetch()
  } finally {
    flagLoading.value = false
  }
}

// 冻结/解冻
async function handleFreezeToggle(record: ReferrerRecord) {
  freezingId.value = record.id
  try {
    const isFrozen = record.status === 'banned' || record.status === 'frozen'
    if (isFrozen) {
      await unfreezeReferrer(record.id)
      message.success('已解冻账户')
    } else {
      await freezeReferrer(record.id)
      message.success('已冻结账户')
    }
    fetch()
  } finally {
    freezingId.value = null
  }
}

function formatCount(n?: number): string {
  if (n == null) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toLocaleString()
}

function formatMoney(n?: number): string {
  if (n == null) return '¥0'
  if (n >= 10000) return '¥' + (n / 10000).toFixed(1) + 'w'
  return '¥' + n.toLocaleString()
}

onMounted(fetch)
</script>

<template>
  <div class="referrers-page">
    <div class="page-header">
      <h2>分享官管理</h2>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="referrers"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 1100 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'tier'">
            <a-tag v-if="record.tier" :color="tierColors[record.tier] || 'default'">
              {{ tierMap[record.tier] || record.tier }}
            </a-tag>
            <span v-else style="color: var(--text-muted)">--</span>
          </template>
          <template v-if="column.key === 'total_referrals'">
            {{ formatCount(record.total_referrals) }}
          </template>
          <template v-if="column.key === 'total_commission_cny'">
            <span :style="{ color: '#10b981', fontWeight: 500 }">
              {{ formatMoney(record.total_commission_cny ?? record.total_revenue_cny) }}
            </span>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status ?? ''] || 'default'">
              {{ statusMap[record.status ?? ''] || record.status || '-' }}
            </a-tag>
            <a-tag v-if="record.flagged" color="orange" style="margin-left: 4px">异常</a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button
                size="small"
                @click="openFlag(record)"
                :disabled="!!record.flagged"
              >
                <WarningOutlined /> 标记异常
              </a-button>
              <a-popconfirm
                :title="
                  record.status === 'banned' || record.status === 'frozen'
                    ? '确定解冻该分享官账户?'
                    : '确定冻结该分享官账户?'
                "
                @confirm="handleFreezeToggle(record)"
              >
                <a-button
                  size="small"
                  :danger="record.status !== 'banned' && record.status !== 'frozen'"
                  :loading="freezingId === record.id"
                >
                  <template
                    v-if="record.status === 'banned' || record.status === 'frozen'"
                  >
                    <UnlockOutlined /> 解冻
                  </template>
                  <template v-else>
                    <LockOutlined /> 冻结
                  </template>
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && referrers.length === 0" description="暂无分享官数据" />
    </a-spin>

    <!-- 标记异常弹窗 -->
    <a-modal
      v-model:open="flagVisible"
      title="标记异常"
      :confirm-loading="flagLoading"
      @ok="handleFlag"
      width="420px"
    >
      <p style="margin-bottom: 12px">
        确定标记 <strong>{{ flagTarget?.name || flagTarget?.phone }}</strong> 为异常分享官？
      </p>
      <a-textarea
        v-model:value="flagReason"
        placeholder="异常原因（选填）"
        :rows="3"
      />
    </a-modal>
  </div>
</template>
