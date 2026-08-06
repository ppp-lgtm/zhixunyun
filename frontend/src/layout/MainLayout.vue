<template>
  <!-- ══════════════════════════════════════
       ZHI · XUN · YUN — Magazine Layout
       对齐 frontend_ui_demo.html
       ══════════════════════════════════════ -->
  <div class="shell min-h-screen">

    <!-- ═══ TOPBAR · Sticky 毛玻璃 ═══ -->
    <div class="topbar-mag">
      <div class="topbar-inner-mag">
        <!-- Brand Mark + Text -->
        <div class="brand-mag">
          <div class="brand-mark-mag">
            <img src="../img/logo.png" alt="智讯Logo" style="position:relative;z-index:1;height:100%;width:auto;">
          </div>
          <div class="brand-text-mag">
            <b>ZHI · XUN · YUN</b>
            <span>Software Training Intelligence Platform</span>
          </div>
        </div>

        <!-- 主导航（桌面） · 已按用户要求移除导航链接（2026-07-31）
             导航入口统一通过左侧快捷目录访问
        -->
        <nav class="nav-mag">
          <router-link v-if="!user" to="/login" class="nav-pill-mag">
            进入平台 →
          </router-link>
        </nav>

        <!-- 右侧：通知 + 用户 -->
        <div class="flex items-center gap-3">
          <!-- 通知铃铛 -->
          <div class="relative" @click.stop="notifyPopoverVisible = !notifyPopoverVisible">
            <button class="w-10 h-10 rounded-full border border-line bg-paper-2 hover:bg-white flex items-center justify-center transition-all text-ink-3 hover:text-ink">
              <Icon icon="mdi:bell-outline" class="text-lg" />
              <span v-if="notifyCount"
                class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-signal text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1 shadow-paper-1 font-mono">
                {{ notifyCount > 99 ? '99+' : notifyCount }}
              </span>
            </button>
            <!-- 通知下拉 -->
            <transition name="fade-in-down">
              <div v-if="notifyPopoverVisible" class="absolute right-0 top-12 w-80 z-50">
                <div class="card-mag !p-0 overflow-hidden">
                  <div class="px-5 py-4 border-b border-line-soft flex items-center justify-between">
                    <span class="font-display text-ink tracking-wider">消息通知</span>
                    <span class="tag ac" v-if="notifyCount">{{ notifyCount }} 未读</span>
                  </div>
                  <div v-if="notifications.length === 0" class="flex flex-col items-center justify-center py-10 text-ink-3">
                    <Icon icon="mdi:bell-off-outline" class="text-3xl mb-3 block" />
                    <p class="font-sub text-sm text-center">暂无新消息</p>
                  </div>
                  <div v-else class="max-h-72 overflow-y-auto">
                    <div
                      v-for="n in notifications" :key="n.type"
                      class="flex items-start gap-3 px-5 py-3.5 hover:bg-paper-2 cursor-pointer transition-colors border-b border-line last:border-0"
                      @click="handleNotification(n)"
                    >
                      <div class="w-9 h-9 rounded-xl bg-seal-soft flex items-center justify-center flex-shrink-0 text-seal-dark">
                        <Icon :icon="n.icon || 'mdi:bell'" class="text-lg" />
                      </div>
                      <div class="min-w-0">
                        <div class="font-sub font-semibold text-ink text-sm">{{ n.title }}</div>
                        <div class="font-body text-xs text-ink-3 mt-0.5 line-clamp-2">{{ n.message }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- 用户信息 -->
          <template v-if="user">
            <div class="relative">
              <div class="flex items-center gap-2.5 cursor-pointer hover:bg-paper-2 rounded-full pl-1 pr-3 py-1 transition-all border border-transparent hover:border-line"
                @click.stop="userDropdownVisible = !userDropdownVisible">
                <div class="relative">
                  <img v-if="avatarUrl" :src="avatarUrl" class="w-9 h-9 rounded-full object-cover ring-2 border-line" />
                  <div v-else class="w-9 h-9 rounded-full bg-gradient-seal flex items-center justify-center text-white text-xs font-bold shadow-paper-2 font-display tracking-wider">
                    {{ (user.real_name || user.username).charAt(0).toUpperCase() }}
                  </div>
                </div>
                <div class="hidden sm:flex flex-col leading-tight">
                  <span class="font-sub font-semibold text-ink text-sm">{{ user.real_name || user.username }}</span>
                  <span class="font-mono text-[11px] text-ink-3">
                    {{
                      user.role === 'teacher' ? 'TEACHER · 教师'
                        : user.role === 'enterprise' ? 'ENTERPRISE · 企业'
                        : 'STUDENT · 学生'
                    }}
                  </span>
                </div>
                <Icon icon="mdi:chevron-down" class="text-ink-3 text-xs hidden sm:block" />
              </div>

              <!-- 用户下拉 -->
              <transition name="fade-in-down">
                <div v-if="userDropdownVisible" class="absolute right-0 top-12 w-56 z-50">
                  <div class="card-mag !p-2 overflow-hidden">
                    <div class="px-3 py-3 mb-1 border-b border-line-soft rounded-xl">
                      <p class="font-sub font-semibold text-ink text-sm">{{ user.real_name || user.username }}</p>
                      <p class="font-mono text-[11px] text-ink-3 mt-0.5 uppercase tracking-wider">
                        {{
                          user.role === 'teacher' ? 'Teacher Account'
                            : user.role === 'enterprise' ? 'Enterprise Account'
                            : 'Student Account'
                        }}
                      </p>
                    </div>
                    <div class="space-y-0.5">
                      <div class="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-paper-2 cursor-pointer transition-colors text-ink-3 hover:text-ink"
                        @click="$router.push('/app/profile'); userDropdownVisible = false">
                        <Icon icon="mdi:account-outline" class="text-lg" />
                        <span class="font-sub text-sm">个人中心</span>
                      </div>
                      <div class="border-t border-line-soft my-0.5"></div>
                      <div class="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-signal-soft cursor-pointer transition-colors text-signal-dark"
                        @click="logout">
                        <Icon icon="mdi:logout" class="text-lg" />
                        <span class="font-sub text-sm font-medium">退出登录</span>
                      </div>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
          </template>
        </div>
      </div>

      <!-- ═══ Chip Anchor 导航条 · 已按用户要求移除（2026-07-31）
           导航入口统一通过左侧快捷目录访问
      -->
    </div>

    <!-- ═══ 主体 · 两栏：左锚点菜单 + 右内容 ═══ -->
    <div class="main-wrap-mag">

      <!-- 左：锚点菜单（卡片式） -->
      <aside class="side-mag">
        <div class="card-mag !p-4">
          <div class="head">
            <div>
              <span class="section-label" style="margin:0;letter-spacing:2px;font-size:11px">Navigator</span>
              <h3 style="font-size:18px;margin-top:2px;font-family:var(--ff-display);letter-spacing:1px">快捷目录</h3>
            </div>
            <span class="tag co" v-if="user">{{ user.role?.toUpperCase() }}</span>
          </div>

          <div class="mt-3 flex flex-col gap-1.5">
            <router-link v-if="user?.role !== 'enterprise'" to="/app" class="side-item-mag" :class="{active: currentPath==='/app'}">
              <Icon icon="mdi:home-variant-outline" class="side-icon-mag" />
              <span>系统首页</span>
            </router-link>

            <!-- 学生 -->
            <template v-if="user?.role==='student'">
              <div class="side-group-mag">学生工具</div>
              <router-link to="/app/student-tasks" class="side-item-mag" :class="{active: currentPath.startsWith('/app/student-tasks')}">
                <Icon icon="mdi:file-document-outline" class="side-icon-mag" />
                <span>提交任务</span>
              </router-link>
              <router-link to="/app/my-classes" class="side-item-mag" :class="{active: currentPath.startsWith('/app/my-classes')}">
                <Icon icon="mdi:book-open-outline" class="side-icon-mag" />
                <span>我的班级</span>
              </router-link>
              <router-link to="/app/my-scores" class="side-item-mag" :class="{active: currentPath.startsWith('/app/my-scores')}">
                <Icon icon="mdi:chart-line-variant" class="side-icon-mag" />
                <span>我的成绩</span>
              </router-link>
              <router-link to="/app/interview-invitations" class="side-item-mag" :class="{active: currentPath.startsWith('/app/interview-invitations')}">
                <Icon icon="mdi:calendar-clock-outline" class="side-icon-mag" />
                <span>面试邀约</span>
              </router-link>
            </template>

            <!-- 教师 -->
            <template v-if="user?.role==='teacher'">
              <div class="side-group-mag">教师工具</div>
              <router-link to="/app/task-manage" class="side-item-mag" :class="{active: currentPath.startsWith('/app/task-manage')}">
                <Icon icon="mdi:clipboard-text-outline" class="side-icon-mag" />
                <span>任务管理</span>
              </router-link>
              <router-link to="/app/class-manage" class="side-item-mag" :class="{active: currentPath.startsWith('/app/class-manage')}">
                <Icon icon="mdi:school-outline" class="side-icon-mag" />
                <span>班级管理</span>
              </router-link>
              <router-link to="/app/criteria" class="side-item-mag" :class="{active: currentPath.startsWith('/app/criteria')}">
                <Icon icon="mdi:tune-variant" class="side-icon-mag" />
                <span>评价标准配置</span>
              </router-link>
            </template>

            <!-- 企业 -->
            <template v-if="user?.role==='enterprise'">
              <div class="side-group-mag">企业中心</div>
              <router-link to="/app/enterprise/dashboard" class="side-item-mag" :class="{active: currentPath==='/app/enterprise/dashboard'}">
                <Icon icon="mdi:view-dashboard-outline" class="side-icon-mag" />
                <span>企业总览</span>
              </router-link>
              <router-link to="/app/enterprise/jobs" class="side-item-mag" :class="{active: currentPath.startsWith('/app/enterprise/jobs')}">
                <Icon icon="mdi:briefcase-outline" class="side-icon-mag" />
                <span>岗位管理</span>
              </router-link>
              <router-link to="/app/enterprise/evaluations" class="side-item-mag" :class="{active: currentPath.startsWith('/app/enterprise/evaluations')}">
                <Icon icon="mdi:star-four-points-outline" class="side-icon-mag" />
                <span>企业评价</span>
              </router-link>
              <router-link to="/app/enterprise/compare" class="side-item-mag" :class="{active: currentPath.startsWith('/app/enterprise/compare')}">
                <Icon icon="mdi:scale-balance" class="side-icon-mag" />
                <span>三方对比</span>
              </router-link>
              <router-link to="/app/enterprise/matching" class="side-item-mag" :class="{active: currentPath.startsWith('/app/enterprise/matching')}">
                <Icon icon="mdi:account-tie-outline" class="side-icon-mag" />
                <span>岗位匹配</span>
              </router-link>
            </template>

            <!-- 通用：企业端无教学统计视图，隐藏"数据分析"分组与入口 -->
            <template v-if="user?.role !== 'enterprise'">
              <div class="side-group-mag">数据分析</div>
              <router-link v-if="user" to="/app/statistics" class="side-item-mag" :class="{active: currentPath.startsWith('/app/statistics')}">
                <Icon icon="mdi:chart-box-outline" class="side-icon-mag" />
                <span>数据统计分析</span>
              </router-link>
            </template>
          </div>

          <!-- 底部状态 -->
          <div class="mt-5 pt-4 border-t border-line-soft">
            <div class="flex items-center gap-3 px-3 py-3 rounded-xl bg-paper-2 border border-line">
              <div class="w-2 h-2 rounded-full bg-jade shadow-[0_0_8px_rgba(29,185,85,0.5)]"></div>
              <span class="font-mono text-[11px] text-ink-3">SYSTEM · ONLINE</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右：内容区 -->
      <main class="content-mag">
        <!-- 页面标题栏 · 已按用户要求移除（2026-07-31）
             避免与各内部页面自身的 h1 标题/描述双重展示，造成 Home / 企业评价 / 企业评价 的重复文字。
        -->

        <router-view v-slot="{ Component, route: r }">
          <transition name="fade-slide">
            <!--
              强制用 fullPath 做 key：
              · 从 /app/my-scores 跳到 /app/result/:id 时，组件一定是销毁-重建，onMounted 必定触发
              · 从 /app/result/1 跳到 /app/result/2 时，也会重建（详情页无需状态缓存），避免复用导致白屏/不渲染
            -->
            <component :is="Component" :key="r.fullPath" class="page-enter" />
          </transition>
        </router-view>
      </main>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import { Icon } from '@iconify/vue'

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
      const res = await api.get(`/api/search/?q=${encodeURIComponent(searchKeyword.value)}`)
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
    return `/uploads/avatars/${user.value.avatar}`
  }
  const saved = localStorage.getItem('user_avatar')
  if (saved) return `/uploads/avatars/${saved}`
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
    if (!target.closest('.relative') && !target.closest('.nav-mag')) {
      notifyPopoverVisible.value = false
      userDropdownVisible.value = false
    }
  })
})

