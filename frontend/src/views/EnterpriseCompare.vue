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
          <span class="text-surface-800 font-medium">三方评价对比</span>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-surface-800 tracking-tight">三方评价对比</h1>
          <p class="text-surface-500 mt-1">对比 AI 评分、教师评分与企业评分的差异，洞察评价一致性</p>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="card p-6 mb-8">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <Icon icon="mdi:filter-variant" class="text-surface-400" />
            <span class="text-sm font-semibold text-surface-700">筛选：</span>
          </div>
          <el-select v-model="filterClass" placeholder="选择班级" size="large" class="w-48 modern-select">
            <el-option label="全部班级" value="" />
            <el-option label="软件技术2401班" value="1" />
            <el-option label="软件工程2402班" value="2" />
          </el-select>
          <el-select v-model="filterTask" placeholder="选择任务" size="large" class="w-56 modern-select">
            <el-option label="全部任务" value="" />
            <el-option label="Web前端开发实训" value="1" />
            <el-option label="Java后端开发项目" value="2" />
            <el-option label="全栈电商系统开发" value="3" />
          </el-select>
          <el-select v-model="filterStudent" placeholder="选择学生" size="large" class="w-44 modern-select" filterable>
            <el-option label="全部学生" value="" />
            <el-option label="张伟 (2024001)" value="1" />
            <el-option label="李娜 (2024002)" value="2" />
            <el-option label="王强 (2024003)" value="3" />
          </el-select>
          <el-date-picker
            v-model="filterDate"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="large"
            class="modern-date"
          />
          <div class="flex-1"></div>
          <button class="btn-ghost px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
            <Icon icon="mdi:filter-variant-remove" />
            重置
          </button>
          <button class="btn-primary text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
            <Icon icon="mdi:chart-bubble" />
            开始对比
          </button>
        </div>
      </div>

      <!-- 统计差异概览 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="card p-6 flex items-center gap-5 border-t-4 border-t-violet-500">
          <div class="w-14 h-14 rounded-2xl bg-violet-50 flex items-center justify-center flex-shrink-0">
            <Icon icon="mdi:robot-outline" class="text-3xl text-violet-500" />
          </div>
          <div>
            <div class="text-sm text-surface-500 mb-1">AI 平均分</div>
            <div class="text-3xl font-black text-surface-800">{{ summary.aiAvg }}</div>
          </div>
        </div>
        <div class="card p-6 flex items-center gap-5 border-t-4 border-t-blue-500">
          <div class="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center flex-shrink-0">
            <Icon icon="mdi:account-tie-outline" class="text-3xl text-blue-500" />
          </div>
          <div>
            <div class="text-sm text-surface-500 mb-1">教师平均分</div>
            <div class="text-3xl font-black text-surface-800">{{ summary.teacherAvg }}</div>
          </div>
        </div>
        <div class="card p-6 flex items-center gap-5 border-t-4 border-t-emerald-500">
          <div class="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center flex-shrink-0">
            <Icon icon="mdi:domain" class="text-3xl text-emerald-500" />
          </div>
          <div>
            <div class="text-sm text-surface-500 mb-1">企业平均分</div>
            <div class="text-3xl font-black text-surface-800">{{ summary.enterpriseAvg }}</div>
          </div>
        </div>
      </div>

      <!-- 三栏评分卡片 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
        <!-- AI 评分卡 -->
        <div class="card overflow-hidden">
          <div class="px-8 py-5 bg-gradient-to-r from-violet-50 to-purple-50 border-b border-violet-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm">
                <Icon icon="mdi:robot-outline" class="text-2xl text-violet-500" />
              </div>
              <div>
                <h3 class="font-bold text-surface-800">AI 评分</h3>
                <p class="text-xs text-surface-500">大模型自动评价</p>
              </div>
            </div>
            <span class="bg-violet-500 text-white text-xs font-bold px-3 py-1 rounded-full">智能</span>
          </div>
          <div class="p-8">
            <div class="flex items-end justify-center mb-6">
              <span class="text-6xl font-black text-violet-600">{{ selectedCompare.aiScore }}</span>
              <span class="text-2xl font-bold text-surface-400 mb-2 ml-1">/ 100</span>
            </div>
            <div class="w-full bg-violet-100 rounded-full h-3 mb-8 overflow-hidden">
              <div class="bg-gradient-to-r from-violet-500 to-purple-500 h-3 rounded-full" :style="{ width: selectedCompare.aiScore + '%' }"></div>
            </div>
            <div class="space-y-4">
              <div v-for="dim in aiDimensions" :key="dim.name">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="text-sm font-medium text-surface-700">{{ dim.name }}</span>
                  <span class="text-sm font-bold text-violet-600">{{ dim.score }}分</span>
                </div>
                <div class="w-full bg-surface-100 rounded-full h-2 overflow-hidden">
                  <div class="bg-violet-400 h-2 rounded-full" :style="{ width: dim.score + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 教师评分卡 -->
        <div class="card overflow-hidden">
          <div class="px-8 py-5 bg-gradient-to-r from-blue-50 to-sky-50 border-b border-blue-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm">
                <Icon icon="mdi:account-tie-outline" class="text-2xl text-blue-500" />
              </div>
              <div>
                <h3 class="font-bold text-surface-800">教师评分</h3>
                <p class="text-xs text-surface-500">授课教师人工评价</p>
              </div>
            </div>
            <span class="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-full">专业</span>
          </div>
          <div class="p-8">
            <div class="flex items-end justify-center mb-6">
              <span class="text-6xl font-black text-blue-600">{{ selectedCompare.teacherScore }}</span>
              <span class="text-2xl font-bold text-surface-400 mb-2 ml-1">/ 100</span>
            </div>
            <div class="w-full bg-blue-100 rounded-full h-3 mb-8 overflow-hidden">
              <div class="bg-gradient-to-r from-blue-500 to-sky-500 h-3 rounded-full" :style="{ width: selectedCompare.teacherScore + '%' }"></div>
            </div>
            <div class="space-y-4">
              <div v-for="dim in teacherDimensions" :key="dim.name">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="text-sm font-medium text-surface-700">{{ dim.name }}</span>
                  <span class="text-sm font-bold text-blue-600">{{ dim.score }}分</span>
                </div>
                <div class="w-full bg-surface-100 rounded-full h-2 overflow-hidden">
                  <div class="bg-blue-400 h-2 rounded-full" :style="{ width: dim.score + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 企业评分卡 -->
        <div class="card overflow-hidden">
          <div class="px-8 py-5 bg-gradient-to-r from-emerald-50 to-green-50 border-b border-emerald-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-sm">
                <Icon icon="mdi:domain" class="text-2xl text-emerald-500" />
              </div>
              <div>
                <h3 class="font-bold text-surface-800">企业评分</h3>
                <p class="text-xs text-surface-500">企业专家标准评价</p>
              </div>
            </div>
            <span class="bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-full">实战</span>
          </div>
          <div class="p-8">
            <div class="flex items-end justify-center mb-6">
              <span class="text-6xl font-black text-emerald-600">{{ selectedCompare.enterpriseScore }}</span>
              <span class="text-2xl font-bold text-surface-400 mb-2 ml-1">/ 100</span>
            </div>
            <div class="w-full bg-emerald-100 rounded-full h-3 mb-8 overflow-hidden">
              <div class="bg-gradient-to-r from-emerald-500 to-green-500 h-3 rounded-full" :style="{ width: selectedCompare.enterpriseScore + '%' }"></div>
            </div>
            <div class="space-y-4">
              <div v-for="dim in enterpriseDimensions" :key="dim.name">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="text-sm font-medium text-surface-700">{{ dim.name }}</span>
                  <span class="text-sm font-bold text-emerald-600">{{ dim.score }}分</span>
                </div>
                <div class="w-full bg-surface-100 rounded-full h-2 overflow-hidden">
                  <div class="bg-emerald-400 h-2 rounded-full" :style="{ width: dim.score + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 差异高亮分析 -->
      <div class="card mb-10">
        <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-5 bg-rose-500 rounded-full"></div>
            <span class="text-lg font-bold text-surface-800">差异高亮分析</span>
            <span class="bg-rose-50 text-rose-600 text-xs font-bold px-2.5 py-0.5 rounded-full">
              自动检测
            </span>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="diff in diffHighlights" :key="dim => dim.name"
              class="p-5 rounded-2xl border transition-all duration-200"
              :class="[
                diff.level === 'high' ? 'border-rose-200 bg-rose-50/50 hover:bg-rose-50' :
                diff.level === 'medium' ? 'border-amber-200 bg-amber-50/50 hover:bg-amber-50' :
                'border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50'
              ]">
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-2">
                  <span :class="[
                    diff.level === 'high' ? 'bg-rose-500' : diff.level === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'
                  ]" class="text-white text-xs font-bold px-2.5 py-1 rounded-lg">
                    {{ diff.level === 'high' ? '高差异' : diff.level === 'medium' ? '中差异' : '一致' }}
                  </span>
                  <span class="font-bold text-surface-800">{{ diff.name }}</span>
                </div>
                <span :class="[
                  diff.level === 'high' ? 'text-rose-600' : diff.level === 'medium' ? 'text-amber-600' : 'text-emerald-600'
                ]" class="text-xl font-black">
                  ±{{ diff.diff }}
                </span>
              </div>
              <div class="flex items-center justify-between text-sm mb-3">
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-violet-500"></span>
                  <span class="text-surface-600">AI: <b class="text-violet-600">{{ diff.ai }}</b></span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span class="text-surface-600">教师: <b class="text-blue-600">{{ diff.teacher }}</b></span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                  <span class="text-surface-600">企业: <b class="text-emerald-600">{{ diff.enterprise }}</b></span>
                </div>
              </div>
              <p class="text-xs text-surface-500 leading-relaxed">{{ diff.advice }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史对比表格 -->
      <div class="card">
        <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
            <span class="text-lg font-bold text-surface-800">历史对比记录</span>
          </div>
          <button class="text-primary-500 text-sm font-semibold hover:text-primary-600 flex items-center gap-1">
            查看全部
            <Icon icon="mdi:chevron-right" class="text-base" />
          </button>
        </div>
        <div class="overflow-hidden">
          <el-table :data="historyData" style="width: 100%" :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }">
            <el-table-column width="70" align="center">
              <template #header><span>序号</span></template>
              <template #default="{ $index }">
                <span class="text-surface-500 font-medium">{{ $index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="学生">
              <template #default="{ row }">
                <div class="flex items-center gap-2.5 py-2">
                  <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-400 to-indigo-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                    {{ row.avatar }}
                  </div>
                  <div>
                    <div class="font-semibold text-surface-800 text-sm">{{ row.name }}</div>
                    <div class="text-xs text-surface-500">{{ row.studentNo }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="taskName" label="实训任务" min-width="180">
              <template #default="{ row }">
                <span class="text-surface-700 text-sm">{{ row.taskName }}</span>
              </template>
            </el-table-column>
            <el-table-column label="AI评分" width="120" align="center">
              <template #default="{ row }">
                <span class="font-black text-violet-600 text-lg">{{ row.aiScore }}</span>
              </template>
            </el-table-column>
            <el-table-column label="教师评分" width="120" align="center">
              <template #default="{ row }">
                <span class="font-black text-blue-600 text-lg">{{ row.teacherScore }}</span>
              </template>
            </el-table-column>
            <el-table-column label="企业评分" width="120" align="center">
              <template #default="{ row }">
                <span class="font-black text-emerald-600 text-lg">{{ row.enterpriseScore }}</span>
              </template>
            </el-table-column>
            <el-table-column label="差异度" width="120" align="center">
              <template #default="{ row }">
                <span :class="[
                  'px-2.5 py-1 rounded-full text-xs font-bold',
                  row.diffLevel === 'high' ? 'bg-rose-50 text-rose-600' :
                  row.diffLevel === 'medium' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'
                ]">
                  {{ row.diffLevel === 'high' ? '高差异' : row.diffLevel === 'medium' ? '中差异' : '一致' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default>
                <button class="px-3 py-1.5 bg-primary-50 text-primary-600 rounded-lg text-xs font-semibold hover:bg-primary-100 transition-colors">
                  详情
                </button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Icon } from '@iconify/vue'

const filterClass = ref('')
const filterTask = ref('')
const filterStudent = ref('')
const filterDate = ref<any>(null)

const summary = reactive({
  aiAvg: '87.2',
  teacherAvg: '85.8',
  enterpriseAvg: '86.5'
})

const selectedCompare = reactive({
  aiScore: 92,
  teacherScore: 88,
  enterpriseScore: 90
})

const aiDimensions = ref([
  { name: '代码质量', score: 94 },
  { name: '功能完成度', score: 95 },
  { name: '技术选型', score: 88 },
  { name: '文档规范', score: 90 }
])

const teacherDimensions = ref([
  { name: '代码质量', score: 86 },
  { name: '功能完成度', score: 92 },
  { name: '技术选型', score: 85 },
  { name: '文档规范', score: 88 }
])

const enterpriseDimensions = ref([
  { name: '代码质量', score: 90 },
  { name: '功能完成度', score: 93 },
  { name: '技术选型', score: 91 },
  { name: '工程实践', score: 86 }
])

const diffHighlights = ref([
  {
    name: '代码质量维度',
    level: 'high',
    diff: 8,
    ai: 94,
    teacher: 86,
    enterprise: 90,
    advice: 'AI评分在代码质量上偏乐观，建议教师加强代码规范审查，企业可补充工程实践标准。'
  },
  {
    name: '技术选型维度',
    level: 'medium',
    diff: 6,
    ai: 88,
    teacher: 85,
    enterprise: 91,
    advice: '三方对技术选型评价存在一定差异，建议统一评价标准中的技术栈权重。'
  },
  {
    name: '功能完成度',
    level: 'low',
    diff: 3,
    ai: 95,
    teacher: 92,
    enterprise: 93,
    advice: '三方评价高度一致，功能完成度评价标准明确，保持当前评价方式。'
  },
  {
    name: '文档规范维度',
    level: 'low',
    diff: 2,
    ai: 90,
    teacher: 88,
    enterprise: 89,
    advice: '三方评价基本一致，文档规范评价体系运行良好。'
  }
])

const historyData = ref([
  { id: 1, name: '张伟', studentNo: '2024001', avatar: '张', taskName: 'Web前端开发实训', aiScore: 92, teacherScore: 88, enterpriseScore: 90, diffLevel: 'medium' },
  { id: 2, name: '李娜', studentNo: '2024002', avatar: '李', taskName: 'Web前端开发实训', aiScore: 95, teacherScore: 93, enterpriseScore: 94, diffLevel: 'low' },
  { id: 3, name: '王强', studentNo: '2024003', avatar: '王', taskName: 'Java后端开发项目', aiScore: 85, teacherScore: 78, enterpriseScore: 82, diffLevel: 'high' },
  { id: 4, name: '刘洋', studentNo: '2024004', avatar: '刘', taskName: 'Java后端开发项目', aiScore: 88, teacherScore: 86, enterpriseScore: 87, diffLevel: 'low' },
  { id: 5, name: '陈静', studentNo: '2024005', avatar: '陈', taskName: '全栈电商系统开发', aiScore: 78, teacherScore: 82, enterpriseScore: 80, diffLevel: 'medium' }
])
</script>

<style scoped>
.modern-select :deep(.el-select__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
}
.modern-date :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
}
:deep(.el-table th.el-table__cell) {
  background-color: #f9fafb !important;
}
</style>
