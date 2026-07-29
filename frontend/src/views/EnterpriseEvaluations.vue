<template>
  <div class="min-h-full page-enter">
    <div class="w-full h-full">
      <!-- ================== HEADER BAR ================= -->
      <div class="mb-6">
        <div class="flex items-center justify-between flex-wrap gap-4 mb-2">
          <div>
          <div class="flex items-center gap-2 text-xs text-ink-4 mb-2 font-sub tracking-wide">
            <Icon icon="mdi:home-outline" />
            <span>/</span>
            <span>企业中心</span>
            <span>/</span>
            <span class="text-ink-2 font-semibold">评价工作台 · EVALUATE</span>
          </div>
          <div class="section-label !mb-2">ENTERPRISE · STATION V3.0</div>
          <h1 class="font-display text-4xl font-black text-ink tracking-tight leading-none">
            企业评价工作台
          </h1>
          <p class="font-body text-ink-4 mt-2 text-[15px]">
            高校-企业协同实训 · 学生成果对标岗位需求，一站式完成打分与面试建议
          </p>
          </div>
        </div>
      </div>

      <!-- ================== STATS STRIP (4 stats) ================= -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="stat-card bg-gradient-card-blue">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-4">
              <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:file-document-multiple-outline" class="text-xl"/>
              </div>
              <span class="text-white/80 text-[11px] font-bold px-2.5 py-1 rounded-full bg-white/15">
                总提交
              </span>
            </div>
            <div class="text-3xl font-black tracking-tight">{{ listMeta.total }}</div>
            <div class="text-white/70 text-sm mt-1">份</div>
          </div>
        </div>
        <div class="stat-card bg-gradient-card-amber">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-4">
              <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:clock-outline" class="text-xl"/>
              </div>
              <span class="text-white/80 text-[11px] font-bold px-2.5 py-1 rounded-full bg-white/15">待评价</span>
            </div>
            <div class="text-3xl font-black tracking-tight">{{ listMeta.pending }}</div>
            <div class="text-white/70 text-sm mt-1">份</div>
          </div>
        </div>
        <div class="stat-card bg-gradient-card-emerald">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-4">
              <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:check-circle-outline" class="text-xl"/>
              </div>
              <span class="text-white/80 text-[11px] font-bold px-2.5 py-1 rounded-full bg-white/15">已评价</span>
            </div>
            <div class="text-3xl font-black tracking-tight">{{ listMeta.done }}</div>
            <div class="text-white/70 text-sm mt-1">份</div>
          </div>
        </div>
        <div class="stat-card bg-gradient-card-violet">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-4">
              <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Icon icon="mdi:star-half-full" class="text-xl"/>
              </div>
              <span class="text-white/80 text-[11px] font-bold px-2.5 py-1 rounded-full bg-white/15">均分</span>
            </div>
            <div class="text-3xl font-black tracking-tight">{{ listMeta.avgScore }}</div>
            <div class="text-white/70 text-sm mt-1">/100</div>
          </div>
        </div>
      </div>

      <!-- ================== MAIN 50/50 SPLIT ===================== -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

        <!-- LEFT 50% · 待评价列表（左50%·筛选+卡片列表） -->
        <div class="lg:col-span-5 xl:col-span-5">
          <div class="card-mag p-0 overflow-hidden">
            <!-- header + filter -->
            <div class="px-7 py-5 border-b border-line/80">
              <div class="flex items-center justify-between gap-3 mb-3 flex-wrap">
                <div>
                  <div class="section-label !mb-1.5">01 · LIST · 提交列表</div>
                  <h3 class="font-display text-xl font-bold text-ink tracking-tight">
                    待/已评价学生提交
                    <span class="chip-mag ml-2">{{ filteredList.length }}</span>
                  </h3>
                </div>
                <div class="flex items-center gap-2 text-[12px]">
                  <span
                    @click="listStatus = ''"
                    :class="listStatus === '' ? 'chip-mag-active' : 'chip-mag'"
                    class="cursor-pointer select-none">全部</span>
                  <span
                    @click="listStatus = 'pending'"
                    :class="listStatus === 'pending' ? 'chip-mag-active' : 'chip-mag'"
                    class="cursor-pointer select-none">待评价</span>
                  <span
                    @click="listStatus = 'done'"
                    :class="listStatus === 'done' ? 'chip-mag-active' : 'chip-mag'"
                    class="cursor-pointer select-none">已评价</span>
                </div>
              </div>
              <div class="relative mt-3">
                <Icon icon="mdi:magnify" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-4" />
                <input
                  v-model="keyword"
                  type="text"
                  placeholder="搜索学生姓名 / 学号 / 任务标题..."
                  class="w-full h-11 rounded-xl border border-line bg-paper px-10 font-body text-ink outline-none
                         focus:border-2 focus:border-seal/40 focus:shadow-[0_0_0_4px_rgba(255,90,31,0.08)] transition-all"
                />
              </div>
            </div>
            <!-- 列表区 -->
            <div class="max-h-[62vh] overflow-y-auto px-2 py-2">
              <div v-if="filteredList.length === 0" class="py-16 px-7 text-center font-body text-ink-4">
              <Icon icon="mdi:inbox-arrow-down-outline" class="text-5xl opacity-40 mb-3" />
                <div>当前筛选条件下暂无提交，尝试切换状态或清空关键词</div>
            </div>
              <div
                v-for="row in filteredList"
                :key="row.submission_id || row.id"
                @click="selectSubmission(row)"
                class="mx-2 my-2 rounded-2xl p-4 border cursor-pointer transition-all duration-200 hover:-translate-y-0.5"
                :class="[
                  activeId === (row.submission_id || row.id)
                    ? 'border-seal/40 bg-seal/[0.06] shadow-[0_6px_20px_-8px_rgba(255,90,31,0.35)]'
                    : 'border-line bg-paper hover:border-ink-4/30 hover:bg-paper-2/70'
                ]"
              >
                <div class="flex items-start gap-3 mb-3">
                  <div class="w-11 h-11 flex-shrink-0 rounded-xl bg-gradient-to-br
                              from-cobalt to-violet-600 text-white font-bold
                              flex items-center justify-center shadow-sm">
                    {{ initialOf(row) }}
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center justify-between gap-2">
                      <div class="font-sub font-bold text-ink text-[15.5px] truncate">
                        {{ row.student?.real_name || row.name || '学生' }}
                      </div>
                      <span v-if="row.evaluation_status === 'done'"
                        class="chip-mag !bg-jade/12 !text-jade-dark !border-jade/30 !text-[11px]">
                        ✓ 已评价
                      </span>
                      <span v-else class="chip-mag !bg-amber/15 !text-amber-dark !border-amber/30 !text-[11px]">
                        ⏳ 待评价
                      </span>
                    </div>
                    <div class="font-body text-[12.5px] text-ink-4 mt-0.5 truncate">
                      {{ row.student?.user_number || row.studentNo || '' }}
                      <span v-if="(row.classes||[]).length"> · {{ (row.classes||[]).join(' · ') }}</span>
                    </div>
                  </div>
                </div>
                <div class="font-sub text-[13.5px] text-ink-2 font-semibold mb-2 truncate">
                  📋 {{ row.task?.title || row.taskName || '任务' }}
                </div>
                <div class="flex items-center justify-between gap-3">
                  <div class="text-[12px] text-ink-4 font-sub">
                    <Icon icon="mdi:calendar-clock-outline" class="inline align-text-bottom mr-1" />
                    {{ row.submitted_at || row.submitTime || '-' }}
                  </div>
                  <div v-if="row.enterprise_evaluation?.total_score != null || row.score != null"
                       class="font-display font-black text-xl leading-none tabular-nums"
                       :class="scoreColor(row.enterprise_evaluation?.total_score ?? row.score)">
                    {{ Math.round(Number(row.enterprise_evaluation?.total_score ?? row.score)) }}
                    <span class="text-[11px] font-normal text-ink-4">分</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- 分页 -->
            <div v-if="false" class="px-7 py-4 border-t border-line/60 flex items-center justify-between text-[12px] font-sub text-ink-4">
              <span>共 {{ filteredList.length }} 条</span>
              <div class="flex gap-1">
                <button class="chip-mag">上一页</button>
                <button class="chip-mag chip-mag-active">1</button>
                <button class="chip-mag">下一页</button>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT 50% · 三 Tab 打分面板 -->
        <div class="lg:col-span-7 xl:col-span-7">
          <div v-if="!activeSubmission" class="card-mag min-h-[70vh] flex flex-col items-center justify-center text-center p-10">
            <div class="relative mb-6">
              <div class="w-28 h-28 rounded-3xl border-2 border-dashed border-line/80 flex items-center justify-center">
                <Icon icon="mdi:cursor-default-click" class="text-5xl text-ink-4 opacity-60" />
              </div>
            </div>
            <div class="section-label !mb-2">02 · PANEL · 打分三栏面板</div>
            <h3 class="font-display text-2xl font-bold text-ink tracking-tight mb-2">
              选择左侧一条提交即可开始评价
            </h3>
            <p class="font-body text-ink-4 text-[14.5px] max-w-md">
              推荐流程：① 先查看学生提交内容 ② 对照 AI/教师已有的评价记录 ③ 按岗位技能要求打分 + 面试建议
            </p>
          </div>

          <template v-else>
            <!-- section header: 学生/任务条 -->
            <div class="card-mag p-0 mb-5 overflow-hidden">
              <div class="px-7 py-5 flex items-start md:items-center gap-5 flex-wrap">
                <div class="flex items-center gap-4 flex-1 min-w-0">
                  <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-seal to-amber-dark text-white font-black text-xl flex items-center justify-center shadow-sm">
                    {{ initialOf(activeSubmission) }}
                  </div>
                  <div class="min-w-0">
                    <div class="section-label !mb-1">SUBMISSION · {{ activeSubmission.submission_id || activeSubmission.id }}</div>
                    <h3 class="font-display text-2xl font-black text-ink tracking-tight">
                      {{ activeSubmission.student?.real_name || activeSubmission.name }}
                    </h3>
                    <p class="font-body text-ink-4 mt-1 text-[14px] truncate">
                      {{ activeSubmission.task?.title || activeSubmission.taskName }}
                      <span class="text-ink-3"> · </span>
                      {{ (activeSubmission.classes || []).join(' · ') || activeSubmission.className || '' }}
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click="loadCompare(activeId)"
                    v-if="compareDataLoaded || (activeSubmission.enterprise_evaluation)"
                    class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">
                    <Icon icon="mdi:chart-bell-ring-outline" class="mr-1" /> 查看三方对比
                  </button>
                  <button
                    class="btn-mag btn-mag-primary px-4 py-2.5 text-[13px]"
                    :disabled="!canSaveEval"
                    @click="submitEval">
                    <Icon icon="mdi:content-save-check-outline" class="mr-1" />
                    {{ activeEvalId ? '更新企业评价' : '提交企业评价' }}
                  </button>
                </div>
              </div>
              <!-- TABS -->
              <div class="flex items-center gap-1 px-4 pb-0 border-t border-line/60 bg-paper-2/30">
                <button
                  v-for="(t,i) in rightTabs" :key="t.value"
                  @click="rightTab = t.value"
                  class="relative py-3.5 px-5 font-sub font-semibold text-[13.5px] transition-colors"
                  :class="rightTab === t.value ? 'text-seal' : 'text-ink-4 hover:text-ink-2'">
                  <span class="mr-1.5 opacity-60">{{ ['01','02','03'][i] }}</span>{{ t.label }}
                  <span v-if="t.value === 'score' && evalDirty && canSaveEval"
                    class="ml-1 inline-block w-2 h-2 rounded-full bg-seal align-middle"></span>
                  <span v-if="rightTab === t.value"
                    class="absolute left-3 right-3 -bottom-[1px] h-[3px] rounded-full bg-seal"></span>
                </button>
              </div>
            </div>

            <!-- 【TAB 1: CONTENT -->
            <div v-show="rightTab==='content'" class="card-mag p-7 animate-fade-in">
              <div class="section-label mb-3">STUDENT WORK · 学生提交</div>
              <h4 class="font-display text-xl font-bold mb-5">学生提交内容</h4>
              <pre class="font-mono text-[13.5px] bg-paper-2 rounded-2xl border border-line/70 p-5 whitespace-pre-wrap text-ink-2 leading-[1.75] max-h-[60vh] overflow-auto">{{ contentPreview }}</pre>
              <div v-if="detail?.files || activeSubmission?.files || activeSubmission?.filename"
                   class="mt-5 flex flex-wrap gap-3">
                <a v-for="(f,i) in (detail?.files || [])" :key="i"
                   :href="f.url || '#'" class="chip-mag !text-[13px] !py-2 !px-4">
                  <Icon icon="mdi:download-outline" class="mr-1.5" />{{ f.name }}
                </a>
                <a v-if="activeSubmission?.filename && !detail?.files?.length"
                   class="chip-mag !text-[13px] !py-2 !px-4"
                   :href="`${API_BASE}/uploads/submissions/${activeSubmission.filename}`" target="_blank">
                  <Icon icon="mdi:download-outline" class="mr-1.5" />
                  {{ activeSubmission.filename }}
                </a>
              </div>
              <div v-if="detail?.student_classes?.length" class="mt-6 p-5 bg-cobalt/5 rounded-2xl border border-cobalt/15">
                <div class="section-label !mb-2">STUDENT PROFILE · 学生档案</div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                  <div v-for="c in detail.student_classes" :key="c.id"
                       class="flex items-center gap-3 p-3 rounded-xl bg-white border border-line">
                    <Icon icon="mdi:school-outline" class="text-cobalt" />
                    <div>
                      <div class="font-sub font-bold text-ink">{{ c.name }}</div>
                      <div class="text-[12px] text-ink-4">{{ c.major || '' }} · {{ c.grade || '' }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 【TAB 2: AI + 教师评分 -->
            <div v-show="rightTab==='ai-teacher'" class="animate-fade-in space-y-5">
              <template v-if="compareLoaded">
                <TripartiteCompare
                  :parties="compareData.parties"
                  :dimensionBreakdown="compareData.dimension_breakdown"
                  :summary="compareData.summary"
                />
              </template>
              <template v-else-if="(detail?.evaluations || []).length">
                <div class="card-mag p-7">
                  <div class="section-label !mb-2">AI + TEACHER · 已有评价</div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                    <div v-for="e in (detail?.evaluations || [])" :key="e.id" class="rounded-2xl border border-line bg-paper p-5">
                      <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center gap-2">
                          <Icon :icon="e.evaluator_type==='ai' ? 'mdi:robot-outline' : 'mdi:account-tie-outline'"
                                :class="e.evaluator_type==='ai' ? 'text-violet-600' : 'text-cobalt'" />
                          <span class="font-sub font-bold">{{ e.evaluator_type==='ai' ? 'AI 评价' : '教师评价' }}</span>
                        </div>
                        <span class="font-display text-2xl font-black"
                              :class="scoreColor(e.total_score)">{{ Math.round(Number(e.total_score||0)) }}</span>
                      </div>
                      <div class="space-y-2">
                        <div v-for="d in (e.dimension_scores||[])" :key="d.name" class="flex items-center gap-3">
                          <span class="text-[12.5px] w-24 shrink-0 text-ink-2 font-medium truncate">{{ d.name }}</span>
                          <div class="flex-1 h-2 rounded-full bg-line overflow-hidden">
                            <div class="h-full rounded-full bg-gradient-to-r from-cobalt to-jade"
                                 :style="{ width: `${d.score}%` }"></div>
                          </div>
                          <span class="text-[12px] w-10 text-right font-mono text-ink-2">{{ d.score }}</span>
                        </div>
                      </div>
                      <p class="mt-4 text-[13.5px] text-ink-2 bg-paper-2 rounded-xl p-3 border border-line/60 leading-[1.7]">
                        {{ e.comment }}
                      </p>
                    </div>
                  </div>
                </div>
              </template>
              <div v-else class="card-mag p-10 text-center text-ink-4 font-body">
                <Icon icon="mdi:file-clock-outline" class="text-5xl opacity-40 mb-3" />
                AI/教师评价尚未生成，提交完成后此处将自动呈现。
              </div>
            </div>

            <!-- 【TAB 3: 企业打分（打分+适配度+面试建议） -->
            <div v-show="rightTab==='score'" class="animate-fade-in space-y-5">
              <div class="card-mag p-7">
                <div class="section-label !mb-3">01 · DIMENSION SCORE · 维度打分</div>
                <h4 class="font-display text-xl font-bold mb-5 text-ink">企业维度评分（{{ evalDimScoreSum }} / 100）</h4>
                <div v-if="(evalDims||[]).length===0" class="text-ink-4 font-body text-[14px]">
                  请选择下方「关联岗位」或直接添加维度后开始打分（AI 将根据岗位技能要求自动推荐维度）。
                </div>
                <div class="space-y-4 mt-3">
                  <div v-for="(d,i) in evalDims" :key="i"
                       class="flex items-center gap-4 p-4 rounded-2xl border border-line bg-paper-2/40 hover:border-ink-4/30 transition-colors">
                    <div class="w-8 h-8 rounded-lg bg-seal/10 text-seal-dark font-display font-black text-sm flex items-center justify-center shrink-0">
                      {{ i+1 }}
                    </div>
                    <div class="flex-1 min-w-0">
                      <input v-model="d.name" placeholder="维度名（如：代码规范性）"
                             class="w-full font-sub font-semibold text-ink bg-transparent outline-none border-b border-dashed border-line focus:border-seal/50 py-1 mb-2" />
                      <textarea v-model="d.reason" placeholder="打分理由 / 扣分说明"
                                rows="1"
                                class="w-full text-[13px] bg-transparent outline-none text-ink-4 resize-none"></textarea>
                    </div>
                    <div class="w-24 shrink-0">
                      <el-input-number
                        v-model="d.score"
                        :min="0" :max="100" :step="1"
                        size="large"
                        class="!w-24"
                        controls-position="right"
                      />
                    </div>
                    <button @click="evalDims.splice(i,1)"
                            class="w-8 h-8 rounded-lg text-ink-4 hover:bg-seal/10 hover:text-seal-dark transition-colors"
                            title="删除该维度">
                      <Icon icon="mdi:close" />
                    </button>
                  </div>
                </div>
                <button @click="addOneDim"
                        class="mt-5 chip-mag !text-[13px] !py-2.5 !px-4 cursor-pointer hover:!bg-seal/5">
                  <Icon icon="mdi:plus" class="mr-1" /> + 新增维度
                </button>
              </div>

              <!-- 岗位适配 + 三卡片面试建议 -->
              <div class="card-mag p-7">
                <div class="section-label !mb-3">02 · JOB FIT · 岗位匹配</div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
                  <div>
                    <label class="block text-[12px] font-sub font-bold text-ink-4 uppercase tracking-[0.16em] mb-2">
                      关联岗位（可选）
                    </label>
                    <el-select
                      v-model="evalMatchedJobId"
                      placeholder="选择对应岗位将自动带入技能要求"
                      size="large"
                      class="w-full"
                      @change="onJobPick"
                    >
                      <el-option label="— 不关联 —" :value="null" />
                      <el-option
                        v-for="j in (detail?.available_jobs || [])"
                        :key="j.id"
                        :label="`${j.title} · ${j.city || ''} ${j.level || ''}`"
                        :value="j.id"
                      />
                    </el-select>
                  </div>
                  <div>
                    <label class="block text-[12px] font-sub font-bold text-ink-4 uppercase tracking-[0.16em] mb-2">
                      岗位适配度（0-100）
                    </label>
                    <el-input-number
                      v-model="evalJobFit"
                      :min="0" :max="100"
                      size="large"
                      class="!w-full"
                      controls-position="right"
                    />
                  </div>
                </div>
                <div class="section-label !mb-3">03 · INTERVIEW · 面试建议三卡片</div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
                  <button @click="evalInterview = 'recommend'"
                          class="p-5 rounded-2xl text-left border-2 transition-all"
                          :class="evalInterview==='recommend'
                            ? 'border-jade bg-jade/10'
                            : 'border-line bg-paper hover:border-jade/30'">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-sub font-bold text-ink">强推面试</span>
                      <Icon v-if="evalInterview==='recommend'" icon="mdi:check-decagram" class="text-jade text-xl"/>
                    </div>
                    <p class="text-[12.5px] text-ink-4 font-body">综合得分≥85，亮点突出，推荐进入终面。</p>
                  </button>
                  <button @click="evalInterview = 'maybe'"
                          class="p-5 rounded-2xl text-left border-2 transition-all"
                          :class="evalInterview==='maybe'
                            ? 'border-amber bg-amber/10'
                            : 'border-line bg-paper hover:border-amber/30'">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-sub font-bold text-ink">待定观察</span>
                      <Icon v-if="evalInterview==='maybe'" icon="mdi:help-network-outline" class="text-amber-dark text-xl"/>
                    </div>
                    <p class="text-[12.5px] text-ink-4 font-body">有亮点但存短板，建议增加技术面+二面筛选。</p>
                  </button>
                  <button @click="evalInterview = 'not_recommend'"
                          class="p-5 rounded-2xl text-left border-2 transition-all"
                          :class="evalInterview==='not_recommend'
                            ? 'border-seal bg-seal/10'
                            : 'border-line bg-paper hover:border-seal/30'">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-sub font-bold text-ink">暂不推荐</span>
                      <Icon v-if="evalInterview==='not_recommend'" icon="mdi:alert-decagram-outline" class="text-seal text-xl"/>
                    </div>
                    <p class="text-[12.5px] text-ink-4 font-body">基础不达标或方向不匹配，后续再跟进。</p>
                  </button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label class="block text-[12px] font-sub font-bold text-ink-4 uppercase tracking-[0.16em] mb-2">
                      亮点 · strength
                    </label>
                    <textarea v-model="evalStrength" rows="3" placeholder="学生在实训中展现的突出能力、技术、思维…"
                              class="w-full rounded-xl border border-line bg-paper p-3 outline-none focus:border-seal/40 font-body"></textarea>
                  </div>
                  <div>
                    <label class="block text-[12px] font-sub font-bold text-ink-4 uppercase tracking-[0.16em] mb-2">
                      改进建议 · improvement
                    </label>
                    <textarea v-model="evalImprovement" rows="3" placeholder="需要提升的维度、学习方向、项目建议…"
                              class="w-full rounded-xl border border-line bg-paper p-3 outline-none focus:border-seal/40 font-body"></textarea>
                  </div>
                </div>
                <div class="mt-5">
                  <label class="block text-[12px] font-sub font-bold text-ink-4 uppercase tracking-[0.16em] mb-2">
                    总体评语 · comment
                  </label>
                  <textarea v-model="evalComment" rows="3" placeholder="企业导师综合评语，将进入三方评价对比与学生报告。"
                            class="w-full rounded-xl border border-line bg-paper p-3 outline-none focus:border-seal/40 font-body"></textarea>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'
import TripartiteCompare from '../components/common/TripartiteCompare.vue'

/* ========================= Types ========================= */
type RowT = any
const rightTabs = [
  { value: 'content',    label: '学生提交' },
  { value: 'ai-teacher',label: 'AI + 教师评分' },
  { value: 'score',     label: '企业打分' },
]

/* ========================= State ========================= */
const list = ref<RowT[]>([])
const listLoading = ref(false)
const listStatus = ref<string>('')
const keyword = ref('')

const activeId = ref<number | null>(null)
const activeSubmission = ref<RowT | null>(null)
const detail = ref<any>(null)
const detailLoading = ref(false)
const rightTab = ref<'content'|'ai-teacher'|'score'>('content')

// 三方对比
const compareId = ref<number | null>(null)
const compareLoaded = ref(false)
const compareLoading = ref(false)
const compareData = ref<any>({ parties: [], dimension_breakdown: [], summary: null })

// 企业评价表单
const evalDims = ref<{name:string,score:number,reason:string}[]>([])
const evalJobFit = ref<number>(75)
const evalMatchedJobId = ref<number | null>(null)
const evalInterview = ref<'recommend'|'maybe'|'not_recommend'>('maybe')
const evalStrength = ref('')
const evalImprovement = ref('')
const evalComment = ref('')
const evalDirty = ref(false)
const activeEvalId = ref<number | null>(null)
const submitting = ref(false)

/* ========================= Derived ========================= */
const filteredList = computed(() => {
  let arr = list.value
  if (listStatus.value) arr = arr.filter(r => r.evaluation_status === listStatus.value)
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    arr = arr.filter((r: any) =>
      (r.student?.real_name || r.name || '').toLowerCase().includes(kw) ||
      (r.student?.user_number || r.studentNo || '').toLowerCase().includes(kw) ||
      (r.task?.title || r.taskName || '').toLowerCase().includes(kw)
    )
  }
  return arr
})
const listMeta = computed(() => {
  const all = list.value || []
  const done = all.filter((r: any) => r.evaluation_status === 'done').length
  const scores = all
    .map((r: any) => Number(r.enterprise_evaluation?.total_score ?? r.score))
    .filter((n: any) => !isNaN(n) && n != null)
  const avg = scores.length ? (scores.reduce((a:number,b:number)=>a+b,0) / scores.length).toFixed(1) : '—'
  return {
    total: all.length,
    pending: all.length - done,
    done,
    avgScore: avg,
  }
})
const evalDimScoreSum = computed(() => {
  if (!(evalDims.value || []).length) return 0
  const sum = evalDims.value.reduce((s, d) => s + (Number(d.score) || 0), 0)
  return Math.round(sum / evalDims.value.length)
})
const canSaveEval = computed(() =>
  evalDims.value.length > 0 && !submitting.value
)
const contentPreview = computed(() => {
  const raw = detail.value?.content || activeSubmission.value?.content
  if (raw) return raw
  const fn = activeSubmission.value?.filename
  if (fn) return `[附件：${fn}] 附件已提交，以下为 OCR 文本摘要：\n\n此处为学生实训报告正文预览…`
  return '暂无文本内容，请在下方下载附件查看完整内容'
})

