<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">数据统计</h1>
        <p class="text-surface-500 mt-1">查看实训评价的整体数据与趋势分析</p>
      </div>

      <!-- 加载中 -->
      <div v-if="!loaded" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-12 h-12 border-[3px] border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-surface-500">加载中...</p>
        </div>
      </div>

      <div v-else>
        <!-- ================================================================ -->
        <!--                         教 师 端                                 -->
        <!-- ================================================================ -->
        <template v-if="isTeacher">

          <!-- ═══════════════════════════════════════════════════════════ -->
          <!--  C 位：AI 教学建议 — 页面最核心模块                           -->
          <!-- ═══════════════════════════════════════════════════════════ -->
          <div class="relative mb-10 overflow-hidden rounded-3xl bg-gradient-to-br from-primary-700 via-primary-600 to-indigo-700 shadow-2xl shadow-primary-500/25">
            <!-- 装饰光晕 -->
            <div class="absolute top-0 right-0 w-80 h-80 bg-white/8 rounded-full blur-3xl -translate-y-1/3 translate-x-1/4"></div>
            <div class="absolute bottom-0 left-0 w-64 h-64 bg-accent-400/15 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4"></div>
            <!-- 网格纹理 -->
            <div class="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_1px_1px,white_1px,transparent_0)] bg-[length:24px_24px]"></div>

            <div class="relative z-10 p-10">
              <!-- 头部 -->
              <div class="flex flex-col md:flex-row md:items-center gap-6 mb-8">
                <div class="flex items-center gap-4 flex-1">
                  <div class="w-16 h-16 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center shadow-inner ring-1 ring-white/20">
                    <Icon icon="mdi:lightbulb-on-outline" class="text-4xl text-accent-300" />
                  </div>
                  <div>
                    <div class="flex items-center gap-3 mb-1">
                      <h2 class="text-2xl font-bold text-white tracking-tight">AI 教学建议</h2>
                      <span class="px-2.5 py-0.5 rounded-full bg-accent-400/25 text-accent-200 text-xs font-bold border border-accent-400/30">AI 驱动</span>
                    </div>
                    <p class="text-primary-200 text-sm">基于当前班级数据智能分析，精准定位教学改进方向</p>
                  </div>
                </div>
                <!-- 筛选器（内嵌在C位卡片中） -->
                <div class="flex flex-wrap items-center gap-3">
                  <el-select v-model="selectedClassId" placeholder="全部班级" clearable @change="onClassChange" class="w-40" size="default">
                    <el-option label="全部班级" :value="0" />
                    <el-option v-for="c in myClasses" :key="c.id" :label="c.name" :value="c.id" />
                  </el-select>
                  <el-select v-model="selectedCourse" placeholder="全部课程" clearable @change="onCourseChange" class="w-36" size="default">
                    <el-option label="全部课程" value="" />
                    <el-option v-for="c in courseList" :key="c.name" :label="c.name" :value="c.name" />
                  </el-select>
                </div>
              </div>

              <!-- 内容区 -->
              <div v-if="teachingAdvice" class="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/15 animate-fade-in-up">
                <div class="flex items-start gap-4">
                  <Icon icon="mdi:format-quote-open" class="text-4xl text-accent-300 flex-shrink-0 opacity-60" />
                  <p class="text-lg text-white/95 leading-relaxed font-medium">{{ teachingAdvice.advice }}</p>
                </div>
              </div>

              <div v-else-if="adviceLoading" class="text-center py-12">
                <div class="w-12 h-12 border-[3px] border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
                <p class="text-primary-200 font-medium">AI 正在深度分析教学质量数据...</p>
                <p class="text-primary-300 text-sm mt-1">综合评估班级成绩、维度得分与提交趋势</p>
              </div>

              <div v-else class="text-center py-12">
                <p class="text-primary-200 mb-6 font-medium">点击下方按钮，让 AI 为您生成专属教学建议</p>
                <button
                  @click="loadTeachingAdvice"
                  class="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 rounded-2xl font-bold text-lg hover:shadow-2xl hover:shadow-white/20 hover:-translate-y-0.5 transition-all duration-300"
                >
                  <Icon icon="mdi:sparkles" class="text-2xl text-accent-500" />
                  AI 分析教学建议
                </button>
              </div>

              <!-- 底部指标快览 -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8" v-if="overview">
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-primary-200 text-xs font-medium mb-0.5">提交总数</div>
                  <div class="text-white text-2xl font-black">{{ overview.total_submissions || 0 }}<span class="text-sm font-normal text-primary-300 ml-1">次</span></div>
                </div>
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-primary-200 text-xs font-medium mb-0.5">评价总数</div>
                  <div class="text-white text-2xl font-black">{{ overview.total_evaluations || 0 }}<span class="text-sm font-normal text-primary-300 ml-1">次</span></div>
                </div>
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-primary-200 text-xs font-medium mb-0.5">平均分</div>
                  <div class="text-white text-2xl font-black">{{ overview.avg_score || 0 }}<span class="text-sm font-normal text-primary-300 ml-1">分</span></div>
                </div>
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-primary-200 text-xs font-medium mb-0.5">学生人数</div>
                  <div class="text-white text-2xl font-black">{{ overview.student_count || 0 }}<span class="text-sm font-normal text-primary-300 ml-1">人</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══════════════════════════════════════════════════════════ -->
          <!--  次要区域：统计卡片 + 图表                                     -->
          <!-- ═══════════════════════════════════════════════════════════ -->

          <!-- 四色统计卡片 -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8 stagger-fade" v-if="teacherCards">
            <div v-for="(card, idx) in teacherCards" :key="card.label"
              class="card p-6 hover:-translate-y-1 transition-all duration-300 group cursor-default"
              :style="`animation-delay: ${idx * 0.08}s`">
              <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
                  :class="[
                    idx === 0 ? 'bg-primary-50 text-primary-500' :
                    idx === 1 ? 'bg-success-50 text-success-500' :
                    idx === 2 ? 'bg-accent-50 text-accent-500' :
                    'bg-violet-50 text-violet-500'
                  ]">
                  <Icon :icon="card.icon" class="text-2xl" />
                </div>
                <span class="text-xs font-semibold px-2.5 py-1 rounded-full"
                  :class="[
                    idx === 0 ? 'bg-primary-50 text-primary-600' :
                    idx === 1 ? 'bg-success-50 text-success-600' :
                    idx === 2 ? 'bg-accent-50 text-accent-600' :
                    'bg-violet-50 text-violet-600'
                  ]">{{ card.label }}</span>
              </div>
              <div class="text-4xl font-black text-surface-800 tracking-tight">{{ card.value }}</div>
              <div class="text-surface-400 text-sm mt-1 font-medium">{{ card.unit }}</div>
            </div>
          </div>

          <!-- 图表 2x2 网格 -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- 成绩分布 -->
            <div class="card p-8">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                  <Icon icon="mdi:chart-bar" class="text-xl text-primary-500" />
                </div>
                <h3 class="text-lg font-bold text-surface-800">成绩分布</h3>
              </div>
              <div v-if="distribution.length === 0" class="text-center py-12">
                <Icon icon="mdi:chart-bar" class="text-4xl text-surface-200 mb-3" />
                <p class="text-surface-400 text-sm">暂无数据</p>
              </div>
              <v-chart v-else :option="barOption" style="height: 300px" />
            </div>

            <!-- 各维度平均分 -->
            <div class="card p-8">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-accent-50 flex items-center justify-center">
                  <Icon icon="mdi:radar" class="text-xl text-accent-500" />
                </div>
                <h3 class="text-lg font-bold text-surface-800">各维度平均分</h3>
              </div>
              <div v-if="dimensionAvg.length === 0" class="text-center py-12">
                <Icon icon="mdi:radar" class="text-4xl text-surface-200 mb-3" />
                <p class="text-surface-400 text-sm">暂无数据</p>
              </div>
              <v-chart v-else :option="radarOption" style="height: 300px" />
            </div>

            <!-- 班级对比 -->
            <div class="card p-8">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-success-50 flex items-center justify-center">
                  <Icon icon="mdi:trophy-outline" class="text-xl text-success-500" />
                </div>
                <h3 class="text-lg font-bold text-surface-800">班级平均分对比</h3>
              </div>
              <div v-if="classCompare.length === 0" class="text-center py-12">
                <Icon icon="mdi:trophy-outline" class="text-4xl text-surface-200 mb-3" />
                <p class="text-surface-400 text-sm">暂无班级数据</p>
              </div>
              <v-chart v-else :option="classCompareOption" style="height: 300px" />
            </div>

            <!-- 提交率 -->
            <div class="card p-8">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                  <Icon icon="mdi:chart-pie" class="text-xl text-blue-500" />
                </div>
                <h3 class="text-lg font-bold text-surface-800">提交率统计</h3>
              </div>
              <div v-if="submitRateData.length === 0" class="text-center py-12">
                <Icon icon="mdi:chart-pie" class="text-4xl text-surface-200 mb-3" />
                <p class="text-surface-400 text-sm">暂无数据</p>
              </div>
              <v-chart v-else :option="submitRateOption" style="height: 300px" />
            </div>
          </div>

          <!-- 趋势图（全宽） -->
          <div class="card p-8 mb-8">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center">
                <Icon icon="mdi:chart-timeline-variant" class="text-xl text-violet-500" />
              </div>
              <h3 class="text-lg font-bold text-surface-800">最近评价趋势</h3>
            </div>
            <div v-if="trend.length === 0" class="text-center py-12">
              <Icon icon="mdi:chart-timeline-variant" class="text-4xl text-surface-200 mb-3" />
              <p class="text-surface-400 text-sm">暂无数据</p>
            </div>
            <v-chart v-else :option="lineOption" style="height: 340px" />
          </div>
        </template>

        <!-- ================================================================ -->
        <!--                         学 生 端                                 -->
        <!-- ================================================================ -->
        <template v-if="isStudent">

          <!-- ═══════════════════════════════════════════════════════════ -->
          <!--  C 位：AI 岗位匹配 — 学生端核心模块                            -->
          <!-- ═══════════════════════════════════════════════════════════ -->
          <div class="relative mb-10 overflow-hidden rounded-3xl bg-gradient-to-br from-violet-700 via-purple-600 to-indigo-700 shadow-2xl shadow-violet-500/25">
            <div class="absolute top-0 right-0 w-80 h-80 bg-white/8 rounded-full blur-3xl -translate-y-1/3 translate-x-1/4"></div>
            <div class="absolute bottom-0 left-0 w-64 h-64 bg-pink-400/10 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4"></div>
            <div class="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_1px_1px,white_1px,transparent_0)] bg-[length:24px_24px]"></div>

            <div class="relative z-10 p-10">
              <div class="flex flex-col md:flex-row md:items-center gap-6 mb-8">
                <div class="flex items-center gap-4 flex-1">
                  <div class="w-16 h-16 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center shadow-inner ring-1 ring-white/20">
                    <Icon icon="mdi:briefcase-outline" class="text-4xl text-pink-300" />
                  </div>
                  <div>
                    <div class="flex items-center gap-3 mb-1">
                      <h2 class="text-2xl font-bold text-white tracking-tight">AI 岗位匹配</h2>
                      <span class="px-2.5 py-0.5 rounded-full bg-pink-400/25 text-pink-200 text-xs font-bold border border-pink-400/30">AI 驱动</span>
                    </div>
                    <p class="text-violet-200 text-sm">基于你的实训成绩智能推荐适合的岗位方向</p>
                  </div>
                </div>
              </div>

              <div v-if="jobMatch">
                <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/15 animate-fade-in-up">
                  <div class="flex items-center justify-between mb-5">
                    <span class="text-2xl font-bold text-white">{{ jobMatch.job }}</span>
                    <span class="text-5xl font-black text-pink-300">{{ jobMatch.match }}%</span>
                  </div>
                  <div class="w-full bg-white/15 rounded-full h-3 mb-8 overflow-hidden">
                    <div class="bg-gradient-to-r from-pink-400 to-pink-300 h-3 rounded-full transition-all duration-1000 ease-out shadow-[0_0_12px_rgba(244,114,182,0.5)]"
                      :style="{ width: jobMatch.match + '%' }"></div>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div v-for="req in jobMatch.requirements" :key="req.skill"
                      class="bg-white/10 rounded-xl p-4 border border-white/10">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-white">{{ req.skill }}</span>
                        <span :class="req.gap.includes('已达标') ? 'bg-success-400/20 text-success-300 border border-success-400/30' : 'bg-accent-400/20 text-accent-300 border border-accent-400/30'"
                          class="px-2 py-0.5 rounded-full text-xs font-semibold">
                          {{ req.gap.includes('已达标') ? '已达标' : '需提升' }} {{ req.student_level }} / {{ req.level }}
                        </span>
                      </div>
                      <p class="text-sm text-violet-200">{{ req.gap }}</p>
                    </div>
                  </div>
                  <div class="bg-white/10 rounded-xl p-5 border border-white/10">
                    <p class="text-white/90 font-medium">{{ jobMatch.advice }}</p>
                  </div>
                </div>
              </div>

              <div v-else-if="jobMatchLoading" class="text-center py-12">
                <div class="w-12 h-12 border-[3px] border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
                <p class="text-violet-200 font-medium">AI 正在深度分析你的能力画像...</p>
                <p class="text-violet-300 text-sm mt-1">综合评估各维度得分、班级排名与成长趋势</p>
              </div>

              <div v-else class="text-center py-12">
                <p class="text-violet-200 mb-6 font-medium">点击下方按钮，让 AI 为你精准匹配岗位方向</p>
                <button
                  @click="loadJobMatch"
                  class="inline-flex items-center gap-2 px-8 py-4 bg-white text-violet-700 rounded-2xl font-bold text-lg hover:shadow-2xl hover:shadow-white/20 hover:-translate-y-0.5 transition-all duration-300"
                >
                  <Icon icon="mdi:sparkles" class="text-2xl text-pink-500" />
                  AI 分析岗位匹配
                </button>
              </div>

              <!-- 底部个人指标 -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-violet-200 text-xs font-medium mb-0.5">提交次数</div>
                  <div class="text-white text-2xl font-black">{{ myStats.total_count }}<span class="text-sm font-normal text-violet-300 ml-1">次</span></div>
                </div>
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-violet-200 text-xs font-medium mb-0.5">平均分</div>
                  <div class="text-white text-2xl font-black">{{ myStats.avg_score }}<span class="text-sm font-normal text-violet-300 ml-1">分</span></div>
                </div>
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-violet-200 text-xs font-medium mb-0.5">最高分</div>
                  <div class="text-white text-2xl font-black">{{ myStats.max_score }}<span class="text-sm font-normal text-violet-300 ml-1">分</span></div>
                </div>
                <div class="bg-white/8 backdrop-blur-sm rounded-xl px-5 py-3.5 border border-white/10">
                  <div class="text-violet-200 text-xs font-medium mb-0.5">最低分</div>
                  <div class="text-white text-2xl font-black">{{ myStats.min_score }}<span class="text-sm font-normal text-violet-300 ml-1">分</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 学生图表区 -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="card p-8">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-success-50 flex items-center justify-center">
                  <Icon icon="mdi:chart-line-variant" class="text-xl text-success-500" />
                </div>
                <h3 class="text-lg font-bold text-surface-800">个人成绩趋势</h3>
              </div>
              <div v-if="myTrend.length === 0" class="text-center py-12">
                <Icon icon="mdi:chart-line-variant" class="text-4xl text-surface-200 mb-3" />
                <p class="text-surface-400 text-sm">暂无数据</p>
              </div>
              <v-chart v-else :option="myLineOption" style="height: 300px" />
            </div>

            <div class="card p-8">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-accent-50 flex items-center justify-center">
                  <Icon icon="mdi:radar" class="text-xl text-accent-500" />
                </div>
                <h3 class="text-lg font-bold text-surface-800">各维度能力雷达</h3>
              </div>
              <div v-if="myRadarData.length === 0" class="text-center py-12">
                <Icon icon="mdi:radar" class="text-4xl text-surface-200 mb-3" />
                <p class="text-surface-400 text-sm">暂无数据</p>
              </div>
              <v-chart v-else :option="myRadarOption" style="height: 300px" />
            </div>
          </div>

          <!-- 薄弱维度 -->
          <div class="card p-8" v-if="myStats.weakness?.length">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-danger-50 flex items-center justify-center">
                <Icon icon="mdi:alert-outline" class="text-xl text-danger-500" />
              </div>
              <h3 class="text-lg font-bold text-surface-800">需要加强的维度</h3>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div v-for="w in myStats.weakness" :key="w.name"
                class="bg-danger-50 border-l-4 border-danger-500 rounded-2xl p-6 text-center">
                <div class="text-lg font-bold text-surface-800 mb-2">{{ w.name }}</div>
                <div class="text-3xl font-black text-danger-500 mb-1">{{ w.count }}次</div>
                <div class="text-surface-500 text-sm">低于70分</div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const loaded = ref(false)
