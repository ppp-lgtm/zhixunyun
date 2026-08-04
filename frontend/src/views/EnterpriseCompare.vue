<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 接口错误提示 -->
      <div v-if="loadError" class="mb-6 rounded-2xl border-2 border-seal/30 bg-seal/[0.06] px-5 py-4 flex items-start gap-3">
        <Icon icon="mdi:alert-circle-outline" class="text-seal text-xl flex-shrink-0 mt-0.5" />
        <div class="text-[13.5px] text-seal-dark leading-[1.7] flex-1">{{ loadError }}</div>
        <button @click="runCompare(true)" class="chip-mag !text-[12px] !py-1 !px-3 flex-shrink-0">
          <Icon icon="mdi:refresh" class="mr-1" inline width="12" /> 重试
        </button>
      </div>

      <!-- 页面 Title 区域 -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">三方评价对比</h1>
        <p class="text-surface-500 mt-1">对比 AI 评分、教师评分与企业评分的差异，洞察评价一致性</p>
      </div>

      <!-- 筛选栏 -->
      <div class="card p-6 mb-8">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <Icon icon="mdi:filter-variant" class="text-surface-400" />
            <span class="text-sm font-semibold text-surface-700">筛选：</span>
          </div>
          <el-select v-model="filterClass" placeholder="选择班级" size="large" class="w-48 modern-select" clearable @change="runCompare">
            <el-option label="全部班级" value="" />
            <el-option v-for="c in filters.classes" :key="'cls_' + c.id" :label="c.name" :value="String(c.id)" />
          </el-select>
          <el-select v-model="filterTask" placeholder="选择任务" size="large" class="w-56 modern-select" clearable @change="runCompare">
            <el-option label="全部任务" value="" />
            <el-option v-for="t in filters.tasks" :key="'tsk_' + t.id" :label="t.title" :value="String(t.id)" />
          </el-select>
          <el-select v-model="filterStudent" placeholder="选择学生" size="large" class="w-44 modern-select" filterable clearable @change="runCompare">
            <el-option label="全部学生" value="" />
            <el-option v-for="s in filters.students" :key="'stu_' + s.id" :label="`${s.name || '学生'} (${s.no || s.id})`" :value="String(s.id)" />
          </el-select>
          <el-date-picker
            v-model="filterDate"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="large"
            class="modern-date"
            value-format="YYYY-MM-DD"
            @change="runCompare"
          />
          <div class="flex-1"></div>
          <button @click="resetFilters" class="btn-ghost px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
            <Icon icon="mdi:filter-variant-remove" />
            重置
          </button>
          <button @click="runCompare(true)" class="btn-primary text-white px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2" :disabled="loading">
            <Icon icon="mdi:chart-bubble" />
            {{ loading ? '加载中…' : '开始对比' }}
          </button>
        </div>
      </div>

      <!-- 历史对比表格 -->
      <div class="card">
        <div class="px-8 py-5 border-b border-surface-100 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-1.5 h-5 bg-primary-500 rounded-full"></div>
            <span class="text-lg font-bold text-surface-800">历史对比记录</span>
            <span class="bg-surface-100 text-surface-600 text-xs font-bold px-2.5 py-0.5 rounded-full">{{ historyData.length }} 条</span>
          </div>
          <button v-if="detailRow" @click="closeDetail" class="text-surface-400 text-sm font-semibold hover:text-surface-600 flex items-center gap-1">
            关闭详情
            <Icon icon="mdi:close" class="text-base" />
          </button>
        </div>
        <div v-if="!historyData.length" class="px-8 py-16 text-center text-surface-400">
          <Icon icon="mdi:file-document-outline" class="text-5xl mx-auto mb-4 opacity-60" />
          <div class="text-sm mb-1">暂无企业评价数据</div>
          <div class="text-xs">请先在「企业评价工作台」完成至少一次企业评价，生成记录后再来查看</div>
        </div>
        <div v-else class="overflow-hidden">
          <el-table :data="historyData" style="width: 100%" :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }" highlight-current-row @row-click="onHistoryRowClick" :row-class-name="(r: any) => r.row.submission_id === detailRow?.submission_id ? 'is-current-selected' : ''">
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
                    {{ row.student?.name ? row.student.name.slice(0, 1) : '?' }}
                  </div>
                  <div>
                    <div class="font-semibold text-surface-800 text-sm">{{ row.student?.name || '未知学生' }}</div>
                    <div class="text-xs text-surface-500">{{ row.student?.no || row.student?.id || '' }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="task.title" label="实训任务" min-width="180">
              <template #default="{ row }">
                <span class="text-surface-700 text-sm">{{ row.task?.title || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="AI评分" width="120" align="center">
              <template #default="{ row }">
                <span :class="row.ai_score != null ? 'font-black text-violet-600 text-lg' : 'text-surface-300'">{{ row.ai_score ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="教师评分" width="120" align="center">
              <template #default="{ row }">
                <span :class="row.teacher_score != null ? 'font-black text-blue-600 text-lg' : 'text-surface-300'">{{ row.teacher_score ?? '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="企业评分" width="120" align="center">
              <template #default="{ row }">
                <span :class="row.enterprise_score != null ? 'font-black text-emerald-600 text-lg' : 'text-surface-300'">{{ row.enterprise_score ?? '—' }}</span>
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
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row }">
                <button @click.stop="selectHistory(row)" class="px-3 py-1.5 bg-primary-50 text-primary-600 rounded-lg text-xs font-semibold hover:bg-primary-100 transition-colors">
                  {{ row.submission_id === detailRow?.submission_id ? '再次查看' : '查看详情' }}
                </button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- ========== 查看详情：对比详情弹窗 ========== -->
    <!-- 遮罩层：独立 fixed，永远不参与滚动 -->
    <div v-if="detailVisible" class="fixed inset-0 z-[99] bg-ink/55 backdrop-blur-[2px]" @click="closeDetail"></div>
    <!-- 内容层：独立 fixed + overflow-y-auto，只滚卡片，不影响遮罩 -->
    <div v-if="detailVisible" class="fixed inset-0 z-[100] overflow-y-auto">
      <transition name="fade-in-down" appear>
        <div v-if="detailVisible" class="min-h-full flex items-start justify-center p-4 md:p-10">
          <div class="w-full max-w-[1280px] card-mag !rounded-3xl shadow-2xl !p-0 my-8 relative overflow-hidden bg-white/95">
            <!-- 弹窗 Header -->
            <div class="px-8 py-6 border-b border-surface-100 flex items-start justify-between gap-5 flex-wrap bg-gradient-to-br from-primary-50 via-white to-sky-50 sticky top-0 z-10 backdrop-blur">
              <div class="flex items-start gap-4 min-w-0">
                <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-primary-500 to-seal flex items-center justify-center text-white shadow-lg shadow-primary-500/25 flex-shrink-0">
                  <Icon icon="mdi:scale-balance" class="text-3xl" />
                </div>
                <div class="min-w-0">
                  <div class="flex items-center gap-2 mb-1 flex-wrap">
                    <span class="text-[11px] font-mono tracking-[0.2em] uppercase text-primary-600/80">THREE-WAY · COMPARE · DETAIL</span>
                    <span v-if="current.meta.needsReview" class="bg-rose-50 text-rose-600 text-[10.5px] font-bold px-2 py-0.5 rounded-full border border-rose-100">⚠ 需人工复核</span>
                  </div>
                  <h2 class="font-display font-black text-ink text-2xl tracking-tight leading-tight">
                    {{ detailRow?.student?.name || '学生' }}
                    <span class="text-surface-400 font-medium text-base mx-2">·</span>
                    <span class="text-ink-2 font-semibold text-lg">{{ detailRow?.task?.title || '实训任务' }}</span>
                  </h2>
                  <div class="mt-1.5 text-[12.5px] text-surface-500 flex items-center gap-3 flex-wrap">
                    <span class="flex items-center gap-1">
                      <Icon icon="mdi:tag-outline" inline width="13" />
                      学号：<b class="text-surface-700">{{ detailRow?.student?.no || detailRow?.student?.id || '—' }}</b>
                    </span>
                    <span v-if="current.meta.consistency != null" class="flex items-center gap-1">
                      <Icon icon="mdi:swap-vertical" inline width="13" />
                      一致性指数：<b class="text-emerald-700">{{ Math.round(Number(current.meta.consistency) * 100) }} / 100</b>
                    </span>
                    <span class="flex items-center gap-1">
                      <Icon icon="mdi:chart-bubble" inline width="13" />
                      共 <b class="text-ink">{{ summary.count }}</b> 条对比数据
                    </span>
                  </div>
                </div>
              </div>
              <button @click="closeDetail" class="w-10 h-10 rounded-xl hover:bg-ink/5 flex items-center justify-center text-ink-3 hover:text-ink transition-colors flex-shrink-0 border border-transparent hover:border-surface-100">
                <Icon icon="mdi:close" class="text-xl" />
              </button>
            </div>

          <!-- 弹窗 Body -->
          <div class="px-6 md:px-10 py-8 space-y-8">
            <!-- 3 张平均分卡片 -->
            <div>
              <div class="flex items-center gap-2 mb-4">
                <div class="w-1 h-4 bg-indigo-500 rounded-full"></div>
                <h3 class="font-display font-black text-ink text-lg">整体对比概览</h3>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div class="p-6 rounded-2xl border border-violet-200/70 bg-gradient-to-br from-violet-50 via-white to-white flex items-center gap-5 shadow-sm shadow-violet-100/50">
                  <div class="w-14 h-14 rounded-2xl bg-white border border-violet-100 flex items-center justify-center flex-shrink-0 shadow-inner">
                    <Icon icon="mdi:robot-outline" class="text-3xl text-violet-600" />
                  </div>
                  <div>
                    <div class="text-xs text-surface-500 mb-1 tracking-wide">AI 平均分 · 智能</div>
                    <div class="flex items-baseline gap-1">
                      <div class="text-3xl font-black text-violet-700 tabular-nums">{{ summary.aiAvg ?? '—' }}</div>
                      <span v-if="summary.aiAvg != null" class="text-sm text-surface-400 font-semibold">/ 100</span>
                    </div>
                  </div>
                </div>
                <div class="p-6 rounded-2xl border border-blue-200/70 bg-gradient-to-br from-blue-50 via-white to-white flex items-center gap-5 shadow-sm shadow-blue-100/50">
                  <div class="w-14 h-14 rounded-2xl bg-white border border-blue-100 flex items-center justify-center flex-shrink-0 shadow-inner">
                    <Icon icon="mdi:account-tie-outline" class="text-3xl text-blue-600" />
                  </div>
                  <div>
                    <div class="text-xs text-surface-500 mb-1 tracking-wide">教师平均分 · 专业</div>
                    <div class="flex items-baseline gap-1">
                      <div class="text-3xl font-black text-blue-700 tabular-nums">{{ summary.teacherAvg ?? '—' }}</div>
                      <span v-if="summary.teacherAvg != null" class="text-sm text-surface-400 font-semibold">/ 100</span>
                    </div>
                  </div>
                </div>
                <div class="p-6 rounded-2xl border border-emerald-200/70 bg-gradient-to-br from-emerald-50 via-white to-white flex items-center gap-5 shadow-sm shadow-emerald-100/50">
                  <div class="w-14 h-14 rounded-2xl bg-white border border-emerald-100 flex items-center justify-center flex-shrink-0 shadow-inner">
                    <Icon icon="mdi:domain" class="text-3xl text-emerald-600" />
                  </div>
                  <div>
                    <div class="text-xs text-surface-500 mb-1 tracking-wide">企业平均分 · 实战</div>
                    <div class="flex items-baseline gap-1">
                      <div class="text-3xl font-black text-emerald-700 tabular-nums">{{ summary.enterpriseAvg ?? '—' }}</div>
                      <span v-if="summary.enterpriseAvg != null" class="text-sm text-surface-400 font-semibold">/ 100</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 三栏评分详情卡片 -->
            <div>
              <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
                <div class="flex items-center gap-2">
                  <div class="w-1 h-4 bg-primary-500 rounded-full"></div>
                  <h3 class="font-display font-black text-ink text-lg">三方评分维度明细</h3>
                </div>
                <div class="text-xs text-surface-500 flex items-center gap-1">
                  <Icon icon="mdi:information-outline" inline width="13" />
                  仅展示当前选中提交的详情
                </div>
              </div>
              <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- AI 评分卡 -->
                <div class="rounded-2xl border border-violet-200/60 bg-white overflow-hidden shadow-sm">
                  <div class="px-6 py-4 bg-gradient-to-r from-violet-50 to-purple-50 border-b border-violet-100 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-xl bg-white flex items-center justify-center shadow-sm border border-violet-100">
                        <Icon icon="mdi:robot-outline" class="text-lg text-violet-600" />
                      </div>
                      <div>
                        <h4 class="font-bold text-ink text-[15px]">AI 评分</h4>
                        <p class="text-[11px] text-surface-500">
                          {{ current.evaluations.ai ? (current.evaluations.ai.created_at || '大模型自动评价') : '暂无 AI 评价数据' }}
                        </p>
                      </div>
                    </div>
                    <span v-if="current.evaluations.ai" class="bg-violet-500 text-white text-[10.5px] font-bold px-2.5 py-1 rounded-full shadow-sm shadow-violet-300/40">智能</span>
                    <span v-else class="bg-surface-200 text-surface-500 text-[10.5px] font-bold px-2.5 py-1 rounded-full">待生成</span>
                  </div>
                  <div class="p-6">
                    <div class="flex items-end justify-center mb-5">
                      <span class="text-5xl font-black text-violet-600 tabular-nums">{{ current.scores.aiScore ?? '—' }}</span>
                      <span v-if="current.scores.aiScore != null" class="text-xl font-bold text-surface-400 mb-1 ml-1">/ 100</span>
                    </div>
                    <div v-if="current.scores.aiScore != null" class="w-full bg-violet-100 rounded-full h-3 mb-6 overflow-hidden">
                      <div class="bg-gradient-to-r from-violet-500 to-purple-500 h-3 rounded-full transition-all" :style="{ width: current.scores.aiScore + '%' }"></div>
                    </div>
                    <div v-else class="mb-6 text-center text-xs text-surface-400 py-2 border border-dashed border-surface-200 rounded-xl">暂无 AI 评分数据</div>
                    <div class="space-y-3.5 max-h-[260px] overflow-y-auto pr-1">
                      <div v-for="dim in aiDimensions" :key="'ai_' + dim.name">
                        <div class="flex items-center justify-between mb-1.5">
                          <span class="text-[12.5px] font-medium text-surface-700">{{ dim.name }}</span>
                          <span class="text-[12px] font-bold text-violet-600 tabular-nums">{{ dim.score != null ? dim.score + '分' : '—' }}</span>
                        </div>
                        <div class="w-full bg-surface-100 rounded-full h-2 overflow-hidden">
                          <div v-if="dim.score != null" class="bg-violet-400 h-2 rounded-full" :style="{ width: dim.score + '%' }"></div>
                        </div>
                      </div>
                      <div v-if="!aiDimensions.length" class="text-xs text-surface-400 text-center py-4">暂无维度数据</div>
                    </div>
                  </div>
                </div>

                <!-- 教师评分卡 -->
                <div class="rounded-2xl border border-blue-200/60 bg-white overflow-hidden shadow-sm">
                  <div class="px-6 py-4 bg-gradient-to-r from-blue-50 to-sky-50 border-b border-blue-100 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-xl bg-white flex items-center justify-center shadow-sm border border-blue-100">
                        <Icon icon="mdi:account-tie-outline" class="text-lg text-blue-600" />
                      </div>
                      <div>
                        <h4 class="font-bold text-ink text-[15px]">教师评分</h4>
                        <p class="text-[11px] text-surface-500">
                          {{ current.evaluations.teacher ? (current.evaluations.teacher.created_at || '授课教师人工评价') : '暂无教师评价数据' }}
                        </p>
                      </div>
                    </div>
                    <span v-if="current.evaluations.teacher" class="bg-blue-500 text-white text-[10.5px] font-bold px-2.5 py-1 rounded-full shadow-sm shadow-blue-300/40">专业</span>
                    <span v-else class="bg-surface-200 text-surface-500 text-[10.5px] font-bold px-2.5 py-1 rounded-full">待评</span>
                  </div>
                  <div class="p-6">
                    <div class="flex items-end justify-center mb-5">
                      <span class="text-5xl font-black text-blue-600 tabular-nums">{{ current.scores.teacherScore ?? '—' }}</span>
                      <span v-if="current.scores.teacherScore != null" class="text-xl font-bold text-surface-400 mb-1 ml-1">/ 100</span>
                    </div>
                    <div v-if="current.scores.teacherScore != null" class="w-full bg-blue-100 rounded-full h-3 mb-6 overflow-hidden">
                      <div class="bg-gradient-to-r from-blue-500 to-sky-500 h-3 rounded-full transition-all" :style="{ width: current.scores.teacherScore + '%' }"></div>
                    </div>
                    <div v-else class="mb-6 text-center text-xs text-surface-400 py-2 border border-dashed border-surface-200 rounded-xl">暂无教师评分数据</div>
                    <div class="space-y-3.5 max-h-[260px] overflow-y-auto pr-1">
                      <div v-for="dim in teacherDimensions" :key="'tc_' + dim.name">
                        <div class="flex items-center justify-between mb-1.5">
                          <span class="text-[12.5px] font-medium text-surface-700">{{ dim.name }}</span>
                          <span class="text-[12px] font-bold text-blue-600 tabular-nums">{{ dim.score != null ? dim.score + '分' : '—' }}</span>
                        </div>
                        <div class="w-full bg-surface-100 rounded-full h-2 overflow-hidden">
                          <div v-if="dim.score != null" class="bg-blue-400 h-2 rounded-full" :style="{ width: dim.score + '%' }"></div>
                        </div>
                      </div>
                      <div v-if="!teacherDimensions.length" class="text-xs text-surface-400 text-center py-4">暂无维度数据</div>
                    </div>
                  </div>
                </div>

                <!-- 企业评分卡 -->
                <div class="rounded-2xl border border-emerald-200/60 bg-white overflow-hidden shadow-sm">
                  <div class="px-6 py-4 bg-gradient-to-r from-emerald-50 to-green-50 border-b border-emerald-100 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-xl bg-white flex items-center justify-center shadow-sm border border-emerald-100">
                        <Icon icon="mdi:domain" class="text-lg text-emerald-600" />
                      </div>
                      <div>
                        <h4 class="font-bold text-ink text-[15px]">企业评分</h4>
                        <p class="text-[11px] text-surface-500">
                          {{ current.evaluations.enterprise ? (current.evaluations.enterprise.mentor?.real_name || current.evaluations.enterprise.enterprise?.name || '企业专家标准评价') : '暂无企业评价数据' }}
                        </p>
                      </div>
                    </div>
                    <span v-if="current.evaluations.enterprise" class="bg-emerald-500 text-white text-[10.5px] font-bold px-2.5 py-1 rounded-full shadow-sm shadow-emerald-300/40">实战</span>
                    <span v-else class="bg-surface-200 text-surface-500 text-[10.5px] font-bold px-2.5 py-1 rounded-full">待评</span>
                  </div>
                  <div class="p-6">
                    <div class="flex items-end justify-center mb-5">
                      <span class="text-5xl font-black text-emerald-600 tabular-nums">{{ current.scores.enterpriseScore ?? '—' }}</span>
                      <span v-if="current.scores.enterpriseScore != null" class="text-xl font-bold text-surface-400 mb-1 ml-1">/ 100</span>
                    </div>
                    <div v-if="current.scores.enterpriseScore != null" class="w-full bg-emerald-100 rounded-full h-3 mb-6 overflow-hidden">
                      <div class="bg-gradient-to-r from-emerald-500 to-green-500 h-3 rounded-full transition-all" :style="{ width: current.scores.enterpriseScore + '%' }"></div>
                    </div>
                    <div v-else class="mb-6 text-center text-xs text-surface-400 py-2 border border-dashed border-surface-200 rounded-xl">暂无企业评分数据</div>
                    <div class="space-y-3.5 max-h-[260px] overflow-y-auto pr-1">
                      <div v-for="dim in enterpriseDimensions" :key="'en_' + dim.name">
                        <div class="flex items-center justify-between mb-1.5">
                          <span class="text-[12.5px] font-medium text-surface-700">{{ dim.name }}</span>
                          <span class="text-[12px] font-bold text-emerald-600 tabular-nums">{{ dim.score != null ? dim.score + '分' : '—' }}</span>
                        </div>
                        <div class="w-full bg-surface-100 rounded-full h-2 overflow-hidden">
                          <div v-if="dim.score != null" class="bg-emerald-400 h-2 rounded-full" :style="{ width: dim.score + '%' }"></div>
                        </div>
                      </div>
                      <div v-if="!enterpriseDimensions.length" class="text-xs text-surface-400 text-center py-4">暂无维度数据</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 差异高亮分析 -->
            <div>
              <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
                <div class="flex items-center gap-2">
                  <div class="w-1 h-4 bg-rose-500 rounded-full"></div>
                  <h3 class="font-display font-black text-ink text-lg">差异高亮分析</h3>
                  <span v-if="current.meta.needsReview" class="bg-rose-50 text-rose-600 text-xs font-bold px-2.5 py-0.5 rounded-full border border-rose-100">需复核</span>
                  <span v-else class="bg-emerald-50 text-emerald-600 text-xs font-bold px-2.5 py-0.5 rounded-full border border-emerald-100">自动检测</span>
                </div>
                <div v-if="current.meta.consistency != null" class="text-[12.5px] text-surface-500">
                  一致性指数：<b class="text-ink tabular-nums">{{ Math.round(Number(current.meta.consistency) * 100) }}</b> / 100
                </div>
              </div>
              <div class="rounded-2xl border border-surface-100 bg-white shadow-sm overflow-hidden">
                <div v-if="!diffHighlights.length" class="text-center py-14 text-surface-400 text-sm">
                  <Icon icon="mdi:cloud-check-outline" class="text-5xl mx-auto mb-3 opacity-50 text-emerald-400" />
                  <div class="font-semibold text-ink-2 mb-1">当前没有显著差异</div>
                  <div class="text-xs text-surface-500">AI、教师与企业三方的评分维度整体一致</div>
                </div>
                <div v-else class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-for="diff in diffHighlights" :key="'dh_' + diff.name"
                    class="p-5 rounded-2xl border transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
                    :class="[
                      diff.level === 'high' ? 'border-rose-200 bg-rose-50/50 hover:bg-rose-50' :
                      diff.level === 'medium' ? 'border-amber-200 bg-amber-50/50 hover:bg-amber-50' :
                      'border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50'
                    ]">
                    <div class="flex items-start justify-between mb-3">
                      <div class="flex items-center gap-2 flex-wrap min-w-0">
                        <span :class="[
                          diff.level === 'high' ? 'bg-rose-500' : diff.level === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'
                        ]" class="text-white text-[10.5px] font-bold px-2.5 py-1 rounded-lg shadow-sm">
                          {{ diff.level === 'high' ? '高差异' : diff.level === 'medium' ? '中差异' : '一致' }}
                        </span>
                        <span class="font-bold text-ink truncate">{{ diff.name }}</span>
                      </div>
                      <span :class="[
                        diff.level === 'high' ? 'text-rose-600' : diff.level === 'medium' ? 'text-amber-600' : 'text-emerald-600'
                      ]" class="text-xl font-black tabular-nums flex-shrink-0 ml-2">
                        ±{{ diff.diff }}
                      </span>
                    </div>
                    <div class="flex items-center justify-between text-[12px] mb-3 gap-2 flex-wrap">
                      <div class="flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-violet-500 flex-shrink-0"></span>
                        <span class="text-surface-600 whitespace-nowrap">AI: <b class="text-violet-600 tabular-nums">{{ diff.ai != null ? diff.ai : '—' }}</b></span>
                      </div>
                      <div class="flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0"></span>
                        <span class="text-surface-600 whitespace-nowrap">教师: <b class="text-blue-600 tabular-nums">{{ diff.teacher != null ? diff.teacher : '—' }}</b></span>
                      </div>
                      <div class="flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0"></span>
                        <span class="text-surface-600 whitespace-nowrap">企业: <b class="text-emerald-600 tabular-nums">{{ diff.enterprise != null ? diff.enterprise : '—' }}</b></span>
                      </div>
                    </div>
                    <p class="text-xs text-surface-500 leading-relaxed">{{ diff.advice || '三方评分保持一致，无需额外复核。' }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 弹窗底部操作栏 -->
            <div class="flex items-center justify-end gap-3 pt-4 border-t border-dashed border-surface-200">
              <button @click="closeDetail" class="btn-mag btn-mag-ghost px-5 py-2.5 text-[13px]">关闭</button>
            </div>
          </div>
        </div>
      </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { API_BASE } from '../config'
import { useRouter } from 'vue-router'

// Token：Header + URL 双保险（后端 _extract_token 同时支持两种方式）
const __TOKEN__ = (() => {
  const t = localStorage.getItem('token')
  return t ? String(t).trim() : ''
})()
function authConfig(cfg: any = {}): any {
  const headers: any = cfg.headers ? { ...cfg.headers } : {}
  const params: any = cfg.params ? { ...cfg.params } : {}
  if (__TOKEN__) {
    headers.Authorization = `Bearer ${__TOKEN__}`
    params.token = __TOKEN__
  }
  return { ...cfg, headers, params }
}

const authHeaders = () => {
  const headers: any = {}
  if (__TOKEN__) headers.Authorization = `Bearer ${__TOKEN__}`
  return headers
}

// 筛选条件
const filterClass = ref('')
const filterTask = ref('')
const filterStudent = ref('')
const filterDate = ref<any>(null)
const selectedSubmissionId = ref<number | null>(null)

// 详情弹窗开关与当前行
const detailVisible = ref(false)
const detailRow = ref<any>(null)

// 防滚动穿透：打开弹窗时锁定 body 滚动，关闭时恢复（记录原值，避免误清）
let __prevBodyOverflow = ''
function _lockBody(lock: boolean) {
  if (typeof document === 'undefined' || !document.body) return
  if (lock) {
    if (document.body.style.overflow !== 'hidden') {
      __prevBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
    }
  } else {
    if (document.body.style.overflow === 'hidden') {
      document.body.style.overflow = __prevBodyOverflow || ''
    }
  }
}
watch(detailVisible, v => _lockBody(!!v), { flush: 'post' })
onBeforeUnmount(() => _lockBody(false))

function closeDetail() {
  detailVisible.value = false
  // 不立即清空 detailRow，避免弹窗关闭动画期间标题/数据闪烁
}

// 加载与错误
const loading = ref(false)
const loadError = ref('')

// 页面展示数据：真实接口
const filters = reactive({
  classes: [] as any[],
  tasks: [] as any[],
  students: [] as any[],
})
const summary = reactive({
  aiAvg: null as number | null,
  teacherAvg: null as number | null,
  enterpriseAvg: null as number | null,
  count: 0,
})
const historyData = ref<any[]>([])
const current = reactive({
  scores: { aiScore: null as number | null, teacherScore: null as number | null, enterpriseScore: null as number | null },
  evaluations: { ai: null as any, teacher: null as any, enterprise: null as any },
  meta: { consistency: null as number | null, needsReview: false },
  dimension_breakdown: [] as any[],
})

// 派生：三方维度
const aiDimensions = computed(() => (current.dimension_breakdown || []).map((d: any) => ({
  name: d.name,
  score: typeof d.ai_score === 'number' ? Math.round(d.ai_score) : d.ai_score,
})))
const teacherDimensions = computed(() => (current.dimension_breakdown || []).map((d: any) => ({
  name: d.name,
  score: typeof d.teacher_score === 'number' ? Math.round(d.teacher_score) : d.teacher_score,
})))
const enterpriseDimensions = computed(() => (current.dimension_breakdown || []).map((d: any) => ({
  name: d.name,
  score: typeof d.enterprise_score === 'number' ? Math.round(d.enterprise_score) : d.enterprise_score,
})))

// 派生：差异高亮
const diffHighlights = computed(() => {
  const list = current.dimension_breakdown || []
  if (!list.length) return []
  return list.map((d: any) => {
    const vals = [d.ai_score, d.teacher_score, d.enterprise_score].filter(v => typeof v === 'number')
    const diff = vals.length ? Math.round((Math.max(...vals) - Math.min(...vals))) : 0
    const level = diff >= 20 ? 'high' : diff >= 10 ? 'medium' : 'low'
    let advice = d.warning || ''
    if (!advice) {
      if (level === 'high') advice = `三方在「${d.name}」维度差异超过 20 分，建议组织跨方复盘对齐标准。`
      else if (level === 'medium') advice = `「${d.name}」维度存在一定差异，建议确认评价侧重点并统一打分口径。`
      else advice = `「${d.name}」维度三方评价高度一致，保持当前评价方式。`
    }
    return {
      name: d.name,
      level,
      diff,
      ai: typeof d.ai_score === 'number' ? Math.round(d.ai_score) : d.ai_score,
      teacher: typeof d.teacher_score === 'number' ? Math.round(d.teacher_score) : d.teacher_score,
      enterprise: typeof d.enterprise_score === 'number' ? Math.round(d.enterprise_score) : d.enterprise_score,
      advice,
    }
  })
})

function resetFilters() {
  filterClass.value = ''
  filterTask.value = ''
  filterStudent.value = ''
  filterDate.value = null
  selectedSubmissionId.value = null
  detailRow.value = null
  detailVisible.value = false
  runCompare(true)
}

function onHistoryRowClick(row: any) {
  selectHistory(row)
}

function selectHistory(row: any) {
  const sid = Number(row.submission_id)
  if (!sid || Number.isNaN(sid)) return
  detailRow.value = row
  selectedSubmissionId.value = sid
  // 先打开弹窗（loading=true 时展示骨架/loading态即可），runCompare 内会用 submission_id 拉取三栏详情
  detailVisible.value = true
  runCompare()
}

async function runCompare(forceAll = false) {
  loading.value = true
  loadError.value = ''
  try {
    if (!__TOKEN__) {
      ElMessage.warning('请先登录企业导师账号')
      setTimeout(() => useRouter().push({
        path: '/login',
        query: { redirect: '/app/enterprise/compare' },
      }), 400)
      return
    }

    const params: any = {}
    if (filterClass.value) params.class_id = Number(filterClass.value)
    if (filterTask.value) params.task_id = Number(filterTask.value)
    if (filterStudent.value) params.student_id = Number(filterStudent.value)
    if (Array.isArray(filterDate.value) && filterDate.value.length === 2) {
      params.date_from = filterDate.value[0]
      params.date_to = filterDate.value[1]
    }
    if (selectedSubmissionId.value != null) {
      params.submission_id = selectedSubmissionId.value
    } else if (forceAll) {
      // 无选中项
    }

    // 筛选条件摘要（用于空结果时给用户明确提示）
    const filterSummary = (() => {
      const parts: string[] = []
      if (filterClass.value)   parts.push('班级')
      if (filterTask.value)    parts.push('任务')
      if (filterStudent.value) parts.push('学生')
      if (Array.isArray(filterDate.value) && filterDate.value.length === 2) parts.push('日期范围')
      return parts.length ? parts.join('、') : ''
    })()

    let resp: any
    try {
      resp = await axios.get(`${API_BASE}/api/enterprise/evaluations/compare-summary`, authConfig({ params }))
    } catch (httpErr: any) {
      const is401 = httpErr?.response?.status === 401
      const is403 = httpErr?.response?.status === 403
      const detail =
        httpErr?.response?.data?.detail ||
        httpErr?.response?.data?.error  ||
        httpErr?.message ||
        '网络异常'
      if (is401) {
        ElMessage.error('登录状态已过期，请重新登录企业导师账号')
        setTimeout(() => useRouter().push({
          path: '/login',
          query: { redirect: '/app/enterprise/compare' },
        }), 500)
        throw httpErr
      }
      if (is403) {
        ElMessage.error(`无权限访问该班级（错误：${detail}）`)
        throw httpErr
      }
      ElMessage.error(`加载对比数据失败：${detail}`)
      throw httpErr
    }

    const data = resp?.data
    const payload: any = data?.success === true ? data : (data?.data || data)

    // summary
    const s = payload.summary || {}
    summary.aiAvg = s.ai_avg ?? null
    summary.teacherAvg = s.teacher_avg ?? null
    summary.enterpriseAvg = s.enterprise_avg ?? null
    summary.count = Number(s.count ?? 0)

    // filters
    const f = payload.filters || {}
    filters.classes = Array.isArray(f.classes) ? f.classes : []
    filters.tasks = Array.isArray(f.tasks) ? f.tasks : []
    filters.students = Array.isArray(f.students) ? f.students : []

    // history
    const hist = Array.isArray(payload.history) ? payload.history : []
    historyData.value = hist.map((h: any) => ({ ...h, diffLevel: h.diff_level || 'low' }))

    // current：若接口没返回 current，但 history 里有一条且选中了 submission_id，降级为纯 summary 展示
    const cur: any = payload.current || null
    if (cur) {
      const parties = Array.isArray(cur.parties) ? cur.parties : []
      const aiP = parties.find((p: any) => p.role === 'ai')
      const tcP = parties.find((p: any) => p.role === 'teacher')
      const enP = parties.find((p: any) => p.role === 'enterprise')
      current.scores.aiScore = aiP?.total != null ? Math.round(Number(aiP.total)) : null
      current.scores.teacherScore = tcP?.total != null ? Math.round(Number(tcP.total)) : null
      current.scores.enterpriseScore = enP?.total != null ? Math.round(Number(enP.total)) : null
      current.evaluations.ai = cur.evaluations?.ai || null
      current.evaluations.teacher = cur.evaluations?.teacher || null
      current.evaluations.enterprise = cur.evaluations?.enterprise || null
      current.meta.consistency = cur.summary?.consistency_index ?? null
      current.meta.needsReview = !!cur.summary?.needs_review
      current.dimension_breakdown = Array.isArray(cur.dimension_breakdown) ? cur.dimension_breakdown : []
    } else {
      // 没有选中 submission：不展示三栏详情数据
      current.scores.aiScore = null
      current.scores.teacherScore = null
      current.scores.enterpriseScore = null
      current.evaluations.ai = null
      current.evaluations.teacher = null
      current.evaluations.enterprise = null
      current.meta.consistency = null
      current.meta.needsReview = false
      current.dimension_breakdown = []
    }

    // ===== 无数据时给出明确反馈，避免用户感觉"点击无响应" =====
    if (!historyData.value.length) {
      const hasFilter = !!(filterClass.value || filterTask.value || filterStudent.value ||
        (Array.isArray(filterDate.value) && filterDate.value.length === 2))
      if (hasFilter) {
        ElMessage.warning(
          `当前${filterSummary}筛选下没有符合条件的企业评价记录。` +
          `注意：该页面仅展示【按企业岗位设计】（is_enterprise_project=1）的任务评价，` +
          `可尝试放宽筛选条件。`
        )
      } else if (!filters.classes.length && !filters.tasks.length && !filters.students.length) {
        ElMessage.warning(
          '当前企业导师暂无可对比数据：请先在「岗位管理」发布岗位，' +
          '再在「企业评价」中对「按企业岗位设计」的任务完成至少一次企业评分后再来对比。'
        )
      } else {
        ElMessage.warning('当前没有可对比的企业评价记录，可更换筛选条件或等待学生完成企业评分。')
      }
    } else if (forceAll) {
      // 手动点击开始对比 + 有数据时给出成功反馈（短提示避免打扰）
      ElMessage({
        type: 'success',
        message: `已加载 ${historyData.value.length} 条对比记录`,
        duration: 1500,
        grouping: true,
        showClose: false,
      })
    }

    loadError.value = ''
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '接口请求失败'
    loadError.value = `三方对比加载失败：${msg}（请确认后端服务已启动，当前企业账号已发布岗位并完成至少一次企业评价）`
    historyData.value = []
    filters.classes = []
    filters.tasks = []
    filters.students = []
    summary.aiAvg = null
    summary.teacherAvg = null
    summary.enterpriseAvg = null
    summary.count = 0
    current.scores.aiScore = null
    current.scores.teacherScore = null
    current.scores.enterpriseScore = null
    current.evaluations.ai = null
    current.evaluations.teacher = null
    current.evaluations.enterprise = null
    current.meta.consistency = null
    current.meta.needsReview = false
    current.dimension_breakdown = []
  } finally {
    loading.value = false
  }
}

onMounted(() => runCompare())
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
:deep(.el-table .is-current-selected td) {
  background-color: #fff7ed !important;
}
:deep(.el-table .el-table__row:hover td) {
  cursor: pointer;
}
</style>
