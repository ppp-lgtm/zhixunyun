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
            <el-table-column prop="title" label="任务标题" min-width="240">
              <template #default="{ row }">
                <div class="flex items-start gap-3">
                  <div class="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Icon icon="mdi:file-document" class="text-primary-500" />
                  </div>
                  <div class="min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="font-medium text-gray-800">{{ row.title }}</span>
                      <span v-if="row.is_enterprise_project"
                            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold border border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50 text-orange-600 shadow-[0_1px_0_rgba(251,146,60,0.1)]">
                        <Icon icon="mdi:office-building" inline width="12" />
                        企业级项目实训
                        <span v-if="row.enterprise_label" class="opacity-75 ml-0.5">· {{ row.enterprise_label.enterprise_name }} / {{ row.enterprise_label.job_title }}</span>
                      </span>
                    </div>
                    <div class="text-[11.5px] text-gray-400 mt-1">
                      <span v-if="row.created_at">{{ String(row.created_at).slice(0, 16) }}</span>
                      <span v-if="row.status === 'draft'" class="ml-2 text-amber-600">草稿</span>
                      <span v-else-if="row.status === 'paused'" class="ml-2 text-gray-500">已暂停</span>
                      <span v-else-if="row.status === 'closed'" class="ml-2 text-gray-500">已截止</span>
                      <span v-else class="ml-2 text-emerald-600">已发布</span>
                    </div>
                  </div>
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
    <el-dialog v-model="showCreate" :title="(isEnterpriseMode ? '按企业岗位设计实训任务' : '发布实训任务') + (generated ? ' · 完善信息' : '')" width="860px" class="modern-dialog">
      <div class="mb-5 -mt-1">
        <div role="tablist" class="inline-flex items-center gap-1 p-1 rounded-2xl bg-gray-100/80 border border-gray-200 text-sm font-semibold">
          <button
            role="tab"
            :aria-selected="!isEnterpriseMode"
            type="button"
            class="px-4 py-2 rounded-xl transition-all"
            :class="!isEnterpriseMode ? 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-200' : 'text-gray-500 hover:text-gray-700'"
            @click="switchCreateMode(false)">
            <Icon icon="mdi:teacher" class="mr-1 align-text-bottom" inline width="16" />
            教师自主设计
          </button>
          <button
            role="tab"
            :aria-selected="isEnterpriseMode"
            type="button"
            class="px-4 py-2 rounded-xl transition-all"
            :class="isEnterpriseMode ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-[0_8px_20px_-8px_rgba(251,146,60,0.6)] ring-1 ring-orange-400/30' : 'text-gray-500 hover:text-gray-700'"
            @click="switchCreateMode(true)">
            <Icon icon="mdi:office-building" class="mr-1 align-text-bottom" inline width="16" />
            按企业岗位设计
            <span class="ml-1 px-1.5 py-0.5 rounded-md text-[10px] leading-none" :class="isEnterpriseMode ? 'bg-white/20 text-white' : 'bg-orange-100 text-orange-600'">AI</span>
          </button>
        </div>
      </div>

      <!-- 企业岗位模式：先选岗位 -->
      <div v-if="isEnterpriseMode && !generated" class="py-2">
        <div class="rounded-2xl border border-orange-200 bg-gradient-to-br from-orange-50/60 via-amber-50/40 to-white p-5">
          <div class="flex items-start gap-3 mb-4">
            <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 text-white flex items-center justify-center shadow-[0_8px_16px_-8px_rgba(251,146,60,0.6)] flex-shrink-0">
              <Icon icon="mdi:briefcase-star" class="text-xl" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[13.5px] font-bold text-orange-900/90">选择企业发布的岗位，AI 将按岗位要求自动生成实训任务</div>
              <div class="text-[12px] text-orange-900/60 mt-0.5">发布后会在学生端、评分工作台特殊标记为「企业级项目实训」</div>
            </div>
            <button type="button" @click="loadEnterpriseJobs(true)" :disabled="loadingJobs"
                    class="px-3 py-1.5 rounded-lg text-[12px] font-semibold border border-orange-200 bg-white text-orange-600 hover:bg-orange-50">
              <Icon v-if="loadingJobs" icon="mdi:loading" class="mr-1 animate-spin" inline width="12" />
              <Icon v-else icon="mdi:refresh" class="mr-1" inline width="12" />刷新
            </button>
          </div>

          <div class="mb-3 flex items-center gap-2 flex-wrap">
            <div class="relative flex-1 min-w-[240px]">
              <Icon icon="mdi:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" inline width="15" />
              <input v-model="enterpriseKeyword" @input="debounceReloadJobs" placeholder="搜索企业 / 岗位名称 / 城市 / 标签…"
                     class="w-full h-10 pl-9 pr-3 rounded-xl border border-gray-200 bg-white text-[13px] text-gray-800 outline-none focus:border-orange-300 focus:shadow-[0_0_0_4px_rgba(251,146,60,0.1)]" />
            </div>
            <div class="text-[12px] text-gray-500">
              共 <b class="text-gray-700">{{ enterpriseTotal }}</b> 个公开岗位
            </div>
          </div>

          <div class="rounded-xl border border-gray-200 bg-white overflow-hidden">
            <div v-if="loadingJobs && !enterpriseJobs.length" class="py-14 text-center text-gray-400 text-sm">
              <Icon icon="mdi:loading" class="animate-spin text-2xl mb-2 block mx-auto" />正在加载企业发布的岗位…
            </div>
            <div v-else-if="!enterpriseJobs.length" class="py-14 text-center">
              <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gray-100 flex items-center justify-center text-gray-400">
                <Icon icon="mdi:briefcase-off-outline" class="text-3xl" />
              </div>
              <div class="text-gray-500 text-sm mb-1">暂无企业公开岗位</div>
              <div class="text-gray-400 text-xs">可切换到「教师自主设计」创建普通实训任务</div>
            </div>
            <div v-else class="max-h-[320px] overflow-y-auto divide-y divide-gray-100">
              <label
                v-for="j in enterpriseJobs"
                :key="j.id"
                class="flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-orange-50/60 transition-colors"
                :class="{ 'bg-orange-50': selectedEnterpriseJobId === j.id }">
                <input type="radio" :value="j.id" v-model="selectedEnterpriseJobId" class="mt-1 accent-orange-500 w-4 h-4 flex-shrink-0" />
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-bold text-gray-800">{{ j.title }}</span>
                    <span class="text-[11px] px-1.5 py-0.5 rounded-md bg-gray-100 text-gray-600">{{ j.level || '初级' }}</span>
                    <span class="text-[11px] px-1.5 py-0.5 rounded-md bg-orange-50 text-orange-600 border border-orange-100">{{ j.city || '远程' }}</span>
                    <span v-if="j.salary_range" class="text-[11px] font-bold text-orange-600">{{ j.salary_range }}</span>
                  </div>
                  <div class="text-[12px] text-gray-500 mt-1">
                    <span class="font-semibold text-gray-700">{{ j.enterprise_name || '企业' }}</span>
                    <span class="mx-1.5 text-gray-300">·</span>
                    <span>标签：{{ (j.tag_list || []).slice(0, 6).join(' / ') || '—' }}</span>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <div class="mt-4 flex items-center justify-between">
            <div class="text-[12px] text-gray-500">
              <span v-if="enterpriseLoadError" class="text-orange-600">
                <Icon icon="mdi:alert-circle-outline" class="mr-1" inline width="13" />{{ enterpriseLoadError }}
              </span>
              <span v-else>AI 会结合岗位的职责、技能门槛、标签，生成一套可执行的实训任务（教师可修改后发布）</span>
            </div>
            <div class="flex items-center gap-2">
              <button type="button" @click="manualInput" class="px-4 py-2 rounded-xl text-[12.5px] font-semibold border border-gray-200 bg-white text-gray-600 hover:bg-gray-50">
                跳过 AI，直接编辑
              </button>
              <button type="button" @click="aiGenerateFromJob"
                :disabled="!selectedEnterpriseJobId || generating"
                class="px-5 py-2.5 rounded-xl text-[13px] font-bold text-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                :class="!selectedEnterpriseJobId || generating
                  ? 'bg-gray-300'
                  : 'bg-gradient-to-r from-orange-500 to-amber-500 hover:shadow-[0_12px_26px_-10px_rgba(251,146,60,0.7)]'">
                <Icon v-if="generating" icon="mdi:loading" class="mr-1 animate-spin" inline width="14" />
                <Icon v-else icon="mdi:auto-fix" class="mr-1" inline width="14" />
                AI 按岗位生成实训
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 非企业模式（原逻辑：先 title + difficulty） -->
      <div v-else-if="!generated" class="py-4">
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
          <button class="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-10 py-4 rounded-xl text-lg font-medium flex items-center gap-2 mx-auto hover:shadow-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="!form.title || generating"
            @click="aiGenerate">
            <span v-if="generating" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <Icon v-else icon="mdi:robot-outline" class="inline align-text-bottom" />
            {{ generating ? '生成中…' : 'AI 生成实训要求' }}
          </button>
          <p v-if="!form.title" class="text-orange-500 text-sm mt-3">请先输入任务标题</p>
        </div>
      </div>

      <div v-if="generated" class="py-4">
        <!-- 企业级标记条 -->
        <div v-if="isEnterpriseMode"
             class="mb-5 rounded-2xl border border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50 px-5 py-3.5 flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 text-white flex items-center justify-center flex-shrink-0 shadow-[0_6px_14px_-6px_rgba(251,146,60,0.7)]">
            <Icon icon="mdi:certificate-outline" class="text-lg" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-[13px] font-bold text-orange-900">发布后此任务将被特殊标记为「企业级项目实训」</div>
            <div class="text-[11.5px] text-orange-900/70 mt-0.5">
              来源岗位：{{ selectedEnterpriseJob?.enterprise_name || '企业' }} · {{ selectedEnterpriseJob?.title || '—' }}
              <span v-if="selectedEnterpriseJob?.salary_range"> · {{ selectedEnterpriseJob.salary_range }}</span>
              <span v-if="selectedEnterpriseJob?.city"> · {{ selectedEnterpriseJob.city }}</span>
            </div>
          </div>
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold border border-orange-200 bg-white text-orange-600 shadow-[0_1px_0_rgba(251,146,60,0.08)]">
            <Icon icon="mdi:office-building" inline width="12" /> 企业级项目实训
          </span>
        </div>

        <el-form :model="form" label-width="100px">
          <el-form-item label="任务标题">
            <el-input v-model="form.title" size="large" />
          </el-form-item>

          <el-form-item label="实训要求" required>
            <el-input v-model="form.requirements" type="textarea" :rows="4" />
          </el-form-item>

          <el-form-item label="评分维度">
            <!-- 企业模式 · 评分维度与岗位技能门槛对齐提示 -->
            <div v-if="isEnterpriseMode && generated && selectedEnterpriseJob?.skill_requirements?.length"
                 class="mb-4 rounded-2xl border border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50 px-5 py-4">
              <div class="flex items-start gap-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 text-white flex items-center justify-center flex-shrink-0 shadow-[0_6px_14px_-6px_rgba(251,146,60,0.7)]">
                  <Icon icon="mdi:link-variant" class="text-lg" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-[13px] font-bold text-orange-900">
                    评分维度已与岗位技能门槛对齐 · 三方评分标准统一
                  </div>
                  <div class="text-[11.5px] text-orange-900/70 mt-0.5">
                    来源岗位：{{ selectedEnterpriseJob.enterprise_name || '企业' }} · {{ selectedEnterpriseJob.title || '—' }}
                    · 最终保存时，维度名称和权重将以岗位设置为准（即使你在下方表格中修改）
                  </div>
                  <div class="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    <div v-for="(s, idx) in selectedEnterpriseJob.skill_requirements" :key="idx"
                         class="rounded-xl border border-orange-200/70 bg-white/70 px-3 py-2.5">
                      <div class="flex items-center gap-2">
                        <span class="text-[12.5px] font-semibold text-orange-900 truncate">{{ s.name || ('维度 ' + (idx+1)) }}</span>
                        <span v-if="s.must" class="text-[10.5px] px-1.5 py-0.5 rounded-md bg-orange-500/15 text-orange-700 border border-orange-500/20 font-mono">必达</span>
                        <span v-else class="text-[10.5px] px-1.5 py-0.5 rounded-md bg-blue-500/10 text-blue-700 border border-blue-500/20 font-mono">加分</span>
                      </div>
                      <div class="mt-1.5 flex items-center gap-3 text-[11px] text-orange-900/70 font-mono">
                        <span>权重 <b class="text-orange-900">{{ s.weight_pct ?? s.weight ?? '—' }}%</b></span>
                        <span>门槛 <b class="text-orange-900">{{ s.threshold ?? '—' }}/100</b></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
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
          <button v-if="!generated && !isEnterpriseMode"
                  class="px-6 py-2.5 border border-gray-200 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors"
                  @click="manualInput">
            跳过AI，手动填写
          </button>
          <button v-if="generated" class="btn-primary text-white px-6 py-2.5 rounded-xl text-sm font-medium" @click="createTask" :disabled="saving">
            <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
            <span>{{ saving ? '发布中...' : (isEnterpriseMode ? '发布企业级项目实训' : '发布') }}</span>
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 提交详情弹窗 -->
    <el-dialog v-model="showDetail" :title="detailTask ? '提交详情 - ' + detailTask.task?.title : ''" width="1000px" class="modern-dialog">
      <div v-if="detailTask" class="py-4">
        <div class="rounded-xl border border-blue-100 bg-blue-50 p-4 mb-6">
          <div v-if="detailTask.task?.is_enterprise_project"
               class="mb-3 flex items-center gap-2 flex-wrap pb-3 border-b border-blue-100/60">
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11.5px] font-bold border border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50 text-orange-600 shadow-[0_1px_0_rgba(251,146,60,0.1)]">
              <Icon icon="mdi:office-building" inline width="13" /> 企业级项目实训
            </span>
            <span v-if="detailTask.task?.enterprise_label"
                  class="text-[12px] font-semibold text-orange-800">
              {{ detailTask.task.enterprise_label.enterprise_name }} · {{ detailTask.task.enterprise_label.job_title }}
            </span>
          </div>
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