const isTeacher = ref(false)
const isStudent = ref(false)

const overview = ref<any>({})
const distribution = ref<any[]>([])
const trend = ref<any[]>([])
const dimensionAvg = ref<any[]>([])
const selectedClassId = ref(0)
const myClasses = ref<any[]>([])
const classCompare = ref<any[]>([])
const submitRateData = ref<any[]>([])

const myStats = ref<any>({ total_count: 0, avg_score: 0, max_score: 0, min_score: 0, weakness: [] })
const myTrend = ref<any[]>([])
const myRadarData = ref<any[]>([])
const jobMatch = ref<any>(null)
const jobMatchLoading = ref(false)

const teachingAdvice = ref<any>(null)
const adviceLoading = ref(false)

const selectedCourse = ref('')
const courseList = ref<any[]>([])

const loadCourses = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/courses`)
    if (res.data.success) courseList.value = res.data.data
  } catch {}
}

const onCourseChange = () => {
  onClassChange(selectedClassId.value)
}

const loadTeachingAdvice = async () => {
  adviceLoading.value = true
  const params = selectedClassId.value > 0 ? `?class_id=${selectedClassId.value}` : ''
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/teaching-advice${params}`)
    if (res.data.success) teachingAdvice.value = res.data.data
  } catch {} finally { adviceLoading.value = false }
}

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  isTeacher.value = user.role === 'teacher'
  isStudent.value = user.role === 'student'

  if (isTeacher.value) {
    await loadClasses()
    await onClassChange(0)
    await loadClassCompare()
    await loadCourses()
  } else if (isStudent.value) {
    await loadStudentStats()
  }
  loaded.value = true
})

