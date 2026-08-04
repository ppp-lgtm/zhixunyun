<template>
  <div class="min-h-full page-enter">
    <!-- ============ 顶部：岗位条 + 筛选/操作 ============ -->
    <div class="mb-8">
      <div class="flex items-end md:items-center justify-between flex-wrap gap-4 mb-5">
        <div>
          <h1 class="font-display text-3xl font-black text-ink tracking-tight">学生岗位匹配榜</h1>
          <p class="text-ink-3 mt-1 text-[13.5px] font-body">基于学生实训表现，计算学生与岗位的适配度</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="refreshMatch" :disabled="loading" class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">
            <Icon icon="mdi:refresh" class="mr-1" :class="{'animate-spin': loading}" />
            重新匹配
          </button>
          <button @click="exportReport" :disabled="!jobInfo?.id || !classId" class="btn-mag btn-mag-secondary px-4 py-2.5 text-[13px]">
            <Icon icon="mdi:file-document-outline" class="mr-1" /> 下载文字报告
          </button>
        </div>
      </div>

      <!-- 岗位卡片条（横向滚动） -->
      <div class="card-mag p-0 overflow-hidden">
        <div class="px-7 py-4 border-b border-line/80 flex items-center justify-between">
          <div>
            <div class="section-label !mb-1 !text-[10.5px]">01A · 我的岗位</div>
            <h3 class="font-display text-[18px] font-bold text-ink tracking-tight">选择要匹配的岗位</h3>
          </div>
          <div class="flex items-center gap-3 text-[12.5px]">
            <div class="flex items-center gap-2">
              <label class="text-ink-3 font-medium">班级</label>
              <select v-model="classId" class="h-9 rounded-xl border border-line bg-paper px-3 text-ink outline-none focus:border-seal/40 focus:shadow-[0_0_0_4px_rgba(255,90,31,0.08)]">
                <option v-for="c in classList" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div v-if="jobInfo?.skill_requirements?.length" class="chip-mag !text-[12px]">
              门槛维度 {{ jobInfo.skill_requirements.length }} · 权重合计 {{ weightSum }}%
            </div>
          </div>
        </div>
        <div class="flex gap-4 overflow-x-auto px-7 py-5">
          <div v-for="j in jobs" :key="j.id"
               @click="selectJob(j)"
               class="group flex-shrink-0 w-[300px] rounded-2xl border p-5 cursor-pointer transition-all duration-200 hover:-translate-y-0.5 relative overflow-hidden"
               :class="activeJobId === j.id
                 ? 'border-seal/40 bg-seal/[0.06] shadow-[0_10px_30px_-12px_rgba(255,90,31,0.35)]'
                 : 'border-line bg-paper hover:border-ink-4/30 hover:bg-paper-2/70'">
            <div v-if="activeJobId === j.id" class="absolute top-4 right-4 w-7 h-7 rounded-full bg-seal text-white flex items-center justify-center text-[14px] shadow-sm">
              <Icon icon="mdi:check" />
            </div>
            <div class="flex items-center gap-3 mb-4">
              <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-cobalt/15 to-violet-600/15 text-cobalt flex items-center justify-center">
                <Icon icon="mdi:briefcase-outline" class="text-xl" />
              </div>
              <div class="min-w-0">
                <div class="font-display font-bold text-ink text-[15.5px] truncate">{{ j.title }}</div>
                <div class="text-[12px] text-ink-3">{{ j.job_type || '全职' }} · {{ j.city || '远程' }} · {{ j.level || 'P5' }}</div>
              </div>
            </div>
            <div class="flex items-center justify-between text-[12.5px]">
              <span class="chip-mag !text-seal-dark !bg-seal/10 !border-seal/30 !text-[11.5px]">
                <Icon icon="mdi:cash" class="mr-1" inline width="12" /> {{ j.salary_range || '面议' }}
              </span>
              <span class="text-ink-3 font-mono">
                <Icon icon="mdi:account-tie-outline" class="mr-1 align-text-bottom" inline width="14" /> {{ j.enterprise_name || '本企业' }}
              </span>
            </div>
          </div>
          <div v-if="!jobs.length" class="w-full py-10 text-center text-ink-3 text-[13px]">
            <Icon icon="mdi:inbox-arrow-down-outline" class="text-4xl opacity-40 mb-2 block mx-auto" />
            暂无开放岗位，请到「岗位管理」创建。
          </div>
        </div>
      </div>
    </div>

      <!-- 接口错误提示 -->
      <div v-if="loadError" class="mb-6 rounded-2xl border-2 border-seal/30 bg-seal/[0.06] px-5 py-4 flex items-start gap-3">
        <Icon icon="mdi:alert-circle-outline" class="text-seal text-xl flex-shrink-0 mt-0.5" />
        <div class="text-[13.5px] text-seal-dark leading-[1.7] flex-1">{{ loadError }}</div>
        <button @click="loadJobsAndClasses().then(() => refreshMatch())" class="chip-mag !text-[12px] !py-1 !px-3 flex-shrink-0">
          <Icon icon="mdi:refresh" class="mr-1" inline width="12" /> 重试
        </button>
      </div>

    <!-- ============ 主体：单一统一大卡片（仅 TOP 候选人） ============ -->
    <section class="em-unified">
      <!-- 头部：标题 + 搜索 + 统计 -->
      <div class="emu-head">
        <div class="emu-head-l">
          <h2 class="emu-title">
            <Icon icon="mdi:medal-outline" class="emu-ic emu-ic-violet" />
            TOP {{ topRows.length }} 匹配候选人
            <span class="chip-mag !text-[12px] ml-2">{{ classInfo?.name || '班级' }} × {{ jobInfo?.title || '岗位' }}</span>
          </h2>
          <div class="text-[12.5px] text-ink-4 mt-1.5">
            均值 <b class="font-display text-ink text-[15px] mx-1">{{ avgScore }}</b>
            <span class="mx-2 opacity-40">·</span>
            ≥80 分 <b class="font-display text-jade-dark text-[15px] mx-1">{{ gt80Count }}</b> 人
            <span class="mx-2 opacity-40">·</span>
            点击「画像」查看能力对标 / TOP 5 岗位匹配详情
          </div>
        </div>
        <div class="emu-head-r">
          <!-- 搜索框 -->
          <div class="relative w-64">
            <Icon icon="mdi:magnify" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-4" />
            <input v-model="keyword" placeholder="搜索学生姓名 / 学号…"
                   class="w-full h-10 rounded-xl border border-line bg-paper px-10 font-body text-[13.5px] text-ink outline-none focus:border-2 focus:border-seal/40 focus:shadow-[0_0_0_4px_rgba(255,90,31,0.08)] transition-all" />
          </div>
        </div>
      </div>

      <!-- 分区虚线 -->
      <div class="emu-divider"></div>

      <!-- 候选人列表（仅展示排名，不再做 tab 切换） -->
      <div class="emu-section">
        <div v-if="loading" class="py-16 text-center text-ink-3 text-sm">
          <Icon icon="mdi:loading" class="text-4xl animate-spin mb-3 block mx-auto opacity-60" />
          正在根据班级评价数据 × 岗位门槛计算匹配分…
        </div>
        <div v-else-if="!topRows.length" class="py-16 text-center">
          <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
            <Icon icon="mdi:radar" class="text-4xl text-ink-4" />
          </div>
          <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">暂无可匹配的学生</p>
          <p class="text-[12.5px] text-ink-4">请选择岗位 + 班级后，点「重新匹配」开始计算。若该班级无评价数据，可先去评价学生。</p>
        </div>
        <div v-else class="emu-scroll px-2 py-2">
          <div v-for="(r, idx) in topRows" :key="r.student_id || r.id"
               @click="selectStudent(r)"
               class="emu-row rounded-2xl p-5 border cursor-pointer transition-all duration-200 hover:-translate-y-0.5 relative group"
               :class="{
                 'border-seal/40 bg-seal/[0.06] shadow-[0_10px_30px_-12px_rgba(255,90,31,0.35)] z-10': activeStudentId === (r.student_id || r.id),
                 'border-line bg-paper hover:border-ink-4/30 hover:bg-paper-2/70': activeStudentId !== (r.student_id || r.id)
               }">
            <!-- 第1/2/3名 金色徽章 -->
            <div v-if="idx < 3" class="absolute -top-3 -left-2">
              <div class="w-10 h-10 rounded-2xl shadow-lg flex items-center justify-center text-white font-display font-black"
                   :class="[
                     'bg-gradient-to-br',
                     idx === 0 ? 'from-amber-400 via-orange-400 to-rose-500' : idx === 1 ? 'from-slate-300 to-slate-500' : 'from-orange-300 to-amber-600'
                   ]">
                <Icon v-if="idx === 0" icon="mdi:crown" class="text-xl" />
                <template v-else>{{ idx + 1 }}</template>
              </div>
            </div>

            <div class="flex items-start gap-4">
              <!-- 头像 + 环形匹配度 -->
              <div class="flex-shrink-0 flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-cobalt to-violet-600 text-white font-bold font-display text-xl flex items-center justify-center shadow-sm">
                  {{ initialOfRow(r) }}
                </div>
                <div class="relative w-16 h-16">
                  <svg viewBox="0 0 100 100" class="w-full h-full transform -rotate-90">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" class="text-line" stroke-width="8" />
                    <circle cx="50" cy="50" r="42" fill="none"
                            :stroke="matchColor(r.match_score)" stroke-width="8" stroke-linecap="round"
                            :stroke-dasharray="`${Math.round((r.match_score||0) * 2.64)} 264`" />
                  </svg>
                  <div class="absolute inset-0 flex flex-col items-center justify-center">
                    <div class="font-display text-[19px] font-black leading-none" :class="matchTextColor(r.match_score)">
                      {{ Math.round(r.match_score || 0) }}
                    </div>
                    <div class="text-[9px] font-sub uppercase tracking-[0.15em] text-ink-4 mt-0.5">match</div>
                  </div>
                </div>
              </div>

              <!-- 基本信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5 flex-wrap">
                  <h4 class="font-display font-bold text-ink text-[17px] tracking-tight truncate">
                    {{ r.real_name || r.name || `学生 #${r.student_id || r.id}` }}
                  </h4>
                  <span v-if="r.user_number" class="text-[11.5px] font-mono text-ink-3">#{{ r.user_number }}</span>
                  <span v-if="r.class_name" class="chip-mag !py-0.5 !px-2 !text-[10.5px] !font-medium">
                    {{ r.class_name }}
                  </span>
                  <span v-if="r.must_failed_count" class="chip-mag !py-0.5 !px-2 !text-[10.5px] !bg-seal/12 !text-seal-dark !border-seal/30">
                    ❌ 必选未达标 {{ r.must_failed_count }}
                  </span>
                </div>

                <!-- 5 行维度：门槛 vs 学生得分 -->
                <div class="space-y-1.5 mt-3">
                  <div v-for="d in (r.dimension_breakdown || []).slice(0, 5)" :key="d.name" class="flex items-center gap-3">
                    <div class="w-24 shrink-0 flex items-center gap-1.5 min-w-0">
                      <Icon v-if="d.must && !d.passed" icon="mdi:alert-octagon" class="text-seal text-[13px]" />
                      <Icon v-else-if="d.must && d.passed" icon="mdi:shield-check-outline" class="text-jade-dark text-[13px]" />
                      <Icon v-else-if="!d.must && d.passed" icon="mdi:check-circle-outline" class="text-cobalt text-[13px]" />
                      <Icon v-else icon="mdi:minus-circle-outline" class="text-amber-dark text-[13px]" />
                      <span class="text-[12px] text-ink-2 font-medium truncate">{{ d.name }}</span>
                    </div>
                    <div class="flex-1 relative h-5">
                      <!-- 门槛线 -->
                      <div class="absolute top-0 bottom-0 border-l-2 border-dashed border-cobalt"
                           :style="{ left: `${d.threshold ?? 60}%` }"></div>
                      <!-- 学生条 -->
                      <div class="absolute top-1 bottom-1 left-0 rounded-full"
                           :class="(d.passed ? 'bg-gradient-to-r from-jade to-emerald-500' : 'bg-gradient-to-r from-amber to-seal')"
                           :style="{ width: `${Math.min(100, d.student_score ?? 0)}%` }"></div>
                    </div>
                    <span class="font-mono text-[11.5px] text-ink-2 w-20 text-right">
                      <span :class="d.passed ? 'text-jade-dark font-bold' : 'text-seal-dark font-bold'">{{ Math.round(d.student_score ?? 0) }}</span>
                      <span class="text-ink-4 opacity-70"> / {{ Math.round(d.threshold ?? 60) }}</span>
                    </span>
                  </div>
                  <div v-if="(r.dimension_breakdown||[]).length === 0" class="text-[12px] text-ink-3 italic">该岗位无维度门槛配置</div>
                </div>

                <!-- 亮点 + 缺口 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5 mt-4">
                  <div v-if="r.highlights?.length" class="rounded-xl p-3 bg-jade/[0.08] border border-jade/20">
                    <div class="flex items-center gap-1.5 text-[11.5px] font-sub font-bold text-jade-dark uppercase tracking-[0.1em] mb-1.5">
                      <Icon icon="mdi:plus-circle" inline width="14" /> HIGHLIGHT · 亮点
                    </div>
                    <div class="text-[12px] text-ink leading-snug">
                      <template v-for="(h, i) in r.highlights.slice(0,2)" :key="h.name">
                        <span class="font-bold text-jade-dark">{{ h.name }}</span> 超门槛 <span class="font-mono font-bold">+{{ h.delta }}</span> 分
                        <span class="text-ink-4">（{{ h.student_score }}/{{ h.threshold }}）</span>{{ i < Math.min(r.highlights.length, 2) - 1 ? '，' : '' }}
                      </template>
                    </div>
                  </div>
                  <div v-if="r.gaps?.length" class="rounded-xl p-3 bg-seal/[0.08] border border-seal/20">
                    <div class="flex items-center gap-1.5 text-[11.5px] font-sub font-bold text-seal-dark uppercase tracking-[0.1em] mb-1.5">
                      <Icon icon="mdi:minus-circle" inline width="14" /> GAP · 缺口
                    </div>
                    <div class="text-[12px] text-ink leading-snug">
                      <template v-for="(g, i) in r.gaps.slice(0,2)" :key="g.name">
                        <span :class="g.level==='major' ? 'font-bold text-seal-dark' : 'font-semibold text-amber-dark'">{{ g.name }}</span>
                        <span class="text-ink-4"> 差</span> <span class="font-mono font-bold">{{ Math.abs(g.delta) }}</span> 分
                        <span class="text-ink-4">（{{ g.student_score }}/{{ g.threshold }}）</span>{{ i < Math.min(r.gaps.length, 2) - 1 ? '，' : '' }}
                      </template>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 右操作 -->
              <div class="flex-shrink-0 flex flex-col gap-2">
                <button @click.stop="$router.push(`/app/enterprise/student/${r.student_id || r.id}`)"
                        class="btn-mag btn-mag-primary px-3 py-2 text-[12.5px] whitespace-nowrap">
                  <Icon icon="mdi:eye-outline" class="mr-1" inline width="14" /> 画像
                </button>
                <button @click.stop="invite(r)"
                        class="btn-mag btn-mag-ghost px-3 py-2 text-[12.5px] whitespace-nowrap">
                  <Icon icon="mdi:message-outline" class="mr-1" inline width="14" /> 邀约
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'