// ===== 企业岗位联动 =====
const isEnterpriseMode = ref(false)
const loadingJobs = ref(false)
const enterpriseJobs = ref<any[]>([])
const enterpriseTotal = ref(0)
const enterpriseKeyword = ref('')
const enterpriseLoadError = ref('')
const selectedEnterpriseJobId = ref<number | null>(null)
const enterprisePage = ref(1)
const enterprisePageSize = ref(50)
let _jobsTimer: any = null

const selectedEnterpriseJob = computed<any | null>(() => {
  if (!selectedEnterpriseJobId.value) return null
  return enterpriseJobs.value.find((j) => j.id === selectedEnterpriseJobId.value) || null
})

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function _readLoginInfo(): { token: string; tokenEmpty: boolean; userRole: string; userId: string | number | null; userName: string } {
  const token = localStorage.getItem('token') || ''
  let userRole = ''
  let userId: string | number | null = null
  let userName = ''
  try {
    const u = JSON.parse(localStorage.getItem('user') || 'null')
    if (u && typeof u === 'object') {
      userRole = String(u.role || '')
      userId = u.id ?? null
      userName = u.real_name || u.username || ''
    }
  } catch {}
  return { token, tokenEmpty: !token, userRole, userId, userName }
}

function _friendlyAuthMsg(status: number, rawErr: string, hint = '可切换到教师自主设计模式创建'): string {
  const info = _readLoginInfo()
  if (info.tokenEmpty) {
    return `企业岗位加载失败：未登录（localStorage.token 为空）。\n请先退出后用教师账号登录，${hint}。\n[调试信息] user=${info.userName || '空'} role=${info.userRole || '空'}`
  }
  // 尝试从 JWT payload 里读出 role/user_id（不校验签名，只看结构）
  let tokRole = ''; let tokUid = ''; let tokExp = ''
  try {
    const parts = info.token.split('.')
    if (parts.length >= 2) {
      const payload = JSON.parse(decodeURIComponent(atob(parts[1]).split('').map((ch) => '%' + ('00' + ch.charCodeAt(0).toString(16)).slice(-2)).join('')))
      tokRole = String(payload.role || '')
      tokUid = String(payload.user_id ?? payload.id ?? '')
      if (payload.exp) {
        const d = new Date(payload.exp * 1000)
        tokExp = d.toLocaleString()
        if (Date.now() > payload.exp * 1000) tokExp += '（已过期）'
      }
    }
  } catch {}
  if (status === 401) {
    return `企业岗位加载失败（HTTP 401，登录态无效）。\n`
      + `[localStorage] token=${info.token ? info.token.slice(0, 14) + '…' : '空'} user.role=${info.userRole || '空'} id=${info.userId || '空'}\n`
      + `[token 载荷只读] role=${tokRole || '空'} user_id=${tokUid || '空'} exp=${tokExp || '无法解析'}\n`
      + (tokExp.includes('已过期') ? '原因：token 已过期 → 请退出后重新登录。\n' : '')
      + (info.userRole && !['teacher','admin','enterprise'].includes(info.userRole) ? `原因：user.role=${info.userRole} 不是 teacher/admin/enterprise 角色 → 请用教师账号登录。\n` : '')
      + (tokRole && !['teacher','admin','enterprise'].includes(tokRole) ? `原因：token 内 role=${tokRole} 不是 teacher/admin/enterprise 角色 → 请退出后用教师账号重新登录。\n` : '')
      + `原始错误：${rawErr}\n建议：退出登录 → 用教师账号重新登录；或${hint}。`
  }
  if (status === 403) {
    return `企业岗位加载失败（HTTP 403，权限不足）。\n`
      + `当前 user.role=${info.userRole || '空'}，token.role=${tokRole || '空'}。该接口仅 teacher/admin/enterprise 可访问。`
      + `原始错误：${rawErr}`
  }
  return `企业岗位加载失败：${rawErr}（${hint}）。\n[调试] user.role=${info.userRole || '空'}`
}

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
  isEnterpriseMode.value = false
  enterpriseKeyword.value = ''
  enterpriseLoadError.value = ''
  selectedEnterpriseJobId.value = null
  enterpriseJobs.value = []
  enterpriseTotal.value = 0
  showCreate.value = true
}

