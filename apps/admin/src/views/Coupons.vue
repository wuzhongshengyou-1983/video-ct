<script setup lang="ts">
import { listCoupons, createCoupon } from '@/api/admin'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { CopyOutlined } from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

interface CouponRecord {
  id: string
  code: string
  discount_type: string
  discount_value: number
  usage_limit: number
  used_count: number
  is_active: boolean
  expires_at: string
}

const coupons = ref<CouponRecord[]>([])
const total = ref(0)
const loading = ref(false)
const modalVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  code: '',
  discount_type: 'percent_off',
  discount_value: null as number | null,
  usage_limit: 100,
  expires_at: null as string | null,
})

const pagination = reactive({ current: 1, pageSize: 10 })

const columns = [
  { title: '优惠码', dataIndex: 'code', key: 'code', width: 160 },
  { title: '类型', dataIndex: 'discount_type', key: 'discount_type', width: 100 },
  { title: '优惠值', dataIndex: 'discount_value', key: 'discount_value', width: 100 },
  { title: '用量', key: 'usage', width: 120 },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80 },
  { title: '到期时间', dataIndex: 'expires_at', key: 'expires_at', width: 160 },
]

const typeMap: Record<string, string> = { percent_off: '百分比', amount_off: '固定金额' }

const formRules = {
  code: [{ required: true, message: '优惠码不能为空', trigger: 'blur' }],
  discount_value: [
    { required: true, message: '请输入优惠值', trigger: 'blur' },
    {
      validator: (_rule: unknown, value: number | null) => {
        if (value == null || value <= 0) return Promise.reject('优惠值必须大于 0')
        if (form.discount_type === 'percent_off' && value > 100) {
          return Promise.reject('百分比折扣不能超过 100%')
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  expires_at: [
    {
      validator: (_rule: unknown, value: string | null) => {
        if (!value) return Promise.resolve()
        const d = dayjs(value)
        if (d.isBefore(dayjs(), 'day')) {
          return Promise.reject('到期时间不能早于今天')
        }
        return Promise.resolve()
      },
      trigger: 'change',
    },
  ],
}

function openCreate() {
  form.code = ''
  form.discount_type = 'percent_off'
  form.discount_value = null
  form.usage_limit = 100
  form.expires_at = null
  modalVisible.value = true
}

async function fetch() {
  loading.value = true
  try {
    const res = await listCoupons({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    coupons.value = res.data.items ?? res.data.data ?? []
    total.value = res.data.total ?? res.data.count ?? 0
  } finally {
    loading.value = false
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
    const payload = {
      code: form.code,
      discount_type: form.discount_type,
      discount_value: form.discount_value,
      usage_limit: form.usage_limit,
      expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : undefined,
    }
    await createCoupon(payload)
    message.success('优惠券已创建')
    modalVisible.value = false
    fetch()
  } finally {
    submitting.value = false
  }
}

async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code)
    message.success('已复制: ' + code)
  } catch {
    // Fallback
    const textarea = document.createElement('textarea')
    textarea.value = code
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    message.success('已复制: ' + code)
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
  <div class="coupons-page">
    <div class="page-header">
      <h2>优惠券管理</h2>
      <a-button type="primary" @click="openCreate">创建优惠券</a-button>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="coupons"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        :scroll="{ x: 750 }"
        row-key="id"
        @change="({ current, pageSize }: any) => onPageChange(current, pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'code'">
            <a-space>
              <a-tag color="blue">{{ record.code }}</a-tag>
              <a-button type="link" size="small" @click="copyCode(record.code)">
                <CopyOutlined />
              </a-button>
            </a-space>
          </template>
          <template v-if="column.key === 'discount_type'">
            {{ typeMap[record.discount_type] || record.discount_type }}
          </template>
          <template v-if="column.key === 'discount_value'">
            {{ record.discount_type === 'percent_off' ? record.discount_value + '%' : '¥' + record.discount_value }}
          </template>
          <template v-if="column.key === 'usage'">
            {{ record.used_count ?? 0 }} / {{ record.usage_limit ?? '-' }}
          </template>
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'default'">
              {{ record.is_active ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'expires_at'">
            {{ record.expires_at ? dayjs(record.expires_at).format('MM-DD HH:mm') : '永久' }}
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && coupons.length === 0" description="暂无优惠券数据" />
    </a-spin>

    <!-- 创建弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      title="创建优惠券"
      @ok="handleCreate"
      :confirm-loading="submitting"
      width="520px"
    >
      <a-form ref="formRef" :model="form" :rules="formRules" layout="vertical">
        <a-form-item label="优惠码" name="code">
          <a-input v-model:value="form.code" placeholder="例: LAUNCH20" />
        </a-form-item>
        <a-form-item label="折扣类型" required>
          <a-select v-model:value="form.discount_type">
            <a-select-option value="percent_off">百分比折扣</a-select-option>
            <a-select-option value="amount_off">固定金额减免</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="优惠值" name="discount_value">
          <a-input-number
            v-model:value="form.discount_value"
            :min="0.01"
            :precision="0"
            style="width: 100%"
            :placeholder="form.discount_type === 'percent_off' ? '例: 20 (表示 20%)' : '例: 50 (表示 ¥50)'"
          />
        </a-form-item>
        <a-form-item label="使用上限">
          <a-input-number v-model:value="form.usage_limit" :min="1" style="width: 100%" />
        </a-form-item>
        <a-form-item label="到期时间" name="expires_at">
          <a-date-picker
            v-model:value="form.expires_at"
            style="width: 100%"
            :disabled-date="(d: any) => d && d.isBefore(dayjs(), 'day')"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
