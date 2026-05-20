<template>
  <div class="page">
    <van-nav-bar title="提交视频诊断" left-arrow @click-left="router.back()" :border="false" />

    <div class="quota-bar vct-card">
      <div>
        <div class="quota-label">本月已用 / 配额</div>
        <div class="quota-num">{{ used }} / {{ quota }}</div>
      </div>
      <van-button v-if="userStore.tier === 'free'" type="primary" size="small" @click="router.push('/subscribe')">
        升级 PRO
      </van-button>
    </div>

    <div class="vct-card form">
      <van-cell-group inset :border="false">
        <van-field
          v-model="form.video_url"
          label="视频链接"
          placeholder="粘贴抖音/快手/视频号/小红书/B站视频链接"
          autosize
          type="textarea"
          rows="2"
        />
        <van-field
          v-model="form.track"
          is-link
          readonly
          label="赛道"
          placeholder="选择细分赛道"
          @click="trackPickerShow = true"
        />
        <van-field
          v-model="form.diagnosis_type"
          is-link
          readonly
          label="诊断类型"
          @click="typePickerShow = true"
        />
      </van-cell-group>

      <div class="dim-list">
        <div class="dim-title">本次将对以下 6 个维度做 CT 扫描</div>
        <div class="dim-grid">
          <div v-for="d in dims" :key="d.name" class="dim-pill">
            <span class="emoji">{{ d.emoji }}</span>
            <span class="text">{{ d.name }}</span>
          </div>
        </div>
      </div>

      <van-button type="primary" block class="submit-btn" :loading="loading" @click="submit">
        🩺 开始 CT 扫描
      </van-button>
      <div class="tip">扫描通常需要 60-180 秒，期间可关闭页面</div>
    </div>

    <van-popup v-model:show="trackPickerShow" position="bottom">
      <van-picker
        :columns="tracks"
        @confirm="onTrackConfirm"
        @cancel="trackPickerShow = false"
        title="选择细分赛道"
      />
    </van-popup>

    <van-popup v-model:show="typePickerShow" position="bottom">
      <van-picker
        :columns="diagnosisTypes"
        @confirm="onTypeConfirm"
        @cancel="typePickerShow = false"
        title="诊断类型"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Toast } from 'vant'
import { diagnosisApi, benchmarkApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  video_url: '',
  track: '通用',
  diagnosis_type: 'ct_basic',
})
const loading = ref(false)
const trackPickerShow = ref(false)
const typePickerShow = ref(false)
const tracks = ref<{ text: string; value: string }[]>([])
const diagnosisTypes = [
  { text: '基础 CT（6 维评分 + 修复建议）', value: 'ct_basic' },
  { text: '完整 CT（含病灶时间戳定位）', value: 'ct_full' },
]
const dims = [
  { name: '表层观感', emoji: '👁' },
  { name: '内容内核', emoji: '🧠' },
  { name: '视听剪辑', emoji: '🎬' },
  { name: '人设话术', emoji: '🎭' },
  { name: '数据流量', emoji: '📊' },
  { name: '变现预埋', emoji: '💰' },
]

const used = computed(() => userStore.me?.monthly_free_scans_used ?? 0)
const quota = computed(() => userStore.me?.monthly_free_scans_quota ?? 3)

onMounted(async () => {
  try {
    const ts = await benchmarkApi.tracks()
    tracks.value = [
      { text: '通用', value: '通用' },
      ...ts.map((t: any) => ({ text: t.track, value: t.track })),
    ]
  } catch { /* ignore */ }
})

function onTrackConfirm({ selectedValues, selectedOptions }: any) {
  form.track = selectedValues[0]
  trackPickerShow.value = false
}
function onTypeConfirm({ selectedValues }: any) {
  form.diagnosis_type = selectedValues[0]
  typePickerShow.value = false
}

async function submit() {
  if (!form.video_url.trim() || form.video_url.length < 10) {
    Toast.fail('请粘贴有效视频链接')
    return
  }
  loading.value = true
  try {
    const diag = await diagnosisApi.submit({
      video_url: form.video_url.trim(),
      track: form.track === '通用' ? undefined : form.track,
      diagnosis_type: form.diagnosis_type,
    })
    Toast.success('诊断已开始')
    router.replace(`/diagnose/${diag.id}`)
  } catch (e: any) {
    if (e.status === 429) Toast.fail('本月配额已用完，升级 PRO 解锁')
    else Toast.fail(e.message || '提交失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.page { padding-bottom: 24px; }
.quota-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; margin: 0 16px 12px;
  .quota-label { font-size: 11px; color: var(--vct-text-3); }
  .quota-num { font-size: 18px; font-weight: 600; color: var(--vct-primary); }
}
.form { margin: 0 16px; padding: 16px 0; }
.dim-list { margin: 20px 16px; }
.dim-title { font-size: 13px; color: var(--vct-text-2); margin-bottom: 12px; }
.dim-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
  .dim-pill {
    background: var(--vct-surface); border: 1px solid var(--vct-border);
    padding: 10px 6px; border-radius: 8px; text-align: center; font-size: 12px;
    .emoji { font-size: 18px; display: block; margin-bottom: 4px; }
  }
}
.submit-btn { margin: 24px 16px 8px; height: 50px; font-size: 17px; }
.tip { text-align: center; font-size: 11px; color: var(--vct-text-3); margin-bottom: 8px; }
</style>