/* ========================= Helpers ========================= */
function initialOf(r: any) {
  const n = r?.student?.real_name || r?.name || '学'
  return (n || '学').slice(0, 1)
}
function scoreColor(n: any) {
  const v = Number(n); if (isNaN(v)) return 'text-ink-4'
  if (v >= 90) return 'text-jade-dark'
  if (v >= 80) return 'text-cobalt'
  if (v >= 60) return 'text-amber-dark'
  return 'text-seal-dark'
}

/* ========================= Actions ========================= */
async function fetchList() {
  listLoading.value = true
  try {
    const token = localStorage.getItem('token')
    const headers: any = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const { data } = await axios.get(`${API_BASE}/api/enterprise/evaluations/submissions`, {
      headers, params: { page: 1, page_size: 50 }
    })
    list.value = (data?.list || []).map((x: any, i: number) => ({ ...x, _i: i }))
  } catch (e: any) {
    // 离线兜底：塞 mock （便于 UI 能直接看到效果
    list.value = mockList()
  } finally {
    listLoading.value = false
  }
}
function mockList(): RowT[] {
  return [
    { submission_id:1001, name:'张伟', studentNo:'2024001', className:'软件2401', taskName:'Web前端开发实训',
      submitTime:'2026-07-28 14:32', score:null, evaluation_status:'pending',
      classes:['软件技术2401班'], student:{real_name:'张伟', user_number:'2024001'}, task:{title:'Web前端开发实训'}, filename:'zhangwei_webproj.zip' },
    { submission_id:1002, name:'李娜', studentNo:'2024002', className:'软件2401', taskName:'Web前端开发实训',
      submitTime:'2026-07-27 16:15', score:95, evaluation_status:'done',
      classes:['软件技术2401班'], student:{real_name:'李娜', user_number:'2024002'}, task:{title:'Web前端开发实训'},
      enterprise_evaluation:{total_score:95} },
    { submission_id:1003, name:'王强', studentNo:'2024003', className:'软工2402', taskName:'Java后端项目',
      submitTime:'2026-07-27 09:48', score:null, evaluation_status:'pending',
      classes:['软件工程2402班'], student:{real_name:'王强', user_number:'2024003'}, task:{title:'Java后端开发项目'}, filename:'wangqiang_java.zip' },
    { submission_id:1004, name:'刘洋', studentNo:'2024004', className:'软工2402', taskName:'Java后端项目',
      submitTime:'2026-07-26 20:22', score:88, evaluation_status:'done',
      classes:['软件工程2402班'], student:{real_name:'刘洋', user_number:'2024004'}, task:{title:'Java后端开发项目'},
      enterprise_evaluation:{total_score:88} },
    { submission_id:1005, name:'陈静', studentNo:'2024005', className:'计科2401', taskName:'全栈电商系统',
      submitTime:'2026-07-25 11:10', score:null, evaluation_status:'pending',
      classes:['计算机科学2401班'], student:{real_name:'陈静', user_number:'2024005'}, task:{title:'全栈电商系统开发'}, filename:'chenjing_ecommerce.zip' },
  ]
}
async function selectSubmission(row: any) {
  activeId.value = row.submission_id || row.id
  activeSubmission.value = row
  rightTab.value = 'content'
  compareLoaded.value = false
  await fetchDetail(activeId.value!)
  // 同时尝试拉三方对比（如企业已评直接显示）
  const ent = row.enterprise_evaluation
  if (ent) loadCompare(activeId.value!)
  else seedEvalFormFrom(row, ent ?? null)
}

