<template>
  <div class="page">
    <van-nav-bar
      title="个人资料"
      left-arrow
      @click-left="router.back()"
      :border="false"
    />

    <van-loading v-if="loading" size="24" vertical class="loading-center"
      >加载中…</van-loading
    >

    <!-- 网络异常 -->
    <div v-if="!loading && networkError" class="error-box vct-card">
      <van-empty image="network" description="网络异常，请检查网络后重试" />
      <van-button type="primary" block @click="loadProfile">重试</van-button>
    </div>

    <template v-if="!loading && !networkError">
      <!-- 头像上传 -->
      <div class="avatar-section">
        <div class="avatar-wrapper" @click="triggerUpload">
          <img
            v-if="avatarPreview"
            :src="avatarPreview"
            alt="头像"
            class="avatar-img"
          />
          <div v-else class="avatar-placeholder">
            {{ (form.nickname || "?").charAt(0).toUpperCase() }}
          </div>
          <div class="avatar-edit-icon">📷</div>
        </div>
        <div class="avatar-tip">点击更换头像（jpeg/png/webp，≤2MB）</div>
        <!-- 隐藏的 van-uploader -->
        <van-uploader
          ref="uploaderRef"
          v-model="avatarFiles"
          :max-count="1"
          :before-read="beforeRead"
          :after-read="afterRead"
          accept="image/jpeg,image/png,image/webp"
          style="display: none"
        />
        <div v-if="avatarError" class="avatar-error">{{ avatarError }}</div>
      </div>

      <div class="form-section">
        <van-field
          v-model="form.nickname"
          label="昵称"
          placeholder="你的昵称"
          maxlength="20"
          :error="!!errors.nickname"
          :error-message="errors.nickname"
          @update:model-value="errors.nickname = ''"
        />
        <van-field
          v-model="form.track"
          label="赛道"
          placeholder="如：职场干货、美妆教程"
        />
        <van-field
          v-model="form.platform"
          label="主平台"
          placeholder="如：抖音、B站"
        />
        <van-field
          v-model="form.follower_count"
          label="粉丝数"
          placeholder="输入数字"
          type="number"
          :error="!!errors.follower_count"
          :error-message="errors.follower_count"
          @update:model-value="errors.follower_count = ''"
        />
        <van-field
          v-model="form.bio"
          label="简介"
          placeholder="简单介绍你的账号定位"
          type="textarea"
          rows="3"
          autosize
        />
        <van-field
          v-model="form.goal"
          label="目标"
          placeholder="你的短视频目标（如：百万粉、月入5万）"
          type="textarea"
          rows="2"
          autosize
        />
      </div>

      <div class="save-section">
        <van-button
          type="primary"
          block
          size="large"
          :loading="saving"
          @click="save"
        >
          保存
        </van-button>
      </div>
    </template>

    <!-- 服务端错误 -->
    <div v-if="!loading && serverError" class="error-box vct-card">
      <p>{{ serverError }}</p>
      <van-button size="small" @click="loadProfile">重试</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Toast } from "vant";
import { userApi } from "@/api";
import { useUserStore } from "@/stores/user";
import { formatFollowerCount } from "@video-ct/shared";

const router = useRouter();
const userStore = useUserStore();

const loading = ref(true);
const networkError = ref(false);
const serverError = ref("");
const saving = ref(false);

// 头像上传
const uploaderRef = ref<any>(null);
const avatarFiles = ref<any[]>([]);
const avatarPreview = ref<string>("");
const avatarError = ref("");
const MAX_AVATAR_SIZE = 2 * 1024 * 1024; // 2MB
const ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp"];

const form = reactive({
  nickname: "",
  track: "",
  platform: "",
  follower_count: "",
  bio: "",
  goal: "",
});

const errors = reactive({
  nickname: "",
  follower_count: "",
});

function loadProfile() {
  loading.value = true;
  networkError.value = false;
  serverError.value = "";
  try {
    const me = userStore.me;
    if (me) {
      form.nickname = me.nickname || "";
      form.track = me.track || "";
      form.platform = me.platform || me.platform_main || "";
      form.follower_count = me.follower_count ? String(me.follower_count) : "";
      form.bio = me.bio || "";
      form.goal = me.goal || me.goals || "";
      avatarPreview.value = me.avatar_url || "";
    } else {
      // no user data yet, not a network error
    }
  } catch {
    networkError.value = true;
  } finally {
    loading.value = false;
  }
}

/** 触发隐藏的上传器 */
function triggerUpload() {
  const input = (uploaderRef.value?.$el ||
    document.querySelector(".van-uploader__input")) as HTMLInputElement | null;
  if (input) input.click();
}

