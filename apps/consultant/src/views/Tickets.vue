<script setup lang="ts">
import { listTickets, createTicket, listClients } from '@/api/consultant'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { PlusOutlined } from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

interface TicketRecord {
  id: string
  title: string
  description?: string
  client_name?: string
  user_nickname?: string
  client_id?: string
  priority: string
  status: string
  created_at: string
  updated_at?: string
}

interface ClientOption {
  id: string
  nickname?: string
  name?: string
}

const tickets = ref<TicketRecord[]>([])
const total = ref(0)
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 10 })
const statusFilter = ref<string | undefined>(undefined)

// 创建工单弹窗
const modalVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const clientOptions = ref<ClientOption[]>([])
const clientLoading = ref(false)

const form = reactive({
  title: '',
  description: '',
  client_id: undefined as string | undefined,
  priority: 'normal',
})

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', width: 220 },
  { title: '客户', dataIndex: 'client_name', key: 'client_name', width: 120 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 150 },
]

const priorityColors: Record<string, string> = {
  urgent: 'red', high: 'orange', normal: 'blue', low: 'default',
}
const priorityLabels: Record<string, string> = {
  urgent: '紧急', high: '高', normal: '中', low: '低',
}
const statusMap: Record<string, string> = {
  open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭',
}
const statusColors: Record<string, string> = {
  open: 'red', in_progress: 'blue', resolved: 'green', closed: 'default',
}

const formRules = {
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
}

async function fetch() {
  loading.value = true
  try {
    const params: { page?: number; page_size?: number; status?: string } = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await listTickets(params)
    tickets.value = res.data.items ?? res.data.data ?? []
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

// 打开创建弹窗
async function openCreate() {
  form.title = ''
  form.description = ''
  form.client_id = undefined
  form.priority = 'normal'
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
    await createTicket({
      title: form.title,
      description: form.description || undefined,
      client_id: form.client_id,
      priority: form.priority,
    })
    message.success('工单已创建')
    modalVisible.value = false
    fetch()
  } finally {
    submitting.value = false
  }
}

onMounted(fetch)
</script>

<template>
  <div class="tickets-page">
    <div class="page-header">
      <h2>工单列表</h2>
      <a-space>
        <a-select
          v-model:value="statusFilter"
          placeholder="状态筛选"
          allow-clear
          style="width: 130px"
          @change="() => { pagination.current = 1; fetch() }"
        >
          <a-select-option value="open">待处理</a-select-option>
          <a-select-option value="in_progress">处理中</a-select-option>
          <a-select-option value="resolved">已解决</a-select-option>
        </a-select>
        <a-button type="primary" @click="openCreate">
          <PlusOutlined /> 创建工单
        </a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="tickets"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 750 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'priority'">
            <a-tag :color="priorityColors[record.priority] || 'default'">
              {{ priorityLabels[record.priority] || record.priority }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status] || 'default'">
              {{ statusMap[record.status] || record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && tickets.length === 0" description="暂无工单" />
    </a-spin>

    <!-- 创建工单弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      title="创建工单"
      :confirm-loading="submitting"
      @ok="handleCreate"
      width="520px"
    >
      <a-spin :spinning="clientLoading" tip="加载客户列表...">
        <a-form ref="formRef" :model="form" :rules="formRules" layout="vertical">
          <a-form-item label="工单标题" name="title">
            <a-input v-model:value="form.title" placeholder="例: 客户需要紧急修改诊断报告" />
          </a-form-item>
          <a-form-item label="关联客户">
            <a-select
              v-model:value="form.client_id"
              placeholder="选择客户（选填）"
              allow-clear
              show-search
              option-filter-prop="label"
              :options="clientOptions.map((c) => ({ value: c.id, label: c.nickname || c.name || c.id }))"
            />
          </a-form-item>
          <a-form-item label="优先级">
            <a-select v-model:value="form.priority">
              <a-select-option value="urgent">
                <a-tag color="red" style="margin-right: 0">紧急</a-tag>
              </a-select-option>
              <a-select-option value="high">
                <a-tag color="orange" style="margin-right: 0">高</a-tag>
              </a-select-option>
              <a-select-option value="normal">
                <a-tag color="blue" style="margin-right: 0">中</a-tag>
              </a-select-option>
              <a-select-option value="low">
                <a-tag color="default" style="margin-right: 0">低</a-tag>
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea
              v-model:value="form.description"
              :rows="4"
              placeholder="详细描述工单内容..."
            />
          </a-form-item>
        </a-form>
      </a-spin>
    </a-modal>
  </div>
</template>
