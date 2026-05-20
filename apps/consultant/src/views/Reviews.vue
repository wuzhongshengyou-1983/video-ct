<script setup lang="ts">
import { listReviews, submitReview } from '@/api/consultant'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  EyeOutlined,
  CheckOutlined,
  CloseOutlined,
} from '@ant-design/icons-vue'

interface ReviewRecord {
  id: string
  diagnosis_id: string
  user_nickname?: string
  review_status: string
  ai_conclusion?: string
  ai_report?: string
  full_report?: string
  consultant_comment?: string
  score?: number
  created_at: string
  reviewed_at?: string
}

const reviews = ref<ReviewRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const statusFilter = ref<string | undefined>(undefined)
const expandedRowKeys = ref<string[]>([])
const reviewingId = ref<string | null>(null)

const columns = [
  { title: '诊断ID', dataIndex: 'diagnosis_id', key: 'diagnosis_id', width: 120, ellipsis: true },
  { title: '博主', dataIndex: 'user_nickname', key: 'user_nickname', width: 120 },
  { title: 'AI 结论摘要', dataIndex: 'ai_conclusion', key: 'ai_conclusion', width: 240, ellipsis: true },
  { title: '复审状态', dataIndex: 'review_status', key: 'review_status', width: 100 },
  { title: '提交时间', dataIndex: 'created_at', key: 'created_at', width: 140 },
  { title: '操作', key: 'actions', width: 160 },
]

const statusMap: Record<string, string> = {
  pending: '待复审', reviewed: '已复审', approved: '已通过', rejected: '需修改',
}
const statusColors: Record<string, string> = {
  pending: 'orange', reviewed: 'blue', approved: 'green', rejected: 'red',
}

async function fetch() {
  loading.value = true
  try {
    const params: { page?: number; page_size?: number; status?: string } = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await listReviews(params)
    reviews.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  expandedRowKeys.value = []
  fetch()
}

function toggleExpand(record: ReviewRecord) {
  const idx = expandedRowKeys.value.indexOf(record.id)
  if (idx >= 0) {
    expandedRowKeys.value.splice(idx, 1)
  } else {
    expandedRowKeys.value = [record.id]
  }
}

async function handleApprove(record: ReviewRecord) {
  reviewingId.value = record.id
  try {
    await submitReview(record.diagnosis_id, { status: 'approved' })
    message.success('已通过复审')
    fetch()
  } finally {
    reviewingId.value = null
  }
}

async function handleReject(record: ReviewRecord) {
  reviewingId.value = record.id
  try {
    await submitReview(record.diagnosis_id, { status: 'rejected' })
    message.success('已驳回')
    fetch()
  } finally {
    reviewingId.value = null
  }
}

onMounted(fetch)
</script>

<template>
  <div class="reviews-page">
    <div class="page-header">
      <h2>报告复审</h2>
      <a-select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        allow-clear
        style="width: 130px"
        @change="() => { pagination.current = 1; fetch() }"
      >
        <a-select-option value="pending">待复审</a-select-option>
        <a-select-option value="reviewed">已复审</a-select-option>
        <a-select-option value="approved">已通过</a-select-option>
        <a-select-option value="rejected">需修改</a-select-option>
      </a-select>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="reviews"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 900 }"
        row-key="id"
        :expand-row-by-click="false"
        :expanded-row-keys="expandedRowKeys"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'review_status'">
            <a-tag :color="statusColors[record.review_status] || 'default'">
              {{ statusMap[record.review_status] || record.review_status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" @click="toggleExpand(record)">
                <EyeOutlined /> {{ expandedRowKeys.includes(record.id) ? '收起' : '展开' }}
              </a-button>
              <template v-if="record.review_status === 'pending'">
                <a-button
                  size="small"
                  type="primary"
                  :loading="reviewingId === record.id"
                  @click="handleApprove(record)"
                >
                  <CheckOutlined /> 通过
                </a-button>
                <a-button
                  size="small"
                  danger
                  :loading="reviewingId === record.id"
                  @click="handleReject(record)"
                >
                  <CloseOutlined /> 驳回
                </a-button>
              </template>
            </a-space>
          </template>
        </template>

        <!-- 展开内容：AI 报告全文 -->
        <template #expandedRowRender="{ record }">
          <div class="expanded-report">
            <a-descriptions :column="2" size="small" :colon="false" bordered>
              <a-descriptions-item label="诊断 ID">{{ record.diagnosis_id }}</a-descriptions-item>
              <a-descriptions-item label="博主">{{ record.user_nickname || '-' }}</a-descriptions-item>
              <a-descriptions-item label="诊断得分">
                {{ record.score != null ? record.score : '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="提交时间">
                {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="复审时间" :span="2">
                {{ record.reviewed_at ? dayjs(record.reviewed_at).format('MM-DD HH:mm') : '尚未复审' }}
              </a-descriptions-item>
              <a-descriptions-item label="AI 诊断结论" :span="2">
                <div style="white-space: pre-wrap; line-height: 1.7;">
                  {{ record.ai_report || record.full_report || record.ai_conclusion || '暂无详细报告' }}
                </div>
              </a-descriptions-item>
              <a-descriptions-item label="顾问批注" :span="2">
                <div style="white-space: pre-wrap; color: var(--text-secondary);">
                  {{ record.consultant_comment || '无批注' }}
                </div>
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </template>
      </a-table>
      <a-empty v-if="!loading && reviews.length === 0" description="暂无待复审报告" />
    </a-spin>
  </div>
</template>

<style lang="scss" scoped>
.expanded-report {
  padding: 16px;
  background: var(--bg-elevated);
  border-radius: 8px;
}
</style>
