<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-50 to-white">
    <div class="max-w-7xl mx-auto px-6 py-10">
      <!-- 顶部标题区 -->
      <div class="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6 fade-in-up">
        <div class="flex items-start gap-4">
          <div class="hidden md:block w-1.5 h-14 bg-gradient-to-b from-primary-500 to-indigo-600 rounded-full mt-1 shadow-lg shadow-primary-500/20"></div>
          <div>
            <h1 class="text-4xl font-bold text-gray-900 tracking-tight">班级成绩总览</h1>
            <p class="text-gray-500 mt-2 text-lg">查看班级学生的实训评价数据与排名</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button class="px-5 py-2.5 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-all duration-200 flex items-center gap-2 shadow-lg shadow-green-500/20 hover:shadow-green-500/30 hover:-translate-y-0.5 active:translate-y-0"
            @click="batchExport" :disabled="exporting">
            <span v-if="exporting" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <Icon v-else icon="mdi:file-excel" class="text-lg" />
            {{ exporting ? '导出中...' : '导出班级成绩' }}
          </button>
          <button class="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 flex items-center gap-2 hover:-translate-y-0.5 active:translate-y-0 shadow-sm bg-white"
            @click="$router.back()">
            <Icon icon="mdi:arrow-left" class="text-lg" />
            返回
          </button>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-14 h-14 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4 shadow-lg shadow-primary-500/10"></div>
          <p class="text-gray-500 text-lg">加载中...</p>
        </div>
      </div>

      <!-- 主内容 -->
      <div v-else-if="data.total_students">
        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 fade-in-up" style="animation-delay: 0.1s">
          <!-- 班级平均分 -->
          <div class="relative bg-gradient-to-br from-primary-500 to-indigo-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 group overflow-hidden">
            <div class="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -mr-10 -mt-10 transition-transform duration-500 group-hover:scale-150"></div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-white/20"></div>
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-6">
                <div class="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm group-hover:scale-110 transition-transform duration-300 shadow-lg ring-1 ring-white/30">
                  <Icon icon="mdi:chart-line" class="text-2xl" />
                </div>
                <span class="text-white/90 text-sm font-medium bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">班级平均分</span>
              </div>
              <div class="flex items-baseline gap-1">
                <div class="text-5xl font-black tracking-tight">{{ data.class_avg }}</div>
                <div class="text-white/80 text-lg font-medium">分</div>
              </div>
            </div>
          </div>

          <!-- 总人数 -->
          <div class="relative bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 group overflow-hidden">
            <div class="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -mr-10 -mt-10 transition-transform duration-500 group-hover:scale-150"></div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-white/20"></div>
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-6">
                <div class="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm group-hover:scale-110 transition-transform duration-300 shadow-lg ring-1 ring-white/30">
                  <Icon icon="mdi:account-group" class="text-2xl" />
                </div>
                <span class="text-white/90 text-sm font-medium bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">总人数</span>
              </div>
              <div class="flex items-baseline gap-1">
                <div class="text-5xl font-black tracking-tight">{{ data.total_students }}</div>
                <div class="text-white/80 text-lg font-medium">人</div>
              </div>
            </div>
          </div>

          <!-- 总提交数 -->
          <div class="relative bg-gradient-to-br from-orange-500 to-amber-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 group overflow-hidden">
            <div class="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -mr-10 -mt-10 transition-transform duration-500 group-hover:scale-150"></div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-white/20"></div>
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-6">
                <div class="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm group-hover:scale-110 transition-transform duration-300 shadow-lg ring-1 ring-white/30">
                  <Icon icon="mdi:file-document-multiple" class="text-2xl" />
                </div>
                <span class="text-white/90 text-sm font-medium bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">总提交数</span>
              </div>
              <div class="flex items-baseline gap-1">
                <div class="text-5xl font-black tracking-tight">{{ data.total_submissions }}</div>
                <div class="text-white/80 text-lg font-medium">份</div>
              </div>
            </div>
          </div>

          <!-- 提交率 -->
          <div class="relative bg-gradient-to-br from-purple-500 to-violet-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 group overflow-hidden">
            <div class="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -mr-10 -mt-10 transition-transform duration-500 group-hover:scale-150"></div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-white/20"></div>
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-6">
                <div class="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur-sm group-hover:scale-110 transition-transform duration-300 shadow-lg ring-1 ring-white/30">
                  <Icon icon="mdi:percent" class="text-2xl" />
                </div>
                <span class="text-white/90 text-sm font-medium bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">提交率</span>
              </div>
              <div class="flex items-baseline gap-1">
                <div class="text-5xl font-black tracking-tight">{{ submitRate }}</div>
                <div class="text-white/80 text-lg font-medium">%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 成绩表格 -->
        <div class="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden fade-in-up" style="animation-delay: 0.2s">
          <div class="p-8 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <span class="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center shadow-sm ring-1 ring-primary-100">
                <Icon icon="mdi:format-list-numbered" class="text-xl text-primary-500" />
              </span>
              <span>学生成绩排名</span>
            </h3>
            <span class="text-sm text-gray-400 bg-gray-50 px-4 py-1.5 rounded-full font-medium ring-1 ring-gray-100">
              共 {{ data.total_students }} 人
            </span>
          </div>
          <!-- 表格居中容器 -->
          <div class="py-8 px-6">
            <el-table 
              :data="data.students" 
              style="width: 100%" 
              :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }" 
              class="modern-table"
            >
              <!-- 排名 | 固定宽度，居中 -->
              <el-table-column label="排名" width="110" align="center">
                <template #default="{ $index }">
                  <div class="flex justify-center py-2">
                    <div v-if="$index === 0" class="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-300 to-amber-500 flex items-center justify-center text-white text-xl shadow-lg shadow-yellow-500/30 ring-2 ring-yellow-100">
                      1
                    </div>
                    <div v-else-if="$index === 1" class="w-12 h-12 rounded-full bg-gradient-to-br from-gray-200 to-gray-400 flex items-center justify-center text-white text-xl shadow-lg shadow-gray-400/30 ring-2 ring-gray-100">
                      2
                    </div>
                    <div v-else-if="$index === 2" class="w-12 h-12 rounded-full bg-gradient-to-br from-orange-300 to-orange-500 flex items-center justify-center text-white text-xl shadow-lg shadow-orange-500/30 ring-2 ring-orange-100">
                      3
                    </div>
                    <div v-else class="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center ring-1 ring-gray-100">
                      <span class="text-lg font-bold text-gray-500">{{ $index + 1 }}</span>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <!-- 姓名 | 整体居中，无右侧留白 -->
              <el-table-column prop="student_name" label="姓名" min-width="240" align="center">
                <template #default="{ row }">
                  <div class="flex items-center justify-center gap-3 py-2">
                    <div class="w-11 h-11 rounded-full bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-primary-500/20 ring-2 ring-white">
                      {{ row.student_name?.charAt(0) }}
                    </div>
                    <div class="flex flex-col">
                      <span class="font-semibold text-gray-900 text-base">{{ row.student_name }}</span>
                    </div>
                  </div>
                </template>
              </el-table-column>

                <!-- 学号 | 字体放大 + 居中 + 整体左移 -->
                <el-table-column prop="student_number" label="学号" min-width="160" align="center">
                  <template #default="{ row }">
                    <span class="text-gray-600 font-mono text-base bg-gray-50 px-6 py-1.5 rounded-lg ring-1 ring-gray-100 inline-block -ml-30">
                      {{ row.student_number }}
                    </span>
                  </template>
                </el-table-column>

              <!-- 提交数 | 窄宽度居中 -->
              <el-table-column label="提交数" width="120" align="center">
                <template #default="{ row }">
                  <span :class="row.submission_count > 0 ? 'bg-green-50 text-green-600 ring-green-200' : 'bg-red-50 text-red-600 ring-red-200'"
                    class="px-3 py-1.5 rounded-full text-sm font-bold inline-block min-w-[3.5rem] text-center ring-1">
                    {{ row.submission_count }}
                  </span>
                </template>
              </el-table-column>

              <!-- AI平均分 | 适中宽度居中 -->
              <el-table-column label="AI平均分" min-width="150" align="center">
                <template #default="{ row }">
                  <div v-if="row.avg_ai_score" 
                    :class="row.avg_ai_score >= 80 ? 'bg-green-50 text-green-600 ring-green-200' : row.avg_ai_score >= 60 ? 'bg-orange-50 text-orange-500 ring-orange-200' : 'bg-red-50 text-red-500 ring-red-200'"
                    class="inline-flex items-center px-4 py-1.5 rounded-full text-xl font-black ring-1">
                    {{ row.avg_ai_score }}<span class="text-sm font-normal ml-0.5">分</span>
                  </div>
                  <span v-else class="text-gray-400 font-medium">-</span>
                </template>
              </el-table-column>

              <!-- 操作 | 固定宽度 -->
              <el-table-column label="操作" width="140" align="center">
                <template #default="{ row }">
                  <button
                    class="px-4 py-2 bg-primary-50 text-primary-600 rounded-lg text-sm font-semibold hover:bg-primary-100 hover:shadow-md hover:shadow-primary-500/10 transition-all duration-200 active:scale-95 ring-1 ring-primary-100"
                    @click="viewStudentDetail(row)"
                  >
                    查看详情
                  </button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="min-h-[60vh] flex items-center justify-center empty-state">
        <div class="text-center">
          <div class="w-36 h-36 rounded-full bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center mx-auto mb-6 ring-1 ring-gray-200 shadow-inner">
            <Icon icon="mdi:chart-bar" class="text-6xl text-gray-300" />
          </div>
          <p class="text-gray-400 text-xl mb-2 font-medium">暂无学生数据</p>
          <p class="text-gray-300 text-sm">该班级暂时还没有学生成绩记录</p>
        </div>
      </div>
    </div>

    <!-- 学生详情弹窗 -->
    <el-dialog
      v-model="showStudentDetail"
      :title="studentDetail ? '学生详情 - ' + studentDetail.student_name : ''"
      width="850px"
      class="modern-dialog"
      destroy-on-close
      align-center
    >
      <div v-if="studentDetail" class="py-2">
        <!-- 顶部统计 -->
        <div class="grid grid-cols-3 gap-5 mb-8">
          <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-5 text-center border border-blue-100 hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div class="absolute -right-4 -top-4 w-20 h-20 bg-blue-100/50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
            <div class="relative">
              <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 shadow-sm">
                <Icon icon="mdi:upload-circle" class="text-xl" />
              </div>
              <div class="text-sm text-blue-600 mb-1 font-semibold">提交次数</div>
              <div class="text-3xl font-black text-blue-700">{{ studentDetail.submit_count }}<span class="text-base font-medium ml-1">次</span></div>
            </div>
          </div>
          <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-5 text-center border border-green-100 hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div class="absolute -right-4 -top-4 w-20 h-20 bg-green-100/50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
            <div class="relative">
              <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-green-100 flex items-center justify-center text-green-600 shadow-sm">
                <Icon icon="mdi:brain" class="text-xl" />
              </div>
              <div class="text-sm text-green-600 mb-1 font-semibold">AI平均分</div>
              <div class="text-3xl font-black text-green-700">{{ studentDetail.ai_avg }}<span class="text-base font-medium ml-1">分</span></div>
            </div>
          </div>
          <div class="bg-gradient-to-br from-purple-50 to-violet-50 rounded-2xl p-5 text-center border border-purple-100 hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div class="absolute -right-4 -top-4 w-20 h-20 bg-purple-100/50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
            <div class="relative">
              <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600 shadow-sm">
                <Icon icon="mdi:podium" class="text-xl" />
              </div>
              <div class="text-sm text-purple-600 mb-1 font-semibold">班级排名</div>
              <div class="text-3xl font-black text-purple-700">
                第{{ data.students.findIndex((s: any) => s.student_id === currentStudentId) + 1 }}名
              </div>
            </div>
          </div>
        </div>

        <!-- 提交记录标题 -->
        <div class="flex items-center gap-3 mb-5">
          <div class="w-1.5 h-6 bg-gradient-to-b from-primary-500 to-indigo-500 rounded-full"></div>
          <h4 class="font-bold text-gray-800 text-lg">提交记录</h4>
        </div>

        <!-- 提交记录表格 -->
        <div class="rounded-2xl border border-gray-200 overflow-hidden mb-8 shadow-sm bg-white">
          <el-table :data="studentDetail.records" border stripe class="modern-table" max-height="320">
            <el-table-column prop="task_title" label="任务标题" min-width="180">
              <template #default="{ row }">
                <span class="font-medium text-gray-800">{{ row.task_title }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="filename" label="文件名" min-width="200">
              <template #default="{ row }">
                <div class="flex items-center gap-2">
                  <Icon icon="mdi:file-document-outline" class="text-gray-400" />
                  <span class="text-gray-600 text-sm truncate max-w-[180px]">{{ row.filename }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="time" label="时间" width="170">
              <template #default="{ row }">
                <span class="text-gray-500 text-sm font-mono bg-gray-50 px-2 py-1 rounded">{{ row.time }}</span>
              </template>
            </el-table-column>
            <el-table-column label="AI评分" width="110" align="center">
              <template #default="{ row: r }">
                <span
                  v-if="r.ai_score"
                  class="px-3 py-1 bg-primary-50 text-primary-600 rounded-full text-sm font-bold ring-1 ring-primary-100"
                >
                  {{ r.ai_score }}分
                </span>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            <el-table-column label="教师评分" width="110" align="center">
              <template #default="{ row: r }">
                <span
                  v-if="r.teacher_score"
                  class="px-3 py-1 bg-orange-50 text-orange-500 rounded-full text-sm font-bold ring-1 ring-orange-100"
                >
                  {{ r.teacher_score }}分
                </span>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- AI评语 -->
        <div class="bg-gradient-to-r from-blue-50 via-indigo-50 to-blue-50 rounded-2xl p-6 border-l-4 border-blue-400 relative overflow-hidden">
          <div class="absolute top-2 left-3 text-blue-200 text-5xl font-serif leading-none select-none">"</div>
          <div class="relative z-10 pl-6">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-blue-500 text-sm font-bold bg-blue-100 px-2 py-0.5 rounded">AI 评语</span>
            </div>
            <p class="text-lg text-blue-800 font-medium leading-relaxed">
              {{ studentDetail.ai_comment }}
            </p>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'
import { API_BASE } from '../config'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const data = ref<any>({ students: [], class_avg: 0, total_students: 0, total_submissions: 0 })
const exporting = ref(false)

const showStudentDetail = ref(false)
const studentDetail = ref<any>(null)
const currentStudentId = ref(0)

const submitRate = computed(() => {
  if (!data.value.total_students) return 0
  const submitted = data.value.students.filter((s: any) => s.submission_count > 0).length
  return Math.round((submitted / data.value.total_students) * 100)
})

const batchExport = async () => {
  exporting.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/report/batch-excel`, {
      class_id: route.query.id
    }, { responseType: 'blob' })

    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `班级成绩汇总_${new Date().toISOString().slice(0,10)}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const viewStudentDetail = async (row: any) => {
  currentStudentId.value = row.student_id
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/student/${row.student_id}/summary`)
    if (res.data.success) {
      studentDetail.value = res.data.data
      showStudentDetail.value = true
    }
  } catch {
    ElMessage.error('获取学生详情失败')
  }
}

onMounted(async () => {
  const classId = route.query.id
  if (!classId) return
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/class/${classId}`)
    if (res.data.success) data.value = res.data.data
  } catch {} finally { loading.value = false }
})
</script>