const router = useRouter()

type JobT = any
type ClassT = { id: number; name: string }
type MatchRow = any

const loading = ref(false)
const loadError = ref('')
const keyword = ref('')
const jobs = ref<JobT[]>([])
const classList = ref<ClassT[]>([])
const classId = ref<number | null>(null)
const activeJobId = ref<number | null>(null)
const jobInfo = ref<JobT | null>(null)
const classInfo = ref<ClassT | null>(null)
const allRows = ref<MatchRow[]>([])
const activeStudentId = ref<number | null>(null)

const weightSum = computed(() => {
  const reqs = jobInfo.value?.skill_requirements || []
  return Math.round(reqs.reduce((s: number, r: any) => s + (Number(r.weight) || 0), 0))
})

const topRows = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return allRows.value.filter(r => {
    if (!kw) return true
    return [
      r.real_name, r.name, r.user_number, r.username, r.class_name
    ].map(x => String(x || '').toLowerCase()).some(s => s.includes(kw))
  })
})

const avgScore = computed(() => {
  if (!allRows.value.length) return 0
  const sum = allRows.value.reduce((s, r) => s + (Number(r.match_score) || 0), 0)
  return Math.round(sum / allRows.value.length)
})

const gt80Count = computed(() => allRows.value.filter(r => (r.match_score || 0) >= 80).length)

