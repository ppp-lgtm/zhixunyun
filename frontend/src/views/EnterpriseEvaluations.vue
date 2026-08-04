<template>
  <div class="min-h-full page-enter">
    <div class="w-full h-full">
      <!-- ================== 单张大卡片：标题 / 列表 / 详情 / 评分 全在里面 ================= -->
      <div class="card-mag p-0 overflow-hidden">

        <!-- ---- HEADER：标题 + 简介 ---- -->
        <div class="px-8 pt-7 pb-6 border-b border-line/80">
          <div class="flex items-center justify-between flex-wrap gap-4">
            <div class="min-w-0">
              <h1 class="font-display text-4xl font-black text-ink tracking-tight leading-none">
                企业评价工作台
              </h1>
              <p class="font-body text-ink-4 mt-2 text-[15px]">
                高校-企业协同实训 · 学生成果对标岗位需求，一站式完成打分与面试建议
              </p>
            </div>
            <div class="flex items-center gap-2 text-[12.5px] font-sub text-ink-3">
              <span class="chip-mag">总计 {{ filteredList.length }} 条</span>
              <span class="chip-mag !bg-amber/12 !text-amber-dark !border-amber/25">待评价 {{ listMeta.pending }}</span>
              <span class="chip-mag !bg-jade/12 !text-jade-dark !border-jade/25">已评价 {{ listMeta.done }}</span>
              <button @click="fetchList" class="chip-mag hover:!bg-seal/5">
                <Icon icon="mdi:refresh" class="mr-1" inline width="12" /> 刷新
              </button>
            </div>
          </div>

          <!-- 接口错误提示（总卡内部） -->
          <div v-if="listLoadError" class="mt-5 rounded-2xl border-2 border-seal/30 bg-seal/[0.06] px-5 py-4 flex items-start gap-3">
            <Icon icon="mdi:alert-circle-outline" class="text-seal text-xl flex-shrink-0 mt-0.5" />
            <div class="text-[13.5px] text-seal-dark leading-[1.7] flex-1">{{ listLoadError }}</div>
          </div>
        </div>

        <!-- ---- MAIN：5/7 两列，内部不再用 card-mag，只用分隔线 ---- -->
        <div class="grid grid-cols-1 lg:grid-cols-12">

          <!-- ===== LEFT：提交列表（无外卡，右分隔线） ===== -->
          <div class="lg:col-span-5 xl:col-span-5 lg:border-r border-line/80">
            <!-- 列表头部：筛选 + 搜索 -->
            <div class="px-7 py-5 border-b border-line/80">
              <div class="flex items-center justify-between gap-3 mb-3 flex-wrap">
                <div>
                  <div class="section-label !mb-1.5">01 · LIST · 提交列表</div>
                  <h3 class="font-display text-xl font-bold text-ink tracking-tight">
                    待/已评价学生提交
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
            <div class="max-h-[72vh] overflow-y-auto px-2 py-3">
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
          </div>

          <!-- ===== RIGHT：单页融合（无外卡） ===== -->
          <div class="lg:col-span-7 xl:col-span-7">
            <!-- 未选中：空态（用内部留白，不套卡） -->
            <div v-if="!activeSubmission" class="min-h-[72vh] flex flex-col items-center justify-center text-center p-12">
              <div class="relative mb-6">
                <div class="w-28 h-28 rounded-3xl border-2 border-dashed border-line/80 flex items-center justify-center">
                  <Icon icon="mdi:cursor-default-click" class="text-5xl text-ink-4 opacity-60" />
                </div>
              </div>
              <div class="section-label !mb-2">02 · UNIFIED WORKSPACE · 一体化工作面板</div>
              <h3 class="font-display text-2xl font-bold text-ink tracking-tight mb-2">
                选择左侧一条提交即可开始评价
              </h3>
              <p class="font-body text-ink-4 text-[14.5px] max-w-md">
                融合视图：① 学生卡 ② 提交内容 ③ AI/教师参考评分 ④ 企业维度评分 + 岗位匹配，一站式完成打分。
              </p>
            </div>

            <template v-else>
              <!-- ===== 01 · 顶部学生卡（吸顶保存条）===== -->
              <div class="sticky top-3 z-20 bg-paper border-y border-line/80 px-8 py-5 shadow-[0_8px_20px_-14px_rgba(30,41,59,0.2)] backdrop-blur-sm">
                <div class="flex items-start md:items-center gap-5 flex-wrap">
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
                      <p class="font-body text-[12.5px] text-ink-3 mt-0.5">
                        学号：{{ activeSubmission.student?.user_number || activeSubmission.studentNo || '—' }}
                        <span class="text-ink-3 mx-2">·</span>
                        提交时间：{{ activeSubmission.submitted_at || activeSubmission.submitTime || '—' }}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span
                      v-if="activeSubmission.evaluation_status === 'done'"
                      class="chip-mag !bg-jade/12 !text-jade-dark !border-jade/30">✓ 已评价</span>
                    <span v-else class="chip-mag !bg-amber/15 !text-amber-dark !border-amber/30">⏳ 待评价</span>
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

                <!-- ===== Tab 标签（5 步） ===== -->
                <div class="mt-5 -mx-1 overflow-x-auto">
                  <div class="flex items-center gap-1 min-w-max p-1 rounded-xl bg-paper-2 border border-line/60">
                    <button
                      v-for="t in rightTabs"
                      :key="t.value"
                      @click="rightTabIdx = t.value"
                      class="group relative flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-sub transition-all"
                      :class="rightTabIdx === t.value
                        ? 'bg-white text-ink shadow-sm border border-line/70'
                        : 'text-ink-4 hover:text-ink-2 hover:bg-white/40'">
                      <span class="w-6 h-6 rounded-md text-[11.5px] font-black flex items-center justify-center"
                            :class="rightTabIdx === t.value
                              ? 'bg-seal/10 text-seal-dark'
                              : 'bg-ink-4/10 text-ink-3 group-hover:bg-ink-4/15'">
                        {{ t.value + 1 }}
                      </span>
                      <Icon :icon="t.icon" class="opacity-80" />
                      <span class="font-semibold whitespace-nowrap">{{ t.label }}</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- ===== 02 · 学生提交内容 ===== -->
              <div v-show="rightTabIdx===0" class="px-8 py-7 animate-fade-in border-b border-line/80">
                <div class="section-label mb-3">02 · STUDENT WORK · 学生提交</div>
                <h4 class="font-display text-xl font-bold mb-5">提交内容预览</h4>
                <pre class="font-mono text-[13.5px] bg-paper-2 rounded-2xl border border-line/70 p-5 whitespace-pre-wrap text-ink-2 leading-[1.75] max-h-[52vh] overflow-auto">{{ contentPreview }}</pre>
                <div v-if="detail?.files || activeSubmission?.files || activeSubmission?.download_url"
                     class="mt-5 flex flex-wrap gap-3">
                  <a v-for="(f,i) in (detail?.files || [])" :key="i"
                     :href="f.url || '#'" class="chip-mag !text-[13px] !py-2 !px-4">
                    <Icon icon="mdi:download-outline" class="mr-1.5" />{{ f.name }}
                  </a>
                  <a v-if="activeSubmission?.download_url && !detail?.files?.length"
                     class="chip-mag !text-[13px] !py-2 !px-4"
                     :href="API_BASE + activeSubmission.download_url" target="_blank">
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

              <!-- ===== 03 · AI 评价 + 教师评价 ===== -->
              <div v-show="rightTabIdx===1" class="px-8 py-7 animate-fade-in border-b border-line/80">
                <template v-if="compareLoaded">
                  <TripartiteCompare
                    :parties="compareData.parties"
                    :dimensionBreakdown="compareData.dimension_breakdown"
                    :summary="compareData.summary"
                    :hideConsistencyCard="true"
                  />
                </template>
                <template v-else-if="(detail?.evaluations || []).length">
                  <div class="section-label !mb-2">03 · REFERENCE · AI + 教师参考评分</div>
                  <h4 class="font-display text-xl font-bold mb-5 text-ink">已有评价记录（供企业导师参考）</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                </template>
                <div v-else class="py-12 text-center text-ink-4 font-body">
                  <Icon icon="mdi:file-clock-outline" class="text-5xl opacity-40 mb-3" />
                  AI/教师评价尚未生成，提交完成后此处将自动呈现。
                </div>
              </div>

              <!-- ===== 04 · 企业维度评分 ===== -->
              <div v-show="rightTabIdx===2" class="px-8 py-7 animate-fade-in border-b border-line/80">
                <div class="section-label !mb-3">04 · ENTERPRISE SCORE · 企业维度评分（{{ evalDimScoreSum }} / 100）</div>
                <h4 class="font-display text-xl font-bold mb-5 text-ink">按岗位要求逐项打分</h4>
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

              <!-- ===== 05 · 岗位匹配 + 面试建议 ===== -->
              <div v-show="rightTabIdx===3" class="px-8 py-7 animate-fade-in border-b border-line/80">
                <div class="section-label !mb-3">05 · JOB FIT + INTERVIEW · 岗位匹配与面试建议</div>
                <h4 class="font-display text-xl font-bold mb-5 text-ink">岗位匹配 / 适配度 / 面试建议</h4>
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
                <div class="section-label !mb-3">面试建议（三选一）</div>
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

              <!-- ===== 底部：上一步 / 下一步（每步都有） ===== -->
              <div class="px-8 py-4 border-t border-line/80 bg-paper/40 flex items-center justify-between gap-4 flex-wrap">
                <div class="font-sub text-ink-4 text-[13px] tracking-wide">
                  STEP <span class="font-black text-ink">{{ rightTabIdx + 1 }}</span> / {{ rightTabs.length }}
                  <span class="ml-2 text-ink-3">· {{ rightTabs[rightTabIdx].label }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]"
                    :disabled="rightTabIdx===0"
                    @click="prevTab">
                    <Icon icon="mdi:arrow-left-bold-outline" class="mr-1" /> 上一步
                  </button>
                  <button
                    class="btn-mag btn-mag-primary px-4 py-2.5 text-[13px]"
                    :disabled="rightTabIdx===rightTabs.length-1"
                    @click="nextTab">
                    下一步 <Icon icon="mdi:arrow-right-bold-outline" class="ml-1" />
                  </button>
                </div>
              </div>

              <!-- ===== 底部汇总保存（第 5 步出现） ===== -->
              <div v-show="rightTabIdx===4" class="px-8 py-6 bg-paper-2/40 border-t border-line/80 flex items-center justify-between gap-4 flex-wrap">
                <div>
                  <div class="section-label !mb-1">READY TO SUBMIT</div>
                  <div class="font-sub text-ink">
                    当前企业均分：<span class="font-display font-black text-2xl" :class="scoreColor(evalDimScoreSum)">{{ evalDimScoreSum }}</span>
                    <span class="text-ink-3 text-sm mx-2">·</span>
                    岗位适配度：<span class="font-display font-black text-xl" :class="scoreColor(evalJobFit)">{{ evalJobFit }}</span>
                    <span v-if="evalDirty" class="chip-mag !bg-seal/12 !text-seal-dark !border-seal/30 ml-2">有未保存修改</span>
                  </div>
                </div>
                <button
                  class="btn-mag btn-mag-primary px-6 py-3 text-[14px]"
                  :disabled="!canSaveEval"
                  @click="submitEval">
                  <Icon icon="mdi:content-save-check-outline" class="mr-1" />
                  {{ activeEvalId ? '更新企业评价' : '提交企业评价' }}
                </button>
              </div>
            </template>
          </div>

        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'