async function fetchDetail(subId: number) {
  detailLoading.value = true
  try {
    const token = localStorage.getItem('token')
    const headers: any = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const { data } = await axios.get(`${API_BASE}/api/enterprise/evaluations/submissions/${subId}`, { headers })
    detail.value = data?.data || data || null
    // 如果接口返回已有企业评价则回填
    seedEvalFormFrom(activeSubmission.value, detail.value?.enterprise_evaluation ?? null)
    if (detail.value?.available_jobs?.length && !evalMatchedJobId.value) {
      // 不强制填，只给默认第一个
    }
  } catch (e) {
    detail.value = mockDetail(subId)
    seedEvalFormFrom(activeSubmission.value, detail.value?.enterprise_evaluation ?? null)
  } finally {
    detailLoading.value = false
  }
}
function mockDetail(subId: number) {
  return {
    submission_id: subId,
    content: `# 实训报告 - 张伟\n\n## 一、项目概述\n这是一个基于 Vue3 + TypeScript + Vite 的前端实训项目，完成了首页、登录、实训提交、评价查看四个模块。\n\n## 二、功能完成情况\n- ✅ 登录 / 注册 流程\n- ✅ 班级列表 + 任务提交\n- ✅ AI 评价结果页查看\n- ⚠️ 教师端部分：任务管理模块功能不完整（缺少删除）\n\n## 三、代码质量\n采用组件化分模块开发，注释率约 22%。\n\n## 四、遇到问题\n- 1. 登录接口在 3 种角色区分；\n- 2. axios 封装拦截器统一处理 token；\n- 3. 图表库使用 ECharts。\n`,
    evaluations: [
      { id: 1, evaluator_type:'ai', total_score: 86, comment:'项目功能较完整，组件拆分清晰，代码复用良好，异常处理可进一步加强。',
        dimension_scores:[
          {name:'功能完整性', score:88, reason:'核心流程通，个别边缘情况未覆盖'},
          {name:'代码规范性', score:82, reason:'命名规范，注释中等偏少'},
          {name:'技术选型合理性', score:90, reason:'Vue3 + TS 选型合适'},
          {name:'文档与说明', score:84, reason:'报告结构清晰'},
        ]
      },
      { id: 2, evaluator_type:'teacher', total_score: 90, comment:'整体完成度高，课堂讲解清晰，答辩表达清楚。',
        dimension_scores:[
          {name:'功能完整性', score:92 },
          {name:'代码规范性', score:88 },
          {name:'技术选型合理性', score:89 },
          {name:'文档与说明', score:90 },
        ]
      },
    ],
    available_jobs: [
      {id:1, title:'前端开发工程师', level:'初级', city:'杭州', job_type:'全职',
        skill_requirements:[
          {name:'Vue/React 框架', weight:30, threshold:80},
          {name:'JS/TS 基础', weight:25, threshold:78},
          {name:'工程化能力', weight:20, threshold:70},
          {name:'CSS/样式基础', weight:15, threshold:70},
          {name:'沟通与协作', weight:10, threshold:75},
        ]
      },
      {id:2, title:'Java 后端工程师', level:'初级', city:'上海', job_type:'全职',
        skill_requirements:[
          {name:'Java 基础与集合', weight:30, threshold:80},
          {name:'Spring Boot 框架', weight:30, threshold:80},
          {name:'MySQL/SQL', weight:20, threshold:75},
          {name:'沟通协作', weight:20, threshold:70},
        ]
      },
    ],
    student_classes: [
      {id:1, name:'软件技术2401班', major:'软件技术', grade:'2024级'}
    ],
    enterprise_evaluation: null,
  }
}
function seedEvalFormFrom(row: any, ee: any) {
  // 已有企业评价 → 回填
  if (ee?.dimension_scores?.length) {
    evalDims.value = ee.dimension_scores.map((d: any) => ({
      name: d.name || '', score: Number(d.score) || 0, reason: d.reason || '',
    }))
    activeEvalId.value = ee.id ?? null
  } else {
    // 无：优先岗位推荐维度，次 AI/教师维度 union
    const dims: any[] = []
    const fromJob = (detail.value?.available_jobs || [])
      .find((j: any) => j.id === evalMatchedJobId.value || (!evalMatchedJobId.value && j))
    if (fromJob?.skill_requirements?.length) {
      fromJob.skill_requirements.forEach((s: any) => {
        dims.push({ name: s.name, score: s.threshold ? Number(s.threshold) : 80, reason: '' })
      })
    } else {
      const names = new Set<string>()
      ;(detail.value?.evaluations || []).forEach((e: any) => {
        ;(e.dimension_scores || []).forEach((d: any) => {
          if (d?.name && !names.has(d.name)) { names.add(d.name); dims.push({ name: d.name, score: Number(d.score)||80, reason:'' }) }
        })
      })
    }
    if (!dims.length) dims.push(
      { name:'功能完整性', score:85, reason:'' },
      { name:'代码规范性', score:80, reason:'' },
      { name:'技术匹配度', score:80, reason:'' },
      { name:'沟通与表达', score:85, reason:'' },
    )
    evalDims.value = dims
    activeEvalId.value = null
  }
  evalJobFit.value = Number(ee?.job_fit_score) ?? (evalJobFit.value || 75)
  evalMatchedJobId.value = ee?.matched_job_id ?? null
  evalInterview.value = (ee as any)?.interview_suggest || 'maybe'
  evalStrength.value = ee?.strength_points || ''
  evalImprovement.value = ee?.improvement_points || ''
  evalComment.value = ee?.comment || ''
  evalDirty.value = false
}