const switchCreateMode = (toEnterprise: boolean) => {
  if (isEnterpriseMode.value === toEnterprise) return
  if (generated.value && !confirm('切换模式会清空已生成内容，确定切换吗？')) return
  isEnterpriseMode.value = toEnterprise
  generated.value = false
  form.title = ''
  form.difficulty = '普通'
  form.requirements = ''
  form.template_content = ''
  criteriaList.value = []
  if (toEnterprise) {
    void loadEnterpriseJobs(false)
  }
}

async function loadEnterpriseJobs(force = false) {
  loadingJobs.value = true
  enterpriseLoadError.value = ''
  try {
    const params: any = { page: enterprisePage.value, page_size: enterprisePageSize.value }
    if (enterpriseKeyword.value.trim()) params.keyword = enterpriseKeyword.value.trim()
    const res = await axios.get(`${API_BASE}/api/tasks/enterprise-jobs`, { params, headers: authHeaders() })
    if (res.data?.success === false) throw new Error(res.data?.message || res.data?.error || '加载失败')
    // 后端返回字段在顶层（success/total/page/page_size/list），也兼容包一层 data 的情况
    const d = (res.data && typeof res.data === 'object' && (Array.isArray(res.data.list) || res.data.total != null))
      ? res.data
      : (res.data?.data ?? res.data ?? {})
    const list: any[] = Array.isArray(d.list) ? d.list : (Array.isArray(d.jobs) ? d.jobs : (Array.isArray(d.data) ? d.data : []))
    enterpriseJobs.value = list
    enterpriseTotal.value = Number(d.total ?? list.length)
    if (!force && list.length && !selectedEnterpriseJobId.value) {
      selectedEnterpriseJobId.value = list[0].id
    }
  } catch (e: any) {
    enterpriseJobs.value = []
    enterpriseTotal.value = 0
    const status = Number(e?.response?.status ?? 0)
    const rawMsg = String(e?.response?.data?.detail ?? e?.response?.data?.message ?? e?.response?.data?.error ?? e?.message ?? '接口请求失败')
    enterpriseLoadError.value = _friendlyAuthMsg(status, rawMsg, '可切换到教师自主设计模式创建')
    // 同时在控制台打印一次（方便你截图/定位）
    console.warn('[TaskManage:loadEnterpriseJobs] 401/403 调试快照 =', {
      login: _readLoginInfo(),
      status,
      response: e?.response?.data,
      message: rawMsg,
    })
  } finally {
    loadingJobs.value = false
  }
}

