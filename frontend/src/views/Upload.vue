<template>
  <div class="page-enter">
    <div class="max-w-4xl mx-auto">
      <!-- 页面头部 -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight mb-2">
          {{ currentTask ? '提交作业：' + currentTask.title : '上传实训成果并评价' }}
        </h1>
        <p class="text-surface-500">
          {{ currentTask ? '请按要求提交你的实训成果，系统将自动进行AI评价' : '上传你的实训成果，AI将自动进行多维度智能评价' }}
        </p>
      </div>

      <!-- 主卡片 -->
      <div class="card overflow-hidden">
        <div class="p-8">
          <!-- 当前任务信息 -->
          <div v-if="currentTask" class="mb-8">
            <div class="bg-primary-50 border border-primary-100 rounded-2xl p-6">
              <div class="flex items-center gap-2 mb-2">
                <Icon icon="mdi:clipboard-text-outline" class="text-primary-500" />
                <h3 class="font-bold text-primary-800">{{ currentTask.title }}</h3>
              </div>
              <p class="text-primary-700 leading-relaxed text-sm">{{ currentTask.requirements }}</p>
            </div>
          </div>

          <el-form :model="form" label-width="120px" class="modern-form">
            <!-- 实训要求 -->
            <el-form-item label="实训要求">
              <el-input
                v-model="form.task_requirements"
                type="textarea"
                :rows="4"
                placeholder="请输入实训要求，作为AI评判依据..."
                :disabled="!!currentTask"
                class="modern-textarea"
              />
            </el-form-item>

            <!-- 评价维度 -->
            <el-form-item label="评价维度">
              <div class="flex flex-wrap gap-3">
                <span v-for="c in currentCriteria" :key="c"
                  class="px-4 py-2 bg-primary-50 text-primary-500 rounded-full text-sm font-medium">
                  {{ c }}
                </span>
              </div>
            </el-form-item>

            <!-- 文件上传 -->
            <el-form-item label="上传文件">
              <div class="border-2 border-dashed border-gray-200 rounded-xl p-8 hover:border-primary-300 hover:bg-primary-50 transition-all cursor-pointer">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  multiple
                  :on-change="handleFileChange"
                  :on-remove="handleRemove"
                  accept=".docx,.pdf,.png,.jpg,.jpeg"
                  drag
                  class="w-full"
                >
                  <div class="text-center">
                    <div class="w-16 h-16 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-4">
                      <Icon icon="mdi:cloud-upload" class="text-4xl text-primary-500" />
                    </div>
                    <div class="text-lg font-medium text-gray-700 mb-2">将文件拖到此处，或点击上传</div>
                    <div class="text-sm text-gray-400">
                      支持 .docx / .pdf  / .png / .jpg 格式，可上传多个文件
                    </div>
                  </div>
                </el-upload>
              </div>
              
              <!-- 已上传文件列表 -->
              <div v-if="files.length > 0" class="mt-4 space-y-2">
                <div v-for="f in files" :key="f.uid"
                  class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Icon icon="mdi:file-document" class="text-blue-500" />
                    </div>
                    <span class="text-gray-700 font-medium">{{ f.name }}</span>
                  </div>
                  <button class="p-1.5 hover:bg-red-50 rounded-lg transition-colors" @click="handleRemove(f)">
                    <Icon icon="mdi:close" class="text-red-500" />
                  </button>
                </div>
              </div>
            </el-form-item>

            <!-- 提交按钮 -->
            <el-form-item class="pt-4">
              <button
                type="button"
                class="w-full btn-primary text-white font-semibold py-4 rounded-xl text-lg flex items-center justify-center gap-2"
                @click="submitEvaluate"
                :disabled="files.length === 0 || loading"
              >
                <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <Icon v-else icon="mdi:magic-staff" class="text-xl" />
                <span>{{ loading ? 'AI 正在评价中...' : currentTask ? '提交作业并评价' : '开始智能评价' }}</span>
              </button>
            </el-form-item>
          </el-form>
          <!-- 加载动画 - 步骤式 -->
<div v-if="loading" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
  <div class="bg-white rounded-3xl p-10 w-full max-w-md mx-4 shadow-2xl animate-scale-in">
    <div class="text-center mb-8">
      <div class="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-4">
        <Icon icon="mdi:robot-outline" class="text-4xl text-primary-500" />
      </div>
      <h3 class="text-xl font-bold text-surface-800">AI 正在处理</h3>
      <p class="text-surface-500 text-sm mt-1">请耐心等待，这可能需要几秒钟</p>
    </div>

    <div class="space-y-3">
      <div class="flex items-center gap-4 p-4 rounded-2xl transition-colors duration-300" :class="step >= 1 ? 'bg-success-50' : 'bg-surface-50'">
        <div class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300" :class="step >= 1 ? 'bg-success-500 shadow-lg shadow-success-500/20' : 'bg-surface-300'">
          <Icon v-if="step > 1" icon="mdi:check" class="text-white text-xl" />
          <span v-else class="text-white font-bold text-sm">1</span>
        </div>
        <div>
          <div class="font-semibold text-sm" :class="step >= 1 ? 'text-success-700' : 'text-surface-500'">正在解析文档</div>
          <div class="text-xs" :class="step >= 1 ? 'text-success-500' : 'text-surface-400'">提取文本内容...</div>
        </div>
      </div>

      <div class="flex items-center gap-4 p-4 rounded-2xl transition-colors duration-300" :class="step >= 2 ? 'bg-primary-50' : 'bg-surface-50'">
        <div class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300" :class="step >= 2 ? 'bg-primary-500 shadow-lg shadow-primary-500/20' : 'bg-surface-300'">
          <Icon v-if="step > 2" icon="mdi:check" class="text-white text-xl" />
          <span v-else class="text-white font-bold text-sm">2</span>
        </div>
        <div>
          <div class="font-semibold text-sm" :class="step >= 2 ? 'text-primary-700' : 'text-surface-500'">AI 智能评分</div>
          <div class="text-xs" :class="step >= 2 ? 'text-primary-500' : 'text-surface-400'">多维度分析评价...</div>
        </div>
      </div>

      <div class="flex items-center gap-4 p-4 rounded-2xl transition-colors duration-300" :class="step >= 3 ? 'bg-violet-50' : 'bg-surface-50'">
        <div class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300" :class="step >= 3 ? 'bg-violet-500 shadow-lg shadow-violet-500/20' : 'bg-surface-300'">
          <span v-if="step < 3" class="text-white font-bold text-sm">3</span>
          <Icon v-else icon="mdi:check" class="text-white text-xl" />
        </div>
        <div>
          <div class="font-semibold text-sm" :class="step >= 3 ? 'text-violet-700' : 'text-surface-500'">生成评价报告</div>
          <div class="text-xs" :class="step >= 3 ? 'text-violet-500' : 'text-surface-400'">即将跳转结果页...</div>
        </div>
      </div>
    </div>
  </div>