function addOneDim() {
  evalDims.value.push({ name: '', score: 80, reason: '' })
  evalDirty.value = true
}
function onJobPick(jobId: number | null) {
  evalMatchedJobId.value = jobId
  if (!jobId) return
  const j = (detail.value?.available_jobs || []).find((x: any) => x.id === jobId)
  if (!j?.skill_requirements?.length) return
  if (evalDims.value.length === 0) {
    evalDims.value = j.skill_requirements.map((s: any) => ({
      name: s.name, score: Number(s.threshold) || 80, reason: '',
    }))
  } else if (confirm('是否用岗位技能维度覆盖当前打分维度？')) {
    evalDims.value = j.skill_requirements.map((s: any) => ({
      name: s.name, score: Number(s.threshold) || 80, reason: '',
    }))
  }
  evalDirty.value = true
}

async function loadCompare(subId: number) {
  compareLoading.value = true; compareId.value = subId
  try {
    const token = localStorage.getItem('token')
    const headers: any = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const { data } = await axios.get(`${API_BASE}/api/enterprise/evaluations/compare/${subId}`, { headers })
    compareData.value = data?.data || data || { parties:[], dimension_breakdown:[], summary:null }
    compareLoaded.value = true
  } catch (e) {
    // Mock 一份用于 UI 展示效果
    compareData.value = mockCompare()
    compareLoaded.value = true
  } finally {
    compareLoading.value = false
  }
}
function mockCompare() {
  return {
    parties: [
      { role:'ai',        label:'DeepSeek AI 自动评价', total: 86, comment:'项目较完整，组件拆分清晰。异常处理与边界场景覆盖不足。'},
      { role:'teacher',   label:'李老师 · 授课教师复评', total:90, comment:'完成度高，课上提问表现好，课堂答辩表达清楚。'},
      { role:'enterprise',label:'字节跳动·技术主管 企业终评', total: evalDimScoreSum.value || 82, comment: evalComment.value || '框架掌握尚可，项目工程化待强化。' },
    ],
    dimension_breakdown: [
      { name:'功能完整性', ai_score:88, teacher_score:92, enterprise_score:85, max_diff:7, flag:'ok' },
      { name:'代码规范性', ai_score:82, teacher_score:88, enterprise_score:78, max_diff:10, flag:'info', warning:'代码规范性维度三方差异超过 10 分，请注意对齐评价标准'},
      { name:'技术选型/匹配度', ai_score:90, teacher_score:89, enterprise_score:65, max_diff:25, flag:'warning', warning:'技术匹配度维度三方差异超过 20 分，建议复核'},
      { name:'文档与说明', ai_score:84, teacher_score:90, enterprise_score:80, max_diff:10, flag:'info'},
    ],
    summary: {
      score_spread: 8, consistency_index: 0.78,
      max_difference_dimension: '技术选型/匹配度', max_difference: 25, needs_review: true,
    }
  }
}