const debounceReloadJobs = () => {
  if (_jobsTimer) clearTimeout(_jobsTimer)
  _jobsTimer = setTimeout(() => loadEnterpriseJobs(false), 280)
}

const aiGenerate = async () => {
  if (!form.title) { ElMessage.warning('请输入任务标题'); return }
  generating.value = true
  try {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), 22000)
    const res = await axios.post(`${API_BASE}/api/tasks/generate`, {
      title: form.title,
      difficulty: form.difficulty
    }, {
      signal: controller.signal,
      timeout: 22000,
      headers: authHeaders(),
    })
    clearTimeout(timer)
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
      // ⚠️ 诚实显示后端返回的错误（多行用 ElMessageBox.alert，方便复制 / 查看完整错误）
      const errMsg = String(res.data.error ?? res.data.message ?? 'AI 生成失败，请重试')
      try {
        await ElMessageBox.alert(errMsg, 'AI 生成失败', {
          confirmButtonText: '知道了',
          type: 'error',
          dangerouslyUseHTMLString: false,
          customClass: 'tm-err-dialog'
        })
      } catch { /* user closed */ }
    }
  } catch (e: any) {
    let msg: string
    if (e?.code === 'ERR_CANCELED' || e?.name === 'AbortError') {
      msg = '前端请求超时（22s），已中止。\n\n可能原因：\n  1) 后端服务未启动或端口不对（默认 8000）\n  2) 后端调 AI 超过 15s 未返回\n\n请检查后端日志或配好 DEEPSEEK_API_KEY 后重试。'
    } else if (e?.code === 'ERR_NETWORK' || e?.message?.includes('Network Error')) {
      msg = `无法连接后端（${API_BASE ?? ''}）：${e?.message ?? e}\n\n请确认后端已启动（python run.py），且前端 VITE_API_BASE 指向正确端口。`
    } else {
      msg = String(e?.response?.data?.error ?? e?.response?.data?.message ?? e?.message ?? e ?? '请求失败')
    }
    try {
      await ElMessageBox.alert(msg, '请求失败', {
        confirmButtonText: '知道了',
        type: 'error',
        dangerouslyUseHTMLString: false,
      })
    } catch { /* user closed */ }
  } finally { generating.value = false }
}