/** 上传前校验 */
function beforeRead(file: File | File[]): boolean {
  const f = Array.isArray(file) ? file[0] : file;
  avatarError.value = "";
  if (!ALLOWED_AVATAR_TYPES.includes(f.type)) {
    avatarError.value = "仅支持 jpeg/png/webp 格式";
    Toast.fail("仅支持 jpeg/png/webp 格式");
    return false;
  }
  if (f.size > MAX_AVATAR_SIZE) {
    avatarError.value = "图片大小不能超过 2MB";
    Toast.fail("图片大小不能超过 2MB");
    return false;
  }
  return true;
}

/** 上传后处理 */
async function afterRead(
  fileOrList:
    | { file?: File; content?: string }
    | { file?: File; content?: string }[],
) {
  const item = Array.isArray(fileOrList) ? fileOrList[0] : fileOrList;
  const f = item.file;
  if (!f) return;
  try {
    // 先显示 base64 预览
    const base64 = await fileToBase64(f);
    avatarPreview.value = base64 as string;

    // 尝试调用后端上传接口
    try {
      const uploaded = await userApi.uploadAvatar(f);
      if (uploaded?.url) {
        avatarPreview.value = uploaded.url;
        Toast.success("头像上传成功");
      }
    } catch {
      // 后端不可用时，保存 base64 data URL
      Toast.success("头像已更新（本地）");
    }
    avatarError.value = "";
  } catch (e: any) {
    avatarError.value = "上传失败，请重试";
    Toast.fail(e.message || "上传失败");
  } finally {
    avatarFiles.value = [];
  }
}

/** File → base64 data URL */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error("读取图片失败"));
    reader.readAsDataURL(file);
  });
}

function validate(): boolean {
  let valid = true;

  if (!form.nickname.trim()) {
    errors.nickname = "请输入昵称";
    valid = false;
  }

  if (form.follower_count) {
    const n = Number(form.follower_count);
    if (isNaN(n) || n < 0) {
      errors.follower_count = "请输入有效的粉丝数";
      valid = false;
    } else if (n > 999_999_999) {
      errors.follower_count = "粉丝数不能超过 10 亿";
      valid = false;
    }
  }

  return valid;
}

async function save() {
  if (!validate()) return;

  saving.value = true;
  try {
    const payload: Record<string, any> = {};
    if (form.nickname) payload.nickname = form.nickname.trim();
    if (form.track) payload.track = form.track.trim();
    if (form.platform) payload.platform = form.platform.trim();
    if (form.follower_count)
      payload.follower_count = Number(form.follower_count);
    if (form.bio) payload.bio = form.bio.trim();
    if (form.goal) payload.goal = form.goal.trim();
    // 如果头像有 base64 预览且非远程 URL，一并提交
    if (avatarPreview.value && avatarPreview.value.startsWith("data:")) {
      payload.avatar_url = avatarPreview.value;
    }

    await userApi.updateProfile(payload);
    Toast.success("保存成功");
    await userStore.fetchMe();
    router.back();
  } catch (e: any) {
    if (!navigator.onLine) {
      Toast.fail("网络异常，请检查网络后重试");
    } else if (e.status && e.status >= 500) {
      Toast.fail("服务繁忙，请稍后重试");
    } else {
      Toast.fail(e.message || "保存失败");
    }
  } finally {
    saving.value = false;
  }
}

onMounted(loadProfile);
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
  min-height: 100vh;
}
.loading-center {
  padding-top: 120px;
  display: flex;
  justify-content: center;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px 8px;
  .avatar-wrapper {
    position: relative;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    cursor: pointer;
    overflow: hidden;
    border: 2px solid var(--vct-border);
    .avatar-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .avatar-placeholder {
      width: 100%;
      height: 100%;
      background: linear-gradient(
        135deg,
        var(--vct-primary),
        var(--vct-accent)
      );
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      font-weight: 700;
      color: #fff;
    }
    .avatar-edit-icon {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.5);
      text-align: center;
      font-size: 14px;
      line-height: 24px;
    }
  }
  .avatar-tip {
    font-size: 11px;
    color: var(--vct-text-3);
    margin-top: 8px;
  }
  .avatar-error {
    font-size: 11px;
    color: var(--vct-danger);
    margin-top: 4px;
  }
}

.form-section {
  margin: 0;
  scroll-margin-bottom: 40vh;
  :deep(.van-cell) {
    padding: 14px 16px;
  }
}

.save-section {
  padding: 24px 16px;
}

.error-box {
  margin: 24px 16px;
  text-align: center;
  padding: 24px;
  p {
    color: var(--vct-danger);
    font-size: 13px;
    margin-bottom: 12px;
  }
}
</style>
