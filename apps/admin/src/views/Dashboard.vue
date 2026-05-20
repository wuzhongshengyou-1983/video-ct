<script setup lang="ts">
import { getDashboard } from '@/api/admin'
import {
  RiseOutlined,
  ThunderboltOutlined,
  CrownOutlined,
  DollarOutlined,
  ScanOutlined,
  SmileOutlined,
  ReloadOutlined,
  DisconnectOutlined,
} from '@ant-design/icons-vue'

interface DashboardData {
  total_users: number
  active_pro: number
  active_max: number
  today_revenue_cny: number
  month_revenue_cny: number
  today_diagnoses: number
  avg_ai_satisfaction: number
}

const data = ref<DashboardData | null>(null)
const loading = ref(true)
const error = ref(false)

async function fetchData() {
  loading.value = true
  error.value = false
  try {
    const res = await getDashboard()
    data.value = res.data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>数据看板</h2>
      <a-button type="primary" @click="fetchData" size="small">
        <ReloadOutlined /> 刷新
      </a-button>
    </div>

    <!-- 后端未连接 -->
    <a-result
      v-if="error"
      status="error"
      title="后端服务未连接"
      sub-title="无法获取看板数据，请检查后端服务是否已启动"
    >
      <template #icon><DisconnectOutlined /></template>
      <template #extra>
        <a-button type="primary" @click="fetchData" :loading="loading">
          <ReloadOutlined /> 重试
        </a-button>
      </template>
    </a-result>

    <template v-else>
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 统计卡片 -->
      <div class="stat-cards">
        <a-card>
          <a-statistic title="总用户数" :value="data?.total_users ?? 0">
            <template #prefix><RiseOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card>
          <a-statistic
            title="活跃 PRO 用户"
            :value="data?.active_pro ?? 0"
            :value-style="{ color: '#3b82f6' }"
          >
            <template #prefix><ThunderboltOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card>
          <a-statistic
            title="活跃 MAX 用户"
            :value="data?.active_max ?? 0"
            :value-style="{ color: '#f59e0b' }"
          >
            <template #prefix><CrownOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card>
          <a-statistic
            title="月营收 (CNY)"
            :value="data?.month_revenue_cny ?? 0"
            :precision="2"
            :value-style="{ color: '#10b981' }"
          >
            <template #prefix><DollarOutlined /></template>
          </a-statistic>
        </a-card>
      </div>

      <!-- 今日指标行 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="12">
          <a-card title="今日概览">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic
                  title="今日流水"
                  :value="data?.today_revenue_cny ?? 0"
                  :precision="2"
                  prefix="¥"
                  :value-style="{ color: '#10b981' }"
                />
              </a-col>
              <a-col :span="12">
                <a-statistic
                  title="今日诊断"
                  :value="data?.today_diagnoses ?? 0"
                  :value-style="{ color: '#3b82f6' }"
                >
                  <template #prefix><ScanOutlined /></template>
                </a-statistic>
              </a-col>
            </a-row>
          </a-card>
        </a-col>
        <a-col :span="12">
          <a-card title="AI 满意度">
            <a-statistic
              :value="((data?.avg_ai_satisfaction ?? 0) * 100).toFixed(1)"
              suffix="%"
              :value-style="{
                color: (data?.avg_ai_satisfaction ?? 0) >= 0.8 ? '#10b981' : '#f59e0b',
              }"
            >
              <template #prefix><SmileOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.dashboard {
  .stat-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    @media (max-width: 1200px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  :deep(.ant-statistic-title) {
    font-size: 13px;
  }
  :deep(.ant-statistic-content) {
    font-size: 28px;
  }
}
</style>
