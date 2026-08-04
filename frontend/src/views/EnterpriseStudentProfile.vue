<template>
  <div class="min-h-full page-enter">
    <!-- 接口错误提示 -->
    <div v-if="loadError" class="mb-6 rounded-2xl border-2 border-seal/30 bg-seal/[0.06] px-5 py-4 flex items-start gap-3">
      <Icon icon="mdi:alert-circle-outline" class="text-seal text-xl flex-shrink-0 mt-0.5" />
      <div class="text-[13.5px] text-seal-dark leading-[1.7] flex-1">{{ loadError }}</div>
      <button @click="refreshAll" class="chip-mag !text-[12px] !py-1 !px-3 flex-shrink-0">
        <Icon icon="mdi:refresh" class="mr-1" inline width="12" /> 重试
      </button>
    </div>

    <!-- 顶部：学生信息条 -->
    <div class="mb-8">
      <div class="card-mag p-0 overflow-hidden">
        <div class="px-8 py-7 flex items-start md:items-center gap-6 flex-wrap">
          <div class="w-20 h-20 flex-shrink-0 rounded-2xl bg-gradient-to-br from-cobalt via-violet-600 to-fuchsia-500 text-white font-black font-display text-4xl flex items-center justify-center shadow-lg ring-4 ring-white">
            {{ studentInitial }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 mb-2 flex-wrap">
              <h1 class="font-display text-3xl font-black text-ink tracking-tight truncate">
                {{ studentName }}
              </h1>
              <span class="chip-mag !text-[12px]">{{ studentClass || '未分班' }}</span>
              <span v-if="studentNumber" class="text-[12px] font-mono text-ink-3">#{{ studentNumber }}</span>
            </div>
            <div class="flex items-center gap-5 text-[13.5px] text-ink-3 flex-wrap">
              <span class="flex items-center gap-1.5">
                <Icon icon="mdi:school-outline" class="text-cobalt" inline width="16" /> {{ studentMajor || '未填专业' }}
              </span>
              <span class="flex items-center gap-1.5">
                <Icon icon="mdi:email-outline" class="text-cobalt" inline width="16" /> {{ studentEmail || '无邮箱' }}
              </span>
              <span class="flex items-center gap-1.5">
                <Icon icon="mdi:id-card" class="text-cobalt" inline width="16" /> student_id: <span class="font-mono">{{ sid }}</span>
              </span>
            </div>
            <!-- 三个关键指标：匹配均分/必选漏项数/近5次均分 -->
            <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl">
              <div class="stat-card bg-gradient-card-amber">
                <div class="text-[11px] uppercase tracking-[0.2em] opacity-80 mb-1">TOP1 岗位匹配分</div>
                <div class="font-display text-4xl font-black leading-none">{{ topJob.match ? Math.round(topJob.match) : '-' }}</div>
                <div class="text-[12.5px] opacity-90 mt-1">{{ topJob.title || '暂无岗位数据' }}</div>
              </div>
              <div class="stat-card bg-gradient-card-emerald">
                <div class="text-[11px] uppercase tracking-[0.2em] opacity-80 mb-1">加权历史均分</div>
                <div class="font-display text-4xl font-black leading-none">{{ avgDimScore }}</div>
                <div class="text-[12.5px] opacity-90 mt-1">最近 {{ lastEvaluations.length }} 次评价</div>
              </div>
              <div class="stat-card bg-gradient-card-blue">
                <div class="text-[11px] uppercase tracking-[0.2em] opacity-80 mb-1">TOP5 可投岗位</div>
                <div class="font-display text-4xl font-black leading-none">{{ topJobs.length }}</div>
                <div class="text-[12.5px] opacity-90 mt-1">匹配分 ≥ 75</div>
              </div>
            </div>
          </div>
          <div class="flex flex-col gap-2">
            <button @click="refreshAll" :disabled="loading" class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">
              <Icon icon="mdi:refresh" class="mr-1" :class="{'animate-spin': loading}" /> 刷新画像
            </button>
            <button @click="invite" class="btn-mag btn-mag-primary px-4 py-2.5 text-[13px]">
              <Icon icon="mdi:message-outline" class="mr-1" /> 发起面试邀约
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 统一大卡片：三视图 Tab 切换（能力对标 / TOP 5 匹配岗位 / 成长记录） -->
    <section class="sp-unified">
      <!-- 头部：三 Tab 切换 -->
      <div class="spu-head">
        <div class="spu-head-l">
          <h2 class="spu-title"><Icon icon="mdi:hexagon-multiple-outline" class="spu-ic spu-ic-violet" /> 学生画像分析</h2>
          <p class="spu-sub text-[12.5px] text-ink-4 mt-1.5">
            能力对标 · TOP 5 匹配岗位 · 成长曲线 · 企业评价时间线
            <span class="mx-2 opacity-40">|</span>
            共 <b class="text-ink">{{ enterpriseLogs.length }}</b> 条企业评价
          </p>
        </div>
        <div class="spu-tabs" role="tablist">
          <button @click="spuTab = 'ability'" :class="['spu-tab', {active: spuTab==='ability'}]" role="tab">
            <Icon icon="mdi:hexagon-outline" class="mr-1" /> 能力对标
          </button>
          <button @click="spuTab = 'jobs'" :class="['spu-tab', {active: spuTab==='jobs'}]" role="tab">
            <Icon icon="mdi:briefcase-search-outline" class="mr-1" /> TOP 5 匹配岗位
          </button>
          <button @click="spuTab = 'growth'" :class="['spu-tab', {active: spuTab==='growth'}]" role="tab">
            <Icon icon="mdi:chart-bell-curve" class="mr-1" /> 成长记录
          </button>
          <button @click="spuTab = 'interview'; loadInvitations()" :class="['spu-tab', {active: spuTab==='interview'}]" role="tab">
            <Icon icon="mdi:calendar-clock-outline" class="mr-1" /> 面试邀约
          </button>
        </div>
      </div>

      <!-- 虚线分隔 -->
      <div class="spu-divider"></div>

      <!-- TAB 1：能力对标（雷达 + 图例） -->
      <div v-show="spuTab==='ability'" class="spu-section">
        <div class="spu-subhead">
          <h3 class="spu-subtitle"><Icon icon="mdi:hexagon-outline" class="sh-ic sh-ic-cobalt" /> 该生 vs 全班均值</h3>
          <div class="flex items-center gap-4 text-[12px] font-sub font-semibold">
            <span class="flex items-center gap-2"><span class="inline-block w-4 h-[2.5px] bg-seal rounded-full"></span><span class="text-ink-2">{{ studentName }}（该生）</span></span>
            <span class="flex items-center gap-2"><span class="inline-block w-4 h-[2.5px] bg-cobalt rounded-full"></span><span class="text-ink-2">全班均值</span></span>
          </div>
        </div>
        <div class="spu-chart-wrap">
          <JobMatchRadar :dimensions="q1RadarDims" />
        </div>
      </div>

      <!-- TAB 2：TOP 5 匹配岗位 · 门槛 vs 匹配分（柱状） -->
      <div v-show="spuTab==='jobs'" class="spu-section">
        <div class="spu-subhead">
          <h3 class="spu-subtitle"><Icon icon="mdi:briefcase-search-outline" class="sh-ic sh-ic-amber" /> TOP 5 匹配岗位 · 门槛 vs 匹配分</h3>
          <div class="text-[12.5px] text-ink-3">
            共 {{ topJobs.length }} 个可投岗位，匹配分 ≥ 75
          </div>
        </div>
        <div class="spu-chart-wrap">
          <v-chart :option="q2BarOption" autoresize style="width:100%;height:460px" />
        </div>
      </div>

      <!-- TAB 3：成长记录（成长曲线 + 企业评价时间线，上下排布） -->
      <div v-show="spuTab==='growth'" class="spu-section spu-growth">
        <!-- 上：成长曲线 -->
        <div>
          <div class="spu-subhead">
            <h3 class="spu-subtitle"><Icon icon="mdi:chart-line-variant" class="sh-ic sh-ic-emerald" /> 历次评价总分趋势（AI / 教师）</h3>
            <div v-if="lastEvaluations.length" class="text-[12px] text-ink-3">
              共 <b class="font-display text-ink text-[16px] ml-1">{{ lastEvaluations.length }}</b> 次评价
            </div>
          </div>
          <div class="spu-chart-wrap">
            <v-chart v-if="lastEvaluations.length" :option="q3LineOption" autoresize style="width:100%;height:420px" />
            <div v-else class="h-[420px] flex flex-col items-center justify-center text-center text-ink-3 text-[13px] p-8">
              <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mb-4">
                <Icon icon="mdi:chart-line-variant" class="text-4xl text-ink-4" />
              </div>
              <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">暂无评价记录</p>
              <p>该生尚未产生 AI 或教师评价，完成一次实训后，成长曲线将在此展示。</p>
            </div>
          </div>
        </div>

        <!-- 虚线分隔上下块 -->
        <div class="spu-divider my-8"></div>

        <!-- 下：企业评价时间线 -->
        <div>
          <div class="spu-subhead">
            <h3 class="spu-subtitle"><Icon icon="mdi:clipboard-text-clock-outline" class="sh-ic sh-ic-seal" /> 历史企业评价时间线</h3>
          </div>
          <div class="spu-timeline-wrap py-2">
            <div v-if="!enterpriseLogs.length" class="py-16 text-center text-ink-3 text-[13px] p-8">
              <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
                <Icon icon="mdi:clipboard-text-clock-outline" class="text-4xl text-ink-4" />
              </div>
              <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">暂无企业评价</p>
              <p>当企业导师为该生提交评价后，所有记录会在此留痕（含企业导师、岗位、分数、评语）。</p>
            </div>
            <div v-else class="relative pl-2">
              <div class="absolute left-[22px] top-2 bottom-2 w-[2px] bg-line"></div>
              <div v-for="(log, idx) in enterpriseLogs" :key="log.id || idx" class="relative pl-14 pb-5 last:pb-0">
                <div class="absolute left-0 w-[44px] h-[44px] rounded-2xl flex items-center justify-center font-display font-black text-white shadow-md ring-4 ring-paper"
                     :class="[
                       idx === 0 ? 'bg-gradient-to-br from-seal to-orange-500' : (log.total_score >= 80 ? 'bg-gradient-to-br from-jade to-emerald-500' : 'bg-gradient-to-br from-cobalt to-violet-600')
                     ]">
                  {{ Math.round(log.total_score || 0) }}
                </div>
                <div class="rounded-2xl border border-line/70 bg-paper p-4 hover:border-seal/30 hover:bg-seal/[0.03] transition-all">
                  <div class="flex items-center justify-between gap-3 mb-2 flex-wrap">
                    <div class="flex items-center gap-2">
                      <span class="font-display font-bold text-ink text-[15.5px]">{{ log.job_title || '企业综合评价' }}</span>
                      <span v-if="log.mentor_name" class="chip-mag !text-[11.5px] !py-0.5 !px-2">
                        <Icon icon="mdi:account-tie-outline" class="mr-1" inline width="12" /> {{ log.mentor_name }}
                      </span>
                    </div>
                    <span class="text-[11.5px] font-mono text-ink-3">{{ fmtDate(log.created_at || log.time) }}</span>
                  </div>
                  <div v-if="log.dimension_scores?.length" class="flex flex-wrap gap-1.5 mb-3">
                    <span v-for="d in (log.dimension_scores.slice(0,6))" :key="d.name" class="text-[11.5px] px-2 py-0.5 rounded-lg bg-line/50 text-ink-2 font-mono">
                      {{ d.name }} <b class="font-bold ml-0.5" :class="Number(d.score)>=75?'text-jade-dark':'text-seal-dark'">{{ d.score }}</b>
                    </span>
                    <span v-if="(log.dimension_scores||[]).length > 6" class="text-[11px] px-2 py-0.5 rounded-lg bg-line/30 text-ink-3">+{{ (log.dimension_scores||[]).length - 6 }} …</span>
                  </div>
                  <div v-if="log.comment || log.interview_note" class="text-[13px] text-ink-2 leading-relaxed">
                    <template v-if="log.comment">💬 {{ log.comment }}</template>
                    <template v-if="log.interview_note">
                      <div class="mt-2 pt-2 border-t border-line/60 text-ink-3">
                        <Icon icon="mdi:comment-quote-outline" class="mr-1 align-text-bottom" inline width="14" />面试/备注：{{ log.interview_note }}
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 4：面试邀约记录（方案 B） -->
      <div v-show="spuTab==='interview'" class="spu-section">
        <div class="spu-subhead">
          <h3 class="spu-subtitle"><Icon icon="mdi:calendar-clock-outline" class="sh-ic sh-ic-seal" /> 面试邀约记录</h3>
          <div class="text-[12px] text-ink-3">
            共 <b class="font-display text-ink text-[16px] ml-1">{{ invitations.length }}</b> 条邀约
          </div>
        </div>
        <div class="spu-timeline-wrap py-2">
          <div v-if="invitationsLoading" class="py-16 text-center text-ink-3 text-[13px]">
            <Icon icon="mdi:loading" class="animate-spin text-3xl mb-3 text-seal" />
            <p>加载邀约记录中…</p>
          </div>
          <div v-else-if="!invitations.length" class="py-16 text-center text-ink-3 text-[13px] p-8">
            <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
              <Icon icon="mdi:calendar-blank-outline" class="text-4xl text-ink-4" />
            </div>
            <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">暂无邀约记录</p>
            <p>点击右上角「发起面试邀约」可向该学生发送面试邀请。</p>
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="inv in invitations"
              :key="inv.id"
              class="rounded-2xl border border-line/70 bg-paper p-5 hover:border-seal/30 hover:bg-seal/[0.03] transition-all"
            >
              <div class="flex items-start justify-between gap-4 flex-wrap">
                <div class="flex items-start gap-3 flex-1 min-w-0">
                  <div class="w-[44px] h-[44px] rounded-2xl flex items-center justify-center font-display font-black text-white shadow-md ring-4 ring-paper bg-gradient-to-br from-cobalt via-violet-600 to-fuchsia-500 flex-shrink-0">
                    <Icon icon="mdi:calendar-month-outline" class="text-xl" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2 flex-wrap mb-1.5">
                      <span class="font-display font-bold text-ink text-[16px]">{{ inv.job?.title || '未关联岗位' }}</span>
                      <span v-if="inv.job?.level" class="chip-mag !text-[11.5px] !py-0.5 !px-2">{{ inv.job.level }}</span>
                      <span :class="['chip-mag !text-[11.5px] !py-0.5 !px-2 font-semibold', statusChipClass(inv.status)]">{{ statusLabel(inv.status) }}</span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-y-1.5 gap-x-5 text-[12.5px] text-ink-3 mt-2">
                      <span class="flex items-center gap-1.5">
                        <Icon icon="mdi:clock-outline" class="text-cobalt" inline width="14" />
                        <span class="font-semibold text-ink-2 mr-1">面试时间：</span>
                        {{ fmtDate(inv.interview_time) }}
                      </span>
                      <span class="flex items-center gap-1.5">
                        <Icon :icon="inv.interview_type==='onsite'?'mdi:map-marker-outline':'mdi:video-outline'" class="text-seal" inline width="14" />
                        <span class="font-semibold text-ink-2 mr-1">{{ inv.interview_type === 'onsite' ? '面试地点' : '会议链接' }}：</span>
                        <span class="truncate" :title="inv.location">{{ inv.location }}</span>
                      </span>
                      <span class="flex items-center gap-1.5">
                        <Icon icon="mdi:account-tie-outline" class="text-cobalt" inline width="14" />
                        <span class="font-semibold text-ink-2 mr-1">发起人：</span>
                        {{ inv.mentor?.real_name || '企业导师' }}
                        <template v-if="inv.mentor?.title"> · {{ inv.mentor.title }}</template>
                      </span>
                      <span class="flex items-center gap-1.5">
                        <Icon icon="mdi:history" class="text-ink-3" inline width="14" />
                        <span class="font-semibold text-ink-2 mr-1">发起时间：</span>
                        {{ fmtDate(inv.created_at) }}
                      </span>
                    </div>
                    <template v-if="inv.message || inv.student_reply">
                      <div class="mt-3 space-y-2">
                        <div v-if="inv.message" class="rounded-xl bg-line/40 px-3.5 py-2.5 text-[12.5px] text-ink-2 leading-relaxed">
                          <Icon icon="mdi:message-text-outline" class="mr-1 align-text-bottom text-cobalt" inline width="14" />
                          <b class="mr-1">邀约留言：</b>{{ inv.message }}
                        </div>
                        <div v-if="inv.student_reply" class="rounded-xl bg-seal/[0.08] px-3.5 py-2.5 text-[12.5px] text-seal-dark leading-relaxed">
                          <Icon icon="mdi:message-reply-outline" class="mr-1 align-text-bottom text-seal" inline width="14" />
                          <b class="mr-1">学生回复：</b>{{ inv.student_reply }}
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
                <div v-if="inv.status === 'pending'" class="flex-shrink-0">
                  <button @click="cancelInvitation(inv.id)" class="btn-mag btn-mag-ghost !text-[12px] !py-2 !px-3">
                    <Icon icon="mdi:cancel" class="mr-1" /> 撤回邀约
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═════════ 弹窗：发起面试邀约 ═════════ -->
    <transition name="fade-in-down">
      <div v-if="inviteVisible" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink/50 backdrop-blur-sm" @click.self="closeInviteDialog"></div>
        <div class="relative w-full max-w-xl card-mag !p-0 !rounded-3xl shadow-2xl overflow-hidden z-10">
          <!-- 顶条 -->
          <div class="px-7 py-5 bg-gradient-to-r from-seal/[0.08] via-orange-500/[0.06] to-cobalt/[0.06] border-b border-line/70">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-2xl bg-gradient-seal text-white shadow-md grid place-items-center">
                  <Icon icon="mdi:message-badge-outline" class="text-2xl" />
                </div>
                <div>
                  <h3 class="font-display font-black text-ink text-xl leading-tight">发起面试邀约</h3>
                  <p class="text-[12.5px] text-ink-3 mt-1">
                    向「{{ studentName }}」（学号 {{ studentNumber || '-' }}）发出面试邀请
                  </p>
                </div>
              </div>
              <button @click="closeInviteDialog" class="w-9 h-9 rounded-xl hover:bg-ink/5 flex items-center justify-center text-ink-3 hover:text-ink transition-colors">
                <Icon icon="mdi:close" class="text-xl" />
              </button>
            </div>
          </div>
          <!-- 表单区 -->
          <div class="px-7 py-5 space-y-4 max-h-[70vh] overflow-y-auto">
            <!-- 关联岗位（必选） -->
            <div>
              <label class="block text-[13px] font-sub font-semibold text-ink mb-1.5">
                关联岗位 <span class="text-seal">*</span>
              </label>
              <select
                v-model="inviteForm.job_id"
                class="w-full h-11 px-3.5 rounded-xl border border-line bg-white text-[13.5px] text-ink focus:outline-none focus:border-seal focus:ring-4 focus:ring-seal/10 transition-all"
                :class="{'border-seal': inviteFormErrors.job_id}"
              >
                <option :value="0">-- 请选择岗位 --</option>
                <option v-for="j in jobDropdownList" :key="j.id" :value="j.id">{{ j.title }}（{{ j.level }}）{{ j.city? ' · ' + j.city : '' }}</option>
              </select>
              <p v-if="inviteFormErrors.job_id" class="mt-1 text-[12px] text-seal-dark">{{ inviteFormErrors.job_id }}</p>
            </div>
            <!-- 面试时间（必选） + 形式 一行 -->
            <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
              <div class="md:col-span-3">
                <label class="block text-[13px] font-sub font-semibold text-ink mb-1.5">
                  面试时间 <span class="text-seal">*</span>
                </label>
                <input
                  type="datetime-local"
                  v-model="inviteForm.interview_time"
                  class="w-full h-11 px-3.5 rounded-xl border border-line bg-white text-[13.5px] text-ink focus:outline-none focus:border-seal focus:ring-4 focus:ring-seal/10 transition-all"
                  :class="{'border-seal': inviteFormErrors.interview_time}"
                />
                <p v-if="inviteFormErrors.interview_time" class="mt-1 text-[12px] text-seal-dark">{{ inviteFormErrors.interview_time }}</p>
              </div>
              <div class="md:col-span-2">
                <label class="block text-[13px] font-sub font-semibold text-ink mb-1.5">面试形式</label>
                <div class="h-11 flex items-stretch gap-2 rounded-xl p-1 border border-line bg-line/30">
                  <button
                    @click="inviteForm.interview_type = 'online'"
                    :class="['flex-1 rounded-lg text-[12.5px] font-semibold transition-all', inviteForm.interview_type==='online' ? 'bg-white shadow-sm text-cobalt ring-1 ring-cobalt/30' : 'text-ink-3 hover:text-ink']"
                    type="button"
                  >
                    <Icon icon="mdi:video-outline" class="mr-1" inline width="14" /> 线上
                  </button>
                  <button
                    @click="inviteForm.interview_type = 'onsite'"
                    :class="['flex-1 rounded-lg text-[12.5px] font-semibold transition-all', inviteForm.interview_type==='onsite' ? 'bg-white shadow-sm text-seal ring-1 ring-seal/30' : 'text-ink-3 hover:text-ink']"
                    type="button"
                  >
                    <Icon icon="mdi:map-marker-outline" class="mr-1" inline width="14" /> 线下
                  </button>
                </div>
              </div>
            </div>
            <!-- 会议链接 / 地点（必选） -->
            <div>
              <label class="block text-[13px] font-sub font-semibold text-ink mb-1.5">
                {{ inviteForm.interview_type === 'onsite' ? '面试地点' : '会议链接' }} <span class="text-seal">*</span>
              </label>
              <input
                v-model="inviteForm.location"
                :placeholder="inviteForm.interview_type === 'onsite' ? '如：北京市朝阳区建国路88号A座20层 会议室B' : '如：腾讯会议 https://meeting.tencent.com/dm/xxx 或 Zoom 链接'"
                class="w-full h-11 px-3.5 rounded-xl border border-line bg-white text-[13.5px] text-ink focus:outline-none focus:border-seal focus:ring-4 focus:ring-seal/10 transition-all font-mono"
                :class="{'border-seal': inviteFormErrors.location}"
              />
              <p v-if="inviteFormErrors.location" class="mt-1 text-[12px] text-seal-dark">{{ inviteFormErrors.location }}</p>
            </div>
            <!-- 邀约留言（可选） -->
            <div>
              <label class="block text-[13px] font-sub font-semibold text-ink mb-1.5">
                邀约留言 <span class="text-ink-3 text-[11.5px] font-normal ml-1">（可选）</span>
              </label>
              <textarea
                v-model="inviteForm.message"
                rows="4"
                placeholder="同学你好！通过对你的实训表现与岗位匹配度评估，我们很认可你的能力，诚邀你参加本次面试…"
                class="w-full px-3.5 py-2.5 rounded-xl border border-line bg-white text-[13.5px] text-ink leading-relaxed focus:outline-none focus:border-seal focus:ring-4 focus:ring-seal/10 transition-all resize-none"
              ></textarea>
            </div>
          </div>
          <!-- 底部按钮 -->
          <div class="px-7 py-4 bg-line/30 border-t border-line/70 flex items-center justify-end gap-3">
            <button @click="closeInviteDialog" :disabled="inviteSubmitting" class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">取消</button>
            <button @click="submitInvite" :disabled="inviteSubmitting" class="btn-mag btn-mag-primary px-5 py-2.5 text-[13px] min-w-[120px]">
              <Icon v-if="inviteSubmitting" icon="mdi:loading" class="mr-1 animate-spin" />
              <Icon v-else icon="mdi:send-outline" class="mr-1" />
              {{ inviteSubmitting ? '发送中…' : '发送邀约' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'
import JobMatchRadar from '../components/common/JobMatchRadar.vue'

const route = useRoute()
const sid = computed(() => Number(route.params.studentId) || Number(route.query.student_id) || 0)

const loading = ref(false)
const loadError = ref('')
const student = ref<any>(null)
const dimAvg = ref<Record<string, number>>({})
const classDimAvg = ref<Record<string, number>>({})
const lastEvaluations = ref<any[]>([])
const topJobs = ref<any[]>([])
const enterpriseLogs = ref<any[]>([])
const spuTab = ref<'ability' | 'jobs' | 'growth' | 'interview'>('ability')

/* ============= 面试邀约相关 ============= */
// 弹窗开关 + 表单
const inviteVisible = ref(false)
const inviteSubmitting = ref(false)
const inviteForm = ref({
  job_id: 0 as number,
  interview_time: '',
  interview_type: 'online' as 'online' | 'onsite',
  location: '',
  message: '',
})
const inviteFormErrors = ref<Record<string, string>>({})
// 岗位下拉列表（企业下所有岗位，简单列表即可）
const jobDropdownList = ref<any[]>([])
const jobsLoaded = ref(false)
// 邀约记录列表
const invitations = ref<any[]>([])
const invitationsLoading = ref(false)

function authHeaders(): any {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function statusLabel(s: string): string {
  switch (s) {
    case 'pending': return '待回复'
    case 'accepted': return '已接受'
    case 'declined': return '已拒绝'
    case 'cancelled': return '已撤回'
    case 'completed': return '已完成'
    default: return s
  }
}
function statusChipClass(s: string): string {
  switch (s) {
    case 'pending':   return '!bg-amber-500/10 !text-amber-700 !border-amber-300/60'
    case 'accepted':  return '!bg-emerald-500/10 !text-emerald-700 !border-emerald-300/60'
    case 'declined':  return '!bg-rose-500/10 !text-rose-700 !border-rose-300/60'
    case 'cancelled': return '!bg-slate-500/10 !text-slate-600 !border-slate-300/60'
    case 'completed': return '!bg-sky-500/10 !text-sky-700 !border-sky-300/60'
    default:          return '!bg-slate-500/10 !text-slate-600'
  }
}

async function loadJobDropdown(force = false) {
  if (jobsLoaded.value && !force) return
  try {
    const res = await axios.get(`${API_BASE}/api/enterprise/jobs/all`, { headers: authHeaders() })
    if (res.data?.success) {
      jobDropdownList.value = res.data.list || []
      // 默认选第一个岗位（TOP1 匹配的岗位优先）
      if (!inviteForm.value.job_id && topJobs.value?.[0]?.id) {
        const matchedTop = jobDropdownList.value.find(j => j.id === topJobs.value[0].id)
        if (matchedTop) inviteForm.value.job_id = matchedTop.id
      }
      if (!inviteForm.value.job_id && jobDropdownList.value.length) {
        inviteForm.value.job_id = jobDropdownList.value[0].id
      }
    }
  } catch { /* 失败不阻塞主流程 */ }
  jobsLoaded.value = true
}

function openInviteDialog() {
  // 重置表单（默认值）
  inviteFormErrors.value = {}
  const now = new Date()
  now.setMinutes(0, 0, 0)
  now.setHours(now.getHours() + 25)  // 默认明天这个小时
  const pad = (n: number) => String(n).padStart(2, '0')
  inviteForm.value = {
    job_id: jobDropdownList.value?.[0]?.id || (topJobs.value?.[0]?.id || 0),
    interview_time: `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`,
    interview_type: 'online',
    location: '',
    message: `同学你好！通过对你的实训表现与岗位匹配度评估，我们很认可你的能力，诚邀你参加本次面试，请及时回复。`,
  }
  loadJobDropdown().then(() => {
    if (!inviteForm.value.job_id && jobDropdownList.value.length) {
      inviteForm.value.job_id = jobDropdownList.value[0].id
    }
  })
  inviteVisible.value = true
}
function closeInviteDialog() {
  if (inviteSubmitting.value) return
  inviteVisible.value = false
}

function validateInviteForm(): boolean {
  const errs: Record<string, string> = {}
  if (!inviteForm.value.job_id) errs.job_id = '请选择关联岗位'
  if (!inviteForm.value.interview_time) errs.interview_time = '请选择面试时间'
  if (!inviteForm.value.location.trim()) errs.location = inviteForm.value.interview_type === 'onsite' ? '请填写面试地点' : '请填写会议链接'
  inviteFormErrors.value = errs
  return Object.keys(errs).length === 0
}

async function submitInvite() {
  if (!validateInviteForm()) return
  inviteSubmitting.value = true
  try {
    // interview_time 用 datetime-local 字符串，直接塞给后端（FastAPI datetime 可解析 ISO 格式）
    const payload: any = {
      student_id: Number(sid.value),          // 对外契约：login_accounts.id
      job_id: Number(inviteForm.value.job_id),
      interview_time: new Date(inviteForm.value.interview_time.replace('T', ' ')).toISOString().replace('Z', ''),
      interview_type: inviteForm.value.interview_type,
      location: inviteForm.value.location.trim(),
      message: inviteForm.value.message || '',
    }
    const res = await axios.post(`${API_BASE}/api/enterprise/interview-invitations`, payload, { headers: authHeaders() })
    if (res.data?.success) {
      // 成功：ElMessage 提示 + 自动切到 Tab4 + 刷新列表
      ;(await import('element-plus')).ElMessage.success(`已向「${studentName.value}」发送面试邀约`)
      inviteVisible.value = false
      spuTab.value = 'interview'
      loadInvitations(true)
    } else {
      throw new Error(res.data?.detail || res.data?.message || '发送失败')
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '发送邀约失败，请稍后重试'
    ;(await import('element-plus')).ElMessage.error(msg)
  } finally {
    inviteSubmitting.value = false
  }
}

async function loadInvitations(force = false) {
  if (!sid.value) return
  invitationsLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/enterprise/students/${sid.value}/interview-invitations`, { headers: authHeaders() })
    if (res.data?.success) {
      invitations.value = res.data.list || []
    }
  } catch (e) {
    console.error('加载邀约记录失败', e)
    invitations.value = []
  } finally {
    invitationsLoading.value = false
  }
}

async function cancelInvitation(id: number) {
  const ElMessageBox = (await import('element-plus')).ElMessageBox
  try {
    await ElMessageBox.confirm('确认撤回该面试邀约？学生将无法再看到此邀约。', '撤回邀约', {
      confirmButtonText: '确认撤回',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }
  try {
    const res = await axios.patch(`${API_BASE}/api/enterprise/interview-invitations/${id}/cancel`, null, { headers: authHeaders() })
    if (res.data?.success) {
      ;(await import('element-plus')).ElMessage.success('邀约已撤回')
      loadInvitations(true)
    } else {
      throw new Error(res.data?.detail || '撤回失败')
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '撤回邀约失败'
    ;(await import('element-plus')).ElMessage.error(msg)
  }
}

// 替换原 invite()（alert → 打开弹窗）
function invite() {
  openInviteDialog()
}

/* ============= 派生展示 ============= */
const studentName = computed(() => student.value?.real_name || student.value?.name || (sid.value ? `学生 #${sid.value}` : '学生'))
const studentInitial = computed(() => studentName.value.slice(0, 1))
const studentNumber = computed(() => student.value?.user_number || student.value?.username || '')
const studentClass = computed(() => student.value?.class_name || '')
const studentMajor = computed(() => student.value?.major || '')
const studentEmail = computed(() => student.value?.email || '')

const topJob = computed(() => topJobs.value[0] || { match: 0, title: '暂无' })

const avgDimScore = computed(() => {
  const vals = Object.values(dimAvg.value)
  if (!vals.length) return 0
  return Math.round(vals.reduce((s, v) => s + v, 0) / vals.length)
})

/* Q1 能力雷达 dims */
const q1RadarDims = computed(() => {
  const names = Array.from(new Set([
    ...Object.keys(dimAvg.value || {}),
    ...Object.keys(classDimAvg.value || {})
  ]))
  if (!names.length) {
    return [
      { name: '代码质量', threshold: 70, student_score: 0 },
      { name: '功能完整性', threshold: 70, student_score: 0 },
      { name: '界面设计', threshold: 65, student_score: 0 },
      { name: '文档规范性', threshold: 65, student_score: 0 },
      { name: '异常处理', threshold: 65, student_score: 0 }
    ]
  }
  return names.map(n => ({
    name: n,
    threshold: Math.round(classDimAvg.value[n] || 0),
    student_score: Math.round(dimAvg.value[n] || 0)
  }))
})

/* Q2 TOP5 岗位对比柱状 */
const q2BarOption = computed(() => {
  const rows = topJobs.value.slice(0, 5)
  if (!rows.length) {
    return {
      backgroundColor: 'transparent',
      tooltip: {},
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: { type: 'category', data: ['暂无岗位数据'], axisLabel: { color: '#64748B' } },
      yAxis: { type: 'value', max: 100 },
      series: []
    }
  }
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#111827', borderColor: 'transparent',
      textStyle: { color: '#F9FAFB', fontSize: 12 }
    },
    legend: {
      top: 0, right: 0,
      icon: 'roundRect',
      textStyle: { color: '#475569', fontSize: 12, fontWeight: 600 }
    },
    grid: { left: 40, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: rows.map(r => r.title || `岗位#${r.id}`),
      axisLabel: {
        color: '#475569', fontSize: 11.5, fontWeight: 600,
        interval: 0, rotate: 15,
        formatter: (v: string) => v.length > 10 ? v.slice(0, 9) + '…' : v
      },
      axisLine: { lineStyle: { color: '#CBD5E1' } }
    },
    yAxis: {
      type: 'value', min: 0, max: 100,
      axisLabel: { color: '#64748B', fontSize: 12 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' } }
    },
    series: [
      {
        name: '岗位门槛均值',
        type: 'bar',
        barGap: '25%',
        barWidth: '28%',
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: '#93C5FD' }, { offset: 1, color: '#1E40AF' }] }
        },
        label: { show: true, position: 'top', color: '#1E3A8A', fontSize: 11, fontWeight: 800,
          fontFamily: "'JetBrains Mono', ui-monospace, monospace" },
        data: rows.map(r => Math.round(r.job_threshold_avg || 0))
      },
      {
        name: '匹配分',
        type: 'bar',
        barWidth: '28%',
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: '#FFB65B' }, { offset: 1, color: '#FF5A1F' }] }
        },
        label: { show: true, position: 'top', color: '#9A3412', fontSize: 11, fontWeight: 800,
          fontFamily: "'JetBrains Mono', ui-monospace, monospace" },
        data: rows.map(r => Math.round(r.match || r.match_score || 0))
      }
    ]
  }
})

