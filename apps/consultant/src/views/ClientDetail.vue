<script setup lang="ts">
import {
  getClientDetail,
  getClientDiagnoses,
  getClientGaps,
  getClientPersona,
  getClientPositioning,
  getClientArchive,
  saveConsultantNote,
} from '@/api/consultant'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  ArrowLeftOutlined,
  UserOutlined,
  HistoryOutlined,
  LineChartOutlined,
  IdcardOutlined,
  ShopOutlined,
  EditOutlined,
  SaveOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const clientId = route.params.id as string

// 各数据块
const profile = ref<Record<string, unknown>>({})
const persona = ref<Record<string, unknown> | null>(null)
const positioning = ref<Record<string, unknown> | null>(null)
const archive = ref<Record<string, unknown> | null>(null)
const diagnoses = ref<Record<string, unknown>[]>([])
const gaps = ref<Record<string, unknown>[]>([])
const loading = ref(true)

// 加载失败标记
const loadErrors = reactive<Record<string, boolean>>({
  persona: false,
  positioning: false,
  archive: false,
  diagnoses: false,
  gaps: false,
})

// 顾问笔记
const editingNote = ref(false)
const noteText = ref('')
const savingNote = ref(false)

async function fetchAll() {
  loading.value = true

  // 基本信息 + 诊断 + 差距（核心，必须加载）
  const corePromises = [
    getClientDetail(clientId).then((res) => { profile.value = res.data }),
    getClientDiagnoses(clientId).then((res) => {
      diagnoses.value = res.data.items ?? res.data.data ?? res.data ?? []
    }).catch(() => { loadErrors.diagnoses = true }),
    getClientGaps(clientId).then((res) => {
      gaps.value = res.data.items ?? res.data.data ?? res.data ?? []
    }).catch(() => { loadErrors.gaps = true }),
  ]

  // 人设 / 商业定位 / 归档（可选，加载失败不影响主页面）
  const optionalPromises = [
    getClientPersona(clientId).then((res) => {
      persona.value = res.data
    }).catch(() => { loadErrors.persona = true }),
    getClientPositioning(clientId).then((res) => {
      positioning.value = res.data
    }).catch(() => { loadErrors.positioning = true }),
    getClientArchive(clientId).then((res) => {
      archive.value = res.data
    }).catch(() => { loadErrors.archive = true }),
  ]

  try {
    await Promise.all([...corePromises, ...optionalPromises])
    noteText.value = (profile.value.consultant_note as string) || ''
  } finally {
    loading.value = false
  }
}

async function handleSaveNote() {
  savingNote.value = true
  try {
    await saveConsultantNote(clientId, { note: noteText.value })
    message.success('笔记已保存')
    editingNote.value = false
  } finally {
    savingNote.value = false
  }
}

function goBack() {
  router.push('/clients')
}

// 数字缩写: 1.2w / 123.4w
function formatFollowerCount(n: number | undefined | null): string {
  if (n == null) return '-'
  if (n >= 100000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 10000) return (n / 10000).toFixed(2) + 'w'
  return n.toLocaleString()
}

// 金额格式化
function formatMoney(n: number | undefined | null): string {
  if (n == null) return '-'
  if (n >= 10000) return '¥' + (n / 10000).toFixed(1) + 'w'
  return '¥' + n.toLocaleString()
}

// 以 profile 为主，persona/positioning 为补充
function p(key: string): unknown {
  // 优先从 profile 取，fallback 到 persona -> positioning -> archive
  if (profile.value[key] != null) return profile.value[key]
  if (persona.value?.[key] != null) return persona.value[key]
  if (positioning.value?.[key] != null) return positioning.value[key]
  if (archive.value?.[key] != null) return archive.value[key]
  return null
}

const diagnoseColumns = [
  { title: '日期', dataIndex: 'created_at', key: 'created_at', width: 140 },
  { title: '平台', dataIndex: 'platform', key: 'platform', width: 80 },
  { title: '类型', dataIndex: 'diag_type', key: 'diag_type', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90 },
  { title: '得分', dataIndex: 'score', key: 'score', width: 70 },
  { title: '满意度', dataIndex: 'satisfaction', key: 'satisfaction', width: 80 },
]

const gapColumns = [
  { title: '维度', dataIndex: 'dimension', key: 'dimension', width: 120 },
  { title: '当前值', dataIndex: 'current_value', key: 'current_value', width: 80 },
  { title: '目标值', dataIndex: 'target_value', key: 'target_value', width: 80 },
  { title: '差距', dataIndex: 'gap_pct', key: 'gap_pct', width: 100 },
  { title: '趋势', dataIndex: 'trend', key: 'trend', width: 60 },
]