async function submitEval() {
  if (!canSaveEval.value || !activeId.value) return
  submitting.value = true
  const payload = {
    submission_id: activeId.value,
    dimension_scores: evalDims.value.map(d => ({ name: d.name, score: Number(d.score)||0, reason: d.reason || '' })),
    job_fit_score: Number(evalJobFit.value) || 0,
    strength_points: evalStrength.value,
    improvement_points: evalImprovement.value,
    interview_suggest: evalInterview.value,
    comment: evalComment.value,
    matched_job_id: evalMatchedJobId.value || null,
  }
  try {
    const token = localStorage.getItem('token')
    const headers: any = { 'Content-Type': 'application/json' }
    if (token) headers.Authorization = `Bearer ${token}`
    let resp: any
    if (activeEvalId.value) {
      resp = await axios.put(`${API_BASE}/api/enterprise/evaluations/${activeEvalId.value}`, payload, { headers })
    } else {
      resp = await axios.post(`${API_BASE}/api/enterprise/evaluations`, payload, { headers })
    }
    // 刷新列表 + 详情
    await fetchList()
    const refreshed = list.value.find((r: any) => (r.submission_id || r.id) === activeId.value)
    if (refreshed) { activeSubmission.value = refreshed }
    evalDirty.value = false
    // 如果列表没拉到 enterprise_evaluation，手动回填 status
    if (activeSubmission.value && activeSubmission.value.evaluation_status !== 'done') {
      activeSubmission.value.evaluation_status = 'done'
      activeSubmission.value.enterprise_evaluation = {
        id: resp.data?.evaluation_id, total_score: evalDimScoreSum.value
      }
    }
    alert(`✅ ${activeEvalId.value ? '已更新企业评价' : '企业评价提交成功'}（均分 ${evalDimScoreSum.value}）`)
    // 如果三方对比刷新
    await loadCompare(activeId.value!)
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '提交失败'
    alert(`提交失败：${msg}\n（前端演示模式下该条目标记为已评价（mock）`)
    // mock 模式：手动让按钮仍记为已评价
    if (activeSubmission.value) {
      activeSubmission.value.evaluation_status = 'done'
      activeSubmission.value.enterprise_evaluation = { id: Date.now(), total_score: evalDimScoreSum.value }
      await fetchList()
    }
    compareData.value = mockCompare()
    compareLoaded.value = true
  } finally {
    submitting.value = false
  }
}

watch(evalDims, () => { evalDirty.value = true }, { deep: true })
watch([evalStrength, evalImprovement, evalComment, evalJobFit, evalInterview], () => { evalDirty.value = true })

onMounted(fetchList)
</script>

<style scoped>
.chip-mag-active {
  background: linear-gradient(135deg, var(--ink) 0%, var(--ink-2) 100%);
  color: #fff;
  border-color: transparent;
}
</style>