/* ========= Helpers ========= */
function initialOfRow(r: any) {
  return (r?.real_name || r?.name || '学').slice(0, 1)
}
function matchColor(s: any) {
  const v = Number(s); if (isNaN(v)) return '#94A3B8'
  if (v >= 85) return '#11A367'
  if (v >= 70) return '#2563EB'
  if (v >= 60) return '#F59E0B'
  return '#FF5A1F'
}
function matchTextColor(s: any) {
  const v = Number(s); if (isNaN(v)) return 'text-ink-4'
  if (v >= 85) return 'text-jade-dark'
  if (v >= 70) return 'text-cobalt'
  if (v >= 60) return 'text-amber-dark'
  return 'text-seal-dark'
}
function invite(r: any) {
  const name = r?.real_name || r?.name || '该学生'
  alert(`已向 ${name}（学号 ${r?.user_number || '-'}）发送邀约，演示模式下不会真的发消息。`)
}

/* ========= Actions ========= */
async function loadJobsAndClasses() {
  const token = localStorage.getItem('token') || ''
  const headers: any = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let errJobs: any = null, errCls: any = null
  try {
    const jr = await axios.get(`${API_BASE}/api/enterprise/jobs`, { headers, params: { status: 'open', page_size: 50 } })
    const jlist: any[] = (jr.data as any)?.data?.list || (jr.data as any)?.list || jr.data || []
    jobs.value = jlist.filter(Boolean)
    if (!activeJobId.value && jobs.value[0]) selectJob(jobs.value[0])
  } catch (e) { errJobs = e }
  try {
    const cr = await axios.get(`${API_BASE}/api/enterprise/classes`, { headers })
    const cl: any[] = (cr.data as any)?.data?.list || (cr.data as any)?.list || (Array.isArray(cr.data) ? cr.data : [])
    classList.value = cl.filter(Boolean)
  } catch (e) { errCls = e }
  if (errJobs || errCls) {
    const msgs: string[] = []
    if (errJobs) msgs.push('岗位列表：' + (errJobs?.response?.data?.detail || errJobs?.message || '请求失败'))
    if (errCls)  msgs.push('班级列表：' + (errCls?.response?.data?.detail  || errCls?.message  || '请求失败'))
    loadError.value = '初始化失败：' + msgs.join('；') + '（请启动后端服务，并使用企业导师账号登录）'
  } else {
    loadError.value = ''
  }
  if (!classId.value && classList.value[0]) classId.value = classList.value[0].id
}

