<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 面包屑 + Title 区域 -->
      <div class="mb-10">
        <div class="flex items-center gap-2 text-sm text-surface-500 mb-3">
          <Icon icon="mdi:home-outline" class="text-base" />
          <span>/</span>
          <span>企业中心</span>
          <span>/</span>
          <span class="text-surface-800 font-medium">仪表盘</span>
        </div>
        <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold text-surface-800 tracking-tight">企业仪表盘</h1>
            <p class="text-surface-500 mt-1.5 text-base">一览岗位发布、学生匹配与评价概况</p>
          </div>
          <div class="flex items-center gap-3">
            <button class="btn-ghost px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
              <Icon icon="mdi:download-outline" />
              导出报表
            </button>
            <button class="btn-primary text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
              <Icon icon="mdi:plus" />
              发布新岗位
            </button>
          </div>
        </div>
      </div>

      <!-- KPI 卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 stagger-fade">
        <div class="stat-card bg-gradient-card-blue">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-5">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:briefcase-outline" class="text-2xl" />
              </div>
              <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">本月</span>
            </div>
            <div class="text-4xl font-black tracking-tight">{{ kpiData.jobCount }}</div>
            <div class="text-white/60 text-sm mt-1 font-medium">发布岗位数</div>
          </div>
        </div>

        <div class="stat-card bg-gradient-card-violet">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-5">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:account-multiple-check-outline" class="text-2xl" />
              </div>
              <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">+12%</span>
            </div>
            <div class="text-4xl font-black tracking-tight">{{ kpiData.matchCount }}</div>
            <div class="text-white/60 text-sm mt-1 font-medium">收到匹配数</div>
          </div>
        </div>

        <div class="stat-card bg-gradient-card-emerald">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-5">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:star-check-outline" class="text-2xl" />
              </div>
              <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">本周</span>
            </div>
            <div class="text-4xl font-black tracking-tight">{{ kpiData.evaluatedCount }}</div>
            <div class="text-white/60 text-sm mt-1 font-medium">评价学生数</div>
          </div>
        </div>

        <div class="stat-card bg-gradient-card-amber">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-5">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:chart-line" class="text-2xl" />
              </div>
              <span class="text-white/80 text-xs font-semibold bg-white/15 px-3 py-1 rounded-full">优秀</span>
            </div>
            <div class="text-4xl font-black tracking-tight">{{ kpiData.avgScore }}</div>
            <div class="text-white/60 text-sm mt-1 font-medium">平均分</div>
          </div>
        </div>
      </div>

      <!-- 双栏布局 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- 最近岗位 -->
        <div class="card">
          <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
              <span class="text-lg font-bold text-surface-800">最近岗位</span>
            </div>
            <button class="text-primary-500 text-sm font-semibold hover:text-primary-600 flex items-center gap-1">
              查看全部
              <Icon icon="mdi:chevron-right" class="text-base" />
            </button>
          </div>
          <div class="p-6 space-y-4">
            <div v-for="job in recentJobs" :key="job.id"
              class="flex items-center gap-4 p-4 rounded-2xl border border-surface-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all duration-300">
              <div :class="job.logoBg" class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0">
                <Icon :icon="job.logo" class="text-2xl" :class="job.logoColor" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <h4 class="font-bold text-surface-800 truncate">{{ job.name }}</h4>
                  <span :class="job.statusClass" class="text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0">
                    {{ job.status }}
                  </span>
                </div>
                <p class="text-sm text-surface-500">{{ job.company }} · {{ job.location }}</p>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="font-bold text-primary-600">{{ job.salary }}</div>
                <div class="text-xs text-surface-400 mt-0.5">{{ job.matchCount }}人匹配</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 待评价学生 -->
        <div class="card">
          <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-1.5 h-5 bg-amber-500 rounded-full"></div>
              <span class="text-lg font-bold text-surface-800">待评价学生</span>
              <span class="bg-amber-50 text-amber-600 text-xs font-bold px-2.5 py-0.5 rounded-full">
                {{ pendingStudents.length }}人
              </span>
            </div>
            <button class="text-primary-500 text-sm font-semibold hover:text-primary-600 flex items-center gap-1">
              去评价
              <Icon icon="mdi:chevron-right" class="text-base" />
            </button>
          </div>
          <div class="p-6 space-y-3">
            <div v-for="stu in pendingStudents" :key="stu.id"
              class="flex items-center gap-4 p-4 rounded-2xl hover:bg-surface-50 transition-colors">
              <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-400 to-indigo-500 flex items-center justify-center flex-shrink-0 text-white font-bold text-lg">
                {{ stu.avatar }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-semibold text-surface-800">{{ stu.name }}</span>
                  <span class="text-xs text-surface-400">{{ stu.studentNo }}</span>
                </div>
                <div class="flex items-center gap-3 text-xs text-surface-500">
                  <span class="flex items-center gap-1">
                    <Icon icon="mdi:school-outline" class="text-sm" />
                    {{ stu.major }}
                  </span>
                  <span class="flex items-center gap-1">
                    <Icon icon="mdi:briefcase-clock-outline" class="text-sm" />
                    {{ stu.submitTime }}
                  </span>
                </div>
              </div>
              <button class="px-4 py-2 bg-amber-50 text-amber-600 rounded-xl text-sm font-semibold hover:bg-amber-100 transition-colors flex-shrink-0 flex items-center gap-1">
                <Icon icon="mdi:pencil-outline" />
                去评价
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Icon } from '@iconify/vue'