const aiGenerateFromJob = async () => {
  if (!selectedEnterpriseJobId.value) {
    ElMessage.warning('请先选择一个企业岗位')
    return
  }
  generating.value = true
  try {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), 30000)
    const res = await axios.post(
      `${API_BASE}/api/tasks/ai-from-job`,
      { job_id: selectedEnterpriseJobId.value },
      { signal: controller.signal, timeout: 30000, headers: authHeaders() }
    )
    clearTimeout(timer)
    if (res.data?.success === false) {
      const errMsg = String(res.data?.error ?? res.data?.message ?? 'AI 生成失败')
      try {
        await ElMessageBox.alert(errMsg, 'AI 生成失败', { confirmButtonText: '知道了', type: 'error' })
      } catch {}
      return
    }
    // 后端返回结构可能：{success, draft:{title,requirements_text,template_content,grading_dimensions,criteria,criteria_weights}}
    // 或 {success, data:{title,requirements,template,criteria/grading_dimensions}}
    const draft = (res.data?.draft && typeof res.data.draft === 'object' && (res.data.draft.title || res.data.draft.requirements_text))
      ? res.data.draft
      : (res.data?.data ?? res.data ?? {})
    const payload: any = draft
    if (payload.title) form.title = String(payload.title)
    // requirements_text > requirements（数组） > description fallback
    if (payload.requirements_text) {
      form.requirements = String(payload.requirements_text)
    } else if (Array.isArray(payload.requirements) && payload.requirements.length) {
      form.requirements = (payload.requirements as any[])
        .map((x: any, i: number) => `${i + 1}. ${String(x).trim()}`)
        .join('\n')
    } else if (payload.requirements) {
      form.requirements = String(payload.requirements)
    } else if (payload.description && !form.requirements) {
      form.requirements = String(payload.description)
    }
    // 模板
    if (payload.template_content) {
      form.template_content = String(payload.template_content)
    } else if (payload.template) {
      form.template_content = String(payload.template)
    } else if (Array.isArray(payload.deliverables_list) && payload.deliverables_list.length && !form.template_content) {
      form.template_content =
        '## 交付物清单\n\n' +
        (payload.deliverables_list as any[])
          .map((x: any, i: number) => `${i + 1}. ${String(x).trim()}`)
          .join('\n')
    }
    // 评分维度：grading_dimensions（企业版） > criteria（/tasks/generate 的结构）
    const criteria =
      (Array.isArray(payload.grading_dimensions) && payload.grading_dimensions.length)
        ? payload.grading_dimensions
        : (Array.isArray(payload.criteria) ? payload.criteria : [])
    if (criteria.length) {
      const mapped = criteria.map((c: any) => ({
        name: String(c?.name || ''),
        weight: Number(c?.weight ?? c?.score ?? 20) || 20,
      })).filter((c: any) => c.name)
      if (mapped.length) {
        const total = mapped.reduce((a: number, b: any) => a + (Number(b.weight) || 0), 0) || 1
        if (Math.abs(total - 100) > 0.01) {
          const ratio = 100 / total
          mapped.forEach((c: any) => { c.weight = Math.max(1, Math.round((Number(c.weight) || 0) * ratio)) })
          const off = mapped.reduce((a: number, b: any) => a + (Number(b.weight) || 0), 0) - 100
          if (mapped[0]) mapped[0].weight = Math.max(1, (Number(mapped[0].weight) || 0) - off)
        }
        criteriaList.value = mapped
      }
    }
    // 如果后端 draft 里给了拼好的 criteria 字符串且我们没有维度，则兜底用
    if (!criteriaList.value.length && typeof payload.criteria === 'string' && payload.criteria) {
      const names = String(payload.criteria).split(',').map((x) => x.trim()).filter(Boolean)
      const weights = typeof payload.criteria_weights === 'string' && payload.criteria_weights
        ? String(payload.criteria_weights).split(',').map((x) => Number(x) || 0)
        : []
      if (names.length) {
        criteriaList.value = names.map((nm, i) => {
          let w = Number(weights[i]) || 0
          if (!w) w = Math.max(1, Math.floor(100 / names.length))
          return { name: nm, weight: w }
        })
      }
    }
    generated.value = true
    ElMessage.success('已根据企业岗位生成实训草稿，请审核修改后发布')
  } catch (e: any) {
    let msg: string
    if (e?.code === 'ERR_CANCELED' || e?.name === 'AbortError') {
      msg = 'AI 生成任务请求超时（30s），已中止。请确认后端 LLM 配置。'
    } else if (e?.code === 'ERR_NETWORK' || e?.message?.includes('Network Error')) {
      msg = `无法连接后端（${API_BASE ?? ''}）：${e?.message ?? e}`
    } else {
      msg = String(e?.response?.data?.detail ?? e?.response?.data?.message ?? e?.response?.data?.error ?? e?.message ?? e ?? '请求失败')
    }
    try {
      await ElMessageBox.alert(msg, 'AI 生成失败', { confirmButtonText: '知道了', type: 'error' })
    } catch {}
  } finally {
    generating.value = false
  }
}

