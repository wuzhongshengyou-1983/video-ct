<script setup lang="ts">
import { listMeetings, createMeeting, listClients } from '@/api/consultant'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  CalendarOutlined,
  EnvironmentOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

interface MeetingRecord {
  id: string
  title: string
  client_name?: string
  user_nickname?: string
  client_id?: string
  scheduled_at: string
  status: string
  meeting_type?: string
  location?: string
  notes?: string
}

interface ClientOption {
  id: string
  nickname?: string
  name?: string
}

const meetings = ref<MeetingRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })

// 安排会议弹窗
const modalVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const clientOptions = ref<ClientOption[]>([])
const clientLoading = ref(false)

const form = reactive({
  client_id: '',
  title: '',
  scheduled_at: null as string | null,
  meeting_type: 'online',
  location: '',
  notes: '',
})

const columns = [
  { title: '主题', dataIndex: 'title', key: 'title', width: 200 },
  { title: '客户', dataIndex: 'client_name', key: 'client_name', width: 120 },
  { title: '类型', dataIndex: 'meeting_type', key: 'meeting_type', width: 100 },
  { title: '时间', dataIndex: 'scheduled_at', key: 'scheduled_at', width: 160 },
  { title: '地点', dataIndex: 'location', key: 'location', width: 140 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
]

const statusMap: Record<string, string> = {
  scheduled: '已安排', completed: '已完成', cancelled: '已取消',
}
const statusColors: Record<string, string> = {
  scheduled: 'blue', completed: 'green', cancelled: 'default',
}
const meetingTypeMap: Record<string, string> = {
  online: '线上', offline: '线下', phone: '电话',
}

const formRules = {
  client_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  title: [{ required: true, message: '请输入会议主题', trigger: 'blur' }],
  scheduled_at: [{ required: true, message: '请选择会议时间', trigger: 'change' }],
}

// 判断是否是今天
function isToday(dateStr: string): boolean {
  return dayjs(dateStr).isSame(dayjs(), 'day')
}

async function fetch() {
  loading.value = true
  try {
    const res = await listMeetings({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    meetings.value = res.data.items ?? res.data.data ?? []
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

// 打开安排会议弹窗，加载客户列表
async function openSchedule() {
  form.client_id = ''
  form.title = ''
  form.scheduled_at = null
  form.meeting_type = 'online'
  form.location = ''
  form.notes = ''
  modalVisible.value = true

  clientLoading.value = true
  try {
    const res = await listClients({ page: 1, page_size: 100 })
    clientOptions.value = res.data.items ?? res.data.data ?? []
  } finally {
    clientLoading.value = false
  }
}

async function handleCreate() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    await createMeeting({
      client_id: form.client_id,
      title: form.title,
      scheduled_at: new Date(form.scheduled_at!).toISOString(),
      meeting_type: form.meeting_type,
      location: form.location || undefined,
      notes: form.notes || undefined,
    })
    message.success('会议已安排')
    modalVisible.value = false
    fetch()
  } finally {
    submitting.value = false
  }
}

onMounted(fetch)
</script>

<template>
  <div class="meetings-page">
    <div class="page-header">
      <h2>月度会议</h2>
      <a-button type="primary" @click="openSchedule">
        <PlusOutlined /> 安排会议
      </a-button>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="meetings"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 800 }"
        row-key="id"
        :row-class-name="(record: MeetingRecord) => isToday(record.scheduled_at) ? 'today-row' : ''"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'scheduled_at'">
            <a-space>
              <a-tag v-if="isToday(record.scheduled_at)" color="red">今天</a-tag>
              <CalendarOutlined style="color: var(--text-secondary)" />
              {{ record.scheduled_at ? dayjs(record.scheduled_at).format('MM-DD HH:mm') : '-' }}
            </a-space>
          </template>
          <template v-if="column.key === 'meeting_type'">
            <a-tag>
              {{ meetingTypeMap[record.meeting_type ?? ''] || record.meeting_type || '线上' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'location'">
            <EnvironmentOutlined style="margin-right: 4px; color: var(--text-secondary)" />
            {{ record.location || '线上会议' }}
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status] || 'default'">
              {{ statusMap[record.status] || record.status }}
            </a-tag>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && meetings.length === 0" description="暂无会议安排" />
    </a-spin>

    <!-- 安排会议弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      title="安排会议"
      :confirm-loading="submitting"
      @ok="handleCreate"
      width="520px"
    >
      <a-spin :spinning="clientLoading" tip="加载客户列表...">
        <a-form ref="formRef" :model="form" :rules="formRules" layout="vertical">
          <a-form-item label="客户" name="client_id">
            <a-select
              v-model:value="form.client_id"
              placeholder="选择客户"
              show-search
              option-filter-prop="label"
              :options="clientOptions.map((c) => ({ value: c.id, label: c.nickname || c.name || c.id }))"
            />
          </a-form-item>
          <a-form-item label="会议主题" name="title">
            <a-input v-model:value="form.title" placeholder="例: 月度复盘与下阶段规划" />
          </a-form-item>
          <a-form-item label="会议时间" name="scheduled_at">
            <a-date-picker
              v-model:value="form.scheduled_at"
              show-time
              format="YYYY-MM-DD HH:mm"
              style="width: 100%"
              :disabled-date="(d: any) => d && d.isBefore(dayjs().subtract(1, 'day'), 'day')"
            />
          </a-form-item>
          <a-form-item label="会议类型">
            <a-select v-model:value="form.meeting_type">
              <a-select-option value="online">线上</a-select-option>
              <a-select-option value="offline">线下</a-select-option>
              <a-select-option value="phone">电话</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="会议地点">
            <a-input v-model:value="form.location" placeholder="线上留空或填会议链接" />
          </a-form-item>
          <a-form-item label="备注">
            <a-textarea v-model:value="form.notes" :rows="3" placeholder="会议要点..." />
          </a-form-item>
        </a-form>
      </a-spin>
    </a-modal>
  </div>
</template>

<style lang="scss" scoped>
:deep(.today-row) {
  background: rgba(239, 68, 68, 0.06) !important;
  td {
    font-weight: 500;
  }
}
</style>
