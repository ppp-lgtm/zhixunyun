<template>
  <div class="page-enter">
    <div class="max-w-7xl mx-auto">
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">实训评价详情</h1>
        <p class="text-surface-500 mt-1">查看AI智能评价、教师评分与成果核查结果</p>
      </div>

      <div class="mb-10" v-if="result">
        <div class="relative overflow-hidden rounded-3xl bg-gradient-to-r from-primary-700 via-primary-600 to-primary-700 shadow-2xl shadow-primary-500/20">
          <div class="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
          <div class="absolute bottom-0 left-0 w-64 h-64 bg-white/5 rounded-full blur-2xl translate-y-1/2 -translate-x-1/4"></div>
          <div class="relative z-10 p-10">
            <!-- 学生信息行 -->
            <div v-if="isTeacher" class="flex items-center gap-4 mb-4 text-white/90 text-sm">
              <span class="font-bold text-base">{{ studentInfo.name || '学生' }}</span>
              <span class="text-white/60">|</span>
              <span>学号：{{ studentInfo.number || '-' }}</span>
              <span class="text-white/60">|</span>
              <span>班级：{{ studentInfo.class || '不限' }}</span>
            </div>

            <div class="flex flex-col md:flex-row items-center justify-between gap-8">
              <div class="text-center md:text-left">
                <p class="text-white/80 text-lg font-medium mb-2">
                  {{ activeTab === 'teacher' && teacherSaved ? '教师最终评分' : 'AI 综合评分' }}
                </p>
                <div class="flex items-end gap-4">
                  <div class="text-[120px] font-black text-white leading-none">{{ displayScore }}</div>
                  <div class="mb-4">
                    <span class="px-4 py-1 rounded-full bg-white/20 backdrop-blur text-white font-bold text-base border border-white/30 whitespace-nowrap">
                      {{ displayScore >= 80 ? '优秀' : displayScore >= 60 ? '良好' : '需改进' }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex flex-col items-center md:items-end gap-2">
                <p class="text-white/90 text-sm font-medium">评价维度</p>
                <div class="flex flex-wrap gap-3 justify-center md:justify-end max-w-md">
                  <span v-for="item in result?.evaluation?.scores" :key="item.name"
                    class="px-3 py-1 rounded-full bg-white/10 backdrop-blur text-white text-sm border border-white/20">
                    {{ item.name }}
                  </span>
                </div>
              </div>
            </div>
            <!-- 核心结论 -->
            <div class="mt-6 px-5 py-3 bg-white/10 backdrop-blur rounded-xl text-white/90 text-sm text-center">
              <Icon icon="mdi:lightbulb-outline" class="inline align-text-bottom" /> {{ conclusionText }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="result">
        <div class="flex items-center justify-center mb-10 bg-surface-50 rounded-2xl p-1.5 max-w-2xl mx-auto border border-surface-100">
          <button v-for="tab in tabList" :key="tab.value"
            @click="activeTab = tab.value"
            :class="activeTab === tab.value
              ? 'bg-white shadow-sm text-surface-800 font-bold border border-surface-100'
              : 'text-surface-500 hover:text-surface-700 font-medium border-transparent'"
            class="flex-1 py-2.5 px-4 rounded-xl transition-all duration-300 flex items-center justify-center gap-2 text-sm border">
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <!-- AI评分Tab -->
        <div v-show="activeTab === 'ai'" class="animate-fade-in">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <div v-for="item in result?.evaluation?.scores" :key="item.name"
              class="group bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden">
              <div class="p-6">
                <div class="flex justify-between items-start mb-5">
                  <span class="font-bold text-xl text-gray-900">{{ item.name }}</span>
                  <span class="text-4xl font-black text-primary-600">{{ item.score }}<span class="text-lg font-normal">分</span></span>
                </div>
                <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden mb-4">
                  <div class="h-full rounded-full transition-all duration-1000 ease-out"
                    :style="{ width: item.score + '%', background: item.score >= 80 ? 'linear-gradient(90deg, #22c55e, #16a34a)' : item.score >= 60 ? 'linear-gradient(90deg, #f59e0b, #d97706)' : 'linear-gradient(90deg, #ef4444, #dc2626)' }"></div>
                </div>
                <p class="text-gray-500 text-sm leading-relaxed">{{ item.reason }}</p>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 rounded-3xl p-8 border border-gray-100">
            <h3 class="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span class="w-8 h-8 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-lg"><Icon icon="mdi:text-box-edit-outline" /></span>
              AI 总评
            </h3>
            <p class="text-gray-700 leading-relaxed text-lg">{{ result?.evaluation?.comment }}</p>
          </div>
        </div>

        <!-- 教师评分Tab -->
        <div v-show="activeTab === 'teacher'" class="animate-fade-in">
          <!-- 编辑模式 -->
          <template v-if="isEditing">
            <div class="bg-orange-50 border border-orange-200 rounded-2xl p-5 mb-8 flex items-center gap-3">
              <Icon icon="mdi:alert-circle-outline" class="text-2xl text-orange-500" />
              <p class="text-orange-700 font-medium">编辑模式 | 调整分数后点击保存即可生效</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div v-for="(item, idx) in editingScores" :key="idx"
                class="bg-white rounded-2xl border-2 border-dashed border-orange-300 p-6">
                <div class="flex justify-between items-center mb-4">
                  <span class="font-bold text-lg text-gray-900">{{ item.name }}</span>
                  <el-input-number 
                    v-model="item.score" 
                    :min="0" 
                    :max="100" 
                    controls-position="right"
                    size="large"
                    class="!w-28" />
                </div>
                <el-input 
                  v-model="item.reason" 
                  type="textarea" 
                  :rows="3" 
                  placeholder="请输入评分理由" 
                  class="w-full" />
              </div>
            </div>
            <div class="bg-white rounded-2xl border border-gray-100 p-6 mb-8">
              <label class="block text-lg font-bold text-gray-900 mb-3">教师评语</label>
              <el-input 
                v-model="editingComment" 
                type="textarea" 
                :rows="4" 
                placeholder="请输入教师评语..." 
                class="w-full" />
            </div>
            <div class="flex justify-center gap-4">
              <el-button 
                type="success" 
                size="large" 
                @click="submitTeacherScore" 
                :loading="saving"
                class="!rounded-xl !px-8 !font-bold">
                <Icon icon="mdi:content-save-outline" class="inline align-text-bottom" /> 保存评分
              </el-button>
              <el-button 
                size="large" 
                @click="cancelEdit"
                class="!rounded-xl !px-8 !font-bold">
                取消
              </el-button>
            </div>
          </template>

          <!-- 已保存的教师评分 -->
          <template v-else-if="teacherSaved">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div v-for="item in teacherData.scores" :key="item.name"
                class="group bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div class="p-6">
                  <div class="flex justify-between items-start mb-5">
                    <span class="font-bold text-xl text-gray-900">{{ item.name }}</span>
                    <span class="text-4xl font-black text-orange-500">{{ item.score }}<span class="text-lg font-normal">分</span></span>
                  </div>
                  <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden mb-4">
                    <div class="h-full rounded-full bg-gradient-to-r from-orange-500 to-orange-600 transition-all duration-1000 ease-out"
                      :style="{ width: item.score + '%' }"></div>
                  </div>
                  <p class="text-gray-500 text-sm leading-relaxed">{{ item.reason }}</p>
                </div>
              </div>
            </div>
            <div class="bg-orange-50 rounded-3xl p-8 border border-orange-100">
              <h3 class="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span class="w-8 h-8 rounded-lg bg-orange-100 text-orange-600 flex items-center justify-center text-lg"><Icon icon="mdi:text-box-edit-outline" /></span>
                教师评语
              </h3>
              <p class="text-gray-700 leading-relaxed text-lg">{{ teacherData.comment }}</p>
            </div>
            <div class="mt-8 text-center">
              <el-button 
                type="warning" 
                size="large" 
                @click="startEdit"
                class="!rounded-xl !px-8 !font-bold">
                <Icon icon="mdi:pencil-outline" class="inline align-text-bottom" /> 修改评分
              </el-button>
            </div>
          </template>

          <!-- 未评分状态 -->
          <template v-else>
            <div v-if="isTeacher" class="py-20 text-center">
              <div class="w-24 h-24 rounded-full bg-orange-50 flex items-center justify-center mx-auto mb-6">
                <Icon icon="mdi:pencil-outline" class="text-5xl text-orange-500" />
              </div>
              <p class="text-gray-500 text-xl mb-8">尚未提交教师评分</p>
              <el-button 
                type="warning" 
                size="large" 
                @click="startEdit"
                class="!rounded-xl !px-10 !py-4 !font-bold !text-xl">
                <Icon icon="mdi:pencil-outline" class="inline align-text-bottom" /> 开始评分
              </el-button>
            </div>
            <div v-else class="py-20 text-center">
              <div class="text-gray-300 text-6xl mb-4"><Icon icon="mdi:email-open-outline" /></div>
              <p class="text-gray-500 text-xl">暂无教师评分</p>
            </div>
          </template>
        </div>

        <!-- 智能核查Tab -->
        <div v-show="activeTab === 'check'" class="animate-fade-in">
          <template v-if="hasCompleteness">
            <div class="mb-12">
              <h3 class="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <span class="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center text-lg"><Icon icon="mdi:clipboard-check-outline" /></span>
                步骤完整性核查
              </h3>
              <div class="overflow-hidden rounded-2xl border border-gray-100">
                <el-table :data="result.completeness.steps" style="width: 100%" :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }">
                  <el-table-column prop="step" label="实训步骤" min-width="220" />
                  <el-table-column prop="status" label="完成状态" width="140">
                    <template #default="{ row }">
                      <span :class="row.status === '已完成' ? 'bg-green-50 text-green-600' : row.status === '部分完成' ? 'bg-orange-50 text-orange-600' : 'bg-red-50 text-red-600'"
                        class="px-3 py-1.5 rounded-full text-sm font-bold">{{ row.status }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="detail" label="详细说明" min-width="300" />
                </el-table>
              </div>
            </div>
            <div class="mb-12">
              <h3 class="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <span class="w-8 h-8 rounded-lg bg-red-100 text-red-600 flex items-center justify-center text-lg"><Icon icon="mdi:alert-outline" /></span>
                逻辑漏洞检测
              </h3>
              <div class="space-y-4" v-if="result.completeness.issues?.length">
                <div v-for="(issue, idx) in result.completeness.issues" :key="idx"
                  :class="issue.severity === '高' ? 'bg-red-50 border-red-200' : issue.severity === '中' ? 'bg-orange-50 border-orange-200' : 'bg-blue-50 border-blue-200'"
                  class="border rounded-2xl p-6">
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <p class="font-bold text-lg text-gray-900 mb-1">{{ issue.description }}</p>
                      <p class="text-sm text-gray-600">严重程度：{{ issue.severity }}</p>
                    </div>
                    <span :class="issue.severity === '高' ? 'bg-red-600' : issue.severity === '中' ? 'bg-orange-500' : 'bg-blue-500'"
                      class="px-3 py-1 rounded-full text-white text-xs font-bold">{{ issue.severity }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="bg-green-50 border border-green-200 rounded-2xl p-10 text-center">
                <div class="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                  <Icon icon="mdi:check-circle" class="text-3xl text-green-600" />
                </div>
                <p class="text-green-700 font-bold text-xl">未检测到逻辑漏洞</p>
              </div>
            </div>
            <div class="bg-gray-50 rounded-3xl p-8 border border-gray-100">
              <h3 class="text-2xl font-bold text-gray-900 mb-4"><Icon icon="mdi:text-box-check-outline" class="inline align-text-bottom" /> 核查总结</h3>
              <p class="text-gray-700 leading-relaxed text-lg">{{ result.completeness.summary || '无' }}</p>
            </div>
          </template>
          <div v-else class="py-20 text-center">
            <div class="text-gray-300 text-6xl mb-4"><Icon icon="mdi:email-open-outline" /></div>
            <p class="text-gray-500 text-xl">暂无智能核查数据</p>
          </div>
        </div>

        <!-- 三方对标Tab -->
        <div v-show="activeTab === 'tripartite'" class="animate-fade-in">
          <div v-if="tripartiteLoading" class="py-20 text-center text-surface-500">
            <Icon icon="mdi:loading" class="text-4xl animate-spin mb-3" />
            <p>正在加载三方对标数据...</p>
          </div>
          <template v-else-if="tripartiteData">
            <TripartiteCompare
              :parties="tripartiteData.parties"
              :dimensionBreakdown="tripartiteData.dimension_breakdown"
              :summary="tripartiteData.summary" />
          </template>
          <div v-else class="py-20 text-center card-mag !bg-paper-2/40">
            <div class="w-20 h-20 rounded-2xl bg-line/60 flex items-center justify-center mx-auto mb-5">
              <Icon icon="mdi:scale-balance" class="text-4xl text-ink-4" />
            </div>
            <p class="text-ink-3 text-base font-medium mb-2">暂无三方对标数据</p>
            <p class="text-ink-4 text-sm">当企业评价完成后，将自动展示 AI / 教师 / 企业三方评价差异分析。</p>
            <button v-if="result?.submission_id"
                    @click="loadTripartite(true)"
                    class="btn-mag btn-mag-primary mt-6 px-5 py-2.5 text-[13px]">
              <Icon icon="mdi:refresh" class="mr-1" /> 重新加载
            </button>
          </div>
        </div>

        <!-- 底部操作按钮 -->
        <div class="mt-12 flex flex-wrap justify-center gap-4">
          <el-button v-if="isStudent" type="primary" size="large" @click="$router.push('/app/student-tasks')"
            class="!rounded-xl !px-8 !py-3 !font-bold">
            返回任务列表
          </el-button>

          <template v-if="isTeacher">
            <el-button v-if="nextUnscoredId" type="primary" size="large" @click="goNextUnscored"
              class="!rounded-xl !px-8 !py-3 !font-bold">
              评价下一份（还剩 {{ unscoredCount }} 份）
            </el-button>
            <el-button v-else type="primary" size="large" @click="$router.push('/app/task-manage')"
              class="!rounded-xl !px-8 !py-3 !font-bold">
              返回任务管理
            </el-button>
          </template>

          <el-button type="success" size="large" @click="exportExcel"
            class="!rounded-xl !px-8 !py-3 !font-bold">
            <Icon icon="mdi:file-excel-outline" class="inline align-text-bottom" /> 导出 Excel
          </el-button>
          <el-button type="danger" size="large" @click="exportPdf"
            class="!rounded-xl !px-8 !py-3 !font-bold">
            <Icon icon="mdi:file-pdf-box" class="inline align-text-bottom" /> 导出 PDF
          </el-button>
        </div>
      </div>

      <div v-else class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-24 h-24 rounded-3xl bg-surface-50 flex items-center justify-center mx-auto mb-6 border border-surface-100">
            <Icon icon="mdi:file-document-off-outline" class="text-5xl text-surface-300" />
          </div>
          <p class="text-surface-500 text-lg font-medium mb-8">暂无评价结果</p>
          <button class="btn-primary text-white px-8 py-3 rounded-xl font-bold" @click="$router.push('/app/upload')">去上传评价</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'
import TripartiteCompare from '../components/common/TripartiteCompare.vue'

const router = useRouter()
const result = ref<any>(null)
const activeTab = ref('ai')
const isEditing = ref(false)
const saving = ref(false)
const teacherSaved = ref(false)
const teacherData = ref<any>({ scores: [], comment: '', total: 0 })

// 编辑模式下独立的数据
const editingScores = ref<Array<{name: string, score: number, reason: string}>>([])
const editingComment = ref('')

const unscoredCount = ref(0)
const nextUnscoredId = ref<number | null>(null)
const currentTaskId = ref<number | null>(null)

const conclusionText = computed(() => {
  const scores = result.value?.evaluation?.scores || []
  if (!scores.length) return '暂无评价结论'

  const max = scores.reduce((a: any, b: any) => a.score > b.score ? a : b)
  const min = scores.reduce((a: any, b: any) => a.score < b.score ? a : b)
  const total = displayScore.value

  if (total >= 80) return `表现优秀！${max.name}方面尤为突出，继续保持`
  if (total >= 60) return `整体良好，${max.name}是优势项，建议重点提升${min.name}`
  return `需要加强，特别是${min.name}方面，建议针对薄弱维度系统学习`
})

const studentInfo = reactive({
  name: '',
  number: '',
  class: ''
})

const tabList = [
  { label: 'AI 评分', value: 'ai' },
  { label: '教师评分', value: 'teacher' },
  { label: '智能核查', value: 'check' },
  { label: '三方对标', value: 'tripartite' }
]

// 三方对比
const tripartiteLoading = ref(false)
const tripartiteData = ref<any>(null)

const isStudent = computed(() => {
  try {
    const user = localStorage.getItem('user')
    if (user) return JSON.parse(user).role === 'student'
    return false
  } catch {
    return false
  }
})

const isTeacher = computed(() => {
  try {
    const user = localStorage.getItem('user')
    if (user) return JSON.parse(user).role === 'teacher'
    return false
  } catch {
    return false
  }
})

const studentName = computed(() => {
  return studentInfo.name || (() => {
    const user = localStorage.getItem('user')
    if (user) {
      try {
        return JSON.parse(user).real_name || '学生'
      } catch {
        return '学生'
      }
    }
    return '学生'
  })()
})

const displayScore = computed(() => {
  if (activeTab.value === 'teacher' && teacherSaved.value) {
    return teacherData.value.total
  }
  return result.value?.evaluation?.total || 0
})

const hasCompleteness = computed(() => {
  return result.value?.completeness?.steps?.length || result.value?.completeness?.issues?.length
})

const startEdit = () => {
  try {
    // 确定数据来源
    let sourceScores: any[] = []
    let sourceComment = ''
    
    if (teacherSaved.value) {
      sourceScores = teacherData.value.scores
      sourceComment = teacherData.value.comment
    } else if (result.value?.evaluation?.scores) {
      sourceScores = result.value.evaluation.scores
      sourceComment = result.value.evaluation.comment || ''
    }
    
    // 深拷贝一份，用于编辑
    editingScores.value = JSON.parse(JSON.stringify(sourceScores))
    editingComment.value = sourceComment
    isEditing.value = true
  } catch (err) {
    console.error('启动编辑失败', err)
    ElMessage.error('无法进入编辑模式')
  }
}

const cancelEdit = () => {
  editingScores.value = []
  editingComment.value = ''
  isEditing.value = false
}

const submitTeacherScore = async () => {
  if (!result.value?.submission_id) {
    ElMessage.warning('缺少提交ID')
    return
  }
  
  if (!editingScores.value.length) {
    ElMessage.warning('请先编辑评分内容')
    return
  }
  
  saving.value = true
  
  try {
    const cleanScores = editingScores.value.map(s => ({
      name: String(s.name),
      score: Number(s.score),
      reason: String(s.reason || '')
    }))
    
    const totalScore = Math.round(
      cleanScores.reduce((sum, s) => sum + s.score, 0) / cleanScores.length
    )
    
    const response = await axios.post(`${API_BASE}/api/teacher/score`, {
      submission_id: result.value.submission_id,
      scores: cleanScores,
      total_score: totalScore,
      comment: editingComment.value || '无'
    })
    
    if (response.data.success) {
      teacherData.value = {
        total: totalScore,
        scores: cleanScores,
        comment: editingComment.value
      }
      teacherSaved.value = true
      isEditing.value = false
      activeTab.value = 'teacher'
      ElMessage.success('教师评分已保存')

      // 更新未评数量
      const taskInfo = localStorage.getItem('current_task_info')
      if (taskInfo) {
        const info = JSON.parse(taskInfo)
        const subs = info.submissions || []
        const idx = subs.findIndex((s: any) => s.submission_id === result.value.submission_id)
        if (idx > -1) subs[idx].is_scored = true
        info.submissions = subs
        localStorage.setItem('current_task_info', JSON.stringify(info))
      }

      calcNextUnscored()
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (err: any) {
    console.error('保存评分异常', err)
    ElMessage.error('保存失败：' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

const calcNextUnscored = () => {
  try {
    const taskInfo = localStorage.getItem('current_task_info')
    if (!taskInfo) return
    const info = JSON.parse(taskInfo)
    currentTaskId.value = info.taskId
    const submissions = info.submissions || []
    const unscored = submissions.filter((s: any) => !s.is_scored)
    unscoredCount.value = unscored.length
    nextUnscoredId.value = unscored.length > 0 ? unscored[0].submission_id : null
  } catch (err) {
    console.error('计算未评数量失败', err)
  }
}

const goNextUnscored = async () => {
  if (!nextUnscoredId.value || !currentTaskId.value) {
    ElMessage.warning('没有待评价的作业')
    return
  }
  
  try {
    const res = await axios.get(`${API_BASE}/api/tasks/${currentTaskId.value}/detail`)
    if (res.data.success) {
      const detail = res.data.data
      const nextSub = detail.submissions.find((s: any) => s.submission_id === nextUnscoredId.value)
      if (nextSub) {
        const taskCriteria = detail.task?.criteria || '代码质量,功能完整性,文档规范性,界面设计'
        const names = taskCriteria.split(',').map((n: string) => n.trim())
        let aiScores = nextSub.ai_scores
        if (aiScores && Array.isArray(aiScores)) {
          aiScores = names.map((name: string) => {
            const found = aiScores.find((s: any) => s.name === name)
            return found || { name, score: Math.round(nextSub.ai_score || 60), reason: '' }
          })
        } else {
          const avgPer = Math.round((nextSub.ai_score || 60) / names.length)
          aiScores = names.map((name: string) => ({ name, score: Math.min(avgPer, 100), reason: '' }))
        }
        localStorage.setItem('eval_result', JSON.stringify({
          submission_id: nextSub.submission_id,
          student_name: nextSub.student_name || '',
          class_name: nextSub.class_name || '',
          evaluation: { total: nextSub.ai_score || 0, scores: aiScores, comment: nextSub.ai_comment || '' },
          completeness: { steps: nextSub.ai_steps || [], issues: nextSub.ai_issues || [], summary: nextSub.ai_comment || '' }
        }))
        window.location.reload()
      }
    } else {
      ElMessage.error('获取任务详情失败')
    }
  } catch (err: any) {
    console.error('跳转下一份失败', err)
    ElMessage.error('跳转失败：' + (err.response?.data?.detail || err.message))
  }
}

const exportExcel = async () => {
  try {
    const evaluation = (activeTab.value === 'teacher' && teacherSaved.value)
      ? { total: teacherData.value.total, scores: teacherData.value.scores, comment: teacherData.value.comment }
      : result.value.evaluation
    const res = await axios.post(`${API_BASE}/api/report/excel`, {
      task_requirements: '见实训要求',
      evaluation,
      student_name: studentName.value
    }, { responseType: 'blob' })
    
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `实训评价报告_${Date.now()}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('Excel 报告下载成功！')
  } catch (err: any) {
    console.error('导出Excel失败', err)
    ElMessage.error('导出失败：' + (err.message || '未知错误'))
  }
}

const exportPdf = async () => {
  try {
    const evaluation = (activeTab.value === 'teacher' && teacherSaved.value)
      ? { total: teacherData.value.total, scores: teacherData.value.scores, comment: teacherData.value.comment }
      : result.value.evaluation
    const res = await axios.post(`${API_BASE}/api/report/pdf`, {
      task_requirements: '见实训要求',
      evaluation,
      student_name: studentName.value
    }, { responseType: 'blob' })
    
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `实训评价报告_${Date.now()}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF 报告下载成功！')
  } catch (err: any) {
    console.error('导出PDF失败', err)
    ElMessage.error('导出失败：' + (err.message || '未知错误'))
  }
}

// 拉取三方对比数据
async function loadTripartite(force = false) {
  if (!result.value?.submission_id) return
  tripartiteLoading.value = true
  try {
    const token = localStorage.getItem('token') || ''
    const headers: any = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const { data } = await axios.get(
      `${API_BASE}/api/enterprise/evaluations/compare/${result.value.submission_id}`,
      { headers }
    )
    const payload = (data as any)?.data || (data as any)
    if (payload && (payload.parties || payload.summary)) {
      tripartiteData.value = payload
    } else if (!force) {
      tripartiteData.value = null
    }
  } catch (e: any) {
    if (force) {
      // 构造兜底 mock（演示用）
      const aiTotal = result.value?.evaluation?.total || 0
      const teacherTotal = teacherSaved.value ? teacherData.value.total : Math.min(100, aiTotal + Math.round((Math.random() - 0.4) * 10))
      const entTotal = Math.min(100, aiTotal + Math.round((Math.random() - 0.4) * 14))
      const baseDims: any[] = (result.value?.evaluation?.scores || []).map((s: any, i: number) => {
        const tScore = (teacherData.value.scores || [])[i]?.score ?? Math.min(100, s.score + Math.round((Math.random() - 0.4) * 10))
        const eScore = Math.min(100, s.score + Math.round((Math.random() - 0.4) * 14))
        return {
          name: s.name,
          ai_score: s.score,
          teacher_score: tScore,
          enterprise_score: eScore,
          max_diff: Math.max(Math.abs(s.score - tScore), Math.abs(s.score - eScore), Math.abs(tScore - eScore)),
          flag: 'ok' as any,
          warning: ''
        }
      })
      baseDims.forEach(d => {
        if (d.max_diff >= 20) d.flag = 'warning'
        else if (d.max_diff >= 10) d.flag = 'info'
        if (d.flag === 'warning') d.warning = `三方在【${d.name}】维度存在显著分歧（最大差 ${d.max_diff} 分），建议复核。`
      })
      const maxDiff = Math.max(...baseDims.map(d => d.max_diff), 0)
      const spread = Math.max(aiTotal, teacherTotal, entTotal) - Math.min(aiTotal, teacherTotal, entTotal)
      tripartiteData.value = {
        parties: [
          { role: 'ai', label: 'AI', total: aiTotal, comment: result.value?.evaluation?.comment || '' },
          { role: 'teacher', label: '教师', total: teacherTotal, comment: teacherData.value.comment || '' },
          { role: 'enterprise', label: '企业', total: entTotal, comment: '（演示数据）综合岗位匹配度评估' }
        ],
        dimension_breakdown: baseDims,
        summary: {
          score_spread: spread,
          consistency_index: Math.max(0.4, 1 - spread / 50),
          max_difference_dimension: baseDims.find((d: any) => d.max_diff === maxDiff)?.name || '',
          max_difference: maxDiff,
          needs_review: spread >= 12 || maxDiff >= 15
        }
      }
    }
  } finally {
    tripartiteLoading.value = false
  }
}

onMounted(async () => {
  try {
    const data = localStorage.getItem('eval_result')
    if (data) {
      const parsed = JSON.parse(data)
      result.value = parsed
      studentInfo.name = parsed.student_name || ''
      studentInfo.number = parsed.student_number || ''
      studentInfo.class = parsed.class_name || ''

      if (result.value.submission_id) {
        try {
          const res = await axios.get(`${API_BASE}/api/teacher/scores/${result.value.submission_id}`)
          if (res.data.success && res.data.data.teacher_score) {
            teacherData.value = {
              total: res.data.data.teacher_score.total_score,
              scores: res.data.data.teacher_score.dimension_scores,
              comment: res.data.data.teacher_score.comment
            }
            teacherSaved.value = true
          }
        } catch (err) {
          console.error('获取教师评分失败', err)
        }
        // 拉三方对比
        loadTripartite(false)
      }
    }

    if (isTeacher.value) {
      calcNextUnscored()
    }
  } catch (err) {
    console.error('初始化失败', err)
    ElMessage.error('加载数据失败')
  }
})
</script>

<style scoped>
.animate-fade-in { 
  animation: fadeIn 0.4s ease-out; 
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(10px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

:deep(.el-textarea__inner) { 
  border-radius: 0.75rem; 
  border-color: #e5e7eb; 
  font-size: 0.9375rem; 
  line-height: 1.6; 
}

:deep(.el-table) { 
  --el-table-header-text-color: #111827; 
  --el-table-row-hover-bg-color: #f9fafb; 
}

:deep(.el-table th) { 
  background-color: #f9fafb !important; 
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: center;
}
</style>