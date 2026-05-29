<template>
  <div class="home">
    <!-- 顶部：身份/欢迎 -->
    <header class="hero">
      <div class="logo">视频 <span>CT</span></div>
      <div class="tagline">数据实证驱动 · AI 精准诊断你的短视频</div>
      <div class="hero-stats">
        <div class="stat-pill">
          <div class="num">{{ usedCount }}/{{ quota }}</div>
          <div class="label">本月免费扫描</div>
        </div>
        <div class="stat-pill primary">
          <div class="num">{{ getTierLabel(userStore.tier) }}</div>
          <div class="label">当前档位</div>
        </div>
      </div>
    </header>

    <!-- 主 CTA -->
    <section class="cta">
      <div class="vct-card glow main-cta" @click="goDiagnoseSubmit">
        <div class="cta-icon">⚡</div>
        <div class="cta-text">
          <div class="cta-title">给你的视频做一次 CT 扫描</div>
          <div class="cta-sub">38 维 8 组 · 数据实证 · 秒级出报告</div>
        </div>
        <van-icon name="arrow" />
      </div>
    </section>

    <!-- 三大入口 -->
    <section class="grid-3">
      <div class="grid-item" @click="goPersona">
        <div class="icon">🎭</div>
        <div class="title">人设 IPP</div>
        <div class="sub">12 原型匹配</div>
      </div>
      <div class="grid-item" @click="router.push('/positioning')">
        <div class="icon">💰</div>
        <div class="title">商业 BPS</div>
        <div class="sub">变现路径推荐</div>
      </div>
      <div class="grid-item" @click="router.push('/archive')">
        <div class="icon">📈</div>
        <div class="title">成长档案</div>
        <div class="sub">数据飞轮进度</div>
      </div>
    </section>

    <!-- 绑定账号入口（未绑定时显示） -->
    <section v-if="!accountLoading && myAccounts.length === 0">
      <div class="vct-card bind-account-banner" @click="showBindPopup = true">
        <div class="bind-left">
          <div class="bind-title">📱 绑定你的短视频账号</div>
          <div class="bind-sub">解锁数据仪表盘 · 追踪真实成长曲线</div>
        </div>
        <van-icon name="arrow" class="bind-arrow" />
      </div>
    </section>

    <!-- 已绑定账号快速卡 -->
    <section v-if="!accountLoading && myAccounts.length > 0">
      <div class="vct-section-title">
        📱 我的账号
        <van-button size="mini" plain @click="showBindPopup = true"
          >+ 添加</van-button
        >
      </div>
      <div class="my-accounts">
        <div
          v-for="acc in myAccounts"
          :key="acc.id"
          class="account-chip vct-card"
        >
          <span class="acc-platform">{{
            PLATFORM_LABELS[acc.platform] || acc.platform
          }}</span>
          <span class="acc-name">{{ acc.nickname || "未设置昵称" }}</span>
          <span class="acc-fans">{{
            acc.follower_count > 0
              ? formatFollowerCount(acc.follower_count) + " 粉"
              : ""
          }}</span>
        </div>
      </div>
    </section>

    <!-- 绑定账号弹层 -->
    <van-popup
      v-model:show="showBindPopup"
      position="bottom"
      round
      :style="{ maxHeight: '80vh' }"
    >
      <div class="bind-popup">
        <div class="popup-title">绑定短视频账号</div>
        <van-form @submit="submitBind" ref="bindFormRef">
          <van-cell-group inset>
            <van-field
              label="平台"
              name="platform"
              readonly
              clickable
              :model-value="PLATFORM_LABELS[bindForm.platform] || '选择平台'"
              @click="showPlatformPicker = true"
              :rules="[{ required: true, message: '请选择平台' }]"
            />
            <van-field
              v-model="bindForm.nickname"
              label="账号昵称"
              name="nickname"
              placeholder="抖音昵称 / B站ID..."
              :rules="[{ required: true, message: '请填写昵称' }]"
            />
            <van-field
              v-model.number="bindForm.follower_count"
              label="粉丝数"
              name="follower_count"
              type="digit"
              placeholder="当前粉丝数（选填）"
            />
            <van-field
              label="赛道"
              name="track"
              readonly
              clickable
              :model-value="bindForm.track || '选择赛道（选填）'"
              @click="showTrackPicker = true"
            />
          </van-cell-group>
          <div class="bind-actions">
            <van-button
              block
              type="primary"
              native-type="submit"
              :loading="bindLoading"
            >
              确认绑定
            </van-button>
            <van-button
              block
              plain
              @click="showBindPopup = false"
              style="margin-top: 8px"
            >
              取消
            </van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <!-- 平台选择器 -->
    <van-popup v-model:show="showPlatformPicker" position="bottom" round>
      <van-picker
        :columns="PLATFORM_OPTIONS"
        @confirm="onPlatformConfirm"
        @cancel="showPlatformPicker = false"
        title="选择平台"
      />
    </van-popup>

    <!-- 赛道选择器 -->
    <van-popup v-model:show="showTrackPicker" position="bottom" round>
      <van-picker
        :columns="TRACK_OPTIONS"
        @confirm="onTrackConfirm"
        @cancel="showTrackPicker = false"
        title="选择赛道"
      />
    </van-popup>

    <!-- 头部对标榜 -->
    <section>
      <div class="vct-section-title">
        🔥 赛道头部对标
        <van-button size="mini" plain @click="router.push('/diagnose')"
          >查看全部</van-button
        >
      </div>
      <!-- 骨架屏加载态 -->
      <SkeletonCard
        v-if="benchmarkLoading && benchmarkTop.length === 0"
        :lines="2"
      />
      <div v-else class="benchmark-list">
        <div
          v-for="b in benchmarkTop"
          :key="b.account_id"
          class="benchmark-item vct-card"
        >
          <div class="rank">#{{ b.rank }}</div>
          <div class="info">
            <div class="name">{{ b.nickname }}</div>
            <div class="meta">
              {{ b.platform }} · {{ formatFollowerCount(b.follower_count) }} 粉
            </div>
            <div class="archetype">{{ b.style_archetype }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 分享官入口 -->
    <section>
      <div class="vct-card referrer-banner" @click="goReferrer">
        <div class="banner-left">
          <div class="banner-title">成为品牌分享官</div>
          <div class="banner-sub">
            拉 1 个朋友付费 = {{ REFERRER_REWARD_CNY }} 元 · 拉
            {{ REFERRER_DEDUCT_COUNT }} 个抵 PRO 月卡
          </div>
        </div>
        <div class="banner-right">💎</div>
      </div>
    </section>

    <!-- 8 大 AI 专员介绍 -->
    <section>
      <div class="vct-section-title">🤖 8 大 AI 专员 7×24 守在你账号背后</div>
      <div class="agents">
        <div v-for="a in agents" :key="a.name" class="agent-card vct-card">
          <div class="agent-emoji">{{ a.emoji }}</div>
          <div class="agent-name">{{ a.role }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { benchmarkApi, accountsApi } from "@/api";
import {
  formatFollowerCount,
  getTierLabel,
  REFERRER_REWARD_CNY,
  REFERRER_DEDUCT_COUNT,
} from "@video-ct/shared";
import SkeletonCard from "@/components/SkeletonCard.vue";
import { trackClick } from "@/utils/tracker";
import { useWechatShare, SHARE_TEXT } from "@/composables/useWechatShare";
import { showSuccessToast, showFailToast } from "vant";

const router = useRouter();
const userStore = useUserStore();

const benchmarkTop = ref<any[]>([]);
const benchmarkLoading = ref(true);

// 账号绑定
const myAccounts = ref<any[]>([]);
const accountLoading = ref(true);
const showBindPopup = ref(false);
const showPlatformPicker = ref(false);
const showTrackPicker = ref(false);
const bindLoading = ref(false);
const bindForm = reactive({
  platform: "",
  nickname: "",
  follower_count: 0,
  track: "",
});

const PLATFORM_LABELS: Record<string, string> = {
  douyin: "抖音",
  bilibili: "B站",
  xiaohongshu: "小红书",
};
const PLATFORM_OPTIONS = [
  { text: "抖音", value: "douyin" },
  { text: "B站", value: "bilibili" },
  { text: "小红书", value: "xiaohongshu" },
];
const TRACK_OPTIONS = [
  { text: "职场干货", value: "职场干货" },
  { text: "情感生活", value: "情感生活" },
  { text: "美食探店", value: "美食探店" },
  { text: "知识科普", value: "知识科普" },
  { text: "娱乐搞笑", value: "娱乐搞笑" },
  { text: "母婴育儿", value: "母婴育儿" },
  { text: "健身运动", value: "健身运动" },
  { text: "其他", value: "其他" },
];

function onPlatformConfirm({ selectedOptions }: any) {
  bindForm.platform = selectedOptions[0]?.value ?? "";
  showPlatformPicker.value = false;
}

function onTrackConfirm({ selectedOptions }: any) {
  bindForm.track = selectedOptions[0]?.value ?? "";
  showTrackPicker.value = false;
}

async function submitBind() {
  if (!bindForm.platform) return;
  bindLoading.value = true;
  try {
    const account = await accountsApi.create({
      platform: bindForm.platform,
      nickname: bindForm.nickname || undefined,
      track: bindForm.track || undefined,
      follower_count: bindForm.follower_count || 0,
    });
    myAccounts.value.unshift(account);
    showBindPopup.value = false;
    showSuccessToast("账号绑定成功");
    trackClick("bind_account");
    Object.assign(bindForm, {
      platform: "",
      nickname: "",
      follower_count: 0,
      track: "",
    });
  } catch {
    showFailToast("绑定失败，请重试");
  } finally {
    bindLoading.value = false;
  }
}
const agents = ref([
  { name: "CTRadiologist", role: "CT 诊断官", emoji: "🩺" },
  { name: "BenchmarkAnalyst", role: "对标分析师", emoji: "📊" },
  { name: "PersonaScout", role: "人设观察员", emoji: "🎭" },
  { name: "BizStrategist", role: "商业策略师", emoji: "💎" },
  { name: "ContentMaker", role: "内容生成手", emoji: "✍️" },
  { name: "DataSentinel", role: "数据预警员", emoji: "🚨" },
  { name: "ConsultantCopilot", role: "顾问助理", emoji: "🤝" },
  { name: "CSButler", role: "客户成功管家", emoji: "⭐" },
]);

const usedCount = computed(() => userStore.me?.monthly_free_scans_used ?? 0);
const quota = computed(() => userStore.me?.monthly_free_scans_quota ?? 3);

function goDiagnoseSubmit() {
  trackClick("submit_diagnosis");
  router.push("/diagnose/submit");
}

function goPersona() {
  trackClick("persona");
  router.push("/persona");
}

function goReferrer() {
  trackClick("referrer");
  router.push("/referrer");
}

const { updateShare } = useWechatShare();

onMounted(async () => {
  updateShare(SHARE_TEXT.home.title, SHARE_TEXT.home.desc);
  const [benchmarks, accounts] = await Promise.allSettled([
    benchmarkApi.top10("职场干货"),
    accountsApi.mine(),
  ]);
  if (benchmarks.status === "fulfilled") benchmarkTop.value = benchmarks.value;
  benchmarkLoading.value = false;
  if (accounts.status === "fulfilled") myAccounts.value = accounts.value;
  accountLoading.value = false;
});
</script>

<style lang="scss" scoped>
.home {
  padding: 16px 16px calc(24px + env(safe-area-inset-bottom, 0px));
}
.hero {
  text-align: center;
  padding: 24px 0 16px;
  .logo {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 2px;
    span {
      color: var(--mfc-blue);
      text-shadow: 0 0 20px rgba(0, 122, 255, 0.12);
    }
  }
  .tagline {
    color: var(--mfc-fg-2);
    margin-top: 4px;
    font-size: 13px;
  }
  .hero-stats {
    display: flex;
    gap: 12px;
    margin-top: 20px;
    justify-content: center;
  }
  .stat-pill {
    padding: 8px 16px;
    border-radius: 999px;
    background: var(--mfc-bg-soft);
    border: 1px solid var(--mfc-hairline);
    min-width: 100px;
    .num {
      font-size: 18px;
      font-weight: 700;
      color: var(--mfc-fg);
    }
    .label {
      font-size: 11px;
      color: var(--mfc-fg-3);
      margin-top: 2px;
    }
    &.primary {
      border-color: var(--mfc-blue);
    }
    &.primary .num {
      color: var(--mfc-blue);
    }
  }
}
.main-cta {
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(
    135deg,
    rgba(0, 122, 255, 0.12),
    rgba(88, 86, 214, 0.12)
  );
  border-color: rgba(0, 122, 255, 0.12);
  .cta-icon {
    font-size: 36px;
  }
  .cta-text {
    flex: 1;
  }
  .cta-title {
    font-size: 17px;
    font-weight: 600;
  }
  .cta-sub {
    font-size: 12px;
    color: var(--mfc-fg-2);
    margin-top: 4px;
  }
}
.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
  .grid-item {
    background: var(--mfc-bg-soft);
    border-radius: var(--mfc-r-2xl);
    padding: 16px 8px;
    text-align: center;
    border: 1px solid var(--mfc-hairline);
    .icon {
      font-size: 28px;
    }
    .title {
      font-size: 13px;
      font-weight: 600;
      margin-top: 6px;
    }
    .sub {
      font-size: 10px;
      color: var(--mfc-fg-3);
    }
  }
}
.benchmark-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  &::-webkit-scrollbar {
    display: none;
  }
}
.benchmark-item {
  min-width: 200px;
  display: flex;
  gap: 10px;
  align-items: center;
  .rank {
    font-size: 24px;
    font-weight: 800;
    color: var(--mfc-blue);
    background: linear-gradient(135deg, #007aff, #fb923c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .info {
    flex: 1;
  }
  .name {
    font-size: 14px;
    font-weight: 600;
  }
  .meta {
    font-size: 11px;
    color: var(--mfc-fg-3);
  }
  .archetype {
    font-size: 11px;
    color: var(--mfc-indigo);
    margin-top: 2px;
  }
}
.referrer-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  background: linear-gradient(
    135deg,
    rgba(88, 86, 214, 0.12),
    rgba(0, 122, 255, 0.12)
  );
  border-color: rgba(88, 86, 214, 0.12);
  .banner-left {
    flex: 1;
  }
  .banner-title {
    font-weight: 600;
  }
  .banner-sub {
    font-size: 11px;
    color: var(--mfc-fg-2);
    margin-top: 4px;
  }
  .banner-right {
    font-size: 36px;
  }
}
.agents {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  .agent-card {
    text-align: center;
    padding: 12px 4px;
  }
  .agent-emoji {
    font-size: 24px;
  }
  .agent-name {
    font-size: 11px;
    color: var(--mfc-fg-2);
    margin-top: 4px;
  }
}
.bind-account-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  background: linear-gradient(
    135deg,
    rgba(0, 122, 255, 0.06),
    rgba(88, 86, 214, 0.06)
  );
  border: 1px dashed rgba(0, 122, 255, 0.3);
  .bind-left {
    flex: 1;
    .bind-title {
      font-weight: 600;
      font-size: 15px;
    }
    .bind-sub {
      font-size: 12px;
      color: var(--mfc-fg-2);
      margin-top: 4px;
    }
  }
  .bind-arrow {
    color: var(--mfc-fg-3);
  }
}
.my-accounts {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  .account-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    .acc-platform {
      font-size: 12px;
      font-weight: 600;
      color: var(--mfc-blue);
      background: rgba(0, 122, 255, 0.1);
      padding: 2px 8px;
      border-radius: 999px;
    }
    .acc-name {
      font-size: 14px;
      font-weight: 500;
    }
    .acc-fans {
      font-size: 11px;
      color: var(--mfc-fg-3);
    }
  }
}
.bind-popup {
  padding: 24px 16px calc(32px + env(safe-area-inset-bottom, 0px));
  .popup-title {
    font-size: 18px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 20px;
    color: var(--mfc-fg);
  }
  .bind-actions {
    padding: 20px 16px 0;
  }
}
</style>