const loadClasses = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/classes/?teacher_id=${user.id}`)
    if (res.data.success) myClasses.value = res.data.data
  } catch {}
}

const loadClassCompare = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await axios.get(`${API_BASE}/api/classes/?teacher_id=${user.id}`)
    if (!res.data.success) return
    const classes = res.data.data
    const result = []
    for (const c of classes) {
      try {
        const sRes = await axios.get(`${API_BASE}/api/statistics/class/${c.id}`)
        if (sRes.data.success) {
          result.push({
            name: c.name,
            avg: sRes.data.data.class_avg,
            count: sRes.data.data.total_submissions,
            students: sRes.data.data.total_students
          })
        }
      } catch {}
    }
    classCompare.value = result
    submitRateData.value = result.map(r => ({
      name: r.name,
      rate: r.students > 0 ? Math.round((r.count / r.students) * 100) : 0
    }))
  } catch {}
}

const onClassChange = async (val: number) => {
  loaded.value = false
  let params = ''
  if (val && val > 0) params += `class_id=${val}`
  if (selectedCourse.value) params += (params ? '&' : '') + `course=${encodeURIComponent(selectedCourse.value)}`
  if (params) params = '?' + params

  try {
    const [res1, res2, res3, res4] = await Promise.all([
      axios.get(`${API_BASE}/api/statistics/overview${params}`),
      axios.get(`${API_BASE}/api/statistics/score-distribution${params}`),
      axios.get(`${API_BASE}/api/statistics/trend${params}`),
      axios.get(`${API_BASE}/api/statistics/dimension-avg${params}`)
    ])
    overview.value = res1.data.data
    distribution.value = res2.data.data
    trend.value = res3.data.data
    dimensionAvg.value = res4.data.data
  } catch {} finally { loaded.value = true }
}

const loadStudentStats = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/student/${user.id}`)
    if (res.data.success) {
      const d = res.data.data
      myStats.value = {
        total_count: d.total_count,
        avg_score: d.avg_score,
        max_score: d.records.length > 0 ? Math.max(...d.records.map((r: any) => r.total_score)) : 0,
        min_score: d.records.length > 0 ? Math.min(...d.records.map((r: any) => r.total_score)) : 0,
        weakness: d.weakness
      }
      myTrend.value = d.records.map((r: any) => ({ time: r.time, score: r.total_score })).reverse()
      const dimMap: any = {}
      const dimCount: any = {}
      d.records.forEach((r: any) => {
        r.scores.forEach((s: any) => {
          dimMap[s.name] = (dimMap[s.name] || 0) + s.score
          dimCount[s.name] = (dimCount[s.name] || 0) + 1
        })
      })
      myRadarData.value = Object.keys(dimMap).map(name => ({
        name,
        avg: Math.round(dimMap[name] / dimCount[name])
      }))
    }
  } catch {}
}