<style scoped>
/* 入场动画 */
.fade-in-up {
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 空状态动画 */
.empty-state {
  animation: fadeInUp 0.8s ease-out forwards;
}

/* 表格现代化 */
.modern-table :deep(.el-table__header-wrapper th) {
  background-color: #f9fafb !important;
  color: #374151;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.02em;
  padding: 16px 0;
  border-bottom: 2px solid #e5e7eb;
}

.modern-table :deep(.el-table__row) {
  transition: all 0.25s ease;
}

.modern-table :deep(.el-table__row:hover) {
  background-color: #f9fafb !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 1;
}

.modern-table :deep(.el-table__cell) {
  padding: 14px 0;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 6px;
  height: 6px;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: #d1d5db;
  border-radius: 3px;
}

.modern-table :deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: transparent;
}

/* 弹窗样式 */
.modern-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #f3f4f6;
  padding: 20px 24px;
  margin-bottom: 0;
  font-weight: 700;
  font-size: 1.25rem;
}

.modern-dialog :deep(.el-dialog__body) {
  padding: 24px;
  background: #fafafa;
}

.modern-dialog :deep(.el-dialog__headerbtn) {
  width: 40px;
  height: 40px;
  top: 12px;
  right: 12px;
  border-radius: 50%;
  transition: all 0.2s;
}

.modern-dialog :deep(.el-dialog__headerbtn:hover) {
  background: #f3f4f6;
}

/* 表格内边框优化 */
.modern-table :deep(.el-table--border .el-table__cell) {
  border-right: 1px solid #f3f4f6;
}

.modern-table :deep(.el-table--border::before) {
  display: none;
}
</style>