const statusMap: Record<string, string> = {
  pending: '等待中', running: '分析中', completed: '已完成', failed: '失败',
}
const statusColors: Record<string, string> = {
  pending: 'default', running: 'blue', completed: 'green', failed: 'red',
}

onMounted(fetchAll)
</script>

<template>
  <div class="client-detail">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 顶部导航 -->
      <div class="page-header">
        <a-space>
          <a-button type="text" @click="goBack">
            <ArrowLeftOutlined /> 返回
          </a-button>
          <h2>{{ (profile.nickname as string) || (profile.name as string) || '客户详情' }}</h2>
          <a-tag
            v-if="profile.level"
            :color="profile.level === 'max' ? 'gold' : profile.level === 'pro' ? 'blue' : 'default'"
          >
            {{ String(profile.level).toUpperCase() }}
          </a-tag>
        </a-space>
      </div>

      <!-- 档案卡片：基本信息 + 人设 + 商业定位 -->
      <a-row :gutter="16" style="margin-bottom: 24px">
        <!-- 基本信息 -->
        <a-col :span="8">
          <a-card title="基本信息">
            <template #extra><UserOutlined /></template>
            <a-descriptions v-if="profile.id" :column="1" size="small" :colon="false">
              <a-descriptions-item label="昵称">{{ profile.nickname || profile.name || '-' }}</a-descriptions-item>
              <a-descriptions-item label="手机号">{{ profile.phone || '-' }}</a-descriptions-item>
              <a-descriptions-item label="赛道">{{ p('track') || '-' }}</a-descriptions-item>
              <a-descriptions-item label="等级">
                <a-tag
                  :color="profile.level === 'max' ? 'gold' : profile.level === 'pro' ? 'blue' : 'default'"
                >
                  {{ profile.level || 'free' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="注册时间">
                {{ (profile.created_at as string) ? dayjs(profile.created_at as string).format('YYYY-MM-DD') : '-' }}
              </a-descriptions-item>
            </a-descriptions>
            <a-empty v-else description="暂无数据" :image-style="{ height: '40px' }" />
          </a-card>
        </a-col>

        <!-- 人设卡片 -->
        <a-col :span="8">
          <a-card title="人设卡片">
            <template #extra><IdcardOutlined /></template>
            <template v-if="persona || profile.persona_type || profile.content_style">
              <a-descriptions :column="1" size="small" :colon="false">
                <a-descriptions-item label="账号定位">
                  {{ persona?.persona_type || profile.persona_type || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="内容风格">
                  {{ persona?.content_style || profile.content_style || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="目标受众">
                  {{ persona?.target_audience || profile.target_audience || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="粉丝量级">
                  {{ formatFollowerCount((persona?.follower_count ?? profile.follower_count) as number) }}
                </a-descriptions-item>
                <a-descriptions-item label="发布频率">
                  {{ persona?.post_frequency || profile.post_frequency || '-' }}
                </a-descriptions-item>
              </a-descriptions>
            </template>
            <a-empty v-else description="暂无数据" :image-style="{ height: '40px' }" />
          </a-card>
        </a-col>

        <!-- 商业定位 -->
        <a-col :span="8">
          <a-card title="商业定位">
            <template #extra><ShopOutlined /></template>
            <template v-if="positioning || profile.monetization_type || profile.average_order_value">
              <a-descriptions :column="1" size="small" :colon="false">
                <a-descriptions-item label="变现方式">
                  {{ positioning?.monetization_type || profile.monetization_type || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="客单价">
                  {{ formatMoney((positioning?.average_order_value ?? profile.average_order_value) as number) }}
                </a-descriptions-item>
                <a-descriptions-item label="品牌合作">
                  {{ positioning?.brand_cooperation || profile.brand_cooperation || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="电商平台">
                  {{ positioning?.ecommerce_platform || profile.ecommerce_platform || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="健康度">
                  <a-tag
                    :color="
                      ((positioning?.health_score ?? profile.health_score) as number) >= 80
                        ? 'green'
                        : ((positioning?.health_score ?? profile.health_score) as number) >= 60
                          ? 'orange'
                          : 'red'
                    "
                  >
                    {{ positioning?.health_score ?? profile.health_score ?? '-' }}
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>
            </template>
            <a-empty v-else description="暂无数据" :image-style="{ height: '40px' }" />
          </a-card>
        </a-col>
      </a-row>

      <!-- 差距曲线 -->
      <a-card title="差距曲线" style="margin-bottom: 24px">
        <template #extra><LineChartOutlined /></template>
        <a-table
          v-if="gaps.length > 0"
          :columns="gapColumns"
          :data-source="gaps"
          :pagination="false"
          :scroll="{ x: 500 }"
          row-key="dimension"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'gap_pct'">
              <a-progress
                :percent="Math.abs(Number(record.gap_pct) || 0)"
                :status="Number(record.gap_pct) < 0 ? 'exception' : 'active'"
                :stroke-color="Number(record.gap_pct) < 0 ? '#ef4444' : '#10b981'"
                style="width: 120px"
              />
            </template>
            <template v-if="column.key === 'trend'">
              <span
                :style="{
                  color: record.trend === 'up' ? '#10b981' : record.trend === 'down' ? '#ef4444' : '#9ca3af',
                }"
              >
                {{ record.trend === 'up' ? '↑' : record.trend === 'down' ? '↓' : '→' }}
              </span>
            </template>
          </template>
        </a-table>
        <a-empty v-else description="暂无差距数据" />
      </a-card>

      <!-- 诊断历史 -->
      <a-card title="诊断历史" style="margin-bottom: 24px">
        <template #extra><HistoryOutlined /></template>
        <a-table
          v-if="diagnoses.length > 0"
          :columns="diagnoseColumns"
          :data-source="diagnoses"
          :pagination="{ pageSize: 5 }"
          :scroll="{ x: 550 }"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'created_at'">
              {{ record.created_at ? dayjs(record.created_at as string).format('MM-DD HH:mm') : '-' }}
            </template>
            <template v-if="column.key === 'platform'">
              <a-tag>{{ record.platform || '-' }}</a-tag>
            </template>
            <template v-if="column.key === 'diag_type'">
              {{ record.diag_type || '-' }}
            </template>
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColors[record.status as string] || 'default'">
                {{ statusMap[record.status as string] || record.status }}
              </a-tag>
            </template>
            <template v-if="column.key === 'satisfaction'">
              {{ record.satisfaction != null ? ((record.satisfaction as number) * 100).toFixed(0) + '%' : '-' }}
            </template>
          </template>
        </a-table>
        <a-empty v-else description="暂无诊断记录" />
      </a-card>

      <!-- 归档信息 -->
      <a-card title="平台归档" style="margin-bottom: 24px" v-if="archive">
        <template #extra><FileTextOutlined /></template>
        <a-descriptions :column="3" size="small" :colon="false" bordered>
          <a-descriptions-item label="最近发布">{{ archive.latest_post_at ? dayjs(archive.latest_post_at as string).format('MM-DD HH:mm') : '-' }}</a-descriptions-item>
          <a-descriptions-item label="近 30 天发布">{{ archive.post_count_30d ?? '-' }}</a-descriptions-item>
          <a-descriptions-item label="平均互动率">{{ archive.avg_engagement_rate != null ? (Number(archive.avg_engagement_rate) * 100).toFixed(2) + '%' : '-' }}</a-descriptions-item>
          <a-descriptions-item label="总播放量">{{ formatFollowerCount(archive.total_plays as number) }}</a-descriptions-item>
          <a-descriptions-item label="总点赞">{{ formatFollowerCount(archive.total_likes as number) }}</a-descriptions-item>
          <a-descriptions-item label="总评论">{{ formatFollowerCount(archive.total_comments as number) }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- 顾问笔记 -->
      <a-card title="顾问笔记">
        <template #extra>
          <a-button
            v-if="!editingNote"
            size="small"
            type="primary"
            @click="editingNote = true"
          >
            <EditOutlined /> 编辑
          </a-button>
          <a-button
            v-else
            size="small"
            type="primary"
            :loading="savingNote"
            @click="handleSaveNote"
          >
            <SaveOutlined /> 保存
          </a-button>
        </template>
        <a-textarea
          v-if="editingNote"
          v-model:value="noteText"
          :rows="6"
          placeholder="记录客户的关注点、建议跟进事项、沟通要点..."
        />
        <p v-else-if="noteText" style="white-space: pre-wrap; color: var(--text-secondary)">
          {{ noteText }}
        </p>
        <a-empty v-else description="暂无笔记，点击右上角「编辑」添加" />
      </a-card>
    </a-spin>
  </div>
</template>

<style lang="scss" scoped>
.client-detail {
  :deep(.ant-descriptions-item-label) {
    color: var(--text-secondary);
  }
  :deep(.ant-descriptions-item-content) {
    color: var(--text-primary);
  }
}
</style>