import TripartiteCompare from '../components/common/TripartiteCompare.vue'

/* ========================= Types ========================= */
type RowT = any

/* ========================= State ========================= */
const list = ref<RowT[]>([])
const listLoading = ref(false)
const listLoadError = ref('')
const listStatus = ref<string>('')
const keyword = ref('')

const activeId = ref<number | null>(null)
const activeSubmission = ref<RowT | null>(null)
const detail = ref<any>(null)
const detailLoading = ref(false)

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

// Tab 切换（5 步）+ 上一步 / 下一步
const rightTabIdx = ref(0)
const rightTabs = [
  { value: 0, label: '提交内容', icon: 'mdi:file-document-outline' },
  { value: 1, label: 'AI + 教师评分', icon: 'mdi:account-group-outline' },
  { value: 2, label: '企业维度评分', icon: 'mdi:star-four-points-outline' },
  { value: 3, label: '岗位匹配 / 面试', icon: 'mdi:briefcase-account-outline' },
  { value: 4, label: '提交汇总', icon: 'mdi:send-check-outline' },
]
function prevTab() { if (rightTabIdx.value > 0) rightTabIdx.value-- }
function nextTab() { if (rightTabIdx.value < rightTabs.length - 1) rightTabIdx.value++ }

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
  listLoadError.value = ''
  try {
    const token = localStorage.getItem('token')
    const headers: any = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const { data } = await axios.get(`${API_BASE}/api/enterprise/evaluations/submissions`, {
      headers, params: { page: 1, page_size: 50 }
    })
    list.value = (data?.list || []).map((x: any, i: number) => ({ ...x, _i: i }))
    if (list.value.length === 0) {
      listLoadError.value =
        '当前没有可评测的实训提交。如果企业尚未绑定班级，系统默认展示全部活跃班级的已提交作业；若仍然为空，请联系教师布置实训并让学生提交。'
    }
  } catch (e: any) {
    list.value = []
    const status = e?.response?.status
    const d = e?.response?.data?.detail
    const msg = d || e?.message || '接口请求失败'
    if (status === 401) {
      listLoadError.value = `登录已过期（401）：请退出后使用企业导师账号重新登录。${d ? '详情：' + d : ''}`
    } else if (status === 403) {
      listLoadError.value = `无权访问（403）：当前账号不是企业导师角色，或该企业未被授权查看此班级。${d ? '详情：' + d : ''}`
    } else if (status && status >= 500) {
      listLoadError.value = `服务异常（${status}）：请检查后端日志并联系维护人员。`
    } else {
      listLoadError.value = `提交列表加载失败：${msg}（请启动后端服务，并使用企业导师账号登录）`
    }
  } finally {
    listLoading.value = false
  }
}
async function selectSubmission(row: any) {
  activeId.value = row.submission_id || row.id
  activeSubmission.value = row
  compareLoaded.value = false
  rightTabIdx.value = 0
  await fetchDetail(activeId.value!)
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
    seedEvalFormFrom(activeSubmission.value, detail.value?.enterprise_evaluation ?? null)
  } catch (e) {
    detail.value = null
    seedEvalFormFrom(activeSubmission.value, null)
  } finally {
    detailLoading.value = false
  }
}
function seedEvalFormFrom(row: any, ee: any) {
  if (ee?.dimension_scores?.length) {
    evalDims.value = ee.dimension_scores.map((d: any) => ({
      name: d.name || '', score: Number(d.score) || 0, reason: d.reason || '',
    }))
    activeEvalId.value = ee.id ?? null
  } else {
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
    compareData.value = { parties:[], dimension_breakdown:[], summary:null }
    compareLoaded.value = true
  } finally {
    compareLoading.value = false
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
    await fetchList()
    const refreshed = list.value.find((r: any) => (r.submission_id || r.id) === activeId.value)
    if (refreshed) { activeSubmission.value = refreshed }
    evalDirty.value = false
    if (activeSubmission.value && activeSubmission.value.evaluation_status !== 'done') {
      activeSubmission.value.evaluation_status = 'done'
      activeSubmission.value.enterprise_evaluation = {
        id: resp.data?.evaluation_id, total_score: evalDimScoreSum.value
      }
    }
    alert(`✅ ${activeEvalId.value ? '已更新企业评价' : '企业评价提交成功'}（均分 ${evalDimScoreSum.value}）`)
    await loadCompare(activeId.value!)
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '提交失败'
    alert(`提交失败：${msg}\n（请确认后端服务已启动，且当前为企业导师账号）`)
  } finally {
    submitting.value = false
  }
}

watch(evalDims, () => { evalDirty.value = true }, { deep: true })
watch([evalStrength, evalImprovement, evalComment, evalJobFit, evalInterview], () => { evalDirty.value = true })

onMounted(fetchList)
</script>

<style scoped>
/* 保留原有动画 & 深度样式 */
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
