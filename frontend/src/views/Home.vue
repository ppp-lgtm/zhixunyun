<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 欢迎区域 -->
      <div class="mb-10" v-if="user">
        <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold text-surface-800 tracking-tight">
              欢迎回来，{{ user.real_name || user.username }}
            </h1>
            <p class="text-surface-500 mt-1.5 text-base">
              {{ user.role === 'teacher' ? '今天又有新的实训成果等待评价' : '继续努力，不断提升编程技能' }}
            </p>
          </div>
          <div v-if="user?.role === 'student' && pendingCount > 0"
            class="flex items-center gap-3 bg-accent-50 border border-accent-200 rounded-2xl px-5 py-3 animate-scale-in">
            <Icon icon="mdi:alarm" class="text-2xl text-accent-500" />
            <span class="text-accent-700 font-semibold text-sm">还有 {{ pendingCount }} 份待提交任务</span>
            <button class="btn-accent text-white px-4 py-1.5 rounded-lg text-sm font-bold" @click="$router.push('/app/student-tasks')">
              立即查看
            </button>
          </div>
        </div>
      </div>

      <!-- ==================== 教师端 ==================== -->
      <template v-if="user && user.role === 'teacher'">
        <!-- 数据总览卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 stagger-fade" v-if="teacherStats">
          <!-- 待评分 -->
          <div class="stat-card bg-gradient-card-amber">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:clipboard-alert-outline" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">待评分</span>
              </div>
              <div class="text-4xl font-black tracking-tight">{{ teacherStats.unscored_count }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">份待处理</div>
            </div>
          </div>
          <!-- 我的班级 -->
          <div class="stat-card bg-gradient-card-blue">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:school-outline" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">班级</span>
              </div>
              <div class="text-4xl font-black tracking-tight">{{ teacherStats.class_count }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">个班级</div>
            </div>
          </div>
          <!-- 学生总数 -->
          <div class="stat-card bg-gradient-card-emerald">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:account-group-outline" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">学生</span>
              </div>
              <div class="text-4xl font-black tracking-tight">{{ teacherStats.student_count }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">人</div>
            </div>
          </div>
          <!-- 本月提交 -->
          <div class="stat-card bg-gradient-card-violet">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:trending-up" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">本月</span>
              </div>
              <div class="text-4xl font-black tracking-tight">{{ teacherStats.month_submissions }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">份提交</div>
            </div>
          </div>
        </div>

        <!-- 快捷操作卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          <div v-for="(item, idx) in teacherActions" :key="item.title"
            class="card-hover p-6 group"
            :style="`animation-delay: ${idx * 0.08}s`"
            @click="$router.push(item.path)">
            <div class="w-12 h-12 rounded-2xl bg-primary-50 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary-100 transition-all duration-300">
              <Icon :icon="item.icon" class="text-2xl" />
            </div>
            <div class="font-bold text-surface-800 mb-1.5 text-base">{{ item.title }}</div>
            <div class="text-sm text-surface-500 leading-relaxed">{{ item.desc }}</div>
          </div>
        </div>

        <!-- 最近动态 -->
        <div class="card mb-10" v-if="recentActivities.length > 0">
          <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
              <span class="text-lg font-bold text-surface-800">最近动态</span>
            </div>
          </div>
          <div class="p-6 space-y-1">
            <div v-for="act in recentActivities" :key="act.id"
              class="flex items-center gap-4 p-3.5 rounded-2xl hover:bg-surface-50 transition-colors group">
              <div class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0 group-hover:bg-primary-100 transition-colors">
                <Icon :icon="act.type === 'submission' ? 'mdi:file-document-outline' : 'mdi:clipboard-text-outline'" class="text-primary-500 text-lg" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-surface-700">
                  <template v-if="act.type === 'submission'">
                    <span class="font-semibold">{{ act.student_name }}</span>
                    在 <span class="font-semibold">{{ act.class_name }}</span>
                    提交了 <span class="font-medium">{{ act.task_title }}</span>
                    <span v-if="act.filename" class="text-surface-400">（{{ act.filename }}）</span>
                  </template>
                  <template v-else>
                    <span class="font-semibold">{{ act.teacher_name }}</span>
                    发布了新任务 <span class="font-medium">{{ act.task_title }}</span>
                  </template>
                </p>
                <p class="text-xs text-surface-400 mt-1">{{ act.time }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 我的班级 -->
        <div class="card mb-10">
          <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
              <span class="text-lg font-bold text-surface-800">我的班级</span>
            </div>
            <button class="btn-primary text-white px-5 py-2 rounded-xl text-sm font-semibold" @click="$router.push('/app/class-manage')">
              管理班级
            </button>
          </div>
          <div class="p-6">
            <div v-if="myClasses.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <div v-for="c in myClasses" :key="c.id"
                class="p-6 rounded-2xl border border-surface-100 hover:border-primary-200 hover:bg-primary-50/30 cursor-pointer transition-all duration-300 group"
                @click="$router.push(`/app/class-scores?id=${c.id}`)">
                <div class="flex items-start justify-between mb-3">
                  <h4 class="text-lg font-bold text-surface-800 group-hover:text-primary-600 transition-colors">{{ c.name }}</h4>
                  <Icon icon="mdi:chevron-right" class="text-surface-300 group-hover:text-primary-400 transition-colors" />
                </div>
                <p class="text-surface-500 text-sm mb-4">{{ c.course_name }}</p>
                <div class="flex items-center gap-4 text-sm text-surface-500">
                  <span class="flex items-center gap-1.5">
                    <Icon icon="mdi:account-group" class="text-base" />
                    {{ c.student_count }}人
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="py-12">
              <div class="bg-gradient-to-r from-primary-50 to-indigo-50 rounded-3xl p-10 text-center border border-primary-100">
                <div class="text-5xl mb-5"><Icon icon="mdi:rocket-launch-outline" class="text-primary-500" /></div>
                <h3 class="text-2xl font-bold text-surface-800 mb-3">欢迎使用知训云！</h3>
                <p class="text-surface-500 mb-8 text-base">只需三步即可开始</p>
                <div class="flex justify-center gap-6 mb-8 flex-wrap">
                  <div class="bg-white rounded-2xl p-5 w-40 shadow-sm border border-surface-100">
                    <div class="text-3xl mb-2">①</div>
                    <div class="font-bold text-surface-800">创建班级</div>
                    <div class="text-sm text-surface-400">生成邀请码</div>
                  </div>
                  <div class="bg-white rounded-2xl p-5 w-40 shadow-sm border border-surface-100">
                    <div class="text-3xl mb-2">②</div>
                    <div class="font-bold text-surface-800">发布任务</div>
                    <div class="text-sm text-surface-400">AI辅助生成</div>
                  </div>
                  <div class="bg-white rounded-2xl p-5 w-40 shadow-sm border border-surface-100">
                    <div class="text-3xl mb-2">③</div>
                    <div class="font-bold text-surface-800">查看提交</div>
                    <div class="text-sm text-surface-400">AI自动评分</div>
                  </div>
                </div>
                <button class="btn-primary text-white px-8 py-3 rounded-xl font-bold" @click="$router.push('/app/class-manage')">
                  开始创建班级
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ==================== 学生端 ==================== -->
      <template v-if="user && user.role === 'student'">
        <!-- 数据总览卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 stagger-fade" v-if="studentStats">
          <div class="stat-card bg-gradient-card-amber">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:clock-outline" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">待提交</span>
              </div>
              <div class="text-4xl font-black">{{ studentStats.pending_count }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">份</div>
            </div>
          </div>
          <div class="stat-card bg-gradient-card-emerald">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:check-circle-outline" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">已完成</span>
              </div>
              <div class="text-4xl font-black">{{ studentStats.completed_count }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">份</div>
            </div>
          </div>
          <div class="stat-card bg-gradient-card-blue">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:chart-line-variant" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">平均分</span>
              </div>
              <div class="text-4xl font-black">{{ studentStats.avg_score }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">分</div>
            </div>
          </div>
          <div class="stat-card bg-gradient-card-violet">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-5">
                <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Icon icon="mdi:podium" class="text-2xl" />
                </div>
                <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">班级排名</span>
              </div>
              <div class="text-4xl font-black">{{ studentStats.rank || '-' }}</div>
              <div class="text-white/60 text-sm mt-1 font-medium">名</div>
            </div>
          </div>
        </div>

        <!-- AI 岗位匹配 -->
        <div class="card mb-10 p-8" v-if="cachedJobMatch || jobMatchLoading">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center">
              <Icon icon="mdi:briefcase-outline" class="text-xl text-violet-500" />
            </div>
            <h3 class="text-lg font-bold text-surface-800">AI 岗位匹配</h3>
          </div>
          <div v-if="cachedJobMatch" class="bg-gradient-to-r from-violet-50 to-purple-50 rounded-2xl p-6 border border-violet-100">
            <div class="flex items-center justify-between mb-3">
              <span class="font-bold text-surface-800 text-lg">{{ cachedJobMatch.job }}</span>
              <span class="text-2xl font-black text-violet-500">{{ cachedJobMatch.match }}%</span>
            </div>
            <div class="w-full bg-violet-200 rounded-full h-2.5 mb-4 overflow-hidden">
              <div class="bg-gradient-to-r from-violet-500 to-purple-500 h-2.5 rounded-full transition-all duration-1000 ease-out"
                :style="{ width: cachedJobMatch.match + '%' }"></div>
            </div>
            <p class="text-sm text-surface-600">{{ cachedJobMatch.advice }}</p>
          </div>
          <div v-else-if="jobMatchLoading" class="text-center py-8">
            <div class="w-8 h-8 border-2 border-violet-200 border-t-violet-500 rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-surface-500 text-sm">AI正在分析...</p>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          <div v-for="(item, idx) in studentActions" :key="item.title"
            class="card-hover p-6 group"
            :style="`animation-delay: ${idx * 0.08}s`"
            @click="$router.push(item.path)">
            <div class="w-12 h-12 rounded-2xl bg-primary-50 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary-100 transition-all duration-300">
              <Icon :icon="item.icon" class="text-2xl" />
            </div>
            <div class="font-bold text-surface-800 mb-1.5 text-base">{{ item.title }}</div>
            <div class="text-sm text-surface-500 leading-relaxed">{{ item.desc }}</div>
          </div>
        </div>

        <!-- 我的班级 -->
        <div class="card mb-10">
          <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
              <span class="text-lg font-bold text-surface-800">我的班级</span>
            </div>
            <button class="btn-primary text-white px-5 py-2 rounded-xl text-sm font-semibold" @click="$router.push('/app/my-classes')">
              加入班级
            </button>
          </div>
          <div class="p-6">
            <div v-if="studentClasses.length === 0" class="py-12">
              <div class="bg-gradient-to-r from-emerald-50 to-green-50 rounded-3xl p-10 text-center border border-emerald-100">
                <div class="text-5xl mb-5"><Icon icon="mdi:school-outline" class="text-emerald-500" /></div>
                <h3 class="text-2xl font-bold text-surface-800 mb-3">欢迎加入知训云！</h3>
                <p class="text-surface-500 mb-8 text-base">只需两步即可开始</p>
                <div class="flex justify-center gap-6 mb-8 flex-wrap">
                  <div class="bg-white rounded-2xl p-5 w-44 shadow-sm border border-surface-100">
                    <div class="text-3xl mb-2">①</div>
                    <div class="font-bold text-surface-800">加入班级</div>
                    <div class="text-sm text-surface-400">输入教师邀请码</div>
                  </div>
                  <div class="bg-white rounded-2xl p-5 w-44 shadow-sm border border-surface-100">
                    <div class="text-3xl mb-2">②</div>
                    <div class="font-bold text-surface-800">提交作业</div>
                    <div class="text-sm text-surface-400">AI自动评分反馈</div>
                  </div>
                </div>
                <button class="btn-primary text-white px-8 py-3 rounded-xl font-bold" @click="$router.push('/app/my-classes')">
                  去加入班级
                </button>
              </div>
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <div v-for="c in studentClasses" :key="c.id"
                class="p-6 rounded-2xl border border-surface-100 hover:border-primary-200 hover:bg-primary-50/30 cursor-pointer transition-all duration-300 group"
                @click="$router.push('/app/my-classes')">
                <div class="flex items-start justify-between mb-3">
                  <h4 class="text-lg font-bold text-surface-800 group-hover:text-primary-600 transition-colors">{{ c.name }}</h4>
                  <Icon icon="mdi:chevron-right" class="text-surface-300 group-hover:text-primary-400 transition-colors" />
                </div>
                <p class="text-surface-500 text-sm mb-4">{{ c.course_name }}</p>
                <div class="flex items-center gap-2 text-sm text-surface-500">
                  <Icon icon="mdi:account-tie" class="text-base" />
                  <span>{{ c.teacher_name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 未登录 -->
      <div v-if="!user" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mx-auto mb-8 shadow-xl shadow-primary-500/20">
            <Icon icon="mdi:clipboard-text-outline" class="text-5xl text-white" />
          </div>
          <h1 class="text-4xl font-bold text-surface-800 mb-4 tracking-tight">实训教学评价系统</h1>
          <p class="text-xl text-surface-500 mb-10 max-w-2xl mx-auto">
            基于大模型技术的智能化实训成果评价平台
          </p>
          <div class="flex items-center justify-center gap-4">
            <button class="btn-primary text-white px-8 py-3 rounded-xl text-lg font-semibold" @click="$router.push('/login')">
              登录
            </button>
            <button class="btn-ghost px-8 py-3 rounded-xl text-lg" @click="$router.push('/login')">
              注册
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const user = ref<any>(null)
const myClasses = ref<any[]>([])
const studentClasses = ref<any[]>([])
const pendingCount = ref(0)
const recentActivities = ref<any[]>([])
const teacherStats = ref<any>(null)
const studentStats = ref<any>(null)
const cachedJobMatch = ref<any>(null)
const jobMatchLoading = ref(false)

onMounted(async () => {
  const data = localStorage.getItem('user')
  if (data) {
    user.value = JSON.parse(data)

    if (user.value.role === 'teacher') {
      await loadTeacherStats()
      await loadRecentActivities()
      try {
        const res = await axios.get(`${API_BASE}/api/classes/?teacher_id=${user.value.id}`)
        if (res.data.success) myClasses.value = res.data.data
      } catch {}
    }

    if (user.value.role === 'student') {
      await loadStudentStats()
      try {
        const res = await axios.get(`${API_BASE}/api/classes/my?student_id=${user.value.id}`)
        if (res.data.success) studentClasses.value = res.data.data
      } catch {}
      try {
        const taskRes = await axios.get(`${API_BASE}/api/tasks/pending?student_id=${user.value.id}`)
        if (taskRes.data.success) {
          pendingCount.value = taskRes.data.data.filter((t: any) => !t.submitted).length
        }
      } catch {}
      const cached = localStorage.getItem('home_job_match')
      if (cached) {
        cachedJobMatch.value = JSON.parse(cached)
      } else {
        loadJobMatchForHome()
      }
    }
  }
})

const loadTeacherStats = async () => {
  try {
    const [overviewRes, classesRes] = await Promise.all([
      axios.get(`${API_BASE}/api/statistics/overview`),
      axios.get(`${API_BASE}/api/classes/?teacher_id=${user.value.id}`)
    ])
    const overview = overviewRes.data.success ? overviewRes.data.data : {}
    const classes = classesRes.data.success ? classesRes.data.data : []
    let totalStudents = 0
    classes.forEach((c: any) => { totalStudents += c.student_count || 0 })
    teacherStats.value = {
      unscored_count: overview.total_submissions || 0,
      class_count: classes.length,
      student_count: totalStudents,
      month_submissions: overview.total_submissions || 0
    }
  } catch {}
}

const loadStudentStats = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/student/${user.value.id}`)
    if (res.data.success) {
      const d = res.data.data
      studentStats.value = {
        pending_count: pendingCount.value,
        completed_count: d.total_count,
        avg_score: d.avg_score,
        rank: '-'
      }
    }
  } catch {}
}

const loadRecentActivities = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/activities`)
    if (res.data.success) {
      recentActivities.value = res.data.data
    }
  } catch {}
}

const loadJobMatchForHome = async () => {
  jobMatchLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/job-match/${user.value.id}`)
    if (res.data.success) {
      cachedJobMatch.value = res.data.data
      localStorage.setItem('home_job_match', JSON.stringify(res.data.data))
    }
  } catch {} finally {
    jobMatchLoading.value = false
  }
}

const teacherActions = [
  { icon: 'mdi:clipboard-text-outline', title: '任务管理', desc: '发布实训任务并查看提交', path: '/app/task-manage' },
  { icon: 'mdi:book-open-page-variant-outline', title: '班级管理', desc: '创建班级和管理学生', path: '/app/class-manage' },
  { icon: 'mdi:chart-bar', title: '数据统计', desc: '教学质量画像与趋势', path: '/app/statistics' },
  { icon: 'mdi:tune-variant', title: '评价标准', desc: '预设评价维度与权重', path: '/app/criteria' }
]

const studentActions = [
  { icon: 'mdi:pencil-box-outline', title: '待提交任务', desc: '查看并提交实训作业', path: '/app/student-tasks' },
  { icon: 'mdi:book-open-page-variant-outline', title: '我的班级', desc: '加入班级查看排名', path: '/app/my-classes' },
  { icon: 'mdi:chart-line-variant', title: '我的成绩', desc: '查看评分与薄弱点', path: '/app/my-scores' },
  { icon: 'mdi:chart-bar', title: '数据统计', desc: '整体教学质量概况', path: '/app/statistics' }
]
</script>
