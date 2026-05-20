<script setup lang="ts">
import { listClients, type ClientQuery } from '@/api/consultant'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { getTierLabel } from '@video-ct/shared'

interface ClientRecord {
  id: string
  nickname?: string
  name?: string
  avatar?: string
  phone?: string
  track?: string
  level?: string
  health_score?: number
  last_diagnosis_at?: string
  latest_diagnosis_at?: string
  created_at: string
}

const router = useRouter()
const clients = ref<ClientRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const searchText = ref('')
const trackFilter = ref<string | undefined>(undefined)

const columns = [
  { title: '头像', dataIndex: 'avatar', key: 'avatar', width: 60 },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname', width: 120 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 130 },
  { title: '赛道', dataIndex: 'track', key: 'track', width: 100 },
  { title: '等级', dataIndex: 'level', key: 'level', width: 80 },
  { title: '健康度', dataIndex: 'health_score', key: 'health_score', width: 100 },
  { title: '最近诊断', dataIndex: 'last_diagnosis_at', key: 'last_diagnosis_at', width: 160 },
]

const levelColors: Record<string, string> = { free: 'default', pro: 'blue', max: 'gold' }

function getHealthColor(score?: number) {
  if (score == null) return 'default'
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

async function fetch() {
  loading.value = true
  try {
    const params: ClientQuery = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (searchText.value) params.q = searchText.value
    if (trackFilter.value) params.track = trackFilter.value
    const res = await listClients(params)
    clients.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  pagination.current = 1
  fetch()
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetch()
}

function goDetail(id: string) {
  router.push(`/clients/${id}`)
}

onMounted(fetch)
</script>

<template>
  <div class="clients-page">
    <div class="page-header">
      <h2>客户管理</h2>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索昵称/手机号"
        @search="onSearch"
        allow-clear
        style="max-width: 280px"
      />
      <a-select
        v-model:value="trackFilter"
        placeholder="赛道筛选"
        allow-clear
        style="width: 140px"
        @change="() => { pagination.current = 1; fetch() }"
      >
        <a-select-option value="美妆">美妆</a-select-option>
        <a-select-option value="穿搭">穿搭</a-select-option>
        <a-select-option value="美食">美食</a-select-option>
        <a-select-option value="知识">知识</a-select-option>
        <a-select-option value="Vlog">Vlog</a-select-option>
      </a-select>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="clients"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 850 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
        :custom-row="(record: ClientRecord) => ({ style: { cursor: 'pointer' }, onClick: () => goDetail(record.id) })"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'avatar'">
            <a-avatar :src="record.avatar" :size="32">
              {{ record.nickname?.charAt(0) || record.name?.charAt(0) || 'U' }}
            </a-avatar>
          </template>
          <template v-if="column.key === 'level'">
            <a-tag :color="levelColors[record.level ?? ''] || 'default'">
              {{ getTierLabel(record.level ?? '') }}
            </a-tag>
          </template>
          <template v-if="column.key === 'health_score'">
            <a-tag :color="getHealthColor(record.health_score)">
              {{ record.health_score ?? '-' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'last_diagnosis_at'">
            {{
              (record.last_diagnosis_at ?? record.latest_diagnosis_at)
                ? dayjs(record.last_diagnosis_at ?? record.latest_diagnosis_at).format('YYYY-MM-DD HH:mm')
                : '暂无诊断'
            }}
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && clients.length === 0" description="暂无客户数据" />
    </a-spin>
  </div>
</template>
