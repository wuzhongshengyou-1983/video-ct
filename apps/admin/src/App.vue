<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  DashboardOutlined,
  UserOutlined,
  ShoppingCartOutlined,
  GiftOutlined,
  FileSearchOutlined,
  ShopOutlined,
  TagOutlined,
  TeamOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([route.path])

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
  }
)

const menuItems = [
  { key: '/dashboard', icon: DashboardOutlined, label: '数据看板' },
  { key: '/users', icon: UserOutlined, label: '用户管理' },
  { key: '/orders', icon: ShoppingCartOutlined, label: '订单管理' },
  { key: '/subscriptions', icon: GiftOutlined, label: '订阅管理' },
  { key: '/diagnoses', icon: FileSearchOutlined, label: '诊断管理' },
  { key: '/products', icon: ShopOutlined, label: '产品管理' },
  { key: '/coupons', icon: TagOutlined, label: '优惠券管理' },
  { key: '/referrers', icon: TeamOutlined, label: '分享官管理' },
]

function handleMenuClick(info: { key: string }) {
  router.push(info.key)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <a-layout class="app-layout">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :trigger="null"
      class="app-sider"
      :width="220"
      breakpoint="lg"
    >
      <div class="logo">
        <span v-if="!collapsed" class="logo-text">视频 CT · 管理后台</span>
        <span v-else class="logo-icon">CT</span>
      </div>
      <a-menu
        theme="dark"
        mode="inline"
        :selected-keys="selectedKeys"
        @click="handleMenuClick"
      >
        <a-menu-item v-for="item in menuItems" :key="item.key">
          <component :is="item.icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="app-header">
        <div class="header-left">
          <component
            :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined"
            class="trigger"
            @click="() => (collapsed = !collapsed)"
          />
        </div>
        <div class="header-right">
          <a-dropdown>
            <a-space style="cursor: pointer; color: #e5e7eb">
              <a-avatar size="small" :style="{ backgroundColor: '#f59e0b' }">
                {{ auth.me?.name?.charAt(0) || 'A' }}
              </a-avatar>
              {{ auth.me?.name || 'Admin' }}
            </a-space>
            <template #overlay>
              <a-menu @click="handleLogout">
                <a-menu-item key="logout">
                  <LogoutOutlined />
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style lang="scss" scoped>
.app-layout {
  min-height: 100vh;
  .app-sider {
    background: #0d1117;
    border-right: 1px solid #1e2433;
    .logo {
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid #1e2433;
      .logo-text {
        color: #f59e0b;
        font-size: 16px;
        font-weight: 700;
        white-space: nowrap;
      }
      .logo-icon {
        color: #f59e0b;
        font-size: 20px;
        font-weight: 700;
      }
    }
  }
  .app-header {
    background: #0a0e1a;
    border-bottom: 1px solid #1e2433;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    height: 64px;
    .trigger {
      font-size: 18px;
      cursor: pointer;
      color: #e5e7eb;
      &:hover {
        color: #f59e0b;
      }
    }
  }
  .app-content {
    margin: 16px;
    padding: 24px;
    background: #0d1117;
    border-radius: 8px;
    min-height: calc(100vh - 96px);
  }
}
</style>
