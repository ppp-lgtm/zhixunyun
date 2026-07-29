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
          <span class="text-surface-800 font-medium">学生岗位匹配</span>
        </div>
        <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold text-surface-800 tracking-tight">学生岗位匹配</h1>
            <p class="text-surface-500 mt-1">AI 智能匹配最优候选人，快速发现潜力人才</p>
          </div>
          <div class="flex items-center gap-3">
            <button class="btn-ghost px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
              <Icon icon="mdi:download-outline" />
              导出名单
            </button>
            <button class="btn-primary text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
              <Icon icon="mdi:refresh" />
              重新匹配
            </button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <!-- 左侧岗位筛选 -->
        <div class="lg:col-span-3 space-y-6">
          <!-- 岗位选择卡片 -->
          <div class="card">
            <div class="px-6 py-4 border-b border-surface-100">
              <div class="flex items-center gap-2">
                <Icon icon="mdi:briefcase-outline" class="text-primary-500 text-lg" />
                <h3 class="font-bold text-surface-800">选择岗位</h3>
              </div>
            </div>
            <div class="p-4 space-y-2">
              <div v-for="job in jobList" :key="job.id"
                @click="selectedJob = job.id"
                class="p-4 rounded-xl cursor-pointer transition-all duration-200 border"
                :class="selectedJob === job.id
                  ? 'bg-primary-50 border-primary-300 shadow-sm'
                  : 'bg-white border-surface-100 hover:border-primary-200 hover:bg-primary-50/30'">
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <div :class="job.logoBg" class="w-9 h-9 rounded-lg flex items-center justify-center">
                      <Icon :icon="job.logo" class="text-lg" :class="job.logoColor" />
                    </div>
                    <div>
                      <h4 class="font-bold text-surface-800 text-sm">{{ job.name }}</h4>
                      <p class="text-xs text-surface-500">{{ job.company }}</p>
                    </div>
                  </div>
                  <div v-if="selectedJob === job.id" class="w-5 h-5 rounded-full bg-primary-500 flex items-center justify-center flex-shrink-0">
                    <Icon icon="mdi:check" class="text-white text-xs" />
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs mt-3">
                  <span class="text-primary-600 font-bold">{{ job.salary }}</span>
                  <span class="text-surface-400">{{ job.matchCount }}人匹配</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 筛选条件 -->
          <div class="card">
            <div class="px-6 py-4 border-b border-surface-100 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icon icon="mdi:tune-variant" class="text-primary-500 text-lg" />
                <h3 class="font-bold text-surface-800">筛选条件</h3>
              </div>
              <button class="text-xs text-primary-500 font-semibold hover:text-primary-600">清除</button>
            </div>
            <div class="p-5 space-y-6">
              <!-- 匹配度范围 -->
              <div>
                <div class="flex items-center justify-between mb-3">
                  <label class="text-sm font-semibold text-surface-700">匹配度</label>
                  <span class="text-sm font-bold text-primary-600">{{ matchRange[0] }}% - {{ matchRange[1] }}%</span>
                </div>
                <el-slider v-model="matchRange" range :min="0" :max="100" class="modern-slider" />
              </div>

              <!-- 学历要求 -->
              <div>
                <label class="text-sm font-semibold text-surface-700 block mb-3">学历要求</label>
                <div class="flex flex-wrap gap-2">
                  <button v-for="edu in educationList" :key="edu.value"
                    @click="toggleEducation(edu.value)"
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                    :class="selectedEducation.includes(edu.value)
                      ? 'bg-primary-500 text-white'
                      : 'bg-surface-100 text-surface-600 hover:bg-surface-200'">
                    {{ edu.label }}
                  </button>
                </div>
              </div>

              <!-- 专业方向 -->
              <div>
                <label class="text-sm font-semibold text-surface-700 block mb-3">专业方向</label>
                <div class="space-y-2">
                  <label v-for="maj in majorList" :key="maj.value"
                    class="flex items-center gap-2.5 cursor-pointer group">
                    <input type="checkbox" :checked="selectedMajor.includes(maj.value)"
                      @change="toggleMajor(maj.value)"
                      class="w-4 h-4 rounded border-surface-300 text-primary-500 focus:ring-primary-500" />
                    <span class="text-sm text-surface-700 group-hover:text-primary-600 transition-colors">
                      {{ maj.label }}
                    </span>
                    <span class="ml-auto text-xs text-surface-400">{{ maj.count }}人</span>
                  </label>
                </div>
              </div>

              <!-- 技能标签 -->
              <div>
                <label class="text-sm font-semibold text-surface-700 block mb-3">必备技能</label>
                <el-select
                  v-model="selectedSkills"
                  multiple
                  filterable
                  placeholder="选择技能标签"
                  size="large"
                  class="w-full modern-select"
                >
                  <el-option label="Vue.js" value="Vue.js" />
                  <el-option label="React" value="React" />
                  <el-option label="TypeScript" value="TypeScript" />
                  <el-option label="Node.js" value="Node.js" />
                  <el-option label="Java" value="Java" />
                  <el-option label="Python" value="Python" />
                  <el-option label="MySQL" value="MySQL" />
                  <el-option label="Redis" value="Redis" />
                </el-select>
              </div>

              <!-- 排序方式 -->
              <div>
                <label class="text-sm font-semibold text-surface-700 block mb-3">排序方式</label>
                <el-radio-group v-model="sortBy" class="w-full">
                  <el-radio-button label="match" class="!w-full !mb-2">
                    <span class="flex items-center gap-1.5 px-1">
                      <Icon icon="mdi:percent-outline" class="text-sm" />匹配度优先
                    </span>
                  </el-radio-button>
                  <el-radio-button label="score" class="!w-full !mb-2">
                    <span class="flex items-center gap-1.5 px-1">
                      <Icon icon="mdi:star" class="text-sm" />综合评分
                    </span>
                  </el-radio-button>
                  <el-radio-button label="experience" class="!w-full">
                    <span class="flex items-center gap-1.5 px-1">
                      <Icon icon="mdi:briefcase-clock" class="text-sm" />项目经验
                    </span>
                  </el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧学生排名列表 -->
        <div class="lg:col-span-9 space-y-8">
          <!-- Top 3 金牌榜 -->
          <div class="card overflow-hidden bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50">
            <div class="px-8 py-5 border-b border-amber-100 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
                  <Icon icon="mdi:trophy" class="text-2xl text-white" />
                </div>
                <div>
                  <h3 class="font-bold text-surface-800 text-lg">Top 3 金牌榜</h3>
                  <p class="text-xs text-surface-500">当前岗位综合匹配前三名</p>
                </div>
              </div>
            </div>

            <div class="p-6">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                <!-- 第 2 名 -->
                <div class="relative">
                  <div class="card bg-white/80 backdrop-blur-sm pt-10 pb-6 px-6 h-full hover:shadow-lg transition-all">
                    <div class="absolute -top-4 left-1/2 -translate-x-1/2">
                      <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-slate-300 to-slate-400 flex items-center justify-center shadow-lg">
                        <span class="text-xl font-black text-white">2</span>
                      </div>
                    </div>
                    <div class="text-center">
                      <div class="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 mx-auto mb-4 flex items-center justify-center text-3xl font-bold text-white shadow-md ring-4 ring-white">
                        {{ top3[1].avatar }}
                      </div>
                      <h4 class="font-bold text-surface-800 text-lg">{{ top3[1].name }}</h4>
                      <p class="text-sm text-surface-500 mb-3">{{ top3[1].major }}</p>
                      <div class="flex items-center justify-center gap-2 mb-4">
                        <div class="relative w-16 h-16">
                          <svg class="w-full h-full transform -rotate-90">
                            <circle cx="32" cy="32" r="28" stroke="#e5e7eb" stroke-width="5" fill="none" />
                            <circle cx="32" cy="32" r="28" stroke="url(#silverGradient)" stroke-width="5" fill="none"
                              stroke-linecap="round" :stroke-dasharray="`${top3[1].match * 1.76} 176`" />
                            <defs>
                              <linearGradient id="silverGradient">
                                <stop offset="0%" stop-color="#94a3b8" />
                                <stop offset="100%" stop-color="#64748b" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div class="absolute inset-0 flex items-center justify-center">
                            <span class="font-black text-surface-700 text-sm">{{ top3[1].match }}%</span>
                          </div>
                        </div>
                      </div>
                      <div class="text-2xl font-black text-slate-600 mb-1">{{ top3[1].score }}分</div>
                      <p class="text-xs text-surface-500">综合评分</p>
                    </div>
                  </div>
                </div>

                <!-- 第 1 名 -->
                <div class="relative md:-mt-6">
                  <div class="card bg-white h-full hover:shadow-xl transition-all shadow-xl shadow-amber-200/50 ring-2 ring-amber-300 pt-12 pb-6 px-6">
                    <div class="absolute -top-5 left-1/2 -translate-x-1/2">
                      <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400 to-yellow-500 flex items-center justify-center shadow-xl shadow-amber-500/30">
                        <Icon icon="mdi:crown" class="text-3xl text-white" />
                      </div>
                    </div>
                    <div class="text-center">
                      <div class="w-24 h-24 rounded-full bg-gradient-to-br from-amber-400 via-orange-400 to-rose-500 mx-auto mb-4 flex items-center justify-center text-4xl font-bold text-white shadow-lg ring-4 ring-amber-100">
                        {{ top3[0].avatar }}
                      </div>
                      <h4 class="font-bold text-surface-800 text-xl mb-1">{{ top3[0].name }}</h4>
                      <p class="text-sm text-surface-500 mb-4">{{ top3[0].major }}</p>
                      <div class="flex items-center justify-center gap-2 mb-4">
                        <div class="relative w-20 h-20">
                          <svg class="w-full h-full transform -rotate-90">
                            <circle cx="40" cy="40" r="36" stroke="#fef3c7" stroke-width="6" fill="none" />
                            <circle cx="40" cy="40" r="36" stroke="url(#goldGradient)" stroke-width="6" fill="none"
                              stroke-linecap="round" :stroke-dasharray="`${top3[0].match * 2.26} 226`" />
                            <defs>
                              <linearGradient id="goldGradient">
                                <stop offset="0%" stop-color="#f59e0b" />
                                <stop offset="100%" stop-color="#f97316" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div class="absolute inset-0 flex items-center justify-center">
                            <span class="font-black text-amber-600 text-base">{{ top3[0].match }}%</span>
                          </div>
                        </div>
                      </div>
                      <div class="text-3xl font-black text-amber-600 mb-1">{{ top3[0].score }}分</div>
                      <p class="text-xs text-surface-500">综合评分</p>
                    </div>
                  </div>
                </div>

                <!-- 第 3 名 -->
                <div class="relative">
                  <div class="card bg-white/80 backdrop-blur-sm pt-10 pb-6 px-6 h-full hover:shadow-lg transition-all">
                    <div class="absolute -top-4 left-1/2 -translate-x-1/2">
                      <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-300 to-amber-600 flex items-center justify-center shadow-lg">
                        <span class="text-xl font-black text-white">3</span>
                      </div>
                    </div>
                    <div class="text-center">
                      <div class="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 mx-auto mb-4 flex items-center justify-center text-3xl font-bold text-white shadow-md ring-4 ring-white">
                        {{ top3[2].avatar }}
                      </div>
                      <h4 class="font-bold text-surface-800 text-lg">{{ top3[2].name }}</h4>
                      <p class="text-sm text-surface-500 mb-3">{{ top3[2].major }}</p>
                      <div class="flex items-center justify-center gap-2 mb-4">
                        <div class="relative w-16 h-16">
                          <svg class="w-full h-full transform -rotate-90">
                            <circle cx="32" cy="32" r="28" stroke="#e5e7eb" stroke-width="5" fill="none" />
                            <circle cx="32" cy="32" r="28" stroke="url(#bronzeGradient)" stroke-width="5" fill="none"
                              stroke-linecap="round" :stroke-dasharray="`${top3[2].match * 1.76} 176`" />
                            <defs>
                              <linearGradient id="bronzeGradient">
                                <stop offset="0%" stop-color="#d97706" />
                                <stop offset="100%" stop-color="#b45309" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div class="absolute inset-0 flex items-center justify-center">
                            <span class="font-black text-amber-700 text-sm">{{ top3[2].match }}%</span>
                          </div>
                        </div>
                      </div>
                      <div class="text-2xl font-black text-amber-700 mb-1">{{ top3[2].score }}分</div>
                      <p class="text-xs text-surface-500">综合评分</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 学生排名列表 -->
          <div class="card">
            <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
                <span class="text-lg font-bold text-surface-800">匹配候选人排行</span>
                <span class="bg-primary-50 text-primary-600 text-xs font-bold px-2.5 py-0.5 rounded-full">
                  共 {{ studentRanking.length }} 人
                </span>
              </div>
              <div class="flex items-center gap-2 text-sm">
                <el-input v-model="searchStudent" placeholder="搜索学生..." size="large" class="w-56 modern-input">
                  <template #prefix>
                    <Icon icon="mdi:magnify" class="text-surface-400" />
                  </template>
                </el-input>
              </div>
            </div>

            <div class="p-6 space-y-4">
              <div v-for="(stu, index) in studentRanking" :key="stu.id"
                class="p-5 rounded-2xl border border-surface-100 hover:border-primary-200 hover:bg-primary-50/30 hover:shadow-md transition-all duration-300">
                <div class="flex items-start gap-5">
                  <!-- 排名 -->
                  <div class="flex-shrink-0 w-14 text-center">
                    <div :class="[
                      'w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-2',
                      index < 3 ? 'bg-gradient-to-br from-amber-100 to-orange-100' : 'bg-surface-100'
                    ]">
                      <template v-if="index === 0">
                        <Icon icon="mdi:medal" class="text-2xl text-amber-500" />
                      </template>
                      <template v-else-if="index === 1">
                        <Icon icon="mdi:medal" class="text-2xl text-slate-400" />
                      </template>
                      <template v-else-if="index === 2">
                        <Icon icon="mdi:medal" class="text-2xl text-amber-700" />
                      </template>
                      <span v-else class="font-black text-surface-500 text-lg">{{ index + 1 }}</span>
                    </div>
                  </div>

                  <!-- 头像与信息 -->
                  <div class="flex-shrink-0">
                    <div :class="[
                      'w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-white shadow-md',
                      stu.avatarBg
                    ]">
                      {{ stu.avatar }}
                    </div>
                  </div>

                  <!-- 基本信息 -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2.5 mb-2 flex-wrap">
                      <h4 class="font-bold text-surface-800 text-lg">{{ stu.name }}</h4>
                      <span class="text-xs text-surface-400">{{ stu.studentNo }}</span>
                      <span class="bg-surface-100 text-surface-600 text-xs font-semibold px-2 py-0.5 rounded-full">{{ stu.education }}</span>
                    </div>
                    <div class="flex items-center gap-4 text-sm text-surface-600 mb-3 flex-wrap">
                      <span class="flex items-center gap-1.5">
                        <Icon icon="mdi:school-outline" class="text-primary-500 text-sm" />
                        {{ stu.major }}
                      </span>
                      <span class="flex items-center gap-1.5">
                        <Icon icon="mdi:calendar-outline" class="text-primary-500 text-sm" />
                        {{ stu.grade }}级
                      </span>
                      <span class="flex items-center gap-1.5">
                        <Icon icon="mdi:briefcase-clock-outline" class="text-primary-500 text-sm" />
                        {{ stu.projectCount }}个项目
                      </span>
                    </div>
                    <!-- 技能标签 -->
                    <div class="flex flex-wrap gap-1.5">
                      <span v-for="tag in stu.skills.slice(0, 5)" :key="tag"
                        class="px-2.5 py-1 bg-primary-50 text-primary-600 rounded-lg text-xs font-semibold">
                        {{ tag }}
                      </span>
                      <span v-if="stu.skills.length > 5"
                        class="px-2.5 py-1 bg-surface-100 text-surface-500 rounded-lg text-xs font-semibold">
                        +{{ stu.skills.length - 5 }}
                      </span>
                    </div>
                  </div>

                  <!-- 匹配度环形图 -->
                  <div class="flex-shrink-0 px-4">
                    <div class="relative w-20 h-20">
                      <svg class="w-full h-full transform -rotate-90">
                        <circle cx="40" cy="40" r="34" stroke="#e5e7eb" stroke-width="6" fill="none" />
                        <circle cx="40" cy="40" r="34" :stroke="stu.matchColor" stroke-width="6" fill="none"
                          stroke-linecap="round" :stroke-dasharray="`${stu.match * 2.14} 214`" />
                      </svg>
                      <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <span class="font-black text-xl" :class="stu.matchTextColor">{{ stu.match }}%</span>
                        <span class="text-[10px] text-surface-400 font-medium">匹配度</span>
                      </div>
                    </div>
                  </div>

                  <!-- 亮点 / 缺口 -->
                  <div class="flex-shrink-0 w-56 space-y-2.5 hidden xl:block">
                    <div class="flex items-start gap-2">
                      <div class="w-5 h-5 rounded bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Icon icon="mdi:plus" class="text-emerald-600 text-xs font-bold" />
                      </div>
                      <div class="min-w-0">
                        <span class="text-xs font-semibold text-emerald-700">亮点：</span>
                        <span class="text-xs text-surface-600">{{ stu.highlight }}</span>
                      </div>
                    </div>
                    <div class="flex items-start gap-2">
                      <div class="w-5 h-5 rounded bg-rose-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Icon icon="mdi:minus" class="text-rose-600 text-xs font-bold" />
                      </div>
                      <div class="min-w-0">
                        <span class="text-xs font-semibold text-rose-700">缺口：</span>
                        <span class="text-xs text-surface-600">{{ stu.gap }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 操作按钮 -->
                  <div class="flex-shrink-0 flex flex-col gap-2">
                    <button class="px-4 py-2 bg-gradient-to-r from-primary-500 to-indigo-600 text-white rounded-xl text-sm font-semibold hover:shadow-lg transition-all flex items-center gap-1.5 whitespace-nowrap">
                      <Icon icon="mdi:eye-outline" />
                      查看详情
                    </button>
                    <button class="px-4 py-2 bg-violet-50 text-violet-600 rounded-xl text-sm font-semibold hover:bg-violet-100 transition-colors flex items-center gap-1.5 whitespace-nowrap">
                      <Icon icon="mdi:message-outline" />
                      发起邀约
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 加载更多 -->
            <div class="px-8 pb-8">
              <button class="w-full py-4 border border-dashed border-surface-200 rounded-2xl text-surface-500 font-semibold text-sm hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50/50 transition-all flex items-center justify-center gap-2">
                <Icon icon="mdi:chevron-down" />
                加载更多候选人
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

const selectedJob = ref(1)
const matchRange = ref([60, 100])
const selectedEducation = ref(['本科', '硕士'])
const selectedMajor = ref(['软件工程', '计算机科学'])
const selectedSkills = ref<string[]>(['Vue.js', 'TypeScript'])
const sortBy = ref('match')
const searchStudent = ref('')

const jobList = ref([
  {
    id: 1,
    name: '全栈开发工程师',
    company: '字节跳动',
    salary: '25-45K',
    matchCount: 48,
    logo: 'mdi:language-css3',
    logoBg: 'bg-gradient-to-br from-blue-100 to-blue-200',
    logoColor: 'text-blue-600'
  },
  {
    id: 2,
    name: '高级前端工程师',
    company: '腾讯科技',
    salary: '20-40K',
    matchCount: 36,
    logo: 'mdi:vuejs',
    logoBg: 'bg-gradient-to-br from-emerald-100 to-emerald-200',
    logoColor: 'text-emerald-600'
  },
  {
    id: 3,
    name: '后端开发工程师',
    company: '阿里巴巴',
    salary: '22-42K',
    matchCount: 52,
    logo: 'mdi:language-java',
    logoBg: 'bg-gradient-to-br from-orange-100 to-orange-200',
    logoColor: 'text-orange-600'
  }
])

const educationList = [
  { label: '大专', value: '大专' },
  { label: '本科', value: '本科' },
  { label: '硕士', value: '硕士' },
  { label: '博士', value: '博士' }
]

const majorList = [
  { label: '软件工程', value: '软件工程', count: 86 },
  { label: '计算机科学', value: '计算机科学', count: 72 },
  { label: '数据科学', value: '数据科学', count: 38 },
  { label: '人工智能', value: '人工智能', count: 29 },
  { label: '网络工程', value: '网络工程', count: 24 }
]

const toggleEducation = (val: string) => {
  const idx = selectedEducation.value.indexOf(val)
  if (idx > -1) selectedEducation.value.splice(idx, 1)
  else selectedEducation.value.push(val)
}

const toggleMajor = (val: string) => {
  const idx = selectedMajor.value.indexOf(val)
  if (idx > -1) selectedMajor.value.splice(idx, 1)
  else selectedMajor.value.push(val)
}

const top3 = ref([
  { name: '李娜', avatar: '李', major: '软件工程', match: 96, score: 95.8 },
  { name: '张伟', avatar: '张', major: '计算机科学', match: 93, score: 92.5 },
  { name: '王强', avatar: '王', major: '软件工程', match: 91, score: 90.2 }
])

const studentRanking = ref([
  {
    id: 1,
    name: '李娜',
    avatar: '李',
    avatarBg: 'bg-gradient-to-br from-rose-400 to-pink-500',
    studentNo: '2024002',
    education: '硕士',
    major: '软件工程',
    grade: '2022',
    projectCount: 8,
    match: 96,
    matchColor: '#10b981',
    matchTextColor: 'text-emerald-600',
    score: 95.8,
    skills: ['Vue.js', 'React', 'TypeScript', 'Node.js', 'MySQL', 'Redis', 'Docker'],
    highlight: '全栈项目经验丰富，有大厂实习经历',
    gap: '微服务架构经验较少'
  },
  {
    id: 2,
    name: '张伟',
    avatar: '张',
    avatarBg: 'bg-gradient-to-br from-blue-400 to-indigo-500',
    studentNo: '2024001',
    education: '本科',
    major: '计算机科学',
    grade: '2022',
    projectCount: 6,
    match: 93,
    matchColor: '#3b82f6',
    matchTextColor: 'text-blue-600',
    score: 92.5,
    skills: ['Vue.js', 'TypeScript', 'Webpack', 'JavaScript', 'CSS3'],
    highlight: '前端技术栈扎实，工程化能力强',
    gap: '后端开发经验待补充'
  },
  {
    id: 3,
    name: '王强',
    avatar: '王',
    avatarBg: 'bg-gradient-to-br from-emerald-400 to-teal-500',
    studentNo: '2024003',
    education: '本科',
    major: '软件工程',
    grade: '2022',
    projectCount: 7,
    match: 91,
    matchColor: '#0ea5e9',
    matchTextColor: 'text-sky-600',
    score: 90.2,
    skills: ['Java', 'Spring Boot', 'MySQL', 'Redis', 'RabbitMQ'],
    highlight: 'Java后端功底深厚，高并发项目经验',
    gap: '前端基础相对薄弱'
  },
  {
    id: 4,
    name: '刘洋',
    avatar: '刘',
    avatarBg: 'bg-gradient-to-br from-violet-400 to-purple-500',
    studentNo: '2024004',
    education: '本科',
    major: '数据科学',
    grade: '2022',
    projectCount: 5,
    match: 88,
    matchColor: '#8b5cf6',
    matchTextColor: 'text-violet-600',
    score: 87.6,
    skills: ['Python', 'TensorFlow', 'Pandas', 'NumPy', 'SQL'],
    highlight: '数据分析与机器学习能力出色',
    gap: 'Web开发经验需要积累'
  },
  {
    id: 5,
    name: '陈静',
    avatar: '陈',
    avatarBg: 'bg-gradient-to-br from-orange-400 to-red-500',
    studentNo: '2024005',
    education: '硕士',
    major: '人工智能',
    grade: '2021',
    projectCount: 6,
    match: 85,
    matchColor: '#f97316',
    matchTextColor: 'text-orange-600',
    score: 85.3,
    skills: ['Python', 'PyTorch', 'NLP', 'CV', '算法'],
    highlight: '算法能力强，有顶会论文发表',
    gap: '工程实践经验不足'
  }
])
</script>

<style scoped>
.modern-select :deep(.el-select__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
}
.modern-input :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
}
.modern-slider :deep(.el-slider__runway) {
  height: 6px;
}
.modern-slider :deep(.el-slider__bar) {
  height: 6px;
  background: linear-gradient(90deg, #165DFF 0%, #4F46E5 100%);
}
.modern-slider :deep(.el-slider__button) {
  width: 18px;
  height: 18px;
  border: 3px solid #165DFF;
}
:deep(.el-radio-button__inner) {
  width: 100%;
  padding: 12px 15px;
  border-radius: 0.75rem !important;
  border: 1px solid #e5e7eb !important;
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
}
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #165DFF 0%, #4F46E5 100%);
  border-color: transparent !important;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.25);
}
</style>