function selectJob(j: JobT) {
  activeJobId.value = j.id
  jobInfo.value = {
    ...j,
    skill_requirements: normalizeReqs(j.skill_requirements)
  }
}

function normalizeReqs(reqs: any) {
  if (!reqs) return []
  if (typeof reqs === 'string') {
    try { reqs = JSON.parse(reqs) } catch { return String(reqs).split(/[,，;；]/).map(n => ({ name: n.trim(), weight: 20, threshold: 60, must: false })) }
  }
  if (Array.isArray(reqs)) {
    return reqs.map(r => typeof r === 'string'
      ? { name: r, weight: 20, threshold: 60, must: false }
      : { name: r?.name, weight: Number(r?.weight) || 20, threshold: Number(r?.threshold) || 60, must: !!r?.must }
    ).filter(r => r.name)
  }
  return []
}

function selectStudent(r: MatchRow) {
  activeStudentId.value = r.student_id || r.id
}

async function refreshMatch() {
  if (!activeJobId.value || !classId.value) {
    alert('请先选择岗位和班级')
    return
  }
  loading.value = true
  loadError.value = ''
  const token = localStorage.getItem('token') || ''
  const headers: any = {}
  if (token) headers.Authorization = `Bearer ${token}`
  try {
    const { data } = await axios.get(`${API_BASE}/api/job-match/batch-class`, {
      headers,
      params: { class_id: classId.value, job_id: activeJobId.value, top_n: 50, min_score: 0 }
    })
    const payload: any = data
    classInfo.value = payload.class || null
    jobInfo.value = payload.job ? { ...payload.job, skill_requirements: normalizeReqs(payload.job.skill_requirements) } : jobInfo.value
    allRows.value = payload.list || []
  } catch (e: any) {
    allRows.value = []
    const msg = e?.response?.data?.detail || e?.message || '请求失败'
    loadError.value = `匹配榜单加载失败：${msg}（请确认后端服务已启动，当前企业账号已绑定班级/发布岗位）`
  } finally {
    loading.value = false
  }
}

