<script setup lang="ts">
import { listSubscriptions, type SubQuery } from '@/api/admin'
import dayjs from 'dayjs'

interface SubRecord {
  id: string
  user_id?: string
  user_phone?: string
  product_name?: string
  plan?: string
  status: string
  started_at?: string
  expires_at?: string
  created_at: string
}

const subs = ref<SubRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const statusFilter = ref<string | undefined>(undefined)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 100, ellipsis: true },
  { title: '用户', dataIndex: 'user_phone', key: 'user_phone', width: 130 },
  { title: '方案', dataIndex: 'product_name', key: 'product_name', width: 140 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '开始时间', dataIndex: 'started_at', key: 'started_at', width: 160 },
  { title: '到期时间', dataIndex: 'expires_at', key: 'expires_at', width: 160 },
]

const statusMap: Record<string, string> = {
  active: '生效中', expired: '已过期', cancelled: '已取消', paused: '已暂停',
}
const statusColors: Record<string, string> = {
  active: 'green', expired: 'red', cancelled: 'default', paused: 'orange',
}

async function fetchSubs() {
  loading.value = true
  try {
    const params: SubQuery = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await listSubscriptions(params)
    subs.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetchSubs()
}

onMounted(fetchSubs)
</script>

<template>
  <div class="subscriptions-page">
    <div class="page-header">
      <h2>订阅管理</h2>
      <a-select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        allow-clear
        style="width: 120px"
        @change="() => { pagination.current = 1; fetchSubs() }"
      >
        <a-select-option value="active">生效中</a-select-option>
        <a-select-option value="expired">已过期</a-select-option>
      </a-select>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="subs"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 800 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status] || 'default'">
              {{ statusMap[record.status] || record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'started_at' || column.key === 'expires_at'">
            {{ record[column.dataIndex as keyof SubRecord]
              ? dayjs(record[column.dataIndex as keyof SubRecord] as string).format('YYYY-MM-DD HH:mm')
              : '-' }}
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && subs.length === 0" description="暂无订阅数据" />
    </a-spin>
  </div>
</template>
