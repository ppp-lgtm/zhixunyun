<template>
  <div class="flex h-screen bg-surface-50">
    <!-- ═══════════ 侧边栏 · Refined Sapphire ═══════════ -->
    <aside class="w-64 bg-surface-900 flex flex-col relative z-20">
      <!-- Subtle top glow line -->
      <div class="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-primary-400/30 to-transparent"></div>

      <!-- Logo 区域 -->
      <div class="h-20 flex items-center px-5 border-b border-white/5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg shadow-primary-500/20 ring-2 ring-primary-500/20">
            <img
              src="@/img/logo.png"
              alt="知训云"
              class="w-7 h-7 object-cover rounded-lg"
            >
          </div>
          <div class="flex flex-col">
            <span class="text-sm font-bold text-white tracking-tight leading-tight">知训云</span>
            <span class="text-[10px] text-surface-400 font-medium tracking-wider uppercase">智能实训评价</span>
          </div>
        </div>
      </div>

      <!-- 侧边菜单 -->
      <nav class="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
        <!-- 首页 -->
        <router-link
          to="/app"
          class="nav-item group"
          :class="currentPath === '/app' ? 'nav-item-active' : ''"
        >
          <div class="nav-icon" :class="currentPath === '/app' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
            <Icon icon="mdi:home-variant-outline" class="text-lg" />
          </div>
          <span class="nav-label">系统首页</span>
          <div v-if="currentPath === '/app'" class="nav-dot"></div>
        </router-link>

        <!-- 教师专用菜单 -->
        <template v-if="user && user.role === 'teacher'">
          <div class="px-3 py-2 mt-5 mb-1">
            <span class="text-[10px] font-bold text-surface-500 uppercase tracking-[0.15em]">教师工具</span>
          </div>

          <router-link
            to="/app/task-manage"
            class="nav-item group"
            :class="currentPath === '/app/task-manage' ? 'nav-item-active' : ''"
          >
            <div class="nav-icon" :class="currentPath === '/app/task-manage' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
              <Icon icon="mdi:clipboard-text-outline" class="text-lg" />
            </div>
            <span class="nav-label">任务管理</span>
            <div v-if="currentPath === '/app/task-manage'" class="nav-dot"></div>
          </router-link>

          <router-link
            to="/app/class-manage"
            class="nav-item group"
            :class="currentPath === '/app/class-manage' ? 'nav-item-active' : ''"
          >
            <div class="nav-icon" :class="currentPath === '/app/class-manage' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
              <Icon icon="mdi:school-outline" class="text-lg" />
            </div>
            <span class="nav-label">班级管理</span>
            <div v-if="currentPath === '/app/class-manage'" class="nav-dot"></div>
          </router-link>

          <router-link
            to="/app/criteria"
            class="nav-item group"
            :class="currentPath === '/app/criteria' ? 'nav-item-active' : ''"
          >
            <div class="nav-icon" :class="currentPath === '/app/criteria' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
              <Icon icon="mdi:tune-variant" class="text-lg" />
            </div>
            <span class="nav-label">评价标准配置</span>
            <div v-if="currentPath === '/app/criteria'" class="nav-dot"></div>
          </router-link>
        </template>

        <!-- 学生专用菜单 -->
        <template v-if="user && user.role === 'student'">
          <div class="px-3 py-2 mt-5 mb-1">
            <span class="text-[10px] font-bold text-surface-500 uppercase tracking-[0.15em]">学习工具</span>
          </div>

          <router-link
            to="/app/student-tasks"
            class="nav-item group"
            :class="currentPath === '/app/student-tasks' ? 'nav-item-active' : ''"
          >
            <div class="nav-icon" :class="currentPath === '/app/student-tasks' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
              <Icon icon="mdi:file-document-outline" class="text-lg" />
            </div>
            <span class="nav-label">提交任务</span>
            <div v-if="currentPath === '/app/student-tasks'" class="nav-dot"></div>
          </router-link>

          <router-link
            to="/app/my-classes"
            class="nav-item group"
            :class="currentPath === '/app/my-classes' ? 'nav-item-active' : ''"
          >
            <div class="nav-icon" :class="currentPath === '/app/my-classes' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
              <Icon icon="mdi:book-open-outline" class="text-lg" />
            </div>
            <span class="nav-label">我的班级</span>
            <div v-if="currentPath === '/app/my-classes'" class="nav-dot"></div>
          </router-link>

          <router-link
            to="/app/my-scores"
            class="nav-item group"
            :class="currentPath === '/app/my-scores' ? 'nav-item-active' : ''"
          >
            <div class="nav-icon" :class="currentPath === '/app/my-scores' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
              <Icon icon="mdi:chart-line-variant" class="text-lg" />
            </div>
            <span class="nav-label">我的成绩</span>
            <div v-if="currentPath === '/app/my-scores'" class="nav-dot"></div>
          </router-link>
        </template>

        <!-- 通用菜单 -->
        <div class="px-3 py-2 mt-5 mb-1">
          <span class="text-[10px] font-bold text-surface-500 uppercase tracking-[0.15em]">数据分析</span>
        </div>

        <router-link
          v-if="user"
          to="/app/statistics"
          class="nav-item group"
          :class="currentPath === '/app/statistics' ? 'nav-item-active' : ''"
        >
          <div class="nav-icon" :class="currentPath === '/app/statistics' ? 'text-white' : 'text-surface-400 group-hover:text-white'">
            <Icon icon="mdi:chart-box-outline" class="text-lg" />
          </div>
          <span class="nav-label">数据统计分析</span>
          <div v-if="currentPath === '/app/statistics'" class="nav-dot"></div>
        </router-link>
      </nav>

      <!-- 底部装饰 -->
      <div class="px-5 py-4 border-t border-white/5">
        <div class="flex items-center gap-3 px-3 py-3 rounded-2xl bg-white/[0.03]">
          <div class="w-2 h-2 rounded-full bg-success-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
          <span class="text-xs text-surface-400 font-medium">系统运行中</span>
        </div>
      </div>
    </aside>

    <!-- ═══════════ 右侧主体 ═══════════ -->
    <main class="flex-1 flex flex-col overflow-hidden min-w-0">
      <!-- 顶部导航栏 -->
      <header class="h-18 bg-white/80 backdrop-blur-xl border-b border-surface-100 flex items-center justify-between px-8 shadow-sm relative z-10">
        <!-- 面包屑 + 搜索 -->
        <div class="flex items-center gap-3 min-w-0">
          <div class="flex items-center gap-2 text-sm">
            <span class="text-surface-400 font-medium">首页</span>
            <Icon v-if="pageTitle" icon="mdi:chevron-right" class="text-surface-300 text-xs" />
            <span v-if="pageTitle" class="text-surface-800 font-semibold truncate">{{ pageTitle }}</span>
          </div>

          <!-- 搜索框 -->
          <div class="relative ml-4 hidden lg:block">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索任务、班级..."
              size="default"
              class="search-input w-52"
              clearable
              @input="doSearch"
              @clear="searchResults = []"
              @focus="doSearch"
            >
              <template #prefix>
                <Icon icon="mdi:magnify" class="text-surface-400" />
              </template>
            </el-input>
            <!-- 搜索结果下拉 -->
            <transition name="fade-in-down">
              <div v-if="searchResults.length > 0 && searchKeyword.trim()"
                class="absolute top-11 left-0 w-80 bg-white rounded-2xl shadow-xl border border-surface-100 z-50 max-h-72 overflow-y-auto py-2">
                <div v-for="item in searchResults" :key="item.id + item.type"
                  class="flex items-center gap-3 px-4 py-3 hover:bg-surface-50 cursor-pointer transition-colors mx-2 rounded-xl"
                  @click="goToResult(item)">
                  <div class="w-9 h-9 rounded-xl flex items-center justify-center"
                    :class="item.type === '任务' ? 'bg-primary-50 text-primary-500' : 'bg-success-50 text-success-500'">
                    <Icon :icon="item.type === '任务' ? 'mdi:file-document' : 'mdi:school'" class="text-lg" />
                  </div>
                  <div class="min-w-0">
                    <div class="font-medium text-surface-800 text-sm truncate">{{ item.title }}</div>
                    <div class="text-xs text-surface-400">{{ item.type }}</div>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- 右侧操作区 -->
        <div class="flex items-center gap-4">
          <!-- 通知铃铛 -->
          <div class="relative" @click.stop="notifyPopoverVisible = !notifyPopoverVisible">
            <button class="relative w-10 h-10 rounded-xl hover:bg-surface-50 flex items-center justify-center transition-colors">
              <Icon icon="mdi:bell-outline" class="text-xl text-surface-500" />
              <span v-if="notifyCount"
                class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-danger-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1 shadow-md animate-scale-in">
                {{ notifyCount > 99 ? '99+' : notifyCount }}
              </span>
            </button>

            <!-- 通知下拉 -->
            <transition name="fade-in-down">
              <div v-if="notifyPopoverVisible" class="absolute right-0 top-12 w-80 bg-white rounded-2xl shadow-xl border border-surface-100 z-50 overflow-hidden">
                <div class="p-4 border-b border-surface-100">
                  <span class="font-bold text-surface-800">消息通知</span>
                </div>
                <div v-if="notifications.length === 0" class="text-center py-10 text-surface-400">
                  <Icon icon="mdi:bell-off-outline" class="text-3xl mb-2" />
                  <p class="text-sm">暂无新消息</p>
                </div>
                <div v-else class="max-h-72 overflow-y-auto">
                  <div
                    v-for="n in notifications"
                    :key="n.type"
                    class="flex items-start gap-3 px-4 py-3.5 hover:bg-surface-50 cursor-pointer transition-colors border-b border-surface-50 last:border-0"
                    @click="handleNotification(n)"
                  >
                    <div class="w-9 h-9 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0">
                      <Icon :icon="n.icon || 'mdi:bell'" class="text-primary-500" />
                    </div>
                    <div class="min-w-0">
                      <div class="font-medium text-surface-800 text-sm">{{ n.title }}</div>
                      <div class="text-xs text-surface-500 mt-0.5 line-clamp-2">{{ n.message }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- 用户信息 -->
          <template v-if="user">
            <div class="relative">
              <div class="flex items-center gap-2.5 cursor-pointer hover:bg-surface-50 rounded-xl pl-2 pr-3 py-1.5 transition-all"
                @click.stop="userDropdownVisible = !userDropdownVisible">
                <div class="relative">
                  <img v-if="avatarUrl" :src="avatarUrl" class="w-8 h-8 rounded-full object-cover ring-2 ring-primary-100" />
                  <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white text-xs font-bold shadow-md">
                    {{ (user.real_name || user.username).charAt(0).toUpperCase() }}
                  </div>
                </div>
                <div class="hidden sm:flex flex-col leading-tight">
                  <span class="text-surface-800 font-medium text-sm">{{ user.real_name || user.username }}</span>
                  <span class="text-[11px] text-surface-400">{{ user.role === 'teacher' ? '教师' : '学生' }}</span>
                </div>
                <Icon icon="mdi:chevron-down" class="text-surface-400 text-xs hidden sm:block" />
              </div>

              <!-- 用户下拉菜单 -->
              <transition name="fade-in-down">
                <div v-if="userDropdownVisible" class="absolute right-0 top-12 w-52 bg-white rounded-2xl shadow-xl border border-surface-100 z-50 overflow-hidden py-2">
                  <div class="px-3 py-2 border-b border-surface-50">
                    <p class="text-sm font-semibold text-surface-800">{{ user.real_name || user.username }}</p>
                    <p class="text-xs text-surface-400">{{ user.role === 'teacher' ? '教师账号' : '学生账号' }}</p>
                  </div>
                  <div class="p-1.5">
                    <div class="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-50 cursor-pointer transition-colors"
                      @click="$router.push('/app/profile'); userDropdownVisible = false">
                      <Icon icon="mdi:account-outline" class="text-surface-500 text-lg" />
                      <span class="text-surface-700 text-sm">个人中心</span>
                    </div>
                    <div class="border-t border-surface-50 my-1"></div>
                    <div class="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-danger-50 cursor-pointer transition-colors text-danger-500"
                      @click="logout">
                      <Icon icon="mdi:logout" class="text-lg" />
                      <span class="text-sm font-medium">退出登录</span>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </template>
          <template v-else>
            <button class="btn-primary text-white px-5 py-2 rounded-xl text-sm font-semibold" @click="$router.push('/login')">
              立即登录
            </button>
          </template>
        </div>
      </header>

      <!-- 内容区 -->
      <div class="flex-1 overflow-y-auto bg-surface-50">
        <div class="p-8">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const route = useRoute()

const user = ref<any>(null)
const notifyCount = ref(0)
const notifications = ref<any[]>([])
const notifyPopoverVisible = ref(false)
const userDropdownVisible = ref(false)

const currentPath = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || '')