const manualInput = () => {
  const saved = localStorage.getItem('criteria_config')
  // 企业模式 + 已选岗位 + 岗位有技能门槛：直接用岗位维度初始化，确保三方统一
  if (isEnterpriseMode.value && selectedEnterpriseJob.value?.skill_requirements?.length) {
    const dims: any[] = selectedEnterpriseJob.value.skill_requirements
    const mapped = dims
      .filter((d: any) => d?.name)
      .map((d: any) => ({
        name: String(d.name),
        weight: Number(d.weight_pct ?? d.weight ?? Math.round(100 / dims.length)) || 20,
      }))
    if (mapped.length) {
      // 权重合计=100 兜底
      const total = mapped.reduce((a: number, b: any) => a + (Number(b.weight) || 0), 0) || 1
      if (Math.abs(total - 100) > 0.01) {
        const ratio = 100 / total
        mapped.forEach((c: any) => { c.weight = Math.max(1, Math.round((Number(c.weight) || 0) * ratio)) })
        const off = mapped.reduce((a: number, b: any) => a + (Number(b.weight) || 0), 0) - 100
        if (mapped[0]) mapped[0].weight = Math.max(1, (Number(mapped[0].weight) || 0) - off)
      }
      criteriaList.value = mapped
    } else {
      criteriaList.value = JSON.parse(saved).map((c: any) => ({ name: c.name, weight: c.weight }))
    }
  } else if (saved) {
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
    const res = await axios.get(`${API_BASE}/api/tasks/my?teacher_id=${user.id}`, { headers: authHeaders() })
    if (res.data.success) tasks.value = res.data.data
  } catch {} finally { loading.value = false }
}