/* Q3 成长曲线 */
const q3LineOption = computed(() => {
  const rows = lastEvaluations.value.slice().reverse()
  const xs = rows.map((_, i) => `#${i + 1}`)
  const aiLine = rows.map(r => Number(r.evaluator_type) ? null : (r.evaluator_type === 'ai' ? (Number(r.total_score) || null) : null))
  const teacherLine = rows.map(r => r.evaluator_type === 'teacher' ? (Number(r.total_score) || null) : null)
  // 如果 aiLine/teacherLine 全空，就用 combined line = r.total_score
  const combined = rows.map(r => Number(r.total_score) || 0)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#111827', borderColor: 'transparent',
      textStyle: { color: '#F9FAFB', fontSize: 12 }
    },
    legend: {
      top: 0, right: 0, icon: 'roundRect',
      textStyle: { color: '#475569', fontSize: 12, fontWeight: 600 }
    },
    grid: { left: 40, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: xs,
      axisLabel: { color: '#475569', fontSize: 12, fontWeight: 600 },
      axisLine: { lineStyle: { color: '#CBD5E1' } }
    },
    yAxis: {
      type: 'value', min: 0, max: 100,
      axisLabel: { color: '#64748B', fontSize: 12 },
      splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' } }
    },
    series: [
      {
        name: '综合分',
        type: 'line', smooth: true, symbol: 'circle', symbolSize: 9,
        lineStyle: { width: 3.5, color: '#FF5A1F' },
        itemStyle: { color: '#FF5A1F', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(255,90,31,0.28)' }, { offset: 1, color: 'rgba(255,90,31,0.02)' }]
          }
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#11A367', width: 2 },
          label: { formatter: '均值{c}', color: '#065F46', fontWeight: 700, fontSize: 11.5 },
          data: [{ type: 'average', name: 'Avg' }]
        },
        data: combined
      }
    ]
  }
})

