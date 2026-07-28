<template>
  <div class="page-enter">
    <div class="max-w-7xl mx-auto">
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">我的成绩</h1>
        <p class="text-surface-500 mt-1">查看你的实训评价记录与成绩趋势分析</p>
      </div>

      <div v-if="!loaded" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-12 h-12 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-gray-500">加载中...</p>
        </div>
      </div>

      <div v-else-if="data.records?.length > 0">
        <!-- 顶部数据看板 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <div class="bg-gradient-to-br from-primary-500 to-indigo-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
                <Icon icon="mdi:file-document-multiple" class="text-2xl" />
              </div>
              <span class="text-white/80 text-sm font-medium">提交次数</span>
            </div>
            <div class="text-5xl font-black mb-1">{{ totalRecords }}</div>
            <div class="text-white/70 text-sm">次实训评价</div>
          </div>

          <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
                <Icon icon="mdi:chart-line" class="text-2xl" />
              </div>
              <span class="text-white/80 text-sm font-medium">平均分</span>
            </div>
            <div class="text-5xl font-black mb-1">{{ data.avg_score }}</div>
            <div class="text-white/70 text-sm">综合得分</div>
          </div>

          <div class="bg-gradient-to-br from-orange-500 to-amber-600 rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center">
                <Icon icon="mdi:trophy" class="text-2xl" />
              </div>
              <span class="text-white/80 text-sm font-medium">最高分</span>
            </div>
            <div class="text-5xl font-black mb-1">{{ Math.max(...data.records.map((r: any) => r.total_score)) }}</div>
            <div class="text-white/70 text-sm">历史最佳</div>
          </div>

          <div class="bg-white rounded-3xl p-8 border border-gray-100 shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
            <div class="flex items-center gap-3 mb-5">
              <div class="w-12 h-12 rounded-2xl bg-orange-50 flex items-center justify-center">
                <Icon icon="mdi:alert-outline" class="text-2xl text-orange-500" />
              </div>
              <div>
                <p class="text-gray-900 font-bold text-lg">需加强</p>
                <p class="text-gray-500 text-xs">薄弱维度</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2" v-if="data.weakness?.length">
              <span v-for="w in data.weakness" :key="w.name"
                class="px-3 py-1.5 bg-orange-50 text-orange-600 rounded-full text-sm font-medium">
                {{ w.name }}
              </span>
            </div>
            <p v-else class="text-gray-400 text-sm">暂无明显薄弱项</p>
          </div>
        </div>

        <!-- 成绩趋势图 -->
        <div class="bg-white rounded-3xl border border-gray-100 shadow-xl p-8 mb-10">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span class="w-8 h-8 rounded-lg bg-primary-50 text-primary-500 flex items-center justify-center">
                <Icon icon="mdi:chart-timeline-variant" />
              </span>
              成绩趋势
            </h3>
          </div>
          <v-chart :option="lineOption" style="height: 350px" class="modern-chart" />
        </div>

        <!-- 评价记录表格 -->
        <div class="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden">
          <div class="p-8 border-b border-gray-100">
            <h3 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span class="w-8 h-8 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center">
                <Icon icon="mdi:format-list-bulleted" />
              </span>
              评价记录
            </h3>
          </div>
          <div class="overflow-x-auto">
            <el-table :data="data.records" style="width: 100%" :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }" class="modern-table">
              <el-table-column prop="task_title" label="任务标题" width="180">
                <template #default="{ row }">
                  <div class="flex items-center gap-2">
                    <Icon icon="mdi:clipboard-text" class="text-primary-500 text-sm" />
                    <span class="text-sm text-gray-700 truncate">{{ row.task_title }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="filename" label="文件名" min-width="200">
                <template #default="{ row }">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center">
                      <Icon icon="mdi:file-document" class="text-primary-500" />
                    </div>
                    <span class="font-medium text-gray-900">{{ row.filename }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="time" label="提交时间" width="180" />
              <el-table-column label="AI评分" width="120">
                <template #default="{ row }">
                  <span :class="row.total_score >= 80 ? 'bg-green-50 text-green-600' : row.total_score >= 60 ? 'bg-orange-50 text-orange-600' : 'bg-red-50 text-red-600'"
                    class="px-3 py-1.5 rounded-full text-sm font-bold">
                    {{ row.total_score }}分
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="教师评分" width="120">
                <template #default="{ row }">
                  <span v-if="row.teacher_score !== undefined && row.teacher_score !== null"
                    class="px-3 py-1.5 bg-orange-50 text-orange-600 rounded-full text-sm font-bold">
                    {{ row.teacher_score }}分
                  </span>
                  <span v-else class="text-gray-400 text-sm">未评分</span>
                </template>
              </el-table-column>
              <el-table-column label="各维度" min-width="250">
                <template #default="{ row }">
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="s in row.scores" :key="s.name"
                      class="px-2 py-1 bg-gray-100 text-gray-700 rounded-lg text-xs font-medium">
                      {{ s.name }}: {{ s.score }}
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="教师评语" min-width="200">
                <template #default="{ row }">
                  <span v-if="row.teacher_comment" class="text-sm text-gray-600">{{ row.teacher_comment }}</span>
                  <span v-else class="text-gray-400 text-sm">-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <button class="px-4 py-2 bg-primary-50 text-primary-500 rounded-lg text-sm font-medium hover:bg-primary-100 transition-colors"
                    @click="viewDetail(row)">
                    详情
                  </button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 分页 -->
          <div class="flex justify-center py-6" v-if="totalRecords > pageSize">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="totalRecords"
              layout="total, prev, pager, next, jumper"
              background
              @current-change="handlePageChange"
            />
          </div>
        </div>

        <!-- 能力成长报告 -->
        <div class="bg-white rounded-3xl border border-gray-100 shadow-xl p-8 mt-10" v-if="growth">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center">
              <Icon icon="mdi:trending-up" class="text-xl text-green-500" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900"> 能力成长报告</h3>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 text-center">
              <div class="text-sm text-blue-600 mb-2">首次均分</div>
              <div class="text-4xl font-black text-blue-600">{{ growth.first.total }}<span class="text-lg">分</span></div>
              <div class="text-xs text-blue-400 mt-1">{{ growth.first.time }}</div>
            </div>
            <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6 text-center">
              <div class="text-sm text-green-600 mb-2">最新均分</div>
              <div class="text-4xl font-black text-green-600">{{ growth.latest.total }}<span class="text-lg">分</span></div>
              <div class="text-xs text-green-400 mt-1">{{ growth.latest.time }}</div>
            </div>
            <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-6 text-center">
              <div class="text-sm text-purple-600 mb-2">提升幅度</div>
              <div class="text-4xl font-black" :class="growth.total_change >= 0 ? 'text-green-600' : 'text-red-500'">
                {{ growth.total_change >= 0 ? '+' : '' }}{{ growth.total_change }}<span class="text-lg">分</span>
              </div>
              <div class="text-xs text-purple-400 mt-1">共 {{ growth.total_count }} 次提交</div>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div>
              <h4 class="font-bold text-gray-800 mb-4">各维度成长对比</h4>
              <v-chart :option="growthRadarOption" style="height: 350px" />
            </div>
            <div>
              <h4 class="font-bold text-gray-800 mb-4">维度变化详情</h4>
              <div class="space-y-3">
                <div v-for="item in growth.changes" :key="item.name"
                  class="flex items-center justify-between p-4 rounded-xl"
                  :class="item.change >= 0 ? 'bg-green-50' : 'bg-red-50'">
                  <div>
                    <span class="font-bold text-gray-800">{{ item.name }}</span>
                    <div class="text-sm text-gray-500">
                      {{ item.first_score }} → {{ item.latest_score }}
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-2xl font-black" :class="item.change >= 0 ? 'text-green-500' : 'text-red-500'">
                      {{ item.change >= 0 ? '+' : '' }}{{ item.change }}
                    </span>
                    <span class="text-xs text-gray-500">分</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-blue-50 rounded-2xl p-6">
            <p class="text-lg text-blue-700 font-medium">{{ growth.advice }}</p>
          </div>
        </div>
      </div>

      <div v-else class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-32 h-32 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-6">
            <Icon icon="mdi:file-document-off" class="text-5xl text-gray-300" />
          </div>
          <p class="text-gray-500 text-xl mb-8">暂无评价记录，去提交实训成果吧</p>
          <button class="btn-primary text-white px-8 py-3 rounded-xl font-bold text-lg" @click="$router.push('/app/upload')">
            去上传评价
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const loaded = ref(false)
const data = ref<any>({ records: [], weakness: [], total_count: 0, avg_score: 0 })
const growth = ref<any>(null)
const currentPage = ref(1)
const pageSize = 5
const totalRecords = ref(0)

const loadRecords = async (page = 1) => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  if (!user.id) return

  try {
    const res = await axios.get(`${API_BASE}/api/statistics/student/${user.id}?page=${page}&page_size=${pageSize}`)
    if (res.data.success) {
      data.value = res.data.data
      totalRecords.value = res.data.data.total_count

      try {
        const tRes = await axios.get(`${API_BASE}/api/statistics/student/${user.id}/teacher-scores`)
        if (tRes.data.success) {
          const teacherMap: any = {}
          tRes.data.data.forEach((t: any) => {
            teacherMap[t.submission_id] = { total_score: t.total_score, comment: t.comment }
          })
          data.value.records.forEach((r: any) => {
            const t = teacherMap[r.id]
            r.teacher_score = t ? t.total_score : null
            r.teacher_comment = t ? t.comment : null
          })
        }
      } catch {}
    }
  } catch (err) {
    console.error(err)
  }
}

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  if (!user.id) { router.push('/login'); return }

  loaded.value = false
  await loadRecords(currentPage.value)

  try {
    const growthRes = await axios.get(`${API_BASE}/api/statistics/student/${user.id}/growth`)
    if (growthRes.data.success) growth.value = growthRes.data.data
  } catch {}

  loaded.value = true
})

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadRecords(page)
}

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#111827' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: data.value.records.map((r: any) => r.time).reverse(),
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisLabel: { color: '#6b7280' }
  },
  yAxis: {
    type: 'value', name: '分数', min: 0, max: 100,
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisLabel: { color: '#6b7280' },
    splitLine: { lineStyle: { color: '#f3f4f6' } }
  },
  series: [{
    type: 'line',
    data: data.value.records.map((r: any) => r.total_score).reverse(),
    smooth: true, symbol: 'circle', symbolSize: 10,
    lineStyle: { width: 4, color: '#165DFF' },
    itemStyle: { color: '#165DFF', borderColor: '#fff', borderWidth: 3 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(22, 93, 255, 0.3)' },
          { offset: 1, color: 'rgba(22, 93, 255, 0.05)' }
        ]
      }
    },
    markLine: {
      data: [{ type: 'average', name: '平均值' }],
      lineStyle: { color: '#22c55e', width: 2, type: 'dashed' },
      label: { color: '#22c55e', fontWeight: 600 }
    }
  }]
}))

