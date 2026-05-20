<script setup lang="ts">
import { listUsers, getUserDetail, updateUser, type UserQuery } from '@/api/admin'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTierLabel } from '@video-ct/shared'
import {
  EyeOutlined,
  StopOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'

interface UserRecord {
  id: string
  phone: string
  nickname?: string
  name?: string
  role: string
  status: string
  created_at: string
}

interface UserDetail {
  id: string
  phone: string
  nickname?: string
  name?: string
  role: string
  status: string
  created_at: string
  subscription?: { product_name?: string; status?: string; expires_at?: string } | null
  diagnosis_count?: number
  order_count?: number
}

const users = ref<UserRecord[]>([])
const total = ref(0)
const loading = ref(false)
const searchText = ref('')
const pagination = reactive({ current: 1, pageSize: 10 })

// 详情弹窗
const detailVisible = ref(false)
const detailUser = ref<UserDetail | null>(null)
const detailLoading = ref(false)

// 封禁弹窗
const banDialogVisible = ref(false)
const banTarget = ref<UserRecord | null>(null)
const banLoading = ref(false)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 100, ellipsis: true },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 140 },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname', width: 120 },
  { title: '角色', dataIndex: 'role', key: 'role', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '注册时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' as const },
]

function getRoleLabel(role: string): string {
  if (['free', 'pro', 'max'].includes(role)) return getTierLabel(role)
  if (role === 'admin') return '管理员'
  return role
}
const statusMap: Record<string, string> = { active: '正常', inactive: '未激活', banned: '已封禁' }
const statusColors: Record<string, string> = {
  active: 'green',
  inactive: 'default',
  banned: 'red',
}

async function fetchUsers() {
  loading.value = true
  try {
    const params: UserQuery = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (searchText.value) params.q = searchText.value
    const res = await listUsers(params)
    users.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  pagination.current = 1
  fetchUsers()
}

function onPageChange(page: number, pageSize: number) {
  pagination.current = page
  pagination.pageSize = pageSize
  fetchUsers()
}

// 查看详情
async function showDetail(record: UserRecord) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getUserDetail(record.id)
    detailUser.value = res.data
  } catch {
    detailUser.value = { ...record }
  } finally {
    detailLoading.value = false
  }
}

// 封禁/解封
function confirmBan(record: UserRecord) {
  banTarget.value = record
  banDialogVisible.value = true
}

async function handleBan() {
  if (!banTarget.value) return
  banLoading.value = true
  try {
    const newStatus = banTarget.value.status === 'banned' ? 'active' : 'banned'
    await updateUser(banTarget.value.id, { status: newStatus })
    message.success(
      banTarget.value.status === 'banned' ? '已解封用户' : '已封禁用户'
    )
    banDialogVisible.value = false
    fetchUsers()
  } finally {
    banLoading.value = false
  }
}

// 格式化数字缩写
function formatCount(n: number | undefined | null): string {
  if (n == null) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return n.toLocaleString()
}

onMounted(fetchUsers)
</script>

<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
    </div>

    <div class="search-bar">
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索手机号/昵称"
        @search="onSearch"
        allow-clear
        style="max-width: 300px"
      />
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="users"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 900 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag>{{ getRoleLabel(record.role) }}</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status] || 'default'">
              {{ statusMap[record.status] || record.status }}
            </a-tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? dayjs(record.created_at).format('MM-DD HH:mm') : '-' }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" @click="showDetail(record)">
                <EyeOutlined /> 详情
              </a-button>
              <a-button
                size="small"
                :danger="record.status !== 'banned'"
                :type="record.status === 'banned' ? 'default' : 'default'"
                @click="confirmBan(record)"
              >
                <template v-if="record.status === 'banned'">
                  <CheckCircleOutlined /> 解封
                </template>
                <template v-else>
                  <StopOutlined /> 封禁
                </template>
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && users.length === 0" description="暂无用户数据" />
    </a-spin>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="用户详情"
      width="520px"
      :footer="null"
    >
      <a-spin :spinning="detailLoading">
        <template v-if="detailUser">
          <a-descriptions :column="1" size="small" :colon="false" bordered>
            <a-descriptions-item label="用户 ID">{{ detailUser.id }}</a-descriptions-item>
            <a-descriptions-item label="手机号">{{ detailUser.phone || '-' }}</a-descriptions-item>
            <a-descriptions-item label="昵称">{{ detailUser.nickname || detailUser.name || '-' }}</a-descriptions-item>
            <a-descriptions-item label="角色">
              <a-tag>{{ getRoleLabel(detailUser.role) }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="statusColors[detailUser.status] || 'default'">
                {{ statusMap[detailUser.status] || detailUser.status }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="订阅方案">
              {{ detailUser.subscription?.product_name || '无订阅' }}
              <a-tag
                v-if="detailUser.subscription"
                :color="detailUser.subscription.status === 'active' ? 'green' : 'default'"
                style="margin-left: 8px"
              >
                {{ detailUser.subscription.status === 'active' ? '生效中' : detailUser.subscription.status || '-' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="订阅到期">
              {{ detailUser.subscription?.expires_at ? dayjs(detailUser.subscription.expires_at).format('YYYY-MM-DD') : '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="诊断次数">{{ formatCount(detailUser.diagnosis_count) }}</a-descriptions-item>
            <a-descriptions-item label="订单数量">{{ formatCount(detailUser.order_count) }}</a-descriptions-item>
            <a-descriptions-item label="注册时间">
              {{ detailUser.created_at ? dayjs(detailUser.created_at).format('YYYY-MM-DD HH:mm') : '-' }}
            </a-descriptions-item>
          </a-descriptions>
        </template>
      </a-spin>
    </a-modal>

    <!-- 封禁确认弹窗 -->
    <a-modal
      v-model:open="banDialogVisible"
      :title="banTarget?.status === 'banned' ? '确认解封' : '确认封禁'"
      :ok-text="banTarget?.status === 'banned' ? '解封' : '封禁'"
      :ok-button-props="{ danger: banTarget?.status !== 'banned' }"
      :confirm-loading="banLoading"
      @ok="handleBan"
    >
      <p v-if="banTarget?.status === 'banned'">
        确定要解封用户 <strong>{{ banTarget?.nickname || banTarget?.phone }}</strong> 吗？解封后该用户将恢复正常使用。
      </p>
      <p v-else>
        确定要封禁用户 <strong>{{ banTarget?.nickname || banTarget?.phone }}</strong> 吗？封禁后该用户将无法登录和使用任何功能。
      </p>
    </a-modal>
  </div>
</template>