</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 【完全保留你原有的所有业务逻辑，一个字都没改！】
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { MagicStick, Loading, UploadFilled } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const loading = ref(false)
const files = ref<any[]>([])
const currentTask = ref<any>(null)

const form = reactive({
  task_requirements: '实训任务：实现登录模块，包含用户名密码输入框、登录按钮。要求：输入为空时提示用户、密码掩码显示、验证成功跳转主页、验证失败提示错误、代码有注释、界面美观。',
  task_id: 0
})

const currentCriteria = computed(() => {
  const taskCriteria = localStorage.getItem('current_task_criteria')
  if (taskCriteria) {
    return taskCriteria.split(',').map((c: string) => c.trim())
  }
  const saved = localStorage.getItem('criteria_config')
  if (saved) {
    return JSON.parse(saved).map((c: any) => c.name)
  }
  return ['代码质量', '功能完整性', '文档规范性', '界面设计']
})

onMounted(() => {
  const taskData = localStorage.getItem('current_task')
  if (taskData) {
    const task = JSON.parse(taskData)
    currentTask.value = task
    form.task_requirements = task.requirements
    form.task_id = task.id
    if (task.criteria) {
      localStorage.setItem('current_task_criteria', task.criteria)
    }
  }
})

const handleFileChange = (uploadFile: any) => {
  files.value.push(uploadFile)
}

const handleRemove = (uploadFile: any) => {
  const idx = files.value.findIndex((f: any) => f.uid === uploadFile.uid)
  if (idx > -1) files.value.splice(idx, 1)
}

import { ElMessageBox } from 'element-plus'

const step = ref(0)

const submitEvaluate = async () => {
  if (files.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }

  // 确认弹窗
  try {
    const saved = localStorage.getItem('criteria_config')
    const criteriaNames = saved
      ? JSON.parse(saved).map((c: any) => c.name).join(',')
      : '代码质量,功能完整性,文档规范性,界面设计'

    await ElMessageBox.confirm(
      `文件：${files.value.map(f => f.name).join(', ')}\n\n实训要求：${form.task_requirements.substring(0, 60)}...\n\n评价维度：${criteriaNames}\n\n提交后AI将自动评分，确认无误？`,
      '确认提交',
      { confirmButtonText: '确认提交', cancelButtonText: '取消', type: 'info' }
    )
  } catch {
    return
  }

  loading.value = true
  step.value = 1

  const saved = localStorage.getItem('criteria_config')
  const criteriaNames = saved
    ? JSON.parse(saved).map((c: any) => c.name).join(',')
    : '代码质量,功能完整性,文档规范性,界面设计'

  const formData = new FormData()
  files.value.forEach((f: any) => {
    formData.append('files', f.raw)
  })
  formData.append('task_requirements', form.task_requirements)
  formData.append('criteria', criteriaNames)

  const user = JSON.parse(localStorage.getItem('user') || '{}')
  formData.append('student_id', String(user.id || 0))

  if (form.task_id > 0) {
    formData.append('task_id', String(form.task_id))
  }

  // 模拟步骤1→2
  setTimeout(() => { step.value = 2 }, 1000)

  try {
    const res = await axios.post(`${API_BASE}/api/upload-eval/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    // 标记步骤3完成
    step.value = 3

    // 停留1.5秒让用户看到所有步骤变绿
    await new Promise(resolve => setTimeout(resolve, 1500))

    if (res.data.success) {
      localStorage.setItem('eval_result', JSON.stringify(res.data))
      localStorage.removeItem('current_task')
      localStorage.removeItem('current_task_criteria')
      ElMessage.success(currentTask.value ? '作业提交成功！' : '评价完成！')
      router.replace('/app/result/latest')
    } else {
      ElMessage.error(res.data.error || '评价失败')
    }
  } catch (err: any) {
    ElMessage.error('请求失败：' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 只保留必要的样式，其他全用Tailwind CSS */
.modern-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
}
.modern-textarea :deep(.el-textarea__inner) {
  border-radius: 0.75rem;
  border-color: #e5e7eb;
}
</style>