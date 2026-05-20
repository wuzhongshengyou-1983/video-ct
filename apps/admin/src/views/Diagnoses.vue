<script setup lang="ts">
import { listDiagnoses, rerunDiagnosis, type DiagnosisQuery } from '@/api/admin'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { ReloadOutlined } from '@ant-design/icons-vue'

interface DiagRecord {
  id: string
  user_id?: string
  user_phone?: string
  platform?: string
  diag_type?: string
  quota_source?: string
  status: string
  satisfaction?: number
  created_at: string
}

const diagnoses = ref<DiagRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const searchText = ref('')
const statusFilter = ref<string | undefined>(undefined)
const rerunningId = ref<string | null>(null)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 100, ellipsis: true },
  { title: '用户', dataIndex: 'user_phone', key: 'user_phone', width: 130 },
  { title: '平台', dataIndex: 'platform', key: 'platform', width: 80 },
  { title: '诊断类型', dataIndex: 'diag_type', key: 'diag_type', width: 120 },
  { title: '配额来源', dataIndex: 'quota_source', key: 'quota_source', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '满意度', dataIndex: 'satisfaction', key: 'satisfaction', width: 80 },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'actions', width: 100, fixed: 'right' as const },
]

const statusMap: Record<string, string> = {
  pending: '等待中', running: '分析中', completed: '已完成', failed: '失败',
}
const statusColors: Record<string, string> = {
  pending: 'default', running: 'blue', completed: 'green', failed: 'red',
}

const diagTypeMap: Record<string, string> = {
  video: '视频诊断', account: '账号诊断', competitor: '竞品分析', full: '全面诊断',
}

const quotaSourceMap: Record<string, string> = {
  free: '免费额度', subscription: '订阅额度', gift: '赠送额度', purchase: '购买额度',
}

async function fetchDiags() {
  loading.value = true
  try {
    const params: DiagnosisQuery & { status?: string } = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (searchText.value) params.q = searchText.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await listDiagnoses(params)
    diagnoses.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  pagination.current = 1
  fetchDiags()
}

function onFilterChange() {
  pagination.current = 1
  fetchDiags()
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetchDiags()
}

async function handleRerun(record: DiagRecord) {
  rerunningId.value = record.id
  try {
    await rerunDiagnosis(record.id)
    message.success('诊断已重新提交')
    fetchDiags()
  } finally {
    rerunningId.value = null
  }
}

onMounted(fetchDiags)
</script>

<template>
  <div class="diagnoses-page">
    <div class="page-header">
      <h2>诊断管理</h2>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索用户/诊断ID"
        @search="onSearch"
        allow-clear
        style="max-width: 280px"
      />
      <a-select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        allow-clear
        style="width: 130px"
        @change="onFilterChange"
      >
        <a-select-option value="pending">等待中</a-select-option>
        <a-select-option value="running">分析中</a-select-option>
        <a-select-option value="completed">已完成</a-select-option>
        <a-select-option value="failed">失败</a-select-option>
      </a-select>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="diagnoses"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 1050 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status] || 'default'">
              {{ statusMap[record.status] || record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'diag_type'">
            {{ diagTypeMap[record.diag_type ?? ''] || record.diag_type || '-' }}
          </template>
          <template v-if="column.key === 'quota_source'">
            <a-tag>{{ quotaSourceMap[record.quota_source ?? ''] || record.quota_source || '-' }}</a-tag>
          </template>
          <template v-if="column.key === 'satisfaction'">
            {{ record.satisfaction != null ? (record.satisfaction * 100).toFixed(0) + '%' : '-' }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-button
              v-if="record.status === 'failed'"
              size="small"
              type="primary"
              :loading="rerunningId === record.id"
              @click="handleRerun(record)"
            >
              <ReloadOutlined /> 重跑
            </a-button>
            <span v-else style="color: var(--text-muted)">--</span>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && diagnoses.length === 0" description="暂无诊断数据" />
    </a-spin>
  </div>
</template>
