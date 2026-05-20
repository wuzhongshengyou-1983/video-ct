<script setup lang="ts">
import { listAlerts, acknowledgeAlert, dismissAlert } from '@/api/consultant'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { CheckOutlined, StopOutlined } from '@ant-design/icons-vue'

interface AlertRecord {
  id: string
  type: string
  severity: string
  message: string
  client_name?: string
  user_nickname?: string
  is_acknowledged: boolean
  is_dismissed?: boolean
  created_at: string
}

const alerts = ref<AlertRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const actingId = ref<string | null>(null)

const columns = [
  { title: '级别', dataIndex: 'severity', key: 'severity', width: 80 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '预警内容', dataIndex: 'message', key: 'message', width: 280, ellipsis: true },
  { title: '关联客户', dataIndex: 'client_name', key: 'client_name', width: 120 },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 140 },
  { title: '状态', key: 'alert_status', width: 90 },
  { title: '操作', key: 'actions', width: 140 },
]

const severityColors: Record<string, string> = {
  critical: 'red', warning: 'orange', info: 'blue',
}
const severityLabels: Record<string, string> = {
  critical: '紧急', warning: '预警', info: '提示',
}

const typeMap: Record<string, string> = {
  data_anomaly: '数据异动',
  churn_risk: '流失风险',
  health_drop: '健康下降',
  quota_warning: '额度预警',
}

async function fetch() {
  loading.value = true
  try {
    const res = await listAlerts({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    alerts.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

async function handleAcknowledge(record: AlertRecord) {
  actingId.value = record.id
  try {
    await acknowledgeAlert(record.id)
    message.success('已标记为已处理')
    fetch()
  } finally {
    actingId.value = null
  }
}

async function handleDismiss(record: AlertRecord) {
  actingId.value = record.id
  try {
    await dismissAlert(record.id)
    message.success('已忽略')
    fetch()
  } finally {
    actingId.value = null
  }
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetch()
}

onMounted(fetch)
</script>

<template>
  <div class="alerts-page">
    <div class="page-header">
      <h2>预警中心</h2>
      <a-space>
        <a-tag color="red">紧急</a-tag>
        <a-tag color="orange">预警</a-tag>
        <a-tag color="blue">提示</a-tag>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="alerts"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 950 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <a-badge
              :color="severityColors[record.severity] || 'default'"
              :text="severityLabels[record.severity] || record.severity"
            />
          </template>
          <template v-if="column.key === 'type'">
            {{ typeMap[record.type] || record.type }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'alert_status'">
            <a-tag v-if="record.is_dismissed" color="default">已忽略</a-tag>
            <a-tag v-else-if="record.is_acknowledged" color="green">已处理</a-tag>
            <a-tag v-else color="orange">待处理</a-tag>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space v-if="!record.is_acknowledged && !record.is_dismissed">
              <a-button
                size="small"
                type="primary"
                :loading="actingId === record.id"
                @click="handleAcknowledge(record)"
              >
                <CheckOutlined /> 已处理
              </a-button>
              <a-button
                size="small"
                :loading="actingId === record.id"
                @click="handleDismiss(record)"
              >
                <StopOutlined /> 忽略
              </a-button>
            </a-space>
            <span v-else style="color: var(--text-muted)">--</span>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && alerts.length === 0" description="暂无预警" />
    </a-spin>
  </div>
</template>
