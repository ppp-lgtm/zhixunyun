<template>
  <div class="page-enter">
    <div class="max-w-5xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 class="text-3xl font-bold text-surface-800 tracking-tight">评价标准配置</h1>
          <p class="text-surface-500 mt-1">自定义实训评价的维度与权重</p>
        </div>
        <div class="flex gap-3">
          <button class="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
            @click="$router.push('/')">
            <Icon icon="mdi:arrow-left" />
            返回首页
          </button>
        </div>
      </div>

      <!-- 主卡片 -->
      <div class="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden">
        <!-- 卡片头部 -->
        <div class="p-8 border-b border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h3 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                <Icon icon="mdi:tune" class="text-xl text-primary-500" />
              </span>
              自定义评价维度与权重
            </h3>
            <p class="text-gray-500 mt-1">配置各评价维度的名称、权重和评分说明</p>
          </div>
          <button class="bg-gradient-to-r from-primary-500 to-indigo-600 text-white px-8 py-3 rounded-xl font-bold text-lg hover:shadow-lg hover:shadow-primary-500/30 transition-all flex items-center gap-2"
            @click="addRow">
            <Icon icon="mdi:plus" />
            添加维度
          </button>
        </div>

        <!-- 维度列表（卡片式，更大胆） -->
        <div class="p-8 space-y-6">
          <div
            v-for="(item, index) in form.criteria"
            :key="index"
            class="bg-gray-50 rounded-2xl p-6 border border-gray-100 hover:border-primary-200 hover:shadow-md transition-all duration-300"
          >
            <div class="flex flex-col lg:flex-row gap-6">
              <!-- 维度名称 -->
              <div class="flex-1 min-w-[200px]">
                <label class="block text-sm font-bold text-gray-700 mb-2">维度名称</label>
                <el-input v-model="item.name" placeholder="如：代码质量" size="large" class="modern-input" />
              </div>

              <!-- 权重 -->
              <div class="w-full lg:w-48">
                <label class="block text-sm font-bold text-gray-700 mb-2">权重(%)</label>
                <el-input-number v-model="item.weight" :min="1" :max="100" size="large" class="w-full modern-input-number" />
              </div>

              <!-- 删除按钮 -->
              <div class="flex items-end">
                <button class="w-12 h-12 bg-red-50 text-red-500 rounded-xl hover:bg-red-100 transition-colors flex items-center justify-center"
                  @click="removeRow(index)">
                  <Icon icon="mdi:delete" class="text-xl" />
                </button>
              </div>
            </div>

            <!-- 评分说明（全宽） -->
            <div class="mt-4">
              <label class="block text-sm font-bold text-gray-700 mb-2">评分说明</label>
              <el-input v-model="item.description" type="textarea" :rows="2" placeholder="描述该维度的评分标准" class="modern-textarea" />
            </div>
          </div>
        </div>

        <!-- 权重提示 -->
        <div class="px-8 pb-6">
          <div v-if="totalWeight !== 100" 
            class="bg-orange-50 border border-orange-200 rounded-2xl p-6 flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-orange-100 flex items-center justify-center flex-shrink-0">
              <Icon icon="mdi:alert-outline" class="text-2xl text-orange-500" />
            </div>
            <div>
              <p class="text-orange-700 font-bold text-lg">当前权重合计 {{ totalWeight }}%</p>
              <p class="text-orange-600">建议调整为 100% 以确保评分准确</p>
            </div>
          </div>
          <div v-else 
            class="bg-green-50 border border-green-200 rounded-2xl p-6 flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0">
              <Icon icon="mdi:check-circle" class="text-2xl text-green-500" />
            </div>
            <div>
              <p class="text-green-700 font-bold text-lg">权重合计 100%</p>
              <p class="text-green-600">权重配置正确，可以保存</p>
            </div>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="px-8 pb-8 border-t border-gray-100 pt-8 flex justify-center gap-4">
          <button class="px-8 py-3 border border-gray-200 text-gray-700 rounded-xl font-bold text-lg hover:bg-gray-50 transition-colors"
            @click="loadDefault">
            恢复默认
          </button>
          <button class="px-8 py-3 bg-gradient-to-r from-primary-500 to-indigo-600 text-white rounded-xl font-bold text-lg hover:shadow-lg hover:shadow-primary-500/30 transition-all"
            @click="saveCriteria" :disabled="saving">
            <span v-if="saving" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
            保存标准
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 【完全保留你原有的所有业务逻辑，一行未改！只做视觉升级】
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const saving = ref(false)

const defaultCriteria = [
  { name: '代码质量', weight: 25, description: '代码结构、命名规范、注释完整性' },
  { name: '功能完整性', weight: 35, description: '是否完整实现所有实训要求的功能' },
  { name: '文档规范性', weight: 20, description: '实训报告的完整性、格式规范性' },
  { name: '界面设计', weight: 20, description: 'UI美观度、交互体验、响应式设计' }
]

const form = reactive({
  criteria: [] as { name: string; weight: number; description: string }[]
})

const totalWeight = computed(() => {
  return form.criteria.reduce((sum, item) => sum + item.weight, 0)
})

onMounted(async () => {
  try {
    const taskId = localStorage.getItem('current_task_id') || '1'
    const res = await api.get(`/api/criteria/${taskId}`)
    if (res.data.success && res.data.data.length > 0) {
      form.criteria = res.data.data.map((c: any) => ({
        name: c.name,
        weight: c.weight,
        description: c.description
      }))
    } else {
      loadDefault()
    }
  } catch {
    loadDefault()
  }
})

const addRow = () => {
  form.criteria.push({ name: '', weight: 10, description: '' })
}

const removeRow = (index: number) => {
  form.criteria.splice(index, 1)
}

const loadDefault = () => {
  form.criteria = JSON.parse(JSON.stringify(defaultCriteria))
}

const saveCriteria = async () => {
  if (form.criteria.some(c => !c.name.trim())) {
    ElMessage.warning('请填写所有维度名称')
    return
  }

  saving.value = true
  try {
    const taskId = localStorage.getItem('current_task_id') || '1'
    await api.post(`/api/criteria/batch/${taskId}`, form.criteria)

    localStorage.setItem('criteria_config', JSON.stringify(form.criteria))

    ElMessage.success('评价标准已保存')

  } catch (err: any) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* 表单样式优化 */
.modern-input :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}
.modern-input :deep(.el-input__wrapper):hover {
  border-color: #165DFF;
}
.modern-input :deep(.el-input__wrapper.is-focus) {
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}

.modern-input-number :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}
.modern-input-number :deep(.el-input__wrapper):hover {
  border-color: #165DFF;
}
.modern-input-number :deep(.el-input__wrapper.is-focus) {
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}

.modern-textarea :deep(.el-textarea__inner) {
  border-radius: 0.75rem;
  border-color: #e5e7eb;
  transition: all 0.3s;
  font-size: 0.9375rem;
  line-height: 1.6;
}
.modern-textarea :deep(.el-textarea__inner):hover {
  border-color: #165DFF;
}
.modern-textarea :deep(.el-textarea__inner):focus {
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}
</style>