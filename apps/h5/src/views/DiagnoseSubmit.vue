<template>
  <div class="page">
    <van-nav-bar
      title="提交视频诊断"
      left-arrow
      @click-left="router.back()"
      :border="false"
    />

    <div class="quota-bar vct-card">
      <div>
        <div class="quota-label">本月已用 / 配额</div>
        <div class="quota-num">{{ used }} / {{ quota }}</div>
      </div>
      <van-button
        v-if="userStore.tier === 'free'"
        type="primary"
        size="small"
        @click="router.push('/subscribe')"
      >
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
          :error="!!errors.video_url"
          :error-message="errors.video_url"
          @update:model-value="errors.video_url = ''"
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

      <van-button
        type="primary"
        block
        class="submit-btn"
        :loading="loading"
        @click="submit"
      >
        🩺 开始 CT 扫描
      </van-button>
      <div class="tip">扫描通常需要 60-180 秒，期间可关闭页面</div>
    </div>

    <van-popup
      v-model:show="trackPickerShow"
      position="bottom"
      :style="{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }"
    >
      <van-picker
        :columns="tracks"
        @confirm="onTrackConfirm"
        @cancel="trackPickerShow = false"
        title="选择细分赛道"
      />
    </van-popup>

    <van-popup
      v-model:show="typePickerShow"
      position="bottom"
      :style="{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }"
    >
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
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Toast, Dialog } from "vant";
import { diagnosisApi, benchmarkApi, eventsApi } from "@/api";
import { trackConversion } from "@/utils/tracker";
import { useUserStore } from "@/stores/user";
import { DIAGNOSIS_TYPES } from "@video-ct/shared";
import { subscribeDiagnosisComplete } from "@/utils/subscribe-message";

const router = useRouter();
const userStore = useUserStore();

const form = reactive({
  video_url: "",
  track: "通用",
  diagnosis_type: DIAGNOSIS_TYPES.CT_BASIC,
});
const errors = reactive({
  video_url: "",
});
const loading = ref(false);
const trackPickerShow = ref(false);
const typePickerShow = ref(false);
const tracks = ref<{ text: string; value: string }[]>([]);
const diagnosisTypes = [
  { text: "基础 CT（6 维评分 + 修复建议）", value: DIAGNOSIS_TYPES.CT_BASIC },
  { text: "完整 CT（含病灶时间戳定位）", value: DIAGNOSIS_TYPES.CT_FULL },
];
const dims = [
  { name: "表层观感", emoji: "👁" },
  { name: "内容内核", emoji: "🧠" },
  { name: "视听剪辑", emoji: "🎬" },
  { name: "人设话术", emoji: "🎭" },
  { name: "数据流量", emoji: "📊" },
  { name: "变现预埋", emoji: "💰" },
];

const used = computed(() => userStore.me?.monthly_free_scans_used ?? 0);
const quota = computed(() => userStore.me?.monthly_free_scans_quota ?? 3);

onMounted(async () => {
  try {
    const ts = await benchmarkApi.tracks();
    tracks.value = [
      { text: "通用", value: "通用" },
      ...ts.map((t: any) => ({ text: t.track, value: t.track })),
    ];
  } catch {
    // tracks API 失败不阻塞页面使用，保留默认「通用」选项
    tracks.value = [{ text: "通用", value: "通用" }];
  }
});

function onTrackConfirm({ selectedValues }: any) {
  form.track = selectedValues[0];
  trackPickerShow.value = false;
}
function onTypeConfirm({ selectedValues }: any) {
  form.diagnosis_type = selectedValues[0];
  typePickerShow.value = false;
}

const VIDEO_URL_PATTERN =
  /douyin\.com|kuaishou\.com|xiaohongshu\.com|bilibili\.com|weixin\.qq\.com/;

function validate(): boolean {
  const url = form.video_url.trim();
  if (!url) {
    errors.video_url = "请粘贴视频链接";
    return false;
  }
  if (url.length < 10) {
    errors.video_url = "链接太短，请粘贴完整视频链接";
    return false;
  }
  if (!VIDEO_URL_PATTERN.test(url)) {
    errors.video_url = "目前仅支持抖音/快手/小红书/B站/视频号的链接";
    return false;
  }
  return true;
}

async function submit() {
  if (!validate()) return;

  loading.value = true;
  try {
    trackConversion("diagnose_submitted", {
      track: form.track,
      diagnosis_type: form.diagnosis_type,
    });
    eventsApi.track("diagnosis_started", {
      track: form.track,
      diagnosis_type: form.diagnosis_type,
    });
    const diag = await diagnosisApi.submit({
      video_url: form.video_url.trim(),
      track: form.track === "通用" ? undefined : form.track,
      diagnosis_type: form.diagnosis_type,
    });
    Toast.success("诊断已开始");

    // 询问是否订阅通知
    Dialog.confirm({
      title: "诊断完成后通知你？",
      message: "开启微信通知，诊断完成后第一时间提醒你查看报告",
      confirmButtonText: "好的",
      cancelButtonText: "不用了",
    })
      .then(() => {
        subscribeDiagnosisComplete();
      })
      .catch(() => {
        // 用户拒绝，无操作
      });

    router.replace(`/diagnose/${diag.id}`);
  } catch (e: any) {
    if (e.status === 402) {
      Toast.fail("本月配额已用完，升级 PRO 解锁");
    } else if (e.status === 429) {
      Toast.fail("本月配额已用完，升级 PRO 解锁");
    } else if (e.status && e.status >= 500) {
      Toast.fail("服务繁忙，请稍后重试");
    } else {
      Toast.fail(e.message || "提交失败");
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
}
.quota-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  margin: 0 16px 12px;
  .quota-label {
    font-size: 11px;
    color: var(--mfc-fg-3);
  }
  .quota-num {
    font-size: 18px;
    font-weight: 600;
    color: var(--mfc-blue);
  }
}
.form {
  margin: 0 16px;
  padding: 16px 0;
  scroll-margin-bottom: 40vh;
}
.dim-list {
  margin: 20px 16px;
}
.dim-title {
  font-size: 13px;
  color: var(--mfc-fg-2);
  margin-bottom: 12px;
}
.dim-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  .dim-pill {
    background: var(--mfc-bg-soft);
    border: 1px solid var(--mfc-hairline);
    padding: 10px 6px;
    border-radius: 8px;
    text-align: center;
    font-size: 12px;
    .emoji {
      font-size: 18px;
      display: block;
      margin-bottom: 4px;
    }
  }
}
.submit-btn {
  margin: 24px 16px 8px;
  min-height: 50px;
  font-size: 17px;
}
.tip {
  text-align: center;
  font-size: 11px;
  color: var(--mfc-fg-3);
  margin-bottom: 8px;
}
</style>