const checkNotifications = async () => {
  if (!user.value) return
  try {
    let url = ''
    const readSince = localStorage.getItem(`notifyReadAt_${user.value.id}`) || '0'
    if (user.value.role === 'student') {
      url = `/api/notifications/student/${user.value.id}?read_since=${readSince}`
    } else if (user.value.role === 'teacher') {
      url = `/api/notifications/teacher/${user.value.id}?read_since=${readSince}`
    } else if (user.value.role === 'enterprise') {
      notifyCount.value = 0
      notifications.value = []
      return
    }
    if (!url) return

    const res = await api.get(url)
    if (res.data.success) {
      notifyCount.value = res.data.data.total_unread
      notifications.value = res.data.data.notifications
    }
  } catch {}
}

const handleNotification = (n: any) => {
  notifyPopoverVisible.value = false
  notifyCount.value = 0
  localStorage.setItem(`notifyReadAt_${user.value.id}`, Date.now().toString())
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
/* ══════════════════════════════════════
   Magazine Layout · MainLayout styles
   对齐 frontend_ui_demo.html
   ══════════════════════════════════════ */

.shell {
  position: relative;
  z-index: 2;
}

/* ── Topbar ── */
.topbar-mag {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: rgba(246, 243, 236, 0.72);
  border-bottom: 1px solid var(--line);
}
.topbar-inner-mag {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  gap: 20px;
}

/* Brand */
.brand-mag {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.brand-mark-mag {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--ink);
  color: var(--paper);
  display: grid;
  place-items: center;
  font-family: var(--ff-display);
  font-size: 15px;
  letter-spacing: 1px;
  box-shadow: var(--shadow-2), inset 0 0 0 1px rgba(255,255,255,0.08);
  position: relative;
  overflow: hidden;
}
.brand-mark-mag::after {
  content: "";
  position: absolute;
  inset: auto -40% -60% auto;
  width: 80%;
  height: 80%;
  background: radial-gradient(closest-side, rgba(255,90,31,0.55), transparent 70%);
  filter: blur(2px);
}
.brand-text-mag {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}
.brand-text-mag b {
  font-family: var(--ff-display);
  font-size: 17px;
  letter-spacing: 2px;
  color: var(--ink);
}
.brand-text-mag span {
  font-family: var(--ff-sub);
  font-size: 10px;
  letter-spacing: 2.5px;
  color: var(--ink-3);
  text-transform: uppercase;
  margin-top: 2px;
}

/* Nav links */
.nav-mag {
  display: flex;
  gap: 22px;
  font-family: var(--ff-sub);
  font-size: 14px;
  color: var(--ink-3);
  align-items: center;
  flex: 1;
  justify-content: center;
  flex-wrap: wrap;
}
.nav-link-mag {
  text-decoration: none;
  position: relative;
  padding: 6px 0;
  color: var(--ink-3);
  transition: color .2s;
  display: inline-flex;
  align-items: center;
}
.nav-link-mag::after {
  content: "";
  position: absolute;
  left: 0;
  right: 100%;
  bottom: 0;
  height: 2px;
  background: var(--seal);
  transition: right .25s ease;
}
.nav-link-mag:hover { color: var(--ink); }
.nav-link-mag:hover::after { right: 0; }
.router-link-active.nav-link-mag {
  color: var(--ink);
}
.router-link-active.nav-link-mag::after { right: 0; }

.nav-pill-mag {
  padding: 8px 16px;
  border-radius: 999px;
  background: var(--ink);
  color: var(--paper);
  font-size: 13px;
  box-shadow: var(--shadow-2);
  transition: transform .2s ease;
  text-decoration: none;
  font-family: var(--ff-sub);
}
.nav-pill-mag:hover {
  transform: translateY(-1px);
}

/* Chip nav row */
.chip-nav-mag {
  display: flex;
  gap: 8px;
  padding: 16px 28px 4px;
  max-width: 1400px;
  margin: 0 auto;
  overflow-x: auto;
  scrollbar-width: none;
}
.chip-nav-mag::-webkit-scrollbar { display: none; }

.chip-mag {
  flex: 0 0 auto;
  padding: 6px 12px;
  border: 1px solid var(--line);
  background: var(--paper-2);
  border-radius: 999px;
  font-family: var(--ff-sub);
  font-size: 12px;
  color: var(--ink-3);
  text-decoration: none;
  transition: all .2s;
}
.chip-mag:hover {
  border-color: var(--seal);
  color: var(--ink);
  background: white;
}
.chip-mag b {
  color: var(--seal);
  margin-right: 6px;
  font-family: var(--ff-mono);
  font-weight: 600;
}
.chip-mag.active {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
  box-shadow: var(--shadow-2);
}
.chip-mag.active b { color: #FF8A5C; }

/* Main wrap */
.main-wrap-mag {
  max-width: 1400px;
  margin: 0 auto;
  padding: 28px;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 28px;
  align-items: start;
}

/* Side card */
.side-mag {
  position: sticky;
  top: 96px;
}

.side-group-mag {
  padding: 12px 8px 6px;
  font-family: var(--ff-sub);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: .8;
}
.side-item-mag {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  font-family: var(--ff-sub);
  font-size: 13px;
  color: var(--ink-3);
  text-decoration: none;
  transition: all .2s;
  border: 1px solid transparent;
}
.side-item-mag:hover {
  background: var(--paper);
  color: var(--ink);
  border-color: var(--line);
}
.side-item-mag.active {
  background: linear-gradient(90deg, var(--seal-soft), transparent);
  color: var(--ink);
  border-color: #F4B797;
  box-shadow: var(--shadow-1);
}
.side-icon-mag {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--paper-2);
  display: grid;
  place-items: center;
  font-size: 14px;
  flex-shrink: 0;
  transition: all .2s;
}
.side-item-mag:hover .side-icon-mag {
  background: white;
}
.side-item-mag.active .side-icon-mag {
  background: var(--ink);
  color: var(--paper);
}

/* Content */
.content-mag {
  min-width: 0;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
}

.section-label {
  font-family: var(--ff-sub);
  font-size: 12px;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--seal);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

/* Card mag (replicated scoped - 纯色化：移除渐变顶条) */
.card-mag {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
  box-shadow: var(--shadow-2);
  position: relative;
  overflow: hidden;
}

/* Transition */
.fade-in-down-enter-active { transition: all 0.25s ease-out; }
.fade-in-down-leave-active { transition: all 0.15s ease-in; }
.fade-in-down-enter-from { opacity: 0; transform: translateY(-8px); }
.fade-in-down-leave-to { opacity: 0; transform: translateY(-8px); }

.fade-slide-enter-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-slide-leave-active { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-slide-enter-from { opacity: 0; transform: translateX(24px) scale(0.98); }
.fade-slide-leave-to { opacity: 0; transform: translateX(-16px) scale(0.98); }

.page-enter { animation: pageEnter 0.5s ease-out; }
@keyframes pageEnter {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: none; }
}

/* Responsive */
@media (max-width: 1100px) {
  .main-wrap-mag { grid-template-columns: 1fr; }
  .side-mag { position: static; }
  .nav-mag { display: none; }
}
@media (max-width: 640px) {
  .topbar-inner-mag { padding: 12px 16px; }
  .chip-nav-mag { padding: 12px 16px 4px; }
  .main-wrap-mag { padding: 16px; gap: 16px; }
  .brand-text-mag span { display: none; }
}
</style>