const growthRadarOption = computed(() => {
  if (!growth.value) return {}
  const dims = growth.value.changes.map((c: any) => c.name)
  return {
    tooltip: {},
    legend: { data: ['首次提交', '最新提交'] },
    radar: {
      indicator: dims.map((d: string) => ({ name: d, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#374151', fontSize: 12, fontWeight: 600 }
    },
    series: [
      {
        type: 'radar',
        name: '首次提交',
        data: [{ value: growth.value.changes.map((c: any) => c.first_score), name: '首次提交' }],
        lineStyle: { color: '#93c5fd', width: 2 },
        areaStyle: { color: 'rgba(147,197,253,0.2)' },
        itemStyle: { color: '#3b82f6' }
      },
      {
        type: 'radar',
        name: '最新提交',
        data: [{ value: growth.value.changes.map((c: any) => c.latest_score), name: '最新提交' }],
        lineStyle: { color: '#86efac', width: 2 },
        areaStyle: { color: 'rgba(134,239,172,0.2)' },
        itemStyle: { color: '#22c55e' }
      }
    ]
  }
})

const viewDetail = (row: any) => {
  localStorage.setItem('eval_result', JSON.stringify({
    submission_id: row.id,
    filename: row.filename,
    evaluation: { total: row.total_score, scores: row.scores, comment: row.comment },
    completeness: { steps: row.step_completeness || [], issues: row.logic_issues || [], summary: row.comment || '' }
  }))
  router.push('/app/result/latest')
}
</script>

<style scoped>
.modern-table :deep(.el-table__header-wrapper th) {
  background-color: #f9fafb;
  color: #111827;
  font-weight: 700;
}
.modern-table :deep(.el-table__row:hover) {
  background-color: #f9fafb;
}
.modern-chart {
  width: 100%;
}
</style>