const loadJobMatch = async () => {
  jobMatchLoading.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/job-match/${user.id}`)
    if (res.data.success) jobMatch.value = res.data.data
  } catch {} finally { jobMatchLoading.value = false }
}

const teacherCards = computed(() => [
  { label: '提交总数', value: overview.value?.total_submissions || 0, unit: '次', icon: 'mdi:file-document-multiple-outline' },
  { label: '评价总数', value: overview.value?.total_evaluations || 0, unit: '次', icon: 'mdi:star-outline' },
  { label: '平均分', value: overview.value?.avg_score || 0, unit: '分', icon: 'mdi:chart-line-variant' },
  { label: '学生人数', value: overview.value?.student_count || 0, unit: '人', icon: 'mdi:account-group-outline' }
])

const barOption = computed(() => {
  if (!distribution.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: distribution.value.map(d => d.range), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '人数', axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'bar', data: distribution.value.map(d => d.count), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#4F46E5' }, { offset: 1, color: '#818CF8' }] }, borderRadius: [8, 8, 0, 0] }, barWidth: '50%' }]
  }
})

const radarOption = computed(() => {
  if (!dimensionAvg.value?.length) return {}
  const filtered = dimensionAvg.value.filter(d => d.avg >= 20)
  if (!filtered.length) return {}
  return {
    tooltip: { backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    radar: { indicator: filtered.map(d => ({ name: d.name, max: 100 })), shape: 'polygon', splitNumber: 4, axisName: { color: '#334155', fontSize: 13, fontWeight: 600 }, splitLine: { lineStyle: { color: '#E2E8F0' } }, splitArea: { areaStyle: { color: ['#F8FAFC', '#fff'] } }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    series: [{ type: 'radar', data: [{ value: filtered.map(d => d.avg), name: '平均分', areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5, colorStops: [{ offset: 0, color: 'rgba(245, 158, 11, 0.25)' }, { offset: 1, color: 'rgba(245, 158, 11, 0.04)' }] } }, lineStyle: { color: '#F59E0B', width: 3 }, itemStyle: { color: '#F59E0B', borderColor: '#fff', borderWidth: 3 } }] }]
  }
})

const classCompareOption = computed(() => {
  if (!classCompare.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: classCompare.value.map(c => c.name), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '平均分', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'bar', data: classCompare.value.map(c => c.avg), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#10B981' }, { offset: 1, color: '#059669' }] }, borderRadius: [8, 8, 0, 0] }, barWidth: '40%' }]
  }
})

const submitRateOption = computed(() => {
  if (!submitRateData.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: submitRateData.value.map(r => r.name), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '提交率(%)', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'bar', data: submitRateData.value.map(r => r.rate), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3B82F6' }, { offset: 1, color: '#2563EB' }] }, borderRadius: [8, 8, 0, 0] }, barWidth: '40%' }]
  }
})

const lineOption = computed(() => {
  if (!trend.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: trend.value.map(t => t.time), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '分数', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'line', data: trend.value.map(t => t.score), smooth: true, symbol: 'circle', symbolSize: 10, lineStyle: { width: 4, color: '#8B5CF6' }, itemStyle: { color: '#8B5CF6', borderColor: '#fff', borderWidth: 3 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(139, 92, 246, 0.3)' }, { offset: 1, color: 'rgba(139, 92, 246, 0.05)' }] } } }]
  }
})

const myLineOption = computed(() => {
  if (!myTrend.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: myTrend.value.map(t => t.time), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '分数', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'line', data: myTrend.value.map(t => t.score), smooth: true, symbol: 'circle', symbolSize: 10, lineStyle: { width: 4, color: '#10B981' }, itemStyle: { color: '#10B981', borderColor: '#fff', borderWidth: 3 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }, { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }] } } }]
  }
})

const myRadarOption = computed(() => {
  if (!myRadarData.value?.length) return {}
  const filtered = myRadarData.value.filter(d => d.avg >= 20)
  if (!filtered.length) return {}
  return {
    tooltip: { backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    radar: { indicator: filtered.map(d => ({ name: d.name, max: 100 })), shape: 'polygon', splitNumber: 4, axisName: { color: '#334155', fontSize: 13, fontWeight: 600 }, splitLine: { lineStyle: { color: '#E2E8F0' } }, splitArea: { areaStyle: { color: ['#F8FAFC', '#fff'] } }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    series: [{ type: 'radar', data: [{ value: filtered.map(d => d.avg), name: '我的能力', areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5, colorStops: [{ offset: 0, color: 'rgba(245, 158, 11, 0.25)' }, { offset: 1, color: 'rgba(245, 158, 11, 0.04)' }] } }, lineStyle: { color: '#F59E0B', width: 3 }, itemStyle: { color: '#F59E0B', borderColor: '#fff', borderWidth: 3 } }] }]
  }
})
</script>
