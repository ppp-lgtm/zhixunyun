<template>
  <div class="page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 页面头部 -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-bold text-surface-800 tracking-tight">实训任务管理</h1>
          <p class="text-surface-500 mt-1">发布、管理实训任务，查看学生提交情况</p>
        </div>
        <button class="btn-primary text-white px-5 py-3 rounded-xl font-semibold flex items-center gap-2" @click="openCreate">
          <Icon icon="mdi:plus" class="text-lg" />
          <span>发布新任务</span>
        </button>
      </div>

      <!-- 任务列表卡片 -->
      <div class="card overflow-hidden">
        <div class="px-8 py-5 border-b border-surface-100">
          <span class="text-lg font-bold text-surface-800">任务列表</span>
        </div>
        
        <div class="overflow-x-auto">
          <el-table :data="tasks" border stripe v-loading="loading" style="width: 100%" class="modern-table">
            <el-table-column prop="title" label="任务标题" min-width="200">
              <template #default="{ row }">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                    <Icon icon="mdi:file-document" class="text-primary-500" />
                  </div>
                  <div class="font-medium text-gray-800">{{ row.title }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="requirements" label="实训要求" min-width="300" show-overflow-tooltip />
            <el-table-column label="截止时间" width="160">
              <template #default="{ row }">
                <div class="text-sm text-gray-600">{{ row.deadline?.split('T')[0] || '不限' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="模板" width="100">
              <template #default="{ row }">
                <span v-if="row.template_path" class="px-3 py-1 bg-green-50 text-green-500 text-xs font-medium rounded-full">有</span>
                <span v-else class="text-gray-400">无</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <div class="flex items-center gap-2">
                  <button class="px-4 py-2 bg-primary-50 text-primary-500 rounded-lg text-sm font-medium hover:bg-primary-100 transition-colors" @click="viewDetail(row)">
                    查看提交
                  </button>
                  <button class="px-4 py-2 bg-red-50 text-red-500 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors" @click="deleteTask(row.id)">
                    删除
                  </button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-if="!loading && tasks.length === 0" class="py-20 text-center">
          <div class="w-20 h-20 rounded-full bg-surface-50 flex items-center justify-center mx-auto mb-5">
            <Icon icon="mdi:clipboard-text-outline" class="text-4xl text-surface-300" />
          </div>
          <div class="text-surface-500 font-medium">暂无任务，点击上方按钮发布第一个任务</div>
        </div>
      </div>
    </div>

    <!-- 发布任务弹窗 -->
    <el-dialog v-model="showCreate" :title="generated ? '完善任务信息' : '发布实训任务'" width="750px" class="modern-dialog">
      <div v-if="!generated" class="py-4">
        <el-form label-width="100px">
          <el-form-item label="任务标题" required>
            <el-input v-model="form.title" placeholder="如：登录页面开发" size="large" />
          </el-form-item>
          <el-form-item label="任务难度" required>
            <el-radio-group v-model="form.difficulty">
              <el-radio-button value="简单">简单</el-radio-button>
              <el-radio-button value="普通">普通</el-radio-button>
              <el-radio-button value="困难">困难</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>

        <div class="text-center my-8">
          <button class="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-10 py-4 rounded-xl text-lg font-medium flex items-center gap-2 mx-auto hover:shadow-lg transition-all" 
            @click="aiGenerate" :disabled="!form.title || generating">
            <span v-if="generating" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <Icon icon="mdi:robot-outline" class="inline align-text-bottom" /> AI 生成实训要求
          </button>
          <p v-if="!form.title" class="text-orange-500 text-sm mt-3">请先输入任务标题</p>
        </div>
      </div>

      <div v-if="generated" class="py-4">
        <el-form :model="form" label-width="100px">
          <el-form-item label="任务标题">
            <el-input v-model="form.title" size="large" />
          </el-form-item>

          <el-form-item label="实训要求" required>
            <el-input v-model="form.requirements" type="textarea" :rows="4" />
          </el-form-item>

          <el-form-item label="评分维度">
            <div class="border border-gray-200 rounded-xl overflow-hidden">
              <el-table :data="criteriaList" border style="width: 100%" class="modern-table">
                <el-table-column label="维度名称" min-width="200">
                  <template #default="{ row }">
                    <el-input v-model="row.name" size="small" placeholder="请输入维度名称" />
                  </template>
                </el-table-column>
                <el-table-column label="权重(%)" width="140">
                  <template #default="{ row }">
                    <el-input-number v-model="row.weight" :min="1" :max="100" size="small" class="w-full" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ $index }">
                    <button class="p-2 bg-red-50 text-red-500 rounded-lg hover:bg-red-100 transition-colors" @click="criteriaList.splice($index, 1)">
                      <Icon icon="mdi:delete" />
                    </button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div class="mt-4 flex items-center gap-4">
              <button class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors flex items-center gap-2" 
                @click="criteriaList.push({ name: '', weight: 10 })">
                <Icon icon="mdi:plus" />
                <span>添加维度</span>
              </button>
              <span :class="totalWeight === 100 ? 'text-green-500' : 'text-orange-500'" class="text-sm font-medium">
                权重合计 {{ totalWeight }}%
              </span>
            </div>
          </el-form-item>

          <el-form-item label="成果物模板">
            <el-input v-model="form.template_content" type="textarea" :rows="6"
              placeholder="AI生成或手动填写模板内容，将生成Word文件供学生下载..." />
            <p class="text-gray-400 text-xs mt-2">
              模板将生成Word文件供学生下载，学生按模板结构提交成果物，评分更精准
            </p>
          </el-form-item>

          <div class="grid grid-cols-2 gap-6">
            <el-form-item label="关联班级">
              <el-select v-model="form.class_ids" placeholder="请选择班级" multiple clearable class="w-full">
                <el-option v-for="c in myClasses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="满分">
              <el-input-number v-model="form.total_score" :min="1" :max="100" size="large" class="w-full" />
            </el-form-item>
          </div>
          <el-form-item label="截止时间">
            <el-date-picker v-model="form.deadline" type="datetime" placeholder="不限" class="w-full" value-format="YYYY-MM-DD HH:mm" />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-3">
          <button class="px-6 py-2.5 border border-gray-200 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors" @click="showCreate = false">
            取消
          </button>
          <button v-if="!generated" class="px-6 py-2.5 border border-gray-200 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors" @click="manualInput">
            跳过AI，手动填写
          </button>
          <button v-if="generated" class="btn-primary text-white px-6 py-2.5 rounded-xl text-sm font-medium" @click="createTask" :disabled="saving">
            <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
            <span>{{ saving ? '发布中...' : '发布' }}</span>
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 提交详情弹窗 -->
    <el-dialog v-model="showDetail" :title="detailTask ? '提交详情 - ' + detailTask.task?.title : ''" width="1000px" class="modern-dialog">
      <div v-if="detailTask" class="py-4">
        <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-6">
          <p class="text-blue-800">{{ detailTask.task?.requirements }}</p>
        </div>

        <!-- 一键评分按钮 -->
        <div v-if="detailTask.submissions?.length > 0" class="flex items-center justify-between mb-4">
          <span class="text-sm text-gray-500">
            共 {{ detailTask.submissions.length }} 人提交，{{ detailTask.submissions.filter((s: any) => !s.is_scored).length }} 人待评分
          </span>
          <button 
            v-if="detailTask.submissions.some((s: any) => !s.is_scored)"
            class="px-5 py-2.5 bg-orange-500 text-white rounded-xl font-bold text-sm hover:bg-orange-600 transition-colors flex items-center gap-2"
            @click="startBatchScore">
             教师评分（还剩 {{ detailTask.submissions.filter((s: any) => !s.is_scored).length }} 人）
          </button>
        </div>

        <div class="border border-gray-200 rounded-xl overflow-hidden">
          <el-table :data="detailTask.submissions" border stripe class="modern-table">
            <el-table-column prop="student_name" label="学生" width="120" />
            <el-table-column label="关联班级" width="160">
              <template #default="{ row }">
                <span class="text-gray-700">{{ row.class_name || '不限' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="文件名" min-width="200">
              <template #default="{ row }">
                <button class="text-primary-500 hover:text-primary-600 font-medium flex items-center gap-1" @click="downloadFile(row.submission_id)">
                  <Icon icon="mdi:download" />
                  <span>{{ row.filename }}</span>
                </button>
              </template>
            </el-table-column>
            
            <el-table-column prop="submitted_at" label="提交时间" width="170" />
            <el-table-column label="AI评分" width="110">
              <template #default="{ row }">
                <span v-if="row.ai_score" 
                  :class="row.ai_score >= 80 ? 'bg-green-50 text-green-500' : row.ai_score >= 60 ? 'bg-orange-50 text-orange-500' : 'bg-red-50 text-red-500'"
                  class="px-3 py-1 rounded-full text-xs font-medium">
                  {{ row.ai_score }}分
                </span>
                <span v-else class="text-gray-400">未评</span>
              </template>
            </el-table-column>
            <el-table-column label="教师评分" width="110">
              <template #default="{ row }">
                <span v-if="row.teacher_score" class="px-3 py-1 bg-orange-50 text-orange-500 rounded-full text-xs font-medium">
                  {{ row.teacher_score }}分
                </span>
                <span v-else class="text-gray-400">未评</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="130">
              <template #default="{ row }">
                <button v-if="row.submission_id" 
                  class="px-4 py-2 bg-orange-50 text-orange-500 rounded-lg text-sm font-medium hover:bg-orange-100 transition-colors" 
                  @click="goScore(row)">
                  {{ row.teacher_score ? '修改评分' : '教师评分' }}
                </button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-if="!detailTask.submissions?.length" class="py-16 text-center">
          <div class="text-gray-400 text-6xl mb-4"><Icon icon="mdi:email-open-outline" /></div>
          <div class="text-gray-500">暂无学生提交</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const generated = ref(false)
const tasks = ref<any[]>([])
const myClasses = ref<any[]>([])
const showCreate = ref(false)
const showDetail = ref(false)
const detailTask = ref<any>(null)
const criteriaList = ref<{ name: string; weight: number }[]>([])

const form = reactive({
  title: '',
  difficulty: '普通',
  requirements: '',
  template_content: '',
  class_ids: [] as number[],
  total_score: 100,
  deadline: '',
  teacher_id: 0
})

const totalWeight = computed(() => criteriaList.value.reduce((sum, c) => sum + c.weight, 0))

onMounted(() => {
  loadTasks()
  loadClasses()
})

const openCreate = () => {
  form.title = ''
  form.difficulty = '普通'
  form.requirements = ''
  form.template_content = ''
  form.class_ids = []
  form.total_score = 100
  form.deadline = ''
  criteriaList.value = []
  generated.value = false
  showCreate.value = true
}

const aiGenerate = async () => {
  if (!form.title) { ElMessage.warning('请输入任务标题'); return }
  generating.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/tasks/generate`, {
      title: form.title,
      difficulty: form.difficulty
    })
    if (res.data.success) {
      form.requirements = res.data.data.requirements
      form.template_content = res.data.data.template || ''
      criteriaList.value = res.data.data.criteria.map((c: any) => ({
        name: c.name,
        weight: c.weight
      }))
      generated.value = true
      ElMessage.success('AI 已生成实训要求，你可以直接修改')
    } else {
      ElMessage.error('AI 生成失败，请重试')
    }
  } catch {
    ElMessage.error('请求失败')
  } finally { generating.value = false }
}

const manualInput = () => {
  const saved = localStorage.getItem('criteria_config')
  if (saved) {
    criteriaList.value = JSON.parse(saved).map((c: any) => ({ name: c.name, weight: c.weight }))
  } else {
    criteriaList.value = [
      { name: '代码质量', weight: 25 },
      { name: '功能完整性', weight: 25 },
      { name: '文档规范性', weight: 25 },
      { name: '界面设计', weight: 25 }
    ]
  }
  generated.value = true
}

const loadTasks = async () => {
  loading.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/tasks/my?teacher_id=${user.id}`)
    if (res.data.success) tasks.value = res.data.data
  } catch {} finally { loading.value = false }
}

const loadClasses = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/classes/?teacher_id=${user.id}`)
    if (res.data.success) myClasses.value = res.data.data
  } catch {}
}

const createTask = async () => {
  if (!form.title || !form.requirements) {
    ElMessage.warning('请填写任务标题和实训要求')
    return
  }
  if (criteriaList.value.some(c => !c.name.trim())) {
    ElMessage.warning('请填写所有维度名称')
    return
  }
  saving.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const names = criteriaList.value.map(c => c.name.trim()).join(',')
    const weights = criteriaList.value.map(c => c.weight).join(',')
    await axios.post(`${API_BASE}/api/tasks/`, {
      title: form.title,
      requirements: form.requirements,
      criteria: names,
      criteria_weights: weights,
      template_content: form.template_content,
      class_id: form.class_ids.join(','),
      total_score: form.total_score,
      deadline: form.deadline || null,
      teacher_id: user.id
    })
    ElMessage.success('任务已发布')
    showCreate.value = false
    loadTasks()
  } catch {} finally { saving.value = false }
}

const viewDetail = async (row: any) => {
  try {
    const res = await axios.get(`${API_BASE}/api/tasks/${row.id}/detail`)
    if (res.data.success) {
      detailTask.value = res.data.data
      showDetail.value = true
    }
  } catch {}
}

const downloadFile = (submissionId: number) => {
  window.open(`${API_BASE}/api/tasks/download/${submissionId}`, '_blank')
}

const goScore = (row: any) => {
  const taskCriteria = detailTask.value?.task?.criteria || '代码质量,功能完整性,文档规范性,界面设计'
  const names = taskCriteria.split(',').map((n: string) => n.trim())
  let aiScores = row.ai_scores
  if (aiScores && Array.isArray(aiScores) && aiScores.length > 0) {
    const defaultScores = names.map((name: string) => {
      const found = aiScores.find((s: any) => s.name === name)
      return found || { name, score: Math.round(row.ai_score || 60), reason: '' }
    })
    aiScores = defaultScores
  } else {
    const avgPer = Math.round((row.ai_score || 60) / names.length)
    aiScores = names.map((name: string) => ({ name, score: Math.min(avgPer, 100), reason: '' }))
  }

  // 存任务信息
  localStorage.setItem('current_task_info', JSON.stringify({
    taskId: detailTask.value?.task?.id,
    submissions: detailTask.value?.submissions || []
  }))

  localStorage.setItem('eval_result', JSON.stringify({
    submission_id: row.submission_id,
    student_name: row.student_name || '未知',
    class_name: row.class_name || '不限',
    student_number: row.student_number || '',
    evaluation: { total: row.ai_score || 0, scores: aiScores, comment: row.ai_comment || '' },
    completeness: { steps: row.ai_steps || [], issues: row.ai_issues || [], summary: row.ai_comment || '' }
  }))
  router.push('/app/result/latest')
}

const startBatchScore = () => {
  if (!detailTask.value) return
  const unscored = detailTask.value.submissions.find((s: any) => !s.is_scored)
  if (!unscored) {
    ElMessage.info('所有学生已评分完成')
    return
  }
  goScore(unscored)
}

const deleteTask = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该任务？', '提示', { type: 'warning' })
    await axios.delete(`${API_BASE}/api/tasks/${id}`)
    ElMessage.success('任务已删除')
    loadTasks()
  } catch {}
}
</script>

<style scoped>
.modern-table :deep(.el-table__header-wrapper th) {
  background-color: #f9fafb;
  color: #374151;
  font-weight: 600;
}
.modern-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #f3f4f6;
  padding-bottom: 20px;
  margin-bottom: 0;
}
</style>