const kpiData = reactive({
  jobCount: 12,
  matchCount: 186,
  evaluatedCount: 58,
  avgScore: '92.3'
})

const recentJobs = ref([
  {
    id: 1,
    name: '全栈开发工程师',
    company: '字节跳动',
    location: '北京',
    salary: '25-45K',
    matchCount: 48,
    status: '招聘中',
    statusClass: 'bg-green-50 text-green-600',
    logo: 'mdi:language-css3',
    logoBg: 'bg-gradient-to-br from-blue-100 to-blue-200',
    logoColor: 'text-blue-600'
  },
  {
    id: 2,
    name: '高级前端工程师',
    company: '腾讯科技',
    location: '深圳',
    salary: '20-40K',
    matchCount: 36,
    status: '招聘中',
    statusClass: 'bg-green-50 text-green-600',
    logo: 'mdi:vuejs',
    logoBg: 'bg-gradient-to-br from-emerald-100 to-emerald-200',
    logoColor: 'text-emerald-600'
  },
  {
    id: 3,
    name: '后端开发工程师',
    company: '阿里巴巴',
    location: '杭州',
    salary: '22-42K',
    matchCount: 52,
    status: '即将截止',
    statusClass: 'bg-amber-50 text-amber-600',
    logo: 'mdi:language-java',
    logoBg: 'bg-gradient-to-br from-orange-100 to-orange-200',
    logoColor: 'text-orange-600'
  },
  {
    id: 4,
    name: '算法工程师',
    company: '美团',
    location: '上海',
    salary: '30-55K',
    matchCount: 28,
    status: '招聘中',
    statusClass: 'bg-green-50 text-green-600',
    logo: 'mdi:brain',
    logoBg: 'bg-gradient-to-br from-violet-100 to-violet-200',
    logoColor: 'text-violet-600'
  }
])

const pendingStudents = ref([
  { id: 1, name: '张伟', studentNo: '2024001', avatar: '张', major: '软件工程', submitTime: '2天前' },
  { id: 2, name: '李娜', studentNo: '2024002', avatar: '李', major: '计算机科学', submitTime: '3天前' },
  { id: 3, name: '王强', studentNo: '2024003', avatar: '王', major: '软件工程', submitTime: '4天前' },
  { id: 4, name: '刘洋', studentNo: '2024004', avatar: '刘', major: '数据科学', submitTime: '5天前' },
  { id: 5, name: '陈静', studentNo: '2024005', avatar: '陈', major: '人工智能', submitTime: '1周前' }
])
</script>