const loadClasses = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await axios.get(`${API_BASE}/api/classes/?teacher_id=${user.id}`, { headers: authHeaders() })
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
  if (isEnterpriseMode.value && !selectedEnterpriseJobId.value) {
    ElMessage.warning('企业级模式请先选择岗位或切换到自主设计')
    return
  }
  saving.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const names = criteriaList.value.map(c => c.name.trim()).join(',')
    const weights = criteriaList.value.map(c => c.weight).join(',')
    const body: any = {
      title: form.title,
      requirements: form.requirements,
      criteria: names,
      criteria_weights: weights,
      template_content: form.template_content,
      class_id: form.class_ids.join(','),
      total_score: form.total_score,
      deadline: form.deadline || null,
      teacher_id: user.id,
    }
    if (isEnterpriseMode.value && selectedEnterpriseJobId.value) {
      body.origin = 'enterprise_job'
      body.linked_job_id = selectedEnterpriseJobId.value
      body.is_enterprise_project = 1
      body.ai_generated_job_title = selectedEnterpriseJob.value?.title || form.title || ''
    } else {
      body.origin = 'teacher_manual'
      body.is_enterprise_project = 0
    }
    await axios.post(`${API_BASE}/api/tasks/`, body, { headers: authHeaders() })
    ElMessage.success(isEnterpriseMode.value ? '企业级项目实训已发布' : '任务已发布')
    showCreate.value = false
    loadTasks()
  } catch {} finally { saving.value = false }
}

const viewDetail = async (row: any) => {
  try {
    const res = await axios.get(`${API_BASE}/api/tasks/${row.id}/detail`, { headers: authHeaders() })
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
    await axios.delete(`${API_BASE}/api/tasks/${id}`, { headers: authHeaders() })
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