const searchKeyword = ref('')
const searchResults = ref<any[]>([])
let searchTimer: any = null

const doSearch = () => {
  clearTimeout(searchTimer)
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/search/?q=${encodeURIComponent(searchKeyword.value)}`)
      if (res.data.success) searchResults.value = res.data.data
    } catch { searchResults.value = [] }
  }, 300)
}

const goToResult = (item: any) => {
  searchKeyword.value = ''
  searchResults.value = []
  router.push(item.path)
}

const avatarUrl = computed(() => {
  if (user.value?.avatar) {
    return `${API_BASE}/uploads/avatars/${user.value.avatar}`
  }
  const saved = localStorage.getItem('user_avatar')
  if (saved) return `${API_BASE}/uploads/avatars/${saved}`
  return ''
})

onMounted(() => {
  const data = localStorage.getItem('user')
  if (data) {
    user.value = JSON.parse(data)
    checkNotifications()
  }

  document.addEventListener('click', (e) => {
    const target = e.target as HTMLElement
    if (!target.closest('.relative')) {
      notifyPopoverVisible.value = false
      userDropdownVisible.value = false
    }
  })
})

const checkNotifications = async () => {
  if (!user.value) return
  try {
    let url = ''
    if (user.value.role === 'student') {
      url = `${API_BASE}/api/notifications/student/${user.value.id}`
    } else if (user.value.role === 'teacher') {
      url = `${API_BASE}/api/notifications/teacher/${user.value.id}`
    }
    if (!url) return

    const res = await axios.get(url)
    if (res.data.success) {
      notifyCount.value = res.data.data.total_unread
      notifications.value = res.data.data.notifications
    }
  } catch {}
}

const handleNotification = (n: any) => {
  notifyPopoverVisible.value = false
  notifyCount.value = 0
  if (n.type === 'new_task' && n.task_id) {
    router.push('/app/student-tasks')
  } else if (n.type === 'submission' || n.type === 'unrated') {
    router.push('/app/task-manage')
  } else if (n.type === 'evaluation') {
    router.push('/app/my-scores')
  }
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('criteria_config')
  localStorage.removeItem('eval_result')
  localStorage.removeItem('user_avatar')
  user.value = null
  userDropdownVisible.value = false
  router.push('/login')
}
</script>

<style scoped>
/* ═══════ 侧边栏导航项 ═══════ */
.nav-item {
  @apply flex items-center gap-3 px-3 py-3 rounded-2xl transition-all duration-300 relative;
  color: #94A3B8;
}
.nav-item:hover {
  color: #FFFFFF;
  background: rgba(255, 255, 255, 0.05);
}
.nav-item-active {
  color: #FFFFFF !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.3), rgba(99, 102, 241, 0.15)) !important;
  box-shadow: 0 4px 12px -4px rgba(79, 70, 229, 0.3);
}

.nav-icon {
  @apply w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300;
}
.nav-item-active .nav-icon {
  @apply bg-white/10;
}

.nav-label {
  @apply text-sm font-medium transition-all duration-300;
}

.nav-dot {
  @apply w-1.5 h-1.5 rounded-full bg-primary-400 absolute right-3;
  box-shadow: 0 0 8px rgba(129, 140, 248, 0.6);
}

/* ═══════ 搜索框 ═══════ */
.search-input :deep(.el-input__wrapper) {
  background: #F8FAFC !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 0.75rem !important;
  box-shadow: none !important;
  transition: all 0.2s !important;
}
.search-input :deep(.el-input__wrapper):hover {
  border-color: #A5B4FC !important;
  background: #FFF !important;
}
.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #4F46E5 !important;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.08) !important;
  background: #FFF !important;
  width: 280px !important;
}
.search-input :deep(.el-input__inner) {
  font-size: 0.875rem;
}

/* ═══════ 过渡动画 ═══════ */
.fade-in-down-enter-active {
  transition: all 0.25s ease-out;
}
.fade-in-down-leave-active {
  transition: all 0.15s ease-in;
}
.fade-in-down-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.fade-in-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ═══════ 页面切换 ═══════ */
.fade-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(24px) scale(0.98);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px) scale(0.98);
}

/* ═══════ 滚动条（侧边栏深色） ═══════ */
nav::-webkit-scrollbar {
  width: 3px;
}
nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

/* ═══════ 搜索框展开 ═══════ */
.search-input {
  transition: width 0.3s ease;
}
</style>
