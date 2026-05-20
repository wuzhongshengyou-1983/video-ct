<script setup lang="ts">
import { listProducts, createProduct, updateProduct, deleteProduct } from '@/api/admin'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'

interface ProductRecord {
  id: string
  name: string
  sku?: string
  slug?: string
  price_cny?: number
  price?: number
  duration_days?: number
  features?: string[]
  is_active?: boolean
  created_at?: string
}

const products = ref<ProductRecord[]>([])
const loading = ref(false)
const modalVisible = ref(false)
const editingProduct = ref<ProductRecord | null>(null)
const submitting = ref(false)
const togglingId = ref<string | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  sku: '',
  price_cny: null as number | null,
  duration_days: 30,
  features: '',
})

const columns = [
  { title: '产品名称', dataIndex: 'name', key: 'name', width: 160 },
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 120 },
  { title: '价格 (CNY)', dataIndex: 'price_cny', key: 'price_cny', width: 120 },
  { title: '时长 (天)', dataIndex: 'duration_days', key: 'duration_days', width: 100 },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100 },
  { title: '操作', key: 'actions', width: 240 },
]

// SKU 格式校验: 大写字母+数字+连字符
const skuPattern = /^[A-Z0-9][A-Z0-9_-]*$/

const formRules = {
  name: [{ required: true, message: '产品名称不能为空', trigger: 'blur' }],
  price_cny: [
    { required: true, message: '请输入价格', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '价格必须为正数', trigger: 'blur' },
  ],
  sku: [
    {
      validator: (_rule: unknown, value: string) => {
        if (!value) return Promise.resolve()
        if (!skuPattern.test(value)) {
          return Promise.reject('SKU 格式：大写字母+数字+连字符，如 PRO_MONTHLY_V1')
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  duration_days: [
    { required: true, message: '请输入时长', trigger: 'blur' },
    { type: 'number', min: 1, message: '时长必须大于 0', trigger: 'blur' },
  ],
}

async function fetch() {
  loading.value = true
  try {
    const res = await listProducts()
    products.value = res.data.items ?? res.data.data ?? res.data ?? []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingProduct.value = null
  form.name = ''
  form.sku = ''
  form.price_cny = null
  form.duration_days = 30
  form.features = ''
  modalVisible.value = true
}

function openEdit(record: ProductRecord) {
  editingProduct.value = record
  form.name = record.name
  form.sku = record.sku ?? record.slug ?? ''
  form.price_cny = record.price_cny ?? record.price ?? 0
  form.duration_days = record.duration_days ?? 30
  form.features = Array.isArray(record.features) ? record.features.join('\n') : ''
  modalVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      sku: form.sku || undefined,
      price_cny: form.price_cny,
      duration_days: form.duration_days,
      features: form.features.split('\n').filter(Boolean),
    }
    if (editingProduct.value) {
      await updateProduct(editingProduct.value.id, payload)
      message.success('已更新')
    } else {
      await createProduct(payload)
      message.success('已创建')
    }
    modalVisible.value = false
    fetch()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: string) {
  await deleteProduct(id)
  message.success('已删除')
  fetch()
}

async function handleToggleActive(record: ProductRecord) {
  togglingId.value = record.id
  try {
    await updateProduct(record.id, { is_active: !record.is_active })
    message.success(record.is_active ? '已下架' : '已上架')
    fetch()
  } finally {
    togglingId.value = null
  }
}

function formatPrice(n?: number): string {
  if (n == null) return '¥0'
  if (n >= 1000) return '¥' + n.toLocaleString()
  return '¥' + n.toFixed(2).replace(/\.?0+$/, '')
}

onMounted(fetch)
</script>

<template>
  <div class="products-page">
    <div class="page-header">
      <h2>产品管理</h2>
      <a-button type="primary" @click="openCreate">新增产品</a-button>
    </div>

    <a-spin :spinning="loading">
      <a-table :columns="columns" :data-source="products" :scroll="{ x: 800 }" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'price_cny'">
            <span :style="{ color: '#10b981', fontWeight: 500 }">
              {{ formatPrice(record.price_cny ?? record.price) }}
            </span>
          </template>
          <template v-if="column.key === 'sku'">
            {{ record.sku ?? record.slug ?? '-' }}
          </template>
          <template v-if="column.key === 'is_active'">
            <a-switch
              :checked="record.is_active"
              :loading="togglingId === record.id"
              checked-children="上架"
              un-checked-children="下架"
              @click="handleToggleActive(record)"
            />
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" @click="openEdit(record)">编辑</a-button>
              <a-popconfirm title="确定删除?" @confirm="handleDelete(record.id)">
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
      <a-empty v-if="!loading && products.length === 0" description="暂无产品数据" />
    </a-spin>

    <!-- 弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingProduct ? '编辑产品' : '新增产品'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
      width="520px"
    >
      <a-form ref="formRef" :model="form" :rules="formRules" layout="vertical">
        <a-form-item label="产品名称" name="name">
          <a-input v-model:value="form.name" placeholder="例: PRO 月度版" />
        </a-form-item>
        <a-form-item label="SKU" name="sku">
          <a-input
            v-model:value="form.sku"
            placeholder="例: PRO_MONTHLY_V1（选填）"
          />
        </a-form-item>
        <a-form-item label="价格 (CNY)" name="price_cny">
          <a-input-number
            v-model:value="form.price_cny"
            :min="0"
            :precision="2"
            style="width: 100%"
            placeholder="例: 99.00"
          />
        </a-form-item>
        <a-form-item label="时长 (天)" name="duration_days">
          <a-input-number
            v-model:value="form.duration_days"
            :min="1"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="功能要点（每行一个）">
          <a-textarea v-model:value="form.features" :rows="4" placeholder="功能1&#10;功能2&#10;..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
