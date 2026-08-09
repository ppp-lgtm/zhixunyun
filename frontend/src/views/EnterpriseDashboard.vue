<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 顶部 Header（保留，不套卡片） -->
      <div class="mb-8">
        <div class="flex items-end md:items-center justify-between flex-wrap gap-4 mb-5">
          <div>
            <h1 class="font-display text-3xl font-black text-ink tracking-tight">{{ enterprise_name }} · 企业中心</h1>
            <p class="text-ink-3 mt-1 text-[13.5px] font-body">一览岗位发布、学生匹配与评价工作概况，共 {{ stats.class_count }} 个班级 / {{ stats.student_count }} 名可见学生。</p>
          </div>
          <div class="flex items-center gap-2">
            <button @click="reload" :disabled="loading" class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">
              <Icon icon="mdi:refresh" class="mr-1" :class="{'animate-spin': loading}" /> 刷新
            </button>
            <button @click="$router.push('/app/enterprise/jobs')" class="btn-mag btn-mag-primary px-4 py-2.5 text-[13px]">
              <Icon icon="mdi:briefcase-plus-outline" class="mr-1" inline width="14" /> 发布新岗位
            </button>
          </div>
        </div>
      </div>

      <!-- 统一 Dashboard 大卡片 前：接口异常的错误提示 -->
      <div v-if="errMsg" class="mb-6 rounded-2xl border-2 border-seal/30 bg-seal/[0.06] px-5 py-4 flex items-start gap-3">
        <Icon icon="mdi:alert-circle-outline" class="text-seal text-xl flex-shrink-0 mt-0.5" />
        <div class="text-[13.5px] text-seal-dark leading-[1.7]">{{ errMsg }}</div>
        <button @click="reload" class="ml-auto chip-mag !text-[12px] !py-1 !px-3 flex-shrink-0">
          <Icon icon="mdi:refresh" class="mr-1" inline width="12" /> 重试
        </button>
      </div>

      <!-- ============ 单一统一 Dashboard 大卡片 ============ -->
      <section class="ed-unified">
        <!-- 分区1：KPI 概览（平铺，无外层小卡片） -->
        <div class="ed-section">
          <div class="ed-sec-head">
            <h3 class="ed-sec-title"><Icon icon="mdi:chart-box-outline" class="sh-ic ic-cobalt" /> KPI 概览</h3>
            <span class="ed-sec-tag">实时数据</span>
          </div>
          <div class="ed-kpi-grid four">
            <div class="ed-kpi kpi-cobalt">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:briefcase-outline" /></div>
                <span class="kpi-chip">总计</span>
              </div>
              <div class="kpi-num">{{ stats.job_count }}</div>
              <div class="kpi-lbl">发布岗位数</div>
            </div>
            <div class="ed-kpi kpi-violet">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:radar" /></div>
                <span class="kpi-chip">估算</span>
              </div>
              <div class="kpi-num">{{ stats.match_count }}</div>
              <div class="kpi-lbl">匹配推荐数</div>
            </div>
            <div class="ed-kpi kpi-jade">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:star-check-outline" /></div>
                <span class="kpi-chip chip-jade">{{ stats.evaluated_student_count }} 人</span>
              </div>
              <div class="kpi-num">{{ stats.evaluation_count }}</div>
              <div class="kpi-lbl">评价提交条数</div>
            </div>
            <div class="ed-kpi kpi-seal">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:scale-balance" /></div>
                <span class="kpi-chip chip-seal">待评 {{ stats.pending_evaluation_count }}</span>
              </div>
              <div class="kpi-num">{{ stats.avg_score || '—' }}</div>
              <div class="kpi-lbl">企业评价平均分</div>
            </div>
          </div>
        </div>

        <!-- 分区2：最近岗位 + 待评价学生（双栏，在统一卡片内） -->
        <div class="ed-section ed-columns ed-last">
          <!-- 左：最近岗位 -->
          <div class="ed-col">
            <div class="ed-col-head">
              <div class="ed-col-title">
                <span class="col-bar bar-cv"></span>
                最近岗位
              </div>
              <button @click="$router.push('/app/enterprise/jobs')" class="col-link">
                查看全部 <Icon icon="mdi:chevron-right" class="ml-0.5" inline width="14" />
              </button>
            </div>

            <div v-if="loadingJobs" class="col-empty">
              <Icon icon="mdi:loading" class="text-3xl animate-spin mb-2 block mx-auto opacity-60" />
              <span>加载岗位…</span>
            </div>
            <div v-else-if="!recentJobs.length" class="col-empty">
              <Icon icon="mdi:briefcase-off-outline" class="col-empty-ic" />
              <p>暂无岗位，去「岗位管理」发布第一个岗位吧。</p>
            </div>
            <div v-else class="col-list">
              <div v-for="job in recentJobs" :key="job.id" class="col-row">
                <div class="col-row-ic ic-cv">
                  <Icon icon="mdi:briefcase-outline" />
                </div>
                <div class="col-row-body">
                  <div class="col-row-head">
                    <h4 class="col-row-title">{{ job.title }}</h4>
                    <span :class="statusChipClass(job.status)" class="chip-mag !text-[11px] !py-0.5 !px-2 flex-shrink-0">
                      {{ statusLabel(job.status) }}
                    </span>
                  </div>
                  <p class="col-row-sub">{{ job.city || '远程' }} · {{ job.level || '初级' }}</p>
                </div>
                <div class="col-row-right">
                  <div class="col-row-salary">{{ job.salary_range || '面议' }}</div>
                  <div class="col-row-tag">{{ job.job_type || '技术岗' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 右：待评价学生 -->
          <div class="ed-col">
            <div class="ed-col-head">
              <div class="ed-col-title">
                <span class="col-bar bar-sa"></span>
                待评价学生
                <span class="chip-mag !bg-seal/10 !text-seal-dark !border-seal/30 !text-[11px] !py-0.5 !px-2 ml-2">
                  {{ pendingStudents.length }} 人
                </span>
              </div>
              <button @click="$router.push('/app/enterprise/evaluations')" class="col-link">
                去评价台 <Icon icon="mdi:chevron-right" class="ml-0.5" inline width="14" />
              </button>
            </div>

            <div v-if="loadingPendings" class="col-empty">
              <Icon icon="mdi:loading" class="text-3xl animate-spin mb-2 block mx-auto opacity-60" />
              <span>加载待评价列表…</span>
            </div>
            <div v-else-if="!pendingStudents.length" class="col-empty col-empty-ok">
              <Icon icon="mdi:check-decagram-outline" class="col-empty-ic ic-ok" />
              <p>目前没有待评价的学生提交，完成度 <b>100%</b> 👏</p>
            </div>
            <div v-else class="col-list">
              <div v-for="s in pendingStudents" :key="s.submission_id || s.id" class="col-row">
                <div class="col-row-avatar">
                  {{ (s.student?.real_name || s.student?.username || s.real_name || s.username || '?').charAt(0) }}
                </div>
                <div class="col-row-body">
                  <div class="col-row-head">
                    <span class="col-row-name">{{ s.student?.real_name || s.student?.username || s.real_name || s.username }}</span>
                    <span class="col-row-no">{{ s.student?.user_number || s.student_no || ('S' + (s.student_id || 0)) }}</span>
                  </div>
                  <div class="col-row-meta">
                    <span v-if="(s.classes && s.classes[0]) || s.class_name" class="meta-item">
                      <Icon icon="mdi:google-classroom" class="ic-cobalt" inline width="12" />
                      {{ (s.classes && s.classes[0]) || s.class_name }}
                    </span>
                    <span class="meta-item">
                      <Icon icon="mdi:clock-outline" inline width="12" /> {{ fmtDate(s.submitted_at || s.created_at) }}
                    </span>
                  </div>
                </div>
                <button @click="goEvaluate(s)" class="btn-mag btn-mag-primary !px-3.5 !py-2 text-[12px]">
                  <Icon icon="mdi:pencil-outline" class="mr-1" inline width="12" /> 评价
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'

const loading = ref(false)
const loadingJobs = ref(false)
const loadingPendings = ref(false)
const enterprise_name = ref('企业中心')

const stats = reactive({
  job_count: 0, class_count: 0, student_count: 0,
  evaluation_count: 0, evaluated_student_count: 0,
  pending_evaluation_count: 0, match_count: 0, avg_score: 0,
})

const recentJobs = ref<any[]>([])
const pendingStudents = ref<any[]>([])

function authHeaders(): any {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function loadProfile() {
  loading.value = true
  let err: any = null
  try {
    const r = await axios.get(`${API_BASE}/api/enterprise/profile`, { headers: authHeaders() })
    const payload: any = r.data || {}
    enterprise_name.value = payload.enterprise?.short_name || payload.enterprise?.name || '企业中心'
    const s = payload.stats || {}
    stats.job_count = Number(s.job_count || 0)
    stats.class_count = Number(s.class_count || 0)
    stats.student_count = Number(s.student_count || 0)
    stats.evaluation_count = Number(s.evaluation_count || 0)
    stats.evaluated_student_count = Number(s.evaluated_student_count || 0)
    stats.pending_evaluation_count = Number(s.pending_evaluation_count || 0)
    stats.match_count = Number(s.match_count || 0)
    stats.avg_score = s.avg_score || 0
    errMsg.value = ''
  } catch (e) { err = e } finally {
    loading.value = false
    if (err) {
      const msg = err?.response?.data?.detail || err?.message || '接口请求失败'
      errMsg.value = `企业总览加载失败：${msg}（请先启动后端服务，并使用企业导师账号登录）`
    }
  }
}
const errMsg = ref('')

async function loadJobs() {
  loadingJobs.value = true
  try {
    const r = await axios.get(`${API_BASE}/api/enterprise/jobs`, {
      headers: authHeaders(),
      params: { page: 1, page_size: 4, status: 'open' },
    })
    const list: any[] = (r.data as any)?.list || (r.data as any)?.data?.list || []
    recentJobs.value = list
  } catch (_e) { recentJobs.value = [] } finally {
    loadingJobs.value = false
  }
}

async function loadPendingStudents() {
  loadingPendings.value = true
  try {
    const r = await axios.get(`${API_BASE}/api/enterprise/evaluations/submissions`, {
      headers: authHeaders(),
      params: { page: 1, page_size: 5, status: 'pending' },
    })
    const list: any[] = (r.data as any)?.list || (r.data as any)?.data?.list || []
    pendingStudents.value = list
  } catch (_e) { pendingStudents.value = [] } finally {
    loadingPendings.value = false
  }
}

function goEvaluate(s: any) {
  if (s.submission_id) {
    window.location.hash = `#/app/enterprise/evaluations?submission_id=${s.submission_id}`
  } else {
    window.location.hash = '#/app/enterprise/evaluations'
  }
}

function statusLabel(s: string) {
  return s === 'open' ? '招聘中' : s === 'paused' ? '暂停' : s === 'closed' ? '已截止' : (s || '—')
}
function statusChipClass(s: string) {
  if (s === 'open') return '!bg-jade/10 !text-jade-dark !border-jade/30'
  if (s === 'paused') return '!bg-amber/10 !text-amber-dark !border-amber/30'
  if (s === 'closed') return '!bg-ink-3/10 !text-ink-3 !border-ink-3/30'
  return ''
}
function fmtDate(v: any) {
  if (!v) return '—'
  const d = new Date(v)
  if (isNaN(d.getTime())) return String(v).slice(0, 10)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const day = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (day < 1) return '今天'
  if (day < 2) return '1 天前'
  if (day < 8) return `${day} 天前`
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

async function reload() {
  await Promise.all([loadProfile(), loadJobs(), loadPendingStudents()])
}
onMounted(reload)
</script>

<style scoped>
/* ============ 外壳 ============ */
.ed-unified {
  max-width: 100%;
  background: #fff;
  border: 1px solid #E5E1D2;
  border-top: 4px solid #22C55E;
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04), 0 12px 36px rgba(17, 24, 39, 0.06);
  overflow: hidden;
  margin-bottom: 32px;
}

/* ============ 分区 ============ */
.ed-section {
  padding: 24px 32px;
  border-bottom: 1px dashed #E5E1D2;
}
.ed-section.ed-last { border-bottom: none; }

.ed-sec-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.ed-sec-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0.02em;
}
.sh-ic {
  width: 28px; height: 28px;
  border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 15px;
}
.ic-cobalt  { background: rgba(22, 93, 255, 0.10); color: #165DFF; }

.ed-sec-tag {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.10);
  color: #16A34A;
  letter-spacing: 0.06em;
}

/* ============ KPI 网格（统一配色） ============ */
.ed-kpi-grid { display: grid; gap: 14px; }
.ed-kpi-grid.four { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 1080px) { .ed-kpi-grid.four { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 520px)  { .ed-kpi-grid.four { grid-template-columns: 1fr; } }

.ed-kpi {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  background: #F7F4EC;
  position: relative;
  overflow: hidden;
}
.ed-kpi::before {
  content: '';
  position: absolute;
  right: -20px; top: -20px;
  width: 80px; height: 80px;
  border-radius: 50%;
  opacity: 0.22;
}
.kpi-cobalt::before { background: #165DFF; }
.kpi-violet::before { background: #7C3AED; }
.kpi-jade::before   { background: #10B981; }
.kpi-seal::before   { background: #FF5A1F; }

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
}
.kpi-ic {
  width: 40px; height: 40px;
  border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 20px;
  color: #fff;
}
.kpi-cobalt .kpi-ic { background: #165DFF; }
.kpi-violet .kpi-ic { background: #7C3AED; }
.kpi-jade   .kpi-ic { background: #059669; }
.kpi-seal   .kpi-ic { background: #FF5A1F; }

.kpi-chip {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.7);
  color: #374151;
}
.kpi-chip.chip-jade { background: rgba(16,185,129,0.12); color: #16A34A; border: 1px solid rgba(16,185,129,0.28); }
.kpi-chip.chip-seal { background: rgba(255,90,31,0.12); color: #FF5A1F; border: 1px solid rgba(255,90,31,0.28); }

.kpi-num {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 30px;
  line-height: 1.1;
  color: #111827;
  position: relative;
  z-index: 1;
}
.kpi-lbl {
  font-size: 12.5px;
  color: #6B7280;
  margin-top: 4px;
  position: relative;
  z-index: 1;
}

/* ============ 双栏内容区 ============ */
.ed-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}
@media (max-width: 1080px) { .ed-columns { grid-template-columns: 1fr; gap: 24px; } }

.ed-col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.ed-col-title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.col-bar {
  width: 6px; height: 20px;
  border-radius: 999px;
}
.bar-cv { background: linear-gradient(180deg, #165DFF 0%, #7C3AED 100%); }
.bar-sa { background: linear-gradient(180deg, #FF5A1F 0%, #F59E0B 100%); }

.col-link {
  font-size: 12.5px;
  font-weight: 600;
  color: #165DFF;
  background: none;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.col-link:hover { color: #6366F1; }

/* ============ 通用列表 ============ */
.col-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.col-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  transition: all 0.2s ease;
}
.col-row:hover {
  border-color: rgba(255, 90, 31, 0.30);
  background: rgba(255, 90, 31, 0.03);
}

.col-row-ic {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  color: #fff;
}
.ic-cv { background: linear-gradient(135deg, rgba(22,93,255,0.15) 0%, rgba(124,58,237,0.15) 100%); color: #165DFF; }

.col-row-avatar {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #165DFF 0%, #7C3AED 100%);
  display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 17px;
}

.col-row-body { flex: 1; min-width: 0; }
.col-row-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.col-row-title, .col-row-name {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.col-row-no {
  font-size: 11.5px;
  color: #9CA3AF;
}
.col-row-sub {
  margin: 0;
  font-size: 12.5px;
  color: #6B7280;
}
.col-row-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #6B7280;
}
.meta-item .ic-cobalt { background: none; color: #165DFF; }

.col-row-right {
  text-align: right;
  flex-shrink: 0;
}
.col-row-salary {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  color: #FF5A1F;
  font-size: 17px;
  line-height: 1.1;
}
.col-row-tag {
  font-size: 11.5px;
  color: #9CA3AF;
  margin-top: 4px;
}

/* ============ 空状态 ============ */
.col-empty {
  padding: 34px 20px;
  text-align: center;
  border-radius: 14px;
  border: 1px dashed #E5E1D2;
  background: #F7F4EC;
  font-size: 13px;
  color: #6B7280;
}
.col-empty p { margin: 0; }
.col-empty-ic {
  font-size: 38px;
  color: #9CA3AF;
  display: block;
  margin: 0 auto 8px;
  opacity: 0.7;
}
.col-empty-ic.ic-ok { color: #16A34A; }
.col-empty-ok { background: rgba(16,185,129,0.06); border-color: rgba(16,185,129,0.22); color: #065F46; }
.col-empty-ok b { color: #16A34A; font-weight: 800; }
</style>
