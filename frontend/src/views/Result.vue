<template>
  <div class="page-enter">
    <div class="max-w-7xl mx-auto">
      <div class="mb-8 flex items-end md:items-center justify-between flex-wrap gap-4">
        <div>
          <h1 class="font-display text-3xl font-black text-ink tracking-tight">实训评价详情</h1>
          <p class="text-ink-3 mt-1 text-[13.5px]">AI / 教师 / 企业 三方并排对比，差异 ≥ 6 分自动高亮，薄弱维度一键跳转学习建议</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button v-if="result?.submission_id && enterpriseInvolved"
                  @click="loadTripartite(true)"
                  class="btn-mag btn-mag-ghost !px-4 !py-2 text-[12.5px]">
            <Icon icon="mdi:refresh" class="mr-1" inline width="13" /> 刷新三方对比
          </button>
          <button @click="exportExcel"
                  class="btn-mag btn-mag-ghost !px-4 !py-2 text-[12.5px]">
            <Icon icon="mdi:file-excel-outline" class="mr-1" inline width="13" /> 导出 Excel
          </button>
          <button @click="exportPdf"
                  class="btn-mag btn-mag-danger !px-4 !py-2 text-[12.5px]">
            <Icon icon="mdi:file-pdf-box" class="mr-1" inline width="13" /> 导出 PDF
          </button>
        </div>
      </div>

      <!-- ========== 加载中 ========== -->
      <section v-if="loadingResult" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div
            class="w-16 h-16 rounded-2xl border-4 border-paper-2 border-t-cobalt border-r-seal mx-auto mb-5 animate-spin"></div>
          <p class="text-ink-3 text-[15px] font-medium">正在加载评价详情…</p>
          <p v-if="loadErr" class="text-seal-dark text-[13px] mt-3">{{ loadErr }}</p>
        </div>
      </section>

      <!-- ========== 统一综合头部卡：三方评分 + 核心结论 + 完成度 ========== -->
      <section v-else-if="result" class="ru-unified mb-8">
        <!-- 分区1：三方总分并排（平铺，不单独套小卡片） -->
        <div class="ru-section">
          <div class="ru-sec-head">
            <h3 class="ru-sec-title"><Icon icon="mdi:scale-balance" class="sh-ic ic-cobalt" /> {{ enterpriseInvolved ? '三方综合评分对标' : '两方综合评分对标' }}</h3>
            <div class="flex items-center gap-2">
              <span class="ru-sec-tag">{{ enterpriseInvolved ? 'AI · 教师 · 企业' : 'AI · 教师' }}</span>
              <button v-if="result"
                      @click="showTripartiteDetail = true"
                      class="chip-mag !bg-cobalt/12 !text-cobalt !border-cobalt/30 !text-[11.5px] !py-1 !px-3 hover:!bg-cobalt/18 transition-all">
                <Icon icon="mdi:magnify-plus-outline" inline width="12" class="mr-1" /> 查看详情
              </button>
            </div>
          </div>
          <div class="ru-score-grid" :class="enterpriseInvolved ? 'three' : 'two'">
            <!-- AI -->
            <div class="ru-score-item score-ai" :class="{'diff-hl': scoreSpread >= 6 && aiTotal > 0}">
              <div class="score-top">
                <div class="score-ic"><Icon icon="mdi:robot-outline" /></div>
                <div class="score-meta">
                  <div class="score-name">AI 综合评分</div>
                  <div class="score-sub evaluator">AI已评价</div>
                </div>
                <span class="score-chip chip-auto">自动</span>
              </div>
              <div class="score-val-row">
                <div class="score-val val-ai">{{ aiTotal }}</div>
                <span class="score-level" :class="scoreLevelChip(aiTotal)">{{ scoreLevel(aiTotal) }}</span>
              </div>
              <p class="score-comment line-clamp-2">{{ result?.evaluation?.comment || 'AI 评价进行中…' }}</p>
            </div>
            <!-- 教师 -->
            <div class="ru-score-item score-teacher"
                 :class="{'is-editing': isEditing, 'diff-hl': scoreSpread >= 6 && teacherDisplayScoreFinal >= 0}">
              <div class="score-top">
                <div class="score-ic ic-teacher"><Icon icon="mdi:school-outline" /></div>
                <div class="score-meta">
                  <div class="score-name">教师评分</div>
                  <div class="score-sub">{{ teacherDisplaySaved ? (isEditing ? '编辑中' : '教师已评价') : '待教师评分' }}</div>
                </div>
                <button v-if="isTeacher && !isEditing" @click="startEdit" class="score-chip btn-edit">
                  <Icon icon="mdi:pencil-outline" inline width="12" class="mr-0.5" />
                  {{ teacherDisplaySaved ? '修改' : '开始评分' }}
                </button>
                <span v-else-if="!teacherDisplaySaved" class="score-chip chip-none">未评分</span>
                <span v-else class="score-chip chip-done">已评分</span>
              </div>
              <div class="score-val-row">
                <div class="score-val" :class="teacherDisplaySaved ? 'val-teacher' : 'val-none'">{{ teacherDisplayScoreFinal >= 0 ? teacherDisplayScoreFinal : '—' }}</div>
                <template v-if="teacherDisplaySaved && teacherDisplayScoreFinal >= 0">
                  <span class="score-level" :class="scoreLevelChip(teacherDisplayScoreFinal)">{{ scoreLevel(teacherDisplayScoreFinal) }}</span>
                </template>
                <span v-else class="score-wait">等待评分中…</span>
              </div>
              <p v-if="isEditing" class="score-comment comment-edit">
                <Icon icon="mdi:alert-circle-outline" inline width="13" class="mr-0.5" />
                编辑模式已激活，请在下方填写维度分和评语后保存。
              </p>
              <p v-else class="score-comment line-clamp-2">
                {{ teacherDisplaySaved ? (teacherDisplayComment || '教师暂未添加评语') : (isTeacher ? '点击右上角「开始评分」进入维度打分页面' : '教师尚未为本次提交评分') }}
              </p>
            </div>
            <!-- 企业（仅按企业岗位设计任务时显示） -->
            <div v-if="enterpriseInvolved" class="ru-score-item score-enterprise" :class="{'diff-hl': scoreSpread >= 6 && enterpriseDisplayScore >= 0}">
              <div class="score-top">
                <div class="score-ic ic-enterprise"><Icon icon="mdi:domain" /></div>
                <div class="score-meta">
                  <div class="score-name">企业评价</div>
                  <div class="score-sub">{{ enterpriseParty ? 'HR 已评价' : '等待企业端评价' }}</div>
                </div>
                <span v-if="enterpriseParty" class="score-chip chip-done">已评价</span>
                <span v-else class="score-chip chip-none">待评价</span>
              </div>
              <div class="score-val-row">
                <div class="score-val" :class="enterpriseParty ? 'val-enterprise' : 'val-none'">{{ enterpriseDisplayScore }}</div>
                <template v-if="enterpriseParty">
                  <span class="score-level" :class="scoreLevelChip(enterpriseDisplayScore)">{{ scoreLevel(enterpriseDisplayScore) }}</span>
                </template>
                <span v-else class="score-wait">企业端未发起评价…</span>
              </div>
              <p class="score-comment line-clamp-2">
                {{ enterpriseParty ? (enterpriseParty.comment || '企业端暂未添加点评建议') : (tripartiteData ? '企业端还未评价此提交，但可查看 AI + 教师评分。' : '在企业评价工作台发起评价后，会自动同步到这里进行三方差异比对。') }}
              </p>
            </div>
          </div>
        </div>

        <!-- 分区2：核心结论（左2/3） + 完成度（右1/3） -->
        <div class="ru-section ru-columns ru-last">
          <!-- 左：核心结论 + 学生信息 -->
          <div class="ru-col col-conclusion">
            <div class="ru-col-head">
              <div class="ru-col-title"><span class="col-bar bar-conclusion"></span> 核心结论</div>
            </div>
            <div class="conclusion-body">
              <div class="conclusion-ic"><Icon icon="mdi:lightbulb-on-outline" /></div>
              <div class="conclusion-text">{{ conclusionText }}</div>
            </div>
            <div v-if="studentInfo.name && isTeacher" class="student-meta-row">
              <span><b>学生：</b>{{ studentInfo.name || '-' }}</span>
              <span><b>学号：</b>{{ studentInfo.number || '-' }}</span>
              <span><b>班级：</b>{{ studentInfo.class || '不限' }}</span>
            </div>
          </div>
          <!-- 右：完成度统计 -->
          <div class="ru-col col-progress">
            <div class="ru-col-head">
              <div class="ru-col-title"><span class="col-bar bar-progress"></span> 步骤完成度 / 问题点</div>
            </div>
            <div class="progress-grid two">
              <div class="progress-item pg-done">
                <div class="pg-num">{{ completedStepCount }}</div>
                <div class="pg-lbl">已完成步骤</div>
              </div>
              <div class="progress-item pg-issue">
                <div class="pg-num">{{ issueCount }}</div>
                <div class="pg-lbl">问题 / 改进点</div>
              </div>
            </div>
            <div class="progress-foot">
              <span class="file-info">
                <Icon icon="mdi:file-document-outline" class="ic-doc" inline width="13" />
                {{ result?.filename || 'submission' }}
              </span>
              <button v-if="isStudent" @click="$router.push('/app/student-tasks')" class="back-link">
                返回任务 <Icon icon="mdi:arrow-right" inline width="12" class="ml-0.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      

      <!-- 薄弱维度学习建议（G1-4 · 关键 UX 增强） -->
      <div v-if="weakDimensions.length" class="mb-10">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-1.5 h-5 rounded-full bg-gradient-to-b from-violet-600 to-seal"></div>
          <h3 class="font-display font-bold text-ink text-[18px] leading-none">薄弱维度 · AI 推荐学习路径</h3>
          <span class="chip-mag !bg-violet-600/10 !text-violet-700 !border-violet-600/20 !text-[11px] !py-0.5 !px-2.5 uppercase tracking-[0.14em] font-sub font-bold">生成建议</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="(w, i) in weakDimensions" :key="w.name"
               class="card-mag p-0 overflow-hidden group hover:-translate-y-0.5 transition-all">
            <div class="h-1.5" :class="i === 0 ? 'bg-gradient-to-r from-seal to-amber' : (i === 1 ? 'bg-gradient-to-r from-cobalt to-violet-600' : 'bg-gradient-to-r from-jade to-cobalt')"></div>
            <div class="p-5">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <div class="w-9 h-9 rounded-xl" :class="i === 0 ? 'bg-seal/15 text-seal-dark' : (i === 1 ? 'bg-violet-600/15 text-violet-700' : 'bg-cobalt/15 text-cobalt')">
                    <Icon :icon="w.icon" class="mx-auto mt-[9px] text-lg" />
                  </div>
                  <div>
                    <div class="font-display font-bold text-ink text-[15px] leading-none">{{ w.name }}</div>
                    <div class="text-[11px] text-ink-4 mt-0.5 uppercase tracking-[0.14em]">当前 {{ w.score }} / 100 · 目标 80</div>
                  </div>
                </div>
                <span class="chip-mag !text-[10.5px] !py-0.5 !px-2"
                      :class="i === 0 ? '!bg-seal/12 !text-seal-dark !border-seal/30' : (i === 1 ? '!bg-violet-600/10 !text-violet-700 !border-violet-600/20' : '!bg-cobalt/12 !text-cobalt !border-cobalt/30')">
                  {{ i === 0 ? '第一优先' : (i === 1 ? '第二优先' : '第三优先') }}
                </span>
              </div>
              <p class="text-[12.5px] text-ink-3 leading-[1.85] mb-2 min-h-[52px]">{{ w.hint }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 保留：教师评分编辑表单（原来的 v-show="activeTab==='teacher'+isEditing 内容挪到这里，仅 isEditing 时显示） -->
      <div v-if="isEditing && result" class="mb-10 animate-[fadeIn_.3s_ease-out]">
        <div class="bg-seal/[0.06] border border-seal/25 rounded-2xl p-5 mb-6 flex items-center gap-3">
          <Icon icon="mdi:pencil-outline" class="text-2xl text-seal-dark flex-shrink-0" />
          <div>
            <p class="font-bold text-seal-dark text-[14px] leading-tight">编辑模式 · 教师维度评分表单</p>
            <p class="text-[12px] text-seal-dark/80 mt-0.5">请为每个维度打分并填写评分理由，所有分值保存后立即生效，三方对标会自动更新。</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-7">
          <div v-for="(item, idx) in editingScores" :key="idx"
               class="rounded-2xl bg-paper border-2 border-dashed border-seal/40 p-5">
            <div class="flex justify-between items-center mb-4">
              <span class="font-bold text-[15px] text-ink">{{ item.name }}</span>
              <el-input-number v-model="item.score" :min="0" :max="100"
                               controls-position="right" size="large" class="!w-28" />
            </div>
            <el-input v-model="item.reason" type="textarea" :rows="3"
                      placeholder="请输入评分理由（为什么给这个分数？有哪些改进点？）" class="w-full" />
          </div>
        </div>
        <div class="card-mag p-6 mb-7">
          <label class="block font-display font-bold text-[16px] text-ink mb-3">
            <Icon icon="mdi:text-box-edit-outline" inline width="18" class="mr-1 text-amber-dark" /> 教师评语（整体总结 + 指导建议）
          </label>
          <el-input v-model="editingComment" type="textarea" :rows="4"
                    placeholder="可从以下方面引导学生：①做得好的地方；②需要改进的关键；③下次作业优先级建议。"
                    class="w-full" />
        </div>
        <div class="flex justify-center gap-4">
          <button @click="submitTeacherScore" :disabled="saving"
                  class="btn-mag btn-mag-primary !px-8 !py-3 text-[14px]">
            <Icon v-if="saving" icon="mdi:loading" class="mr-1.5 animate-spin" inline width="15" />
            <Icon v-else icon="mdi:content-save-outline" class="mr-1.5" inline width="15" />
            {{ saving ? '正在保存…' : '确认保存评分' }}
          </button>
          <button @click="cancelEdit"
                  class="btn-mag btn-mag-ghost !px-8 !py-3 text-[14px]">
            <Icon icon="mdi:close" class="mr-1.5" inline width="15" /> 取消编辑
          </button>
        </div>
      </div>

      <div v-if="result">
        <!-- 三栏并排详情（已移入弹窗，这里不再展示）：
             入口按钮放在三方综合评分对标卡头部（见上方"查看详情"）
             下方保留智能核查 Tab 及后续内容 -->

        <!-- 三方对标 · 查看详情弹窗：AI 详细评价 / 教师评价详情 / 企业评价 -->
        <el-dialog v-model="showTripartiteDetail"
                   class="tripartite-detail-dialog"
                   :title="enterpriseInvolved ? '三方综合评分对标 · 查看详情' : '两方综合评分对标 · 查看详情'"
                   :width="enterpriseInvolved ? 1360 : 1120"
                   top="5vh"
                   destroy-on-close>
          <template #header="{ close }">
            <div class="flex items-center justify-between gap-4 pr-12">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-cobalt to-violet-600 text-white flex items-center justify-center shadow-md">
                  <Icon icon="mdi:scale-balance" class="text-xl" />
                </div>
                <div>
                  <h3 class="font-display font-black text-ink text-[18px] leading-none">
                    {{ enterpriseInvolved ? '三方综合评分对标 · 查看详情' : '综合评分对标 · 查看详情' }}
                  </h3>
                  <p class="text-[12px] text-ink-4 mt-1">
                    {{ enterpriseInvolved ? 'AI 初评 · 教师复评 · 企业终评（三方维度分 + 评语并排）' : 'AI 初评 · 教师复评' }}
                  </p>
                </div>
              </div>
              <div class="hidden md:flex items-center gap-2">
                <span class="chip-mag !bg-cobalt/10 !text-cobalt !border-cobalt/20 !text-[11.5px] !py-0.5 !px-2.5 uppercase tracking-[0.14em] font-sub font-bold">AI</span>
                <span class="chip-mag !bg-amber/10 !text-amber-dark !border-amber/30 !text-[11.5px] !py-0.5 !px-2.5 uppercase tracking-[0.14em] font-sub font-bold">教师</span>
                <span v-if="enterpriseInvolved" class="chip-mag !bg-violet-600/10 !text-violet-700 !border-violet-600/20 !text-[11.5px] !py-0.5 !px-2.5 uppercase tracking-[0.14em] font-sub font-bold">企业</span>
                <span class="chip-mag !bg-seal/10 !text-seal-dark !border-seal/30 !text-[11.5px] !py-0.5 !px-2.5">
                  <Icon icon="mdi:alert-circle-outline" inline width="12" class="mr-0.5" />
                  分差 ≥6 已在对标表高亮
                </span>
                <button @click="close"
                        class="ml-2 w-10 h-10 rounded-full bg-paper-2/60 hover:bg-paper-2 text-ink-4 hover:text-ink-7 transition-colors flex items-center justify-center">
                  <Icon icon="mdi:close" class="text-lg" />
                </button>
              </div>
            </div>
          </template>

          <!-- 三栏 / 两栏并排（内容就是原来页面下方展示的三张卡） -->
          <div class="grid grid-cols-1 gap-5" :class="enterpriseInvolved ? 'lg:grid-cols-3' : 'lg:grid-cols-2'">
            <!-- 左：AI 维度 + 总评 -->
            <div class="card-mag p-6">
              <div class="flex items-center gap-2 mb-5">
                <div class="w-8 h-8 rounded-xl bg-cobalt/15 text-cobalt flex items-center justify-center">
                  <Icon icon="mdi:robot-outline" class="text-lg" />
                </div>
                <h3 class="font-display font-bold text-ink text-[16px] leading-none">AI 详细评价</h3>
              </div>
              <div class="space-y-3 mb-6">
                <div v-for="item in result?.evaluation?.scores" :key="item.name"
                     class="rounded-xl bg-paper-2/40 p-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="font-sub font-bold text-ink text-[13.5px]">{{ item.name }}</span>
                    <span class="font-display font-black text-cobalt text-xl leading-none">{{ item.score }}<span class="text-xs text-ink-4 font-normal ml-0.5">/100</span></span>
                  </div>
                  <div class="w-full h-2 rounded-full bg-line overflow-hidden mb-2.5">
                    <div class="h-full rounded-full transition-all duration-1000 ease-out"
                         :style="{ width: item.score + '%', background: item.score >= 80 ? 'linear-gradient(90deg, #10B981, #059669)' : item.score >= 60 ? 'linear-gradient(90deg, #F59E0B, #D97706)' : 'linear-gradient(90deg, #EF4444, #DC2626)' }"></div>
                  </div>
                  <p class="text-[12px] text-ink-3 leading-relaxed">{{ item.reason }}</p>
                </div>
                <div v-if="!result?.evaluation?.scores?.length" class="text-[12.5px] text-ink-4 italic text-center py-6">
                  AI 暂未输出维度细分分数。
                </div>
              </div>
              <div class="rounded-2xl bg-gradient-to-br from-cobalt/8 to-violet-600/8 p-5 border border-cobalt/20">
                <div class="font-display font-bold text-ink text-[14px] mb-2 flex items-center gap-1.5">
                  <Icon icon="mdi:comment-quote-outline" inline width="15" class="text-cobalt" /> AI 总评
                </div>
                <p class="text-[13px] text-ink-2 leading-[1.9] whitespace-pre-wrap">{{ result?.evaluation?.comment || '（AI 暂未生成点评）' }}</p>
              </div>
            </div>

            <!-- 中：教师维度/评语/状态 -->
            <div class="card-mag p-6">
              <div class="flex items-center justify-between mb-5">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 rounded-xl bg-amber/15 text-amber-dark flex items-center justify-center">
                    <Icon icon="mdi:school-outline" class="text-lg" />
                  </div>
                  <h3 class="font-display font-bold text-ink text-[16px] leading-none">教师评价详情</h3>
                </div>
                <button v-if="isTeacher && teacherDisplaySaved" @click="startEdit; showTripartiteDetail=false"
                        class="chip-mag !bg-amber/12 !text-amber-dark !border-amber/30 !text-[11.5px] !py-1 !px-2.5">
                  <Icon icon="mdi:pencil-outline" inline width="12" class="mr-0.5" /> 去修改
                </button>
              </div>
              <template v-if="teacherDisplaySaved">
                <div class="space-y-3 mb-6">
                  <div v-for="item in (teacherDisplayScores.length ? teacherDisplayScores : teacherData.scores)" :key="item.name"
                       class="rounded-xl bg-paper-2/40 p-4">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-sub font-bold text-ink text-[13.5px]">{{ item.name }}</span>
                      <span class="font-display font-black text-amber-dark text-xl leading-none">{{ item.score }}<span class="text-xs text-ink-4 font-normal ml-0.5">/100</span></span>
                    </div>
                    <div class="w-full h-2 rounded-full bg-line overflow-hidden mb-2.5">
                      <div class="h-full bg-gradient-to-r from-amber to-seal transition-all duration-1000 ease-out rounded-full"
                           :style="{ width: item.score + '%' }"></div>
                    </div>
                    <p v-if="item.reason" class="text-[12px] text-ink-3 leading-relaxed">{{ item.reason }}</p>
                  </div>
                </div>
                <div class="rounded-2xl bg-gradient-to-br from-amber/10 to-seal/10 p-5 border border-amber/20">
                  <div class="font-display font-bold text-ink text-[14px] mb-2 flex items-center gap-1.5">
                    <Icon icon="mdi:comment-quote-outline" inline width="15" class="text-amber-dark" /> 教师评语
                  </div>
                  <p class="text-[13px] text-ink-2 leading-[1.9] whitespace-pre-wrap">{{ teacherDisplayComment || teacherData.comment || '教师暂未添加评语' }}</p>
                </div>
              </template>
              <template v-else>
                <div class="py-14 text-center">
                  <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
                    <Icon icon="mdi:email-open-outline" class="text-4xl text-ink-4" />
                  </div>
                  <p class="text-[13.5px] text-ink-3 mb-4">
                    {{ isTeacher ? '你还没有为本次提交评分' : '教师尚未评分' }}
                  </p>
                  <button v-if="isTeacher" @click="startEdit; showTripartiteDetail=false"
                          class="btn-mag btn-mag-primary !px-5 !py-2.5 text-[13px]">
                    <Icon icon="mdi:pencil-outline" inline width="13" class="mr-1" /> 去评分
                  </button>
                </div>
              </template>
            </div>

            <!-- 右：企业评价 + 匹配榜链接（仅企业参与模式显示） -->
            <div v-if="enterpriseInvolved" class="card-mag p-6">
              <div class="flex items-center justify-between mb-5">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 rounded-xl bg-violet-600/15 text-violet-700 flex items-center justify-center">
                    <Icon icon="mdi:domain" class="text-lg" />
                  </div>
                  <h3 class="font-display font-bold text-ink text-[16px] leading-none">企业评价 / HR 评价</h3>
                </div>
              </div>
              <template v-if="enterpriseParty">
                <div class="space-y-3 mb-6">
                  <div v-for="(item, i) in enterpriseDimensions" :key="'ed-'+i"
                       class="rounded-xl bg-paper-2/40 p-4">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-sub font-bold text-ink text-[13.5px]">{{ item.name }}</span>
                      <span class="font-display font-black text-violet-700 text-xl leading-none">{{ item.score }}<span class="text-xs text-ink-4 font-normal ml-0.5">/100</span></span>
                    </div>
                    <div class="w-full h-2 rounded-full bg-line overflow-hidden mb-2.5">
                      <div class="h-full bg-gradient-to-r from-violet-600 to-cobalt rounded-full transition-all duration-1000 ease-out"
                           :style="{ width: item.score + '%' }"></div>
                    </div>
                  </div>
                </div>
                <div class="rounded-2xl bg-gradient-to-br from-violet-600/10 to-cobalt/10 p-5 border border-violet-600/20">
                  <div class="font-display font-bold text-ink text-[14px] mb-2 flex items-center gap-1.5">
                    <Icon icon="mdi:comment-quote-outline" inline width="15" class="text-violet-700" /> 企业端点评
                    <span v-if="enterpriseParty.mentor_name" class="ml-auto text-[11px] text-ink-4 font-sub uppercase tracking-[0.14em]">
                      BY {{ enterpriseParty.mentor_name }}
                    </span>
                  </div>
                  <p class="text-[13px] text-ink-2 leading-[1.9] whitespace-pre-wrap">{{ enterpriseParty.comment || enterpriseParty.interview_note || '企业端暂未添加文字点评' }}</p>
                </div>
              </template>
              <template v-else>
                <div class="py-14 text-center">
                  <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
                    <Icon icon="mdi:briefcase-search-outline" class="text-4xl text-ink-4" />
                  </div>
                  <p class="text-[13.5px] text-ink-3 mb-4">
                    企业 HR 端暂未发起评价 · 教师/学生可先参考 AI + 教师两方
                  </p>
                  <p class="text-[11.5px] text-ink-4 italic mb-5">企业导师登录后，通过「评价工作台」对任一提交打分，本卡片会自动展示企业评价内容。</p>
                </div>
              </template>
            </div>

          </div>

          <template #footer>
            <div class="flex items-center justify-between gap-3 pt-2">
              <div class="flex items-center gap-2 text-[12px] text-ink-4">
              </div>
              <div class="flex items-center gap-2">
                <button @click="showTripartiteDetail = false"
                        class="btn-mag btn-mag-ghost !px-5 !py-2.5 text-[13px]">
                  关闭
                </button>
                <button v-if="result?.submission_id && enterpriseInvolved"
                        @click="loadTripartite(true)"
                        class="btn-mag btn-mag-ghost !px-5 !py-2.5 text-[13px]">
                  <Icon icon="mdi:refresh" inline width="13" class="mr-1" /> 刷新数据
                </button>
              </div>
            </div>
          </template>
        </el-dialog>

        <!-- 智能核查 Tab 仍保留（因为数据量大，单栏展示更清晰） -->
        <div class="mb-10">
          <div class="flex items-center justify-center mb-6 bg-paper-2/60 rounded-2xl p-1.5 max-w-xl mx-auto border border-line/70">
            <button v-for="tab in tabListBottom" :key="tab.value"
                    @click="activeTab = tab.value"
                    :class="activeTab === tab.value
                      ? 'bg-paper text-ink font-bold border border-line shadow-sm'
                      : 'text-ink-4 hover:text-ink-2 font-medium border-transparent'"
                    class="flex-1 py-2.5 px-4 rounded-xl transition-all duration-300 flex items-center justify-center gap-2 text-[13px] border">
              <Icon :icon="tab.icon" inline width="14" />
              <span>{{ tab.label }}</span>
            </button>
          </div>

          <!-- 智能核查 -->
          <div v-show="activeTab === 'check'" class="animate-fade-in">
            <template v-if="hasCompleteness">
              <div class="mb-10">
                <h3 class="text-xl font-bold text-ink mb-5 flex items-center gap-2">
                  <span class="w-8 h-8 rounded-lg bg-cobalt/15 text-cobalt flex items-center justify-center"><Icon icon="mdi:clipboard-check-outline" /></span>
                  步骤完整性核查
                </h3>
                <div class="card-mag p-0 overflow-hidden">
                  <table class="w-full text-[13px]">
                    <thead>
                      <tr class="bg-paper-2/60 text-[11px] uppercase tracking-[0.14em] text-ink-4">
                        <th class="text-left font-bold px-5 py-3">步骤</th>
                        <th class="text-left font-bold px-5 py-3 w-[120px]">状态</th>
                        <th class="text-left font-bold px-5 py-3">详细说明</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(r, i) in tableRows(result.completeness.steps)" :key="i"
                          class="border-t border-line/70 hover:bg-paper-2/30">
                        <td class="px-5 py-3.5 font-semibold text-ink">{{ r.step || r.name || ('步骤 ' + (i+1)) }}</td>
                        <td class="px-5 py-3.5">
                          <span :class="statusChip(r.status)" class="chip-mag !py-1 !px-2.5 !text-[11.5px]">{{ r.status }}</span>
                        </td>
                        <td class="px-5 py-3.5 text-ink-3 leading-relaxed">{{ r.detail || r.description || '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <div class="mb-10">
                <h3 class="text-xl font-bold text-ink mb-5 flex items-center gap-2">
                  <span class="w-8 h-8 rounded-lg bg-seal/15 text-seal-dark flex items-center justify-center"><Icon icon="mdi:alert-outline" /></span>
                  问题 / 改进点
                </h3>
                <div class="space-y-3" v-if="result.completeness.issues?.length">
                  <div v-for="(issue, idx) in result.completeness.issues" :key="idx"
                       :class="issue.severity === '高' ? 'bg-seal/8 border-seal/35' : issue.severity === '中' ? 'bg-amber/10 border-amber/35' : 'bg-cobalt/10 border-cobalt/30'"
                       class="border rounded-2xl p-5">
                    <div class="flex items-start justify-between gap-4">
                      <div>
                        <p class="font-bold text-[15px] text-ink mb-1">{{ issue.description || issue.title }}</p>
                        <p class="text-[12.5px] text-ink-3">严重程度：{{ issue.severity || issue.level || '提示' }}</p>
                        <p v-if="issue.detail" class="text-[12.5px] text-ink-2 mt-2 leading-relaxed">{{ issue.detail }}</p>
                      </div>
                      <span :class="issue.severity === '高' ? 'bg-seal-dark' : issue.severity === '中' ? 'bg-amber-dark' : 'bg-cobalt'"
                            class="px-3 py-1 rounded-full text-white text-[11.5px] font-bold uppercase tracking-wider flex-shrink-0">{{ issue.severity || 'INFO' }}</span>
                    </div>
                  </div>
                </div>
                <div v-else class="card-mag p-10 text-center bg-jade/[0.04] border-jade/25">
                  <div class="w-16 h-16 rounded-2xl bg-jade/15 flex items-center justify-center mx-auto mb-3">
                    <Icon icon="mdi:check-circle" class="text-3xl text-jade-dark" />
                  </div>
                  <p class="text-jade-dark font-bold text-lg">未检测到逻辑漏洞</p>
                </div>
              </div>
              <div class="card-mag p-8 bg-paper-2/60">
                <h3 class="text-xl font-bold text-ink mb-4"><Icon icon="mdi:text-box-check-outline" class="inline align-text-bottom mr-1" /> 核查总结</h3>
                <p class="text-[14px] text-ink-2 leading-[1.9]">{{ result.completeness.summary || '本次提交无总结备注。' }}</p>
              </div>
            </template>
            <div v-else class="py-20 text-center card-mag">
              <Icon icon="mdi:email-open-outline" class="text-5xl text-ink-3 mx-auto mb-3 block" />
              <p class="text-ink-3 text-lg">暂无智能核查数据</p>
            </div>
          </div>

          <!-- 三方/两方对标 Tab（仅企业参与模式显示：教师自主设计任务企业不参与时，按需求完全隐藏） -->
          <div v-show="activeTab === 'tripartite' && enterpriseInvolved" class="animate-fade-in">
            
            <div v-if="tripartiteLoading" class="py-20 text-center text-ink-3">
              <Icon icon="mdi:loading" class="text-4xl animate-spin mb-3 mx-auto block" />
              <p>正在加载对标数据…</p>
            </div>
            <template v-else-if="tripartiteData">
              <TripartiteCompare
                :parties="tripartiteData.parties"
                :dimensionBreakdown="tripartiteData.dimension_breakdown"
                :summary="tripartiteData.summary"
                :enterpriseInvolved="tripartiteData.enterprise_involved" />
            </template>
            <div v-else class="py-16 text-center card-mag !bg-paper-2/40">
              <div class="w-20 h-20 rounded-2xl bg-line/60 flex items-center justify-center mx-auto mb-5">
                <Icon icon="mdi:scale-balance" class="text-4xl text-ink-4" />
              </div>
              <p class="text-ink-3 text-[14.5px] font-medium mb-2">暂无完整三方对标</p>
              <p class="text-ink-4 text-[12.5px] mb-6 max-w-md mx-auto leading-relaxed">
                请确保教师、企业端都已对该提交打分，或点击上方「刷新三方对比」手动触发。
              </p>
              <button @click="loadTripartite(true)"
                      class="btn-mag btn-mag-primary !px-5 !py-2.5 text-[13px]">
                <Icon icon="mdi:refresh" class="mr-1" inline width="13" /> 生成演示数据（兜底）
              </button>
            </div>
          </div>
        </div>

        <!-- 底部操作按钮 -->
        <div class="mt-10 flex flex-wrap justify-center gap-3">
          <button v-if="isStudent" @click="$router.push('/app/student-tasks')"
                  class="btn-mag btn-mag-primary !px-7 !py-3 text-[14px]">
            <Icon icon="mdi:arrow-left" inline width="14" class="mr-1" /> 返回任务列表
          </button>
          <template v-if="isTeacher">
            <button v-if="nextUnscoredId" @click="goNextUnscored"
                    class="btn-mag btn-mag-primary !px-7 !py-3 text-[14px]">
              <Icon icon="mdi:arrow-right" inline width="14" class="mr-1" />
              评价下一份（剩 {{ unscoredCount }} 份）
            </button>
            <button v-else @click="$router.push('/app/task-manage')"
                    class="btn-mag btn-mag-ghost !px-7 !py-3 text-[14px]">
              返回任务管理
            </button>
          </template>
        </div>
      </div>

      <div v-else class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-28 h-28 rounded-3xl bg-paper-2/60 flex items-center justify-center mx-auto mb-7 border border-line/80">
            <Icon icon="mdi:file-document-off-outline" class="text-5xl text-ink-4" />
          </div>
          <p class="text-ink-3 text-lg font-medium mb-8">暂无评价结果</p>
          <button @click="$router.push('/app/upload')" class="btn-mag btn-mag-primary !px-8 !py-3 text-[14px]">
            <Icon icon="mdi:upload-outline" inline width="15" class="mr-1.5" /> 去上传并评价
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onActivated, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'
import TripartiteCompare from '../components/common/TripartiteCompare.vue'

const router = useRouter()
const route = useRoute()
const result = ref<any>(null)
const loadingResult = ref(true)
const loadErr = ref<string | null>(null)
const activeTab = ref('ai')
const isEditing = ref(false)
const showTripartiteDetail = ref(false)
const saving = ref(false)
const teacherSaved = ref(false)
const teacherData = ref<any>({ scores: [], comment: '', total: 0 })

// 编辑模式下独立的数据
const editingScores = ref<Array<{name: string, score: number, reason: string}>>([])
const editingComment = ref('')
const unscoredCount = ref(0)
const nextUnscoredId = ref<number | null>(null)
const currentTaskId = ref<number | null>(null)
const studentInfo = reactive({
  name: '',
  number: '',
  class: ''
})

// 统一认证头：优先从 localStorage 拿 token
function authHeaders() {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ===== Table / Status helpers =====
function tableRows(steps: any[]) {
  if (!steps || !Array.isArray(steps)) return []
  return steps
}
function statusChip(status: string) {
  if (!status) return '!bg-line/40 !text-ink-4 !border-line'
  const s = String(status)
  if (/已完成|完成|pass|ok|done|full/i.test(s)) return '!bg-jade/10 !text-jade-dark !border-jade/30'
  if (/部分|partially|half|missing/i.test(s)) return '!bg-amber/10 !text-amber-dark !border-amber/30'
  if (/未完成|未开始|缺失|no|未做|未实现/i.test(s)) return '!bg-seal/10 !text-seal-dark !border-seal/30'
  return '!bg-cobalt/10 !text-cobalt !border-cobalt/30'
}

// 三方对比数据
const tripartiteLoading = ref(false)
const tripartiteData = ref<any>(null)

/**
 * 从 localStorage + 路由参数加载单条评价结果（同步版，无 async/await，避免时序问题）。
 * 兼容来源：
 *   - route.params.id         (MyScores → 命名路由 /app/result/:id)
 *   - route.query.id/submission_id (教师端任务列表/评分列表 → ?id=xxx)
 *   - localStorage.eval_result (上传页完成评价后，或我的成绩页跳转前先写入缓存)
 *
 * 关键修复点：
 *   1) 先声明 tripartiteData/studentInfo/teacherData 等所有响应式变量，再调用本函数，
 *      避免 setup 同步阶段的 TDZ ReferenceError。
 *   2) 同步执行，不依赖 onMounted/nextTick，路由首次解析即可把 result 填上，
 *      模板 v-if/v-else 能立即命中正确分支（而不是先闪空态）。
 */
function resolveResultSource() {
  // 1) localStorage 兜底（上一页跳转前通常会先写入 eval_result 快照）
  let parsed: any = null
  const raw = typeof localStorage !== 'undefined' ? localStorage.getItem('eval_result') : null
  if (raw) {
    try { parsed = JSON.parse(raw) } catch { parsed = null }
  }

  // 2) 从路由提取 submission_id：route.params.id 优先 → query.id/submission_id 兜底
  let routeSid: number | null = null
  try {
    const pId = route.params?.id
    const qId = route.query?.id ?? route.query?.submission_id
    if (pId) {
      const n = Number(pId)
      if (Number.isFinite(n) && n > 0) routeSid = n
    }
    if (!routeSid && qId) {
      const n = Number(qId)
      if (Number.isFinite(n) && n > 0) routeSid = n
    }
  } catch { /* route 未就绪时忽略 */ }

  // 3) 合并 submission_id 到 result，至少保证 result.value 不为 null 时 v-if 可渲染主体
  const submissionId = routeSid ?? parsed?.submission_id ?? null
  if (parsed || submissionId) {
    result.value = parsed ?? {}
    if (submissionId) result.value.submission_id = Number(submissionId)
    if (parsed?.student_name) studentInfo.name = parsed.student_name
    if (parsed?.student_number) studentInfo.number = parsed.student_number
    if (parsed?.class_name) studentInfo.class = parsed.class_name
  } else {
    result.value = null
  }
  return { submissionId, parsed }
}

// === 关键：在 setup 同步阶段立刻解析一次 ===
//   即使此刻三方对比和教师评分还没拉完，result.value 也会有 submission_id，
//   模板会先进入 v-else-if="result" 渲染统一头部卡，再配合 onMounted 异步数据加载。
resolveResultSource()

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

// ===== G1-4 · 新增：三栏总分与维度对标辅助 computed =====
// 【重要】这整个区块必须放在 tripartiteData 之后声明！避免 setup 同步阶段 TDZ ReferenceError
const enterpriseParty = computed(() => {
  const parties = tripartiteData.value?.parties || []
  const p = parties.find((x: any) => x.role === 'enterprise' || x.role === 'company')
  if (p) return p
  // 兜底：如果 tripartite 还没拉，也尝试从三方 breakdown 反推
  const db = tripartiteData.value?.dimension_breakdown || []
  if (db.length && db[0].enterprise_score != null) {
    const total = Math.round(db.reduce((s: number, d: any) => s + (Number(d.enterprise_score) || 0), 0) / db.length)
    return {
      role: 'enterprise',
      label: '企业',
      total,
      comment: tripartiteData.value?.summary?.notes || '（对标反推数据）HR 综合打分',
      interview_note: tripartiteData.value?.summary?.notes || '',
      mentor_name: null
    }
  }
  return null
})

const enterpriseDimensions = computed<Array<{ name: string, score: number, reason?: string }>>(() => {
  const db = tripartiteData.value?.dimension_breakdown
  if (db && db.length) {
    return db.map((d: any) => ({
      name: d.name,
      score: Number(d.enterprise_score ?? d.ent_score ?? 0),
      reason: d.warning || ''
    }))
  }
  // 兜底：没 breakdown 就用 AI 的维度平均减一点
  const base = result.value?.evaluation?.scores || []
  const entTotal = enterpriseParty.value?.total ?? 0
  if (!base.length) return []
  const aiTotal = result.value?.evaluation?.total || base.reduce((s, b) => s + (Number(b.score) || 0), 0) / base.length
  const factor = aiTotal ? entTotal / aiTotal : 1
  return base.map((b: any) => ({
    name: b.name,
    score: Math.min(100, Math.max(0, Math.round(Number(b.score) * factor)))
  }))
})

const aiTotal = computed(() => result.value?.evaluation?.total || 0)
const teacherDisplayScore = computed(() => (teacherSaved.value ? teacherData.value.total : -1))

// 1) tripartiteData 已声明，enterpriseParty/enterpriseDimensions 已就绪
//    → 再定义 enterpriseInvolved 作为整个企业参与模式的唯一开关
const enterpriseInvolved = computed<boolean>(() => {
  const v = tripartiteData.value?.enterprise_involved
  if (v === false) return false
  return true
})

// ==== 教师评分展示：多数据源合并，避免 /api/teacher/scores 失败时仍显示"待教师评分" ====
// 数据源优先级：
//  1) 教师已手动保存 (teacherSaved===true，优先，因为是教师端主动写入的"真源")
//  2) loadTripartite 返回的 parties 中有 role=teacher 且 total>=0（教师在别处完成的评分）
//  3) /api/teacher/scores 成功返回 (teacherSaved) 已在 onMounted 中写入
const teacherParty = computed<any | null>(() => {
  const parties = tripartiteData.value?.parties || []
  const p = parties.find((x: any) => x.role === 'teacher' || x.role === 'instructor' || x.role === 'reviewer')
  if (p && (typeof p.total === 'number' || Array.isArray(p.scores))) return p
  return null
})

// 兼容 Tripartite 中教师维度的维度分：优先 dimension_breakdown 中的 teacher_score
const teacherDisplayScores = computed<Array<{name: string; score: number; reason?: string}>>(() => {
  if (teacherSaved.value && Array.isArray(teacherData.value.scores) && teacherData.value.scores.length) {
    return teacherData.value.scores
  }
  const db = tripartiteData.value?.dimension_breakdown || []
  if (db.length) {
    return db.map((d: any) => {
      const ts = Number(d.teacher_score ?? d.t_score ?? d.teacherScore ?? d.teacherTotal ?? NaN)
      return {
        name: d.name,
        score: Number.isFinite(ts) ? Math.max(0, Math.min(100, Math.round(ts))) : 0,
        reason: d.warning || d.reason || ''
      }
    })
  }
  // 再次兜底：按 AI 维度做一份空的 0 分结构（避免 v-for 渲染空数组），不视为已评分
  return []
})

// "是否已完成教师评分"的最终布尔 (UI 用这一个，不再单独用 teacherSaved)
const teacherDisplaySaved = computed<boolean>(() => {
  if (teacherSaved.value) return true
  if (teacherParty.value) {
    const total = Number(teacherParty.value.total)
    if (Number.isFinite(total) && total > 0) return true
  }
  if (teacherDisplayScores.value.length &&
      teacherDisplayScores.value.every(s => Number.isFinite(s.score))) {
    // 只有在"有任一维度得分明显大于0"时才认为已评分，避免把0分未评误判成已评
    return teacherDisplayScores.value.some(s => s.score > 0)
  }
  return false
})

// 教师展示总分 (>=0 整数；未评则 -1)
const teacherDisplayScoreFinal = computed<number>(() => {
  if (teacherSaved.value) return Number(teacherData.value.total)
  if (teacherParty.value && Number.isFinite(Number(teacherParty.value.total))) {
    return Math.max(0, Math.min(100, Math.round(Number(teacherParty.value.total))))
  }
  if (teacherDisplayScores.value.length && teacherDisplaySaved.value) {
    const total = teacherDisplayScores.value.reduce((s, b) => s + b.score, 0) / teacherDisplayScores.value.length
    return Math.round(total)
  }
  return -1
})

// 教师评语 (前端展示用)
const teacherDisplayComment = computed<string>(() => {
  if (teacherSaved.value && teacherData.value.comment) return teacherData.value.comment
  if (teacherParty.value?.comment) return teacherParty.value.comment
  if (teacherDisplaySaved.value) return '（已完成维度打分）教师暂未补充文字评语'
  return ''
})

// 2) enterpriseInvolved 就绪 → enterpriseDisplayScore / scoreSpread / dimensionRows / weakDimensions
const enterpriseDisplayScore = computed(() => {
  if (!enterpriseInvolved.value) return -1
  return enterpriseParty.value?.total ?? -1
})

// （紧接 enterpriseInvolved 之后，避免 TDZ）Tab 列表：教师自主设计任务企业不参与时，按需求不展示"三方对标"
const tabListBottom = computed(() => {
  const tabs = [
    { label: '智能核查', value: 'check', icon: 'mdi:clipboard-check-outline' },
  ]
  if (enterpriseInvolved.value) {
    tabs.push({ label: '三方对标', value: 'tripartite', icon: 'mdi:scale-balance' })
  }
  return tabs
})

// 防御：如果当前正在 tripartite Tab，但模式变为「企业不参与」(教师自主设计)，
// 自动跳回「智能核查」Tab，避免页面变成空壳导致用户困惑。
watch(
  [enterpriseInvolved, activeTab],
  ([involved, tab]) => {
    if (!involved && tab === 'tripartite') {
      activeTab.value = 'check'
    }
  },
  { immediate: false }
)

function scoreLevel(score: number) {
  if (score < 0) return '—'
  if (score >= 90) return 'S 级 · 卓越'
  if (score >= 80) return 'A 级 · 优秀'
  if (score >= 70) return 'B 级 · 良好'
  if (score >= 60) return 'C 级 · 合格'
  return 'D 级 · 待加强'
}
function scoreLevelChip(score: number) {
  if (score < 0) return '!bg-line/40 !text-ink-4 !border-line'
  if (score >= 80) return '!bg-jade/10 !text-jade-dark !border-jade/30'
  if (score >= 70) return '!bg-cobalt/10 !text-cobalt !border-cobalt/30'
  if (score >= 60) return '!bg-amber/10 !text-amber-dark !border-amber/30'
  return '!bg-seal/10 !text-seal-dark !border-seal/30'
}

const completedStepCount = computed(() => {
  const steps = result.value?.completeness?.steps || []
  return steps.filter((s: any) => /已完成|完成|done|ok/i.test(s?.status || s?.step || '')).length
})
const issueCount = computed(() => (result.value?.completeness?.issues || []).length)

// 三方总分最大分差（用于头部卡高亮提示）
const scoreSpread = computed(() => {
  const vals = [aiTotal.value, teacherDisplayScoreFinal.value, enterpriseDisplayScore.value].filter(v => v >= 0)
  if (vals.length < 2) return 0
  return Math.max(...vals) - Math.min(...vals)
})

// 维度行：合并 AI / 教师 / 企业
const dimensionRows = computed<Array<{
  name: string; reason: string; ai: number; teacher: number; enterprise: number;
  max_diff: number; diff_ai_t: number; diff_t_e: number; highlight: boolean;
}>>(() => {
  const ai = result.value?.evaluation?.scores || []
  // 教师维度分：优先 teacherSaved 真源，否则用三方回填的维度分
  const t = teacherDisplayScores.value
  const e = enterpriseDimensions.value
  const names = Array.from(new Set([
    ...ai.map((x: any) => x.name),
    ...t.map((x: any) => x.name),
    ...e.map((x: any) => x.name)
  ]))
  const HIGHLIGHT_THRESHOLD = 6
  return names.map(name => {
    const aScore = ai.find((x: any) => x.name === name)
    const tScore = t.find((x: any) => x.name === name)
    const eScore = e.find((x: any) => x.name === name)
    const A = aScore ? Number(aScore.score) : -1
    // 教师分只有在"判定已评"时才参与；否则置 -1，避免 0 分未评影响分差
    const T = (teacherDisplaySaved.value && tScore) ? Number(tScore.score) : -1
    const E = eScore ? Number(eScore.score) : -1
    const diffs: number[] = []
    if (A >= 0 && T >= 0) diffs.push(Math.abs(A - T))
    if (T >= 0 && E >= 0) diffs.push(Math.abs(T - E))
    if (A >= 0 && E >= 0) diffs.push(Math.abs(A - E))
    const max_diff = diffs.length ? Math.max(...diffs) : 0
    const diff_ai_t = A >= 0 && T >= 0 ? Math.abs(A - T) : -1
    const diff_t_e = T >= 0 && E >= 0 ? Math.abs(T - E) : -1
    return {
      name,
      reason: aScore?.reason || tScore?.reason || eScore?.reason || '',
      ai: A, teacher: T, enterprise: E,
      max_diff, diff_ai_t, diff_t_e,
      highlight: max_diff >= HIGHLIGHT_THRESHOLD
    }
  })
})

// 薄弱维度：取三方平均后分数最低的 2~3 个，生成针对性改进建议（不再附学习链接）
const weakDimensions = computed<Array<{
  name: string; score: number; icon: string; hint: string;
}>>(() => {
  const rows = dimensionRows.value
  if (!rows.length) return []
  const scored = rows
    .map(r => {
      const vals = [r.ai, r.teacher, r.enterprise].filter(v => v >= 0)
      const avg = vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : r.ai
      return { name: r.name, score: avg, reason: r.reason }
    })
    .filter(x => x.score >= 0 && x.score < 80)
    .sort((a, b) => a.score - b.score)
  const weak = scored.slice(0, Math.min(3, Math.max(2, scored.length)))
  if (!weak.length) return []

  const HINT_BY_DIM: Record<string, { icon: string; defaultHint: string }> = {
    '代码质量': {
      icon: 'mdi:code-tags',
      defaultHint: '命名、格式、注释与模块化仍有提升空间，可先通读《代码整洁之道》核心章节并在项目中应用 ESLint/Prettier 统一规范。'
    },
    '功能完整性': {
      icon: 'mdi:check-decagram-outline',
      defaultHint: '需求分解与用例覆盖不足，建议先用思维导图列出所有验收点，再逐条对照实现并写单元测试。'
    },
    '文档规范性': {
      icon: 'mdi:file-document-multiple-outline',
      defaultHint: 'README / 接口 / 注释仍需更系统化，可按「为什么 → 怎么跑 → 怎么用 → 怎么改」四部分结构输出文档。'
    },
    '界面设计': {
      icon: 'mdi:monitor-screenshot',
      defaultHint: '视觉层次与交互细节仍可打磨，建议从「排版四原则」入门，并参考优秀组件库建立自己的 UI 参考库。'
    },
    '算法正确性': {
      icon: 'mdi:calculator-variant-outline',
      defaultHint: '边界情况考虑不足，建议练习 LeetCode 经典题并手写断言，掌握复杂度分析与常见陷阱。'
    },
    '性能优化': {
      icon: 'mdi:speedometer',
      defaultHint: '复杂度与资源占用偏高，可学习 Chrome DevTools 的 Performance/Network 面板，量化瓶颈再逐项优化。'
    }
  }

  const DEFAULT: typeof HINT_BY_DIM['代码质量'] = {
    icon: 'mdi:brain',
    defaultHint: '该维度综合评价略低于预期，建议回看本维度的评分理由，针对性地补做 3~5 个同类型小任务，并写复盘笔记。'
  }

  const ICON_POOL = ['mdi:rocket-launch-outline', 'mdi:compass-outline', 'mdi:trophy-outline']

  return weak.map((w, i) => {
    const preset = HINT_BY_DIM[w.name] || DEFAULT
    const hint = w.reason
      ? `${w.reason.replace(/\s+/g, ' ').slice(0, 56)}… ${preset.defaultHint}`
      : preset.defaultHint
    return {
      name: w.name,
      score: w.score,
      icon: preset.icon || ICON_POOL[i % 3],
      hint
    }
  })
})


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
    // 不同角色调用不同接口：企业导师走 evaluations/compare（校验当前登录企业）；
    // 学生/教师走 student/compare（支持 teacher 代查）。
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const subId = result.value.submission_id
    const url = user.role === 'enterprise'
      ? `${API_BASE}/api/enterprise/evaluations/compare/${subId}`
      : `${API_BASE}/api/enterprise/student/compare/${subId}`
    const { data } = await axios.get(url, { headers: authHeaders() })
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
      const teacherTotal = teacherDisplaySaved.value ? teacherDisplayScoreFinal.value : Math.min(100, aiTotal + Math.round((Math.random() - 0.4) * 10))
      const entTotal = Math.min(100, aiTotal + Math.round((Math.random() - 0.4) * 14))
      const baseDims: any[] = (result.value?.evaluation?.scores || []).map((s: any, i: number) => {
        const tScore = (teacherDisplayScores.value || [])[i]?.score ?? Math.min(100, s.score + Math.round((Math.random() - 0.4) * 10))
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
          { role: 'teacher', label: '教师', total: teacherTotal, comment: teacherDisplayComment.value || '' },
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
    // 数据拉取完成后，做一次"教师评分"回填：
    //   如果教师端之前通过 /api/teacher/scores 拿失败、或当前是学生登录，
    //   loadTripartite 返回的 parties 里通常已经带了 teacher 一方的评分，
    //   此时把 teacherData / teacherSaved 补齐，避免 UI 继续显示"待教师评分 / 等待评分中…"
    if (!teacherSaved.value && teacherDisplaySaved.value) {
      const scoresFallback = teacherDisplayScores.value.length
        ? teacherDisplayScores.value
        : (result.value?.evaluation?.scores || []).map((s: any) => ({ name: s.name, score: Number(s.score) || 0, reason: '' }))
      const totalFallback = teacherDisplayScoreFinal.value >= 0
        ? teacherDisplayScoreFinal.value
        : Math.round(scoresFallback.reduce((s, b) => s + b.score, 0) / Math.max(1, scoresFallback.length))
      teacherData.value = {
        total: totalFallback,
        scores: scoresFallback,
        comment: teacherDisplayComment.value
      }
      // 注意：这里不把 teacherSaved 置 true（因为不是教师主动保存的真源），
      //       但 template 会统一通过 teacherDisplaySaved 判定"已评"，所以仍能显示等级。
    }
    tripartiteLoading.value = false
  }
}

/**
 * 异步初始化：拉教师保存分 + 三方对标（仅网络请求，不阻塞 UI）
 * —— 同步解析已在 setup 阶段执行（resolveResultSource），
 *    所以跳转后首次渲染已经能走到 v-else-if="result" 分支，不会白屏/空态。
 */
async function initDetail(forceReload = false) {
  loadingResult.value = true
  loadErr.value = null
  try {
    // 1) 确保同步解析再做一次（localStorage 可能刚写入）
    resolveResultSource()

    // 2) 有 submission_id 就拉教师独立保存分 + 三方对标
    if (result.value?.submission_id) {
      try {
        const res = await axios.get(
          `${API_BASE}/api/teacher/scores/${result.value.submission_id}`,
          { headers: authHeaders() }
        )
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
      // 拉三方对比（如果强制刷新就带 true）
      loadTripartite(Boolean(forceReload))
    } else {
      tripartiteData.value = null
    }

    if (isTeacher.value) {
      calcNextUnscored()
    }
  } catch (err: any) {
    console.error('初始化失败', err)
    loadErr.value = err?.message || '加载数据失败'
    ElMessage.error(loadErr.value)
  } finally {
    loadingResult.value = false
  }
}

// onMounted：做异步数据拉取（组件重建 = 每次跳转都必触发，因为 router-view 已设置 :key="fullPath"）
onMounted(() => {
  nextTick(() => initDetail(false))
})

// onActivated：保留 KeepAlive 兜底（当前 MainLayout 没 <KeepAlive>，防御性保留）
onActivated(() => {
  nextTick(() => initDetail(false))
})

// 路由参数变化：防御性再拉一次；主要保障是 router-view :key 强制重建
watch(
  () => [route.params.id, route.query.id, route.query.submission_id],
  () => {
    resolveResultSource()
    nextTick(() => initDetail(false))
  },
  { flush: 'post' }
)
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

/* ============ 统一头部卡：ru-unified ============ */
.ru-unified {
  max-width: 100%;
  background: #fff;
  border: 1px solid #E5E1D2;
  border-top: 4px solid #165DFF;
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04), 0 12px 36px rgba(17, 24, 39, 0.06);
  overflow: hidden;
}
.ru-section {
  padding: 24px 32px;
  border-bottom: 1px dashed #E5E1D2;
}
.ru-section.ru-last { border-bottom: none; }

.ru-sec-head {
  display: flex; align-items: center; gap: 12px; margin-bottom: 18px;
}
.ru-sec-title {
  margin: 0;
  font-size: 16px; font-weight: 700; color: #111827;
  display: inline-flex; align-items: center; gap: 10px;
  letter-spacing: 0.02em;
}
.sh-ic {
  width: 28px; height: 28px; border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 15px;
}
.ic-cobalt { background: rgba(22, 93, 255, 0.10); color: #165DFF; }

.ru-sec-tag {
  margin-left: auto; font-size: 11px; font-weight: 600;
  padding: 3px 10px; border-radius: 999px;
  background: rgba(22, 93, 255, 0.10);
  color: #165DFF; letter-spacing: 0.08em;
}

/* ====== 三方评分网格 ====== */
.ru-score-grid { display: grid; gap: 14px; }
.ru-score-grid.three { grid-template-columns: repeat(3, minmax(0,1fr)); }
@media (max-width: 1080px) { .ru-score-grid.three { grid-template-columns: 1fr; } }

.ru-score-item {
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  background: #F7F4EC;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
}
.ru-score-item::before {
  content: '';
  position: absolute;
  right: -24px; top: -24px;
  width: 96px; height: 96px;
  border-radius: 50%;
  opacity: 0.20;
}
.score-ai::before { background: #165DFF; }
.score-teacher::before { background: #F59E0B; }
.score-enterprise::before { background: #7C3AED; }

.ru-score-item.is-editing {
  outline: 2px solid rgba(255, 90, 31, 0.45);
  background: rgba(255, 90, 31, 0.04);
}
.ru-score-item.diff-hl {
  border-color: rgba(255, 90, 31, 0.35);
  background: rgba(255, 90, 31, 0.05);
}

.score-top {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 12px;
  position: relative; z-index: 1;
}
.score-ic {
  width: 40px; height: 40px; border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 20px; color: #fff; flex-shrink: 0;
  background: #165DFF;
}
.ic-teacher { background: #D97706; }
.ic-enterprise { background: #7C3AED; }

.score-meta { flex: 1; min-width: 0; }
.score-name {
  font-size: 14.5px; font-weight: 700; color: #111827; line-height: 1.2;
}
.score-sub {
  font-size: 11px; color: #9CA3AF; margin-top: 2px;
}
.score-sub.evaluator { letter-spacing: 0.08em; text-transform: uppercase; }

.score-chip {
  font-size: 11px; font-weight: 700;
  padding: 4px 10px; border-radius: 999px;
  background: rgba(255,255,255,0.75);
  color: #374151;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}
.score-chip.chip-auto { background: rgba(22,93,255,0.12); color: #165DFF; border: 1px solid rgba(22,93,255,0.28); }
.score-chip.chip-done { background: rgba(16,185,129,0.12); color: #16A34A; border: 1px solid rgba(16,185,129,0.28); }
.score-chip.chip-none { background: rgba(156,163,175,0.18); color: #6B7280; border: 1px solid rgba(156,163,175,0.32); }
.score-chip.btn-edit {
  background: rgba(255,90,31,0.12); color: #FF5A1F;
  border: 1px solid rgba(255,90,31,0.28);
  cursor: pointer;
  transition: all 0.15s ease;
}
.score-chip.btn-edit:hover { background: rgba(255,90,31,0.20); }

.score-val-row {
  display: flex; align-items: flex-end; gap: 10px;
  margin-bottom: 10px;
  position: relative; z-index: 1;
}
.score-val {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 42px; line-height: 1;
  color: #111827;
}
.val-ai { background: linear-gradient(135deg, #165DFF 0%, #7C3AED 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.val-teacher { background: linear-gradient(135deg, #B45309 0%, #C2410C 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.val-enterprise { background: linear-gradient(135deg, #6D28D9 0%, #165DFF 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.val-none { color: #9CA3AF; font-size: 38px; }

.score-level {
  margin-bottom: 4px;
  font-size: 11.5px; font-weight: 600;
  padding: 3px 10px; border-radius: 999px;
  background: rgba(255,255,255,0.8);
  flex-shrink: 0;
}
.score-wait {
  margin-bottom: 4px;
  font-size: 11.5px; color: #9CA3AF;
  font-style: italic;
}

.score-comment {
  font-size: 12.5px; color: #6B7280;
  line-height: 1.7;
  margin: 0;
  position: relative; z-index: 1;
}
.score-comment.comment-edit { color: #C2410C; font-weight: 500; }
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ====== 双栏区：结论 + 完成度 ====== */
.ru-columns {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 28px;
}
@media (max-width: 900px) { .ru-columns { grid-template-columns: 1fr; gap: 20px; } }

.ru-col-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.ru-col-title {
  font-size: 15px; font-weight: 700; color: #111827;
  display: inline-flex; align-items: center; gap: 10px;
}
.col-bar {
  width: 6px; height: 20px; border-radius: 999px;
}
.bar-conclusion { background: linear-gradient(180deg, #FF5A1F 0%, #F59E0B 100%); }
.bar-progress { background: linear-gradient(180deg, #10B981 0%, #165DFF 100%); }

/* 核心结论 */
.conclusion-body {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 18px 20px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255,90,31,0.06) 0%, rgba(245,158,11,0.06) 100%);
  border: 1px solid rgba(255, 90, 31, 0.20);
}
.conclusion-ic {
  width: 40px; height: 40px; border-radius: 12px;
  background: rgba(255,90,31,0.15);
  color: #C2410C;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.conclusion-text {
  font-size: 14.5px; color: #111827;
  line-height: 1.9; font-weight: 500;
}
.student-meta-row {
  margin-top: 14px;
  display: flex; flex-wrap: wrap;
  gap: 18px;
  font-size: 12.5px; color: #6B7280;
}
.student-meta-row b { color: #374151; font-weight: 600; }

/* 完成度 */
.progress-grid { display: grid; gap: 12px; margin-bottom: 14px; }
.progress-grid.two { grid-template-columns: repeat(2, minmax(0,1fr)); }

.progress-item {
  padding: 16px 10px;
  border-radius: 14px;
  text-align: center;
  border: 1px solid;
}
.pg-done { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.30); }
.pg-issue { background: rgba(255,90,31,0.08); border-color: rgba(255,90,31,0.30); }

.pg-num {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800; font-size: 26px; line-height: 1.1;
}
.pg-done .pg-num { color: #059669; }
.pg-issue .pg-num { color: #C2410C; }
.pg-lbl {
  font-size: 11.5px;
  margin-top: 4px;
  font-weight: 500;
}
.pg-done .pg-lbl { color: #065F46; }
.pg-issue .pg-lbl { color: #7C2D12; }

.progress-foot {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; color: #6B7280;
  padding-top: 10px;
  border-top: 1px dashed #E5E1D2;
}
.file-info { display: inline-flex; align-items: center; gap: 5px; }
.ic-doc { color: #165DFF; }
.back-link {
  color: #165DFF; font-weight: 600;
  background: none; border: none; cursor: pointer;
  display: inline-flex; align-items: center;
}
.back-link:hover { color: #6366F1; }

/* 三方对标 · 查看详情弹窗样式（三栏并排） */
.tripartite-detail-dialog :deep(.el-dialog__body) {
  padding: 24px 28px !important;
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  background: linear-gradient(180deg, #FCFAF6 0%, #FFFFFF 35%);
}
.tripartite-detail-dialog :deep(.el-dialog__header) {
  padding: 20px 28px 18px !important;
}
.tripartite-detail-dialog :deep(.el-dialog__footer) {
  padding: 16px 28px 22px;
  border-top: 1px solid var(--line-soft);
  background: #FFFBF4;
}
/* 弹窗内部滚动条更轻量 */
.tripartite-detail-dialog :deep(.el-dialog__body)::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.tripartite-detail-dialog :deep(.el-dialog__body)::-webkit-scrollbar-thumb {
  background: rgba(22, 93, 255, 0.12);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
.tripartite-detail-dialog :deep(.el-dialog__body)::-webkit-scrollbar-thumb:hover {
  background: rgba(22, 93, 255, 0.22);
  background-clip: padding-box;
  border: 2px solid transparent;
}
</style>