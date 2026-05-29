<template>
  <div class="page">
    <van-nav-bar
      title="复诊 — 对比改善"
      left-arrow
      @click-left="router.back()"
      :border="false"
    />

    <div v-if="origDiag" class="vct-card orig-card">
      <div class="orig-label">上次诊断</div>
      <div class="orig-url">{{ origDiag.video_url }}</div>
      <div class="orig-meta">
        {{ formatDate(origDiag.created_at) }} · 第
        {{ origDiag.diagnosis_sequence ?? 1 }} 次
      </div>
    </div>

    <div class="vct-card form">
      <van-cell-group inset :border="false">
        <van-field
          v-model="videoUrl"
          label="修改后的视频链接"
          placeholder="粘贴修改后的视频链接（可与上次相同）"
          autosize
          type="textarea"
          rows="2"
          :error="!!urlError"
          :error-message="urlError"
          @update:model-value="urlError = ''"
        />
      </van-cell-group>

      <div class="hint">系统将自动对比本次与上次的 CT 结果，生成改善报告。</div>

      <van-button
        type="primary"
        block
        class="submit-btn"
        :loading="loading"
        @click="submit"
      >
        提交复诊
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { Toast } from "vant";
import { diagnosisApi } from "@/api";
import dayjs from "dayjs";

const router = useRouter();
const route = useRoute();
const origId = route.params.id as string;

const origDiag = ref<any>(null);
const videoUrl = ref("");
const urlError = ref("");
const loading = ref(false);

const VIDEO_URL_PATTERN =
  /douyin\.com|kuaishou\.com|xiaohongshu\.com|bilibili\.com|weixin\.qq\.com/;

function formatDate(iso: string) {
  return dayjs(iso).format("MM-DD HH:mm");
}

onMounted(async () => {
  try {
    const d = await diagnosisApi.get(origId);
    origDiag.value = d;
    videoUrl.value = d.video_url ?? "";
  } catch {
    Toast.fail("找不到原始诊断记录");
    router.back();
  }
});

async function submit() {
  const url = videoUrl.value.trim();
  if (!url) {
    urlError.value = "请粘贴视频链接";
    return;
  }
  if (!VIDEO_URL_PATTERN.test(url)) {
    urlError.value = "仅支持抖音/快手/小红书/B站/视频号链接";
    return;
  }

  loading.value = true;
  try {
    const diag = await diagnosisApi.submit({
      video_url: url,
      track: origDiag.value?.track,
      diagnosis_type: origDiag.value?.diagnosis_type ?? "ct_basic",
    });
    Toast.success("复诊已提交");
    router.replace(`/diagnose/${diag.id}`);
  } catch (e: any) {
    Toast.fail(e.message || "提交失败");
  } finally {
    loading.value = false;
  }
}
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
}
.orig-card {
  margin: 12px 16px;
  padding: 14px 16px;
  .orig-label {
    font-size: 11px;
    color: var(--mfc-fg-3);
    margin-bottom: 6px;
  }
  .orig-url {
    font-size: 13px;
    color: var(--mfc-fg);
    word-break: break-all;
    margin-bottom: 4px;
  }
  .orig-meta {
    font-size: 11px;
    color: var(--mfc-fg-3);
  }
}
.form {
  margin: 0 16px;
  padding: 16px 0;
}
.hint {
  margin: 16px 16px 0;
  font-size: 12px;
  color: var(--mfc-fg-2);
  line-height: 1.6;
}
.submit-btn {
  margin: 20px 16px 8px;
  min-height: 50px;
  font-size: 17px;
}
</style>
