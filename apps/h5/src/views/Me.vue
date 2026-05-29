<template>
  <div class="page">
    <van-nav-bar title="我的" :border="false" />

    <!-- 用户头部 -->
    <section class="user-header">
      <div class="avatar-placeholder">{{ avatarText }}</div>
      <div class="user-name">{{ userStore.me?.nickname || "视频创作者" }}</div>
      <div class="user-phone">
        {{ maskPhone(userStore.me?.phone) || "未绑定" }}
      </div>
      <div class="user-tier">
        <span class="tier-badge">{{ getTierLabel(userStore.tier) }}</span>
      </div>
    </section>

    <!-- 配额 -->
    <section class="vct-card quota-card">
      <div class="quota-row">
        <div class="quota-info">
          <div class="quota-label">本月扫描配额</div>
          <div class="quota-detail">
            {{ userStore.me?.monthly_free_scans_used || 0 }} /
            {{ userStore.me?.monthly_free_scans_quota || 3 }}
          </div>
        </div>
        <van-progress
          :percentage="quotaPercent"
          :color="quotaBarColor"
          stroke-width="8"
          :show-pivot="false"
          style="flex: 1"
        />
      </div>
      <div class="quota-tip" v-if="quotaPercent >= 100">
        本月免费额度已用完，
        <span class="link" @click="router.push('/subscribe')"
          >升级 PRO 不限量</span
        >
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="menu-section">
      <van-cell-group :border="false" inset>
        <van-cell
          title="成长档案"
          icon="chart-trending-o"
          is-link
          @click="router.push('/archive')"
        >
          <template #icon><span class="menu-icon">📈</span></template>
        </van-cell>
        <van-cell
          title="人设 IPP"
          icon="friends-o"
          is-link
          @click="router.push('/persona')"
        >
          <template #icon><span class="menu-icon">🎭</span></template>
        </van-cell>
        <van-cell
          title="商业定位 BPS"
          icon="gold-coin-o"
          is-link
          @click="router.push('/positioning')"
        >
          <template #icon><span class="menu-icon">💰</span></template>
        </van-cell>
        <van-cell
          title="品牌分享官"
          icon="share-o"
          is-link
          @click="router.push('/referrer')"
        >
          <template #icon><span class="menu-icon">💎</span></template>
        </van-cell>
        <van-cell
          title="分享榜单"
          icon="medal-o"
          is-link
          @click="router.push('/leaderboard')"
        >
          <template #icon><span class="menu-icon">🏆</span></template>
        </van-cell>
        <van-cell
          title="个人资料"
          icon="user-o"
          is-link
          @click="router.push('/me/profile')"
        >
          <template #icon><span class="menu-icon">👤</span></template>
        </van-cell>
        <van-cell
          title="订阅管理"
          icon="vip-card-o"
          is-link
          @click="router.push('/subscribe')"
        >
          <template #icon><span class="menu-icon">⭐</span></template>
        </van-cell>
        <van-cell
          v-if="isAdmin"
          title="数据仪表盘"
          is-link
          @click="router.push('/admin')"
        >
          <template #icon><span class="menu-icon">📊</span></template>
        </van-cell>
      </van-cell-group>
    </section>

    <!-- 退出登录 -->
    <div class="logout-section">
      <van-button block plain type="danger" @click="doLogout"
        >退出登录</van-button
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Dialog } from "vant";
import { useUserStore } from "@/stores/user";
import { getTierLabel } from "@video-ct/shared";

const router = useRouter();
const userStore = useUserStore();

const avatarText = computed(() => {
  return (userStore.me?.nickname || "创").charAt(0).toUpperCase();
});

const isAdmin = computed(() =>
  ["admin", "consultant"].includes(userStore.me?.role ?? ""),
);

const quotaPercent = computed(() => {
  const used = userStore.me?.monthly_free_scans_used || 0;
  const quota = userStore.me?.monthly_free_scans_quota || 3;
  if (quota === 0) return 100;
  return Math.min(100, (used / quota) * 100);
});

// ≥ 50% 剩余 → 绿色, < 50% → 橙色, 0 剩余 → 红色
const quotaBarColor = computed(() => {
  const pct = quotaPercent.value;
  if (pct >= 100) return "linear-gradient(90deg, var(--mfc-red), #f87171)";
  if (pct >= 50) return "linear-gradient(90deg, #007aff, #0070f3)";
  return "linear-gradient(90deg, var(--mfc-green), #34d399)";
});

function maskPhone(phone: string | undefined): string {
  if (!phone) return "";
  return phone.replace(/(\d{3})\d{4}(\d{4})/, "$1****$2");
}

function doLogout() {
  Dialog.confirm({
    title: "退出登录",
    message: "确定要退出登录吗？",
  })
    .then(() => {
      userStore.logout();
      router.replace("/login");
    })
    .catch(() => {});
}
</script>

<style lang="scss" scoped>
.page {
  padding: 0 16px calc(24px + env(safe-area-inset-bottom, 0px));
  min-height: 100vh;
}

.user-header {
  text-align: center;
  padding: 24px 0 16px;
  .avatar-placeholder {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    margin: 0 auto 12px;
    background: linear-gradient(135deg, var(--mfc-blue), #0070f3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 700;
    color: var(--mfc-fg);
  }
  .user-name {
    font-size: 18px;
    font-weight: 600;
  }
  .user-phone {
    font-size: 12px;
    color: var(--mfc-fg-3);
    margin-top: 4px;
  }
  .user-tier {
    margin-top: 8px;
  }
  .tier-badge {
    display: inline-block;
    padding: 2px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    background: rgba(0, 122, 255, 0.12);
    color: var(--mfc-blue);
    border: 1px solid rgba(0, 122, 255, 0.12);
  }
}

.quota-card {
  margin: 8px 0 16px;
  padding: 16px;
  .quota-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .quota-info {
    min-width: 80px;
  }
  .quota-label {
    font-size: 12px;
    color: var(--mfc-fg-3);
  }
  .quota-detail {
    font-size: 18px;
    font-weight: 700;
    color: var(--mfc-blue);
  }
  .quota-tip {
    margin-top: 12px;
    font-size: 12px;
    color: var(--mfc-fg-2);
    .link {
      color: var(--mfc-blue);
      text-decoration: underline;
      cursor: pointer;
    }
  }
}

.menu-section {
  margin-bottom: 24px;
  .menu-icon {
    font-size: 18px;
    margin-right: 4px;
  }
}

.logout-section {
  padding: 16px 0;
}
</style>
