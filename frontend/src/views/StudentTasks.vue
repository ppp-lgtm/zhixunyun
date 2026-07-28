<template>
  <div class="page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">实训任务</h1>
        <p class="text-surface-500 mt-1">点击下方卡片切换查看不同状态的任务</p>
      </div>

      <!-- 顶部数据看板（可点击切换筛选） -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10" v-if="!loading && tasks.length > 0">

        <!-- 总任务数 -->
        <div
          @click="activeFilter = 'all'"
          class="cursor-pointer bg-gradient-to-br from-primary-500 to-indigo-600 rounded-3xl p-8 text-white shadow-xl transition-all duration-300"
          :class="activeFilter === 'all' ? 'shadow-2xl scale-[1.02] ring-4 ring-primary-200' : 'hover:shadow-2xl hover:-translate-y-1'"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
              <Icon icon="mdi:format-list-bulleted" class="text-2xl" />
            </div>
            <span class="text-white/80 text-sm font-medium">总任务</span>
          </div>
          <div class="text-5xl font-black mb-1">{{ tasks.length }}</div>
          <div class="text-white/70 text-sm">项任务</div>
        </div>
        
        <!-- 待提交数 -->
        <div
          @click="activeFilter = 'pending'"
          class="cursor-pointer bg-gradient-to-br from-orange-500 to-amber-600 rounded-3xl p-8 text-white shadow-xl transition-all duration-300"
          :class="activeFilter === 'pending' ? 'shadow-2xl scale-[1.02] ring-4 ring-orange-200' : 'hover:shadow-2xl hover:-translate-y-1'"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
              <Icon icon="mdi:clock-outline" class="text-2xl" />
            </div>
            <span class="text-white/80 text-sm font-medium">待提交</span>
          </div>
          <div class="text-5xl font-black mb-1">{{ tasks.filter(t => !t.submitted).length }}</div>
          <div class="text-white/70 text-sm">项任务</div>
        </div>

        <!-- 已提交数 -->
        <div
          @click="activeFilter = 'submitted'"
          class="cursor-pointer bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-8 text-white shadow-xl transition-all duration-300"
          :class="activeFilter === 'submitted' ? 'shadow-2xl scale-[1.02] ring-4 ring-green-200' : 'hover:shadow-2xl hover:-translate-y-1'"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
              <Icon icon="mdi:check-circle-outline" class="text-2xl" />
            </div>
            <span class="text-white/80 text-sm font-medium">已提交</span>
          </div>
          <div class="text-5xl font-black mb-1">{{ tasks.filter(t => t.submitted).length }}</div>
          <div class="text-white/70 text-sm">项任务</div>
        </div>

        
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-12 h-12 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-gray-500">加载中...</p>
        </div>
      </div>

      <!-- 有数据时（渲染筛选后的列表） -->
      <div v-else-if="filteredTasks.length > 0">
        <!-- 任务列表 -->
        <div class="space-y-6">
          <div
            v-for="task in filteredTasks"
            :key="task.id"
            class="bg-white rounded-3xl border border-gray-100 shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
          >
            <div class="p-8">
              <div class="flex flex-col md:flex-row md:items-start justify-between gap-6">
                <!-- 左侧：任务信息 -->
                <div class="flex-1">
                  <div class="flex items-center gap-4 mb-4">
                    <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-white text-2xl">
                      <Icon icon="mdi:file-document" />
                    </div>
                    <div>
                      <h3 class="text-2xl font-bold text-gray-900 mb-1">{{ task.title }}</h3>
                      <div class="flex items-center gap-3 flex-wrap">
                        <span :class="task.submitted ? 'bg-green-50 text-green-600' : 'bg-orange-50 text-orange-600'"
                          class="px-3 py-1.5 rounded-full text-sm font-bold">
                          {{ task.submitted ? '已提交' : '待提交' }}
                        </span>
                        <span v-if="task.deadline" class="text-gray-500 text-sm flex items-center gap-1">
                          <Icon icon="mdi:calendar" />
                          截止：{{ task.deadline?.split('T')[0] }}
                        </span>
                        <span class="text-gray-500 text-sm flex items-center gap-1">
                          <Icon icon="mdi:star" />
                          满分：{{ task.total_score }}分
                        </span>
                      </div>
                    </div>
                  </div>

                  <p class="text-gray-600 leading-relaxed mb-6">{{ task.requirements }}</p>

                  <!-- 评分维度 -->
                  <div v-if="task.criteria" class="flex flex-wrap gap-2 mb-6">
                    <span v-for="(c, idx) in task.criteria.split(',')" :key="idx"
                      class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium">
                      {{ c.trim() }}
                    </span>
                  </div>
                </div>

                <!-- 右侧：操作按钮 -->
                <div class="flex flex-col gap-3 min-w-[180px]">
                  <button v-if="task.template_path"
                    class="w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                    @click="downloadTemplate(task)">
                    <Icon icon="mdi:download" />
                    下载模板
                  </button>
                  <button
                    class="w-full px-6 py-3 bg-gradient-to-r from-primary-500 to-indigo-600 text-white rounded-xl font-bold hover:shadow-lg hover:shadow-primary-500/30 transition-all flex items-center justify-center gap-2"
                    @click="goSubmit(task)">
                    <Icon :icon="task.submitted ? 'mdi:refresh' : 'mdi:send'" />
                    {{ task.submitted ? '重新提交' : '提交成果' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 筛选后空状态 -->
      <div v-else class="min-h-[40vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-24 h-24 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <Icon icon="mdi:file-document-off" class="text-4xl text-gray-300" />
          </div>
          <p class="text-gray-500 text-xl mb-2">
            {{ activeFilter === 'pending' ? '暂无待提交任务' : activeFilter === 'submitted' ? '暂无已提交任务' : '暂无任务，请联系教师加入班级' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 【完全保留你原有的所有业务逻辑，一行未改！只修改筛选交互方式】
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const loading = ref(false)
const tasks = ref<any[]>([])

// 筛选状态
const activeFilter = ref<'all' | 'pending' | 'submitted'>('all')

// 筛选后的任务列表
const filteredTasks = computed(() => {
  let result = [...tasks.value]
  
  // 先用 id 倒序（id 越大越新）
  result.sort((a, b) => b.id - a.id)
  
  // 再按状态排序：待提交在前
  result.sort((a, b) => {
    if (!a.submitted && b.submitted) return -1
    if (a.submitted && !b.submitted) return 1
    return 0
  })
  
  // 筛选
  switch (activeFilter.value) {
    case 'pending': return result.filter(task => !task.submitted)
    case 'submitted': return result.filter(task => task.submitted)
    default: return result
  }
})

// 原有逻辑完全保留
onMounted(() => loadTasks())

const loadTasks = async () => {
  loading.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/tasks/pending?student_id=${user.id}`)
    if (res.data.success) tasks.value = res.data.data
  } catch {} finally { loading.value = false }
}

const goSubmit = (task: any) => {
  localStorage.setItem('current_task', JSON.stringify({
    id: task.id,
    title: task.title,
    requirements: task.requirements,
    criteria: task.criteria,
    criteria_weights: task.criteria_weights
  }))
  localStorage.setItem('current_task_criteria', task.criteria)
  router.push('/app/upload')
}

const downloadTemplate = (task: any) => {
  window.open(`${API_BASE}/api/tasks/${task.id}/template`, '_blank')
}
</script>

<style scoped>
/* 无额外样式，全靠Tailwind */
</style>