/* ============= Helpers ============= */
function fmtDate(v: any) {
  if (!v) return '—'
  const d = new Date(v)
  if (isNaN(d.getTime())) return String(v).slice(0, 10)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

/* ============= 加载 ============= */
async function loadStudentAll(force = false) {
  if (!sid.value) return
  loading.value = true
  loadError.value = ''
  const token = localStorage.getItem('token') || ''
  const headers: any = {}
  if (token) headers.Authorization = `Bearer ${token}`

  // 1) 基础信息 + 维度均分：从 /api/job-match/student/{id} 拿（该接口返回 dimension_avg + top岗位 list）
  let topRows: any[] = []
  let errA: any = null
  try {
    const { data } = await axios.get(`${API_BASE}/api/job-match/student/${sid.value}`, {
      headers, params: { top_n: 20, last_n: 5, decay: 0.8 }
    })
    const payload: any = data
    student.value = payload.student || student.value || {}
    dimAvg.value = (payload.student?.dimension_avg as Record<string, number>) || {}
    topRows = (payload.list || []).map((r: any) => {
      // 算门槛均值用于柱状
      const reqs: any[] = r.job?.skill_requirements || []
      let tsum = 0
      reqs.forEach((rq: any) => { tsum += Number(rq.threshold || 60) })
      const avg = reqs.length ? tsum / reqs.length : 60
      return {
        ...r,
        id: r.job?.id || r.id,
        title: r.job?.title || r.title || '岗位',
        match: r.match_score || r.match,
        job_threshold_avg: Math.round(avg)
      }
    })
    topJobs.value = topRows
  } catch (e: any) {
    errA = e
    dimAvg.value = {}
    topJobs.value = []
  }

  // 2) + 3) 拉 /api/enterprise/students/{id}：拿全班维度均分 + 评价列表 + 企业评价时间线
  try {
    const res2 = await axios.get(`${API_BASE}/api/enterprise/students/${sid.value}`, { headers })
    const p2: any = res2.data?.data || res2.data || {}
    if (p2.basic_info) student.value = { ...student.value, ...p2.basic_info }
    // 全班维度均分
    if (p2.class_dimension_avg && Object.keys(p2.class_dimension_avg).length) {
      classDimAvg.value = p2.class_dimension_avg
    }
    if (p2.evaluations) {
      lastEvaluations.value = (p2.evaluations || []).map((ev: any, i: number) => ({
        evaluator_type: ev.evaluator_type || ev.type || (i % 2 === 0 ? 'ai' : 'teacher'),
        total_score: ev.total_score,
        created_at: ev.created_at,
        dimension_scores: ev.dimension_scores || []
      }))
    }
    if (p2.enterprise_evaluations) {
      enterpriseLogs.value = (p2.enterprise_evaluations || []).map((ev: any) => ({
        id: ev.id,
        total_score: ev.total_score,
        mentor_name: ev.mentor_name || ev.evaluator || ev.mentor?.real_name,
        job_title: ev.job_title || ev.position || ev.matched_job?.title,
        dimension_scores: ev.dimension_scores || [],
        comment: ev.comment,
        interview_note: ev.interview_note || ev.note || ev.strength_points,
        created_at: ev.created_at || ev.time
      }))
    }
  } catch (e: any) {
    // 保留已经拿到的数据
  }

  // 拼接错误提示：A/B 都失败才显示
  if (errA) {
    const msg = errA?.response?.data?.detail || errA?.message || '接口请求失败'
    loadError.value = `学生画像加载失败：${msg}（请确认后端服务已启动，当前企业账号已绑定班级/发布岗位）`
  }

  loading.value = false
}

async function refreshAll() {
  await loadStudentAll(true)
}

/* init */
onMounted(() => loadStudentAll())
watch(sid, () => loadStudentAll())
</script>

<style scoped>
.card-mag :deep(.btn-mag-secondary) { font-family: inherit; }

/* ========= 学生画像页 · 统一大卡片 ======== */
.sp-unified {
  background: var(--paper, #F4F1EA);
  border: 1px solid var(--line, #DED6C7);
  border-radius: 16px;
  padding: 22px 26px 26px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}

/* 头部 */
.spu-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}
.spu-title {
  font-family: "Noto Serif SC", "Georgia", "SimSun", serif;
  font-weight: 900;
  font-size: 26px;
  letter-spacing: 0.01em;
  color: var(--ink, #2C2418);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.spu-ic { width: 26px; height: 26px; }
.spu-ic-violet { color: #7C3AED; }
.spu-sub { margin: 0; }

/* Tabs */
.spu-tabs {
  display: inline-flex;
  padding: 4px;
  background: rgba(222, 214, 199, 0.35);
  border: 1px solid var(--line, #DED6C7);
  border-radius: 12px;
  gap: 4px;
  flex-shrink: 0;
}
.spu-tab {
  appearance: none;
  border: none;
  background: transparent;
  padding: 9px 16px;
  border-radius: 9px;
  font-size: 13.5px;
  font-family: inherit;
  font-weight: 600;
  color: var(--ink-4, #8A7F68);
  cursor: pointer;
  transition: all .2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.spu-tab:hover { color: var(--ink-2, #4B4235); background: rgba(255,255,255,.4); }
.spu-tab.active {
  background: var(--ink, #2C2418);
  color: #fff;
  box-shadow: 0 4px 12px -4px rgba(44,36,24,0.4);
}

/* 虚线分区 */
.spu-divider {
  margin: 18px 0 4px;
  border-top: 1px dashed rgba(222,214,199,0.9);
}

/* 每个 section */
.spu-section { padding: 12px 4px 4px; }

/* 子区块头部 */
.spu-subhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 4px 4px 12px;
}
.spu-subtitle {
  font-family: "Noto Serif SC", "Georgia", "SimSun", serif;
  font-weight: 900;
  font-size: 19px;
  letter-spacing: 0.01em;
  color: var(--ink, #2C2418);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sh-ic { width: 20px; height: 20px; }
.sh-ic-cobalt  { color: #1D4ED8; }
.sh-ic-amber   { color: #B45309; }
.sh-ic-emerald { color: #047857; }
.sh-ic-seal    { color: #FF5A1F; }

/* 图表容器 */
.spu-chart-wrap {
  background: rgba(255,255,255,.35);
  border: 1px dashed rgba(222,214,199,0.9);
  border-radius: 14px;
  padding: 18px 14px;
  min-height: 460px;
}

/* 成长 Tab 的时间线容器 */
.spu-timeline-wrap {
  background: rgba(255,255,255,.35);
  border: 1px dashed rgba(222,214,199,0.9);
  border-radius: 14px;
  padding: 18px 20px;
  max-height: 520px;
  overflow-y: auto;
}
.spu-timeline-wrap::-webkit-scrollbar { width: 8px; }
.spu-timeline-wrap::-webkit-scrollbar-thumb { background: rgba(222,214,199,0.9); border-radius: 99px; }

/* 小屏 */
@media (max-width: 900px) {
  .sp-unified { padding: 18px 16px 20px; }
  .spu-title { font-size: 21px; }
  .spu-tab { padding: 7px 12px; font-size: 12.5px; }
  .spu-tabs { width: 100%; justify-content: flex-start; overflow-x: auto; }
}
</style>