async function exportReport() {
  if (!activeJobId.value || !classId.value) { alert('请先选择岗位和班级'); return }
  const token = localStorage.getItem('token') || ''
  const headers: any = {}
  if (token) headers.Authorization = `Bearer ${token}`
  try {
    const { data } = await axios.get(`${API_BASE}/api/job-match/generate-report`, {
      headers, params: { class_id: classId.value, job_id: activeJobId.value, top_n: 50, fmt: 'text' }
    })
    const text = data?.report_text || data || '（无报告内容）'
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `岗位匹配报告_${classInfo.value?.name || 'class'}_${jobInfo.value?.title || 'job'}_${Date.now()}.txt`
    document.body.appendChild(a); a.click(); a.remove()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    alert('报告生成失败：' + (e?.message || '未知错误'))
  }
}

/* ========= Init + Watch ========= */
watch([activeJobId, classId], () => {
  if (activeJobId.value && classId.value) refreshMatch()
})
onMounted(async () => {
  await loadJobsAndClasses()
  if (activeJobId.value && classId.value) refreshMatch()
})
</script>

<style scoped>
.card-mag select, .card-mag input, .card-mag button { font-family: inherit; }

/* ========= 岗位匹配 · 统一卡片 ======== */
.em-unified {
  background: var(--paper, #F4F1EA);
  border: 1px solid var(--line, #DED6C7);
  border-radius: 16px;
  padding: 22px 26px 26px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}

/* 头部 */
.emu-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}
.emu-title {
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
.emu-ic { width: 26px; height: 26px; }
.emu-ic-violet { color: #7C3AED; }
.emu-head-r {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

/* 虚线分区 */
.emu-divider {
  margin: 18px 0 4px;
  border-top: 1px dashed rgba(222,214,199,0.9);
}

/* 每个 section */
.emu-section { padding: 12px 4px 4px; }

/* 候选人列表滚动区 */
.emu-scroll {
  max-height: 72vh;
  overflow-y: auto;
}
.emu-scroll::-webkit-scrollbar { width: 8px; }
.emu-scroll::-webkit-scrollbar-thumb { background: rgba(222,214,199,0.8); border-radius: 99px; }
.emu-scroll::-webkit-scrollbar-track { background: transparent; }

/* 紧凑小屏 */
@media (max-width: 900px) {
  .em-unified { padding: 18px 16px 20px; }
  .emu-title { font-size: 21px; }
  .emu-head-r { width: 100%; justify-content: flex-start; }
}
</style>
