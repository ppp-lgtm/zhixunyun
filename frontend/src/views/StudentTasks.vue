<template>
  <div class="st-page">
    <!-- 背景装饰 -->
    <div class="st-glow st-glow-seal" aria-hidden="true"></div>
    <div class="st-glow st-glow-jade" aria-hidden="true"></div>
    <div class="st-ledger-mark" aria-hidden="true">TASK · LEDGER</div>

    <div class="st-inner page-enter-stagger">

      <!-- ============== HERO 标题区 ============== -->
      <header class="st-hero reveal reveal-1">
        <div class="st-hero-left">
          <span class="st-hero-chip">
            <span class="st-hero-chip-num">INDEX</span>
            <span class="st-hero-chip-text"> TASK LEDGER · 任务台</span>
          </span>
          <h1 class="st-hero-title">
            任务台
            <span class="st-hero-sub-en">· TASK LEDGER ·</span>
          </h1>
          <p class="st-hero-sub">
            来自教师与企业的实训任务集中派发于此，按截止日优先排序。完成后投递成果物，
            AI 初评 → 教师复评{{ enterpriseTotal > 0 ? ' → 企业终评' : '' }}，形成最终评价档案。
          </p>
        </div>

        <!-- 4 枚数字邮票（可点击筛选） -->
        <div class="st-stamps">
          <button @click="setFilter('all')"
                  class="st-stamp st-stamp-all"
                  :class="{active: activeFilter === 'all' && !enterpriseOnly}">
            <div class="st-stamp-holes" aria-hidden="true"></div>
            <div class="st-stamp-label">ALL TASKS</div>
            <div class="st-stamp-num">{{ tasks.length }}</div>
            <div class="st-stamp-foot">全部</div>
          </button>
          <button @click="setFilter('pending')"
                  class="st-stamp st-stamp-pending"
                  :class="{active: activeFilter === 'pending'}">
            <div class="st-stamp-holes" aria-hidden="true"></div>
            <div class="st-stamp-label">TO SUBMIT</div>
            <div class="st-stamp-num">{{ pendingCount }}</div>
            <div class="st-stamp-foot">待提交</div>
          </button>
          <button @click="setFilter('submitted')"
                  class="st-stamp st-stamp-done"
                  :class="{active: activeFilter === 'submitted'}">
            <div class="st-stamp-holes" aria-hidden="true"></div>
            <div class="st-stamp-label">RECEIVED</div>
            <div class="st-stamp-num">{{ submittedCount }}</div>
            <div class="st-stamp-foot">已提交</div>
          </button>
          <button @click="toggleEnterpriseOnly"
                  class="st-stamp st-stamp-enterprise"
                  :class="{active: enterpriseOnly}">
            <div class="st-stamp-holes" aria-hidden="true"></div>
            <div class="st-stamp-label">ENTERPRISE</div>
            <div class="st-stamp-num">{{ enterpriseTotal }}</div>
            <div class="st-stamp-foot">企业级</div>
          </button>
        </div>
      </header>

      <!-- ============== 筛选 / 搜索条 ============== -->
      <section class="st-toolbar reveal reveal-2">
        <div class="st-filter-row">
          <button
            v-for="f in filters" :key="f.key"
            class="st-filter-chip"
            :class="[{active: activeFilter === f.key && !enterpriseOnly}, f.tone]"
            @click="setFilter(f.key)"
          >
            <Icon :icon="f.icon" class="st-filter-ic" inline width="13" />
            <span>{{ f.label }}</span>
            <span class="st-filter-count">{{ f.count }}</span>
          </button>
          <button
            class="st-filter-chip st-enterprise-chip"
            :class="[{active: enterpriseOnly}, 'tone-enterprise']"
            @click="toggleEnterpriseOnly"
          >
            <Icon icon="mdi:office-building" class="st-filter-ic" inline width="13" />
            <span>仅企业级</span>
            <span class="st-filter-count">{{ enterpriseTotal }}</span>
          </button>
        </div>

        <div class="st-tool-right">
          <div class="st-search">
            <Icon icon="mdi:magnify" class="st-search-ic" />
            <input v-model="searchKeyword"
                   placeholder="搜索任务标题 / 企业 / 要求关键词…"
                   class="st-search-input" />
            <button v-if="searchKeyword"
                    @click="searchKeyword = ''"
                    class="st-search-clear"
                    title="清空搜索">
              <Icon icon="mdi:close" />
            </button>
          </div>
          <select v-model="sortKey" class="st-sort">
            <option value="priority">智能排序（优先待提交+截止近）</option>
            <option value="deadline_asc">截止期 · 近→远</option>
            <option value="deadline_desc">截止期 · 远→近</option>
            <option value="created_desc">发布日期 · 新→旧</option>
            <option value="score_desc">满分 · 高→低</option>
          </select>
        </div>
      </section>

      <!-- ============== 加载态 ============== -->
      <div v-if="loading" class="st-loading reveal reveal-3">
        <div class="st-loading-ring"></div>
        <div class="st-loading-text">
          <span class="st-loading-title">正在调阅任务台账…</span>
          <span class="st-loading-sub">FETCHING DISPATCHES FROM ACADEMY · 3s 内完成</span>
        </div>
      </div>

      <!-- ============== 任务卡网格 ============== -->
      <section v-else-if="displayTasks.length > 0" class="st-grid reveal reveal-3">
        <article
          v-for="(task, idx) in displayTasks"
          :key="task.id"
          class="st-card"
          :class="{
            'is-enterprise': !!task.is_enterprise_project,
            'is-submitted': !!task.submitted,
            'is-urgent': daysLeft(task) >= 0 && daysLeft(task) <= 3 && !task.submitted,
            'is-overdue': daysLeft(task) < 0 && !task.submitted
          }"
          :style="{'--stagger-i': idx}"
        >
          <!-- 左上：编号 + 企业印章 -->
          <div class="st-card-head">
            <div class="st-card-no">
              № {{ String(task.id).padStart(4, '0') }}
            </div>
            <span v-if="task.is_enterprise_project"
                  class="st-ep-chip">
              <Icon icon="mdi:stamper" inline width="10" />
              ENTERPRISE
            </span>
          </div>

          <!-- 右上：邮票形状状态标 -->
          <div class="st-status-stamp"
               :class="task.submitted ? 'status-done' : (daysLeft(task) < 0 ? 'status-overdue' : 'status-pending')">
            <div class="st-status-teeth" aria-hidden="true"></div>
            <div class="st-status-icon">
              <Icon :icon="task.submitted ? 'mdi:check-decagram' : (daysLeft(task) < 0 ? 'mdi:alert-octagon' : 'mdi:clock-outline')" />
            </div>
            <div class="st-status-text">
              {{ task.submitted ? 'RECEIVED' : (daysLeft(task) < 0 ? 'OVERDUE' : 'PENDING') }}
            </div>
            <div class="st-status-cn">
              {{ task.submitted ? '已提交' : (daysLeft(task) < 0 ? '已逾期' : '待提交') }}
            </div>
          </div>

          <!-- 企业级：企业 + 岗位信息条 -->
          <div v-if="task.enterprise_label" class="st-ep-row">
            <div class="st-ep-ic">
              <Icon icon="mdi:domain" />
            </div>
            <div class="st-ep-text">
              <div class="st-ep-name">{{ task.enterprise_label.enterprise_name }}</div>
              <div class="st-ep-job">
                <Icon icon="mdi:briefcase" inline width="11" class="mr-1" />
                {{ task.enterprise_label.job_title }}
              </div>
            </div>
            <div class="st-ep-badge">企业项目实训</div>
          </div>

          <!-- 标题 -->
          <h3 class="st-card-title">
            {{ task.title }}
          </h3>

          <!-- 摘要 -->
          <p class="st-card-summary">
            {{ task.requirements || '（教师未补充任务要求，请按课堂说明完成。）' }}
          </p>

          <!-- 评分维度胶囊 -->
          <div v-if="task.criteria?.length" class="st-crits">
            <span v-for="(c, i) in parseCrits(task.criteria)"
                  :key="i"
                  class="st-crit-chip"
                  :class="`tone-${criteriaTone(i)}`">
              <Icon :icon="criteriaIconFor(c)" inline width="11" class="mr-1" />
              {{ c }}
            </span>
          </div>

          <!-- 分隔装饰线 -->
          <div class="st-card-divider" aria-hidden="true">
            <span class="st-card-divider-diamond">❖</span>
          </div>

          <!-- Meta 三栏 -->
          <div class="st-card-meta">
            <div class="st-meta-item">
              <div class="st-meta-label">满分</div>
              <div class="st-meta-value score">
                <Icon icon="mdi:trophy-outline" inline width="13" class="mr-1" />
                {{ task.total_score || 100 }}
              </div>
            </div>
            <div class="st-meta-item">
              <div class="st-meta-label">截止日</div>
              <div class="st-meta-value date">
                <Icon icon="mdi:calendar-month-outline" inline width="13" class="mr-1" />
                {{ fmtDeadline(task.deadline) }}
              </div>
            </div>
          </div>

          <!-- 剩余天数进度条 -->
          <div v-if="task.deadline && !task.submitted" class="st-progress">
            <div class="st-progress-bar"
                 :style="{width: clampPct(progressPct(task)) + '%'}"
                 :class="{'is-danger': daysLeft(task) < 0, 'is-warn': daysLeft(task) >= 0 && daysLeft(task) <= 3}"></div>
          </div>

          <!-- 按钮组 -->
          <div class="st-card-actions">
            <button v-if="task.template_path"
                    @click="downloadTemplate(task)"
                    class="st-btn st-btn-ghost">
              <Icon icon="mdi:download-outline" inline width="13" class="mr-1.5" />
              下载模板
            </button>
            <button
              @click="goSubmit(task)"
              class="st-btn"
              :class="task.submitted ? 'st-btn-cobalt' : 'st-btn-seal'"
            >
              <Icon :icon="task.submitted ? 'mdi:refresh-variant' : 'mdi:send-check-outline'" inline width="13" class="mr-1.5" />
              {{ task.submitted ? '重新提交' : '🔥 投递成果 · 去提交' }}
            </button>
          </div>
        </article>
      </section>

      <!-- ============== 空态 ============== -->
      <section v-else class="st-empty reveal reveal-3">
        <div class="st-empty-art">
          <div class="st-empty-stamp-ring"></div>
          <Icon icon="mdi:empty-folder-outline" class="st-empty-ic" />
        </div>
        <h3 class="st-empty-title">
          {{ emptyTitle }}
        </h3>
        <p class="st-empty-sub">
          {{ emptySubtitle }}
        </p>
        <button v-if="activeFilter !== 'all' || enterpriseOnly || searchKeyword"
                @click="resetFilters"
                class="btn-mag btn-mag-ghost !px-6 !py-3 text-[13px]">
          <Icon icon="mdi:refresh" inline width="13" class="mr-1.5" />
          重置筛选 · 查看全部
        </button>
      </section>

      <!-- ============== 页脚信息 ============== -->
      <footer class="st-foot reveal reveal-4">
        <div class="st-foot-left">
          <Icon icon="mdi:information-outline" class="st-foot-ic" />
          共 {{ tasks.length }} 项任务 · 当前显示 {{ displayTasks.length }} 项
          <span v-if="pendingCount > 0">
            · 其中 <span class="st-foot-k">{{ pendingCount }}</span> 项等待你的投递
          </span>
        </div>
        <div class="st-foot-right">
          <span class="st-foot-divider">·</span>
          <span>知训云 · ZHI XUN YUN ACADEMY</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
// 【核心 API 调用与业务逻辑完全保留，仅做展示层增量：辅助函数 / 状态 / 筛选排序】
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const tasks = ref<any[]>([])

/* -------- 筛选/搜索/排序 -------- */
const activeFilter = ref<'all' | 'pending' | 'submitted'>('all')
const enterpriseOnly = ref(false)
const searchKeyword = ref('')
const sortKey = ref<'priority' | 'deadline_asc' | 'deadline_desc' | 'created_desc' | 'score_desc'>('priority')

const pendingCount = computed(() => tasks.value.filter(t => !t.submitted).length)
const submittedCount = computed(() => tasks.value.filter(t => t.submitted).length)
const enterpriseTotal = computed(() => tasks.value.filter(t => !!t.is_enterprise_project).length)

/* 顶部筛选 chip 的 label / count / icon / 色调 */
const filters = computed(() => [
  { key: 'all' as const,       label: '全部任务', count: tasks.value.length,               icon: 'mdi:format-list-text', tone: 'tone-all' },
  { key: 'pending' as const,   label: '待提交',   count: pendingCount.value,                icon: 'mdi:clock-fast',     tone: 'tone-pending' },
  { key: 'submitted' as const, label: '已提交',   count: submittedCount.value,              icon: 'mdi:check-circle-2', tone: 'tone-done' },
])

function setFilter(k: 'all' | 'pending' | 'submitted') {
  activeFilter.value = k
}
function toggleEnterpriseOnly() {
  enterpriseOnly.value = !enterpriseOnly.value
}
function resetFilters() {
  activeFilter.value = 'all'
  enterpriseOnly.value = false
  searchKeyword.value = ''
}

/* -------- 筛选 + 搜索 + 排序后的最终任务列表 -------- */
const displayTasks = computed(() => {
  let list = [...tasks.value]

  // 状态筛选
  if (activeFilter.value === 'pending')   list = list.filter(t => !t.submitted)
  if (activeFilter.value === 'submitted') list = list.filter(t =>  t.submitted)

  // 企业级筛选
  if (enterpriseOnly.value) list = list.filter(t => !!t.is_enterprise_project)

  // 关键字搜索
  const kw = (searchKeyword.value || '').trim().toLowerCase()
  if (kw) {
    list = list.filter(t => {
      const blobs = [
        t.title || '',
        t.requirements || '',
        t.enterprise_label?.enterprise_name || '',
        t.enterprise_label?.job_title || '',
        t.criteria || ''
      ].join(' ').toLowerCase()
      return blobs.includes(kw)
    })
  }

  // 排序
  const now = Date.now()
  const dlMs = (t: any) => t.deadline ? new Date(t.deadline).getTime() : Number.MAX_SAFE_INTEGER

  switch (sortKey.value) {
    case 'deadline_asc':   list.sort((a, b) => dlMs(a) - dlMs(b)); break
    case 'deadline_desc':  list.sort((a, b) => dlMs(b) - dlMs(a)); break
    case 'created_desc':   list.sort((a, b) => (b.id ?? 0) - (a.id ?? 0)); break
    case 'score_desc':     list.sort((a, b) => (Number(b.total_score) || 100) - (Number(a.total_score) || 100)); break
    case 'priority':
    default:
      // 智能排序：① 未提交在前；② 截止更近在前；③ 逾期再提前；④ id倒序作为tiebreaker
      list.sort((a, b) => {
        const sa = a.submitted ? 1 : 0
        const sb = b.submitted ? 1 : 0
        if (sa !== sb) return sa - sb
        const oa = daysLeft(a) < 0 ? -1 : 0
        const ob = daysLeft(b) < 0 ? -1 : 0
        if (oa !== ob) return oa - ob
        const d = dlMs(a) - dlMs(b)
        if (d !== 0) return d
        return (b.id ?? 0) - (a.id ?? 0)
      })
  }

  return list
})

/* 空态文案 */
const emptyTitle = computed(() => {
  if (tasks.value.length === 0) return '尚未派发任何任务'
  if (searchKeyword.value) return '没有匹配搜索关键字的任务'
  if (enterpriseOnly.value && activeFilter.value === 'all') return '当前没有企业级项目实训'
  if (enterpriseOnly.value && activeFilter.value === 'pending') return '当前没有待提交的企业级任务'
  if (enterpriseOnly.value && activeFilter.value === 'submitted') return '当前没有已提交的企业级任务'
  if (activeFilter.value === 'pending') return '所有任务均已完成投递'
  if (activeFilter.value === 'submitted') return '暂无已提交记录，快去投递第一项成果吧'
  return '当前筛选没有任务'
})
const emptySubtitle = computed(() => {
  if (tasks.value.length === 0) return '请联系授课教师加入对应班级，或稍后刷新页面等待教师派发。'
  if (searchKeyword.value || enterpriseOnly.value || activeFilter.value !== 'all') return '试着清除筛选条件，或调整关键字后重试。'
  return '暂无任务，请联系教师或稍后刷新。'
})

/* -------- 纯展示辅助函数 -------- */
const CRIT_TONES = ['cobalt', 'jade', 'amber', 'violet', 'seal', 'ink'] as const
function parseCrits(s: string): string[] {
  return (s || '').split(',').map(x => x.trim()).filter(Boolean)
}
function criteriaTone(i: number) {
  return CRIT_TONES[i % CRIT_TONES.length]
}
function criteriaIconFor(c: string): string {
  const s = (c || '').toLowerCase()
  if (s.includes('代码') || s.includes('code') || s.includes('质量')) return 'mdi:code-tags'
  if (s.includes('功能') || s.includes('完整') || s.includes('function')) return 'mdi:check-decagram-outline'
  if (s.includes('文档') || s.includes('规范') || s.includes('doc')) return 'mdi:notebook-outline'
  if (s.includes('界面') || s.includes('ui') || s.includes('设计')) return 'mdi:palette-outline'
  if (s.includes('岗位') || s.includes('匹配')) return 'mdi:briefcase-outline'
  if (s.includes('注释') || s.includes('可读')) return 'mdi:tooltip-text-outline'
  return 'mdi:star-four-points-outline'
}
function fmtDeadline(d: any): string {
  if (!d) return '未设定'
  const s = String(d).split('T')[0]
  return s || '未设定'
}
function daysLeft(task: any): number {
  if (!task.deadline) return Number.MAX_SAFE_INTEGER
  const dl = new Date(task.deadline).getTime()
  const ms = dl - Date.now()
  return Math.floor(ms / (1000 * 60 * 60 * 24))
}
function progressPct(task: any): number {
  if (!task.deadline) return 100
  // 进度 = 已经过的时间 / (deadline - created)，没有created用id当近似
  const dl = new Date(task.deadline).getTime()
  const start = Math.max(Date.now() - 14 * 86400_000, dl - 30 * 86400_000)
  const total = Math.max(1, dl - start)
  const passed = Date.now() - start
  return Math.round(100 * passed / total)
}
function clampPct(v: number): number {
  if (!Number.isFinite(v)) return 50
  return Math.max(2, Math.min(100, v))
}
function statusText(task: any): string {
  if (task.submitted) {
    const d = daysLeft(task)
    if (!isFinite(d)) return '已投递成功'
    if (d >= 0) return `提前 ${d + 1} 天投递`
    return '已投递'
  }
  const d = daysLeft(task)
  if (!isFinite(d)) return '等待投递'
  if (d < 0)  return `已逾期 ${-d} 天`
  if (d === 0) return '今日截止！'
  if (d <= 3) return `仅剩 ${d} 天`
  return `剩余 ${d} 天`
}

/* -------- 原业务逻辑（一字未改） -------- */
onMounted(() => loadTasks())

const loadTasks = async () => {
  loading.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(`/api/tasks/pending?student_id=${user.id}`)
    if (res.data.success) tasks.value = res.data.data
  } catch {
    ElMessage.error('任务台账加载失败，请稍后重试')
  } finally { loading.value = false }
}

const goSubmit = (task: any) => {
  localStorage.setItem('current_task', JSON.stringify({
    id: task.id,
    title: task.title,
    requirements: task.requirements,
    criteria: task.criteria,
    criteria_weights: task.criteria_weights
  }))
  localStorage.setItem('current_task_criteria', task.criteria)
  router.push('/app/upload')
}

const downloadTemplate = (task: any) => {
  window.open(`/api/tasks/${task.id}/template`, '_blank')
}
</script>

<style scoped>
/* ============================================================
   Student Tasks Page · 任务台账 · 派单大厅
   美学：Editorial Magazine × Ledger × Dispatch
   ============================================================ */

/* ── 1. 页面整体与背景 ── */
.st-page {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  padding: 56px 24px 80px;
  background:
    linear-gradient(180deg, rgba(255, 246, 238, 0.85) 0%, var(--paper) 32%, var(--paper) 100%);
}

.st-glow {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  filter: blur(100px);
  opacity: 0.5;
  border-radius: 50%;
}
.st-glow-seal {
  top: -180px; right: -60px;
  width: 520px; height: 520px;
  background: radial-gradient(circle, var(--seal) 0%, transparent 65%);
}
.st-glow-jade {
  top: 25%; left: -140px;
  width: 460px; height: 460px;
  background: radial-gradient(circle, #1DB955 0%, transparent 65%);
  opacity: 0.25;
}

.st-ledger-mark {
  position: fixed;
  left: -10px; top: 40%;
  z-index: 0;
  pointer-events: none;
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 110px;
  letter-spacing: 8px;
  color: transparent;
  -webkit-text-stroke: 2px rgba(61, 90, 254, 0.06);
  transform: rotate(-90deg);
  transform-origin: left center;
  white-space: nowrap;
}

.st-inner {
  position: relative;
  z-index: 2;
  max-width: 1360px;
  margin: 0 auto;
}

/* ── 2. 入场交错揭示 ── */
.page-enter-stagger .reveal {
  opacity: 0;
  transform: translateY(18px);
  animation: st-reveal 700ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.reveal-1 { animation-delay: 40ms; }
.reveal-2 { animation-delay: 140ms; }
.reveal-3 { animation-delay: 220ms; }
.reveal-4 { animation-delay: 320ms; }

@keyframes st-reveal {
  to { opacity: 1; transform: translateY(0); }
}

/* ── 3. HERO 标题区 ── */
.st-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.95fr);
  gap: 36px;
  align-items: stretch;
  margin-bottom: 40px;
}

.st-hero-left { position: relative; }

.st-hero-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 8px 10px;
  border: 1px solid rgba(61, 90, 254, 0.32);
  background: linear-gradient(135deg, rgba(61, 90, 254, 0.1), rgba(139, 92, 246, 0.05));
  border-radius: 999px;
  margin-bottom: 22px;
}
.st-hero-chip-num {
  font-family: var(--ff-mono);
  font-weight: 700;
  font-size: 10.5px;
  letter-spacing: 2px;
  color: #fff;
  background: linear-gradient(135deg, var(--cobalt), var(--cobalt-dark));
  padding: 4px 10px;
  border-radius: 999px;
  box-shadow: 0 6px 14px -8px rgba(61, 90, 254, 0.8);
}
.st-hero-chip-text {
  font-family: var(--ff-sub);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--cobalt-dark);
}

.st-hero-title {
  font-family: var(--ff-display);
  font-size: clamp(42px, 5.6vw, 78px);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin-bottom: 18px;
  position: relative;
  display: inline-block;
}
.st-hero-sub-en {
  font-family: var(--ff-sub);
  font-size: 0.38em;
  font-weight: 600;
  letter-spacing: 6px;
  color: var(--seal);
  opacity: 0.75;
  margin-left: 14px;
  vertical-align: middle;
}

.st-hero-sub {
  font-family: var(--ff-body);
  font-size: 15.5px;
  line-height: 1.8;
  color: var(--ink-3);
  max-width: 660px;
  margin: 20px 0 0;
  font-weight: 400;
  letter-spacing: 0.005em;
}

/* HERO 右侧：4 枚数字邮票 */
.st-stamps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  align-content: center;
}
.st-stamp {
  position: relative;
  padding: 20px 14px 16px;
  border-radius: 20px;
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.35) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #fff 0%, #fdf7ed 55%, #fbeed9 100%);
  border: 1.5px solid var(--line);
  box-shadow:
    0 16px 36px -18px rgba(15, 17, 21, 0.22),
    inset 0 0 0 5px rgba(255, 255, 255, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  text-align: center;
}
.st-stamp:nth-child(1) { transform: rotate(-1.5deg); }
.st-stamp:nth-child(2) { transform: rotate(1deg); }
.st-stamp:nth-child(3) { transform: rotate(1.5deg); }
.st-stamp:nth-child(4) { transform: rotate(-1deg); }
.st-stamp:hover {
  transform: rotate(0deg) translateY(-4px) scale(1.02);
  box-shadow:
    0 24px 46px -20px rgba(15, 17, 21, 0.3),
    inset 0 0 0 5px rgba(255, 255, 255, 0.5);
}
.st-stamp.active {
  transform: rotate(0deg) translateY(-3px) scale(1.03);
  z-index: 1;
}
.st-stamp-holes {
  position: absolute;
  left: 8px; right: 8px; top: 6px; bottom: 6px;
  border: 1px dashed rgba(15, 17, 21, 0.08);
  border-radius: 14px;
  pointer-events: none;
}
.st-stamp-label {
  font-family: var(--ff-sub);
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: 0.8;
  margin-bottom: 6px;
}
.st-stamp-num {
  font-family: var(--ff-display);
  font-size: 38px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.01em;
  margin-bottom: 4px;
}
.st-stamp-foot {
  font-family: var(--ff-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2);
  letter-spacing: 0.3px;
}

.st-stamp-all .st-stamp-num       { color: var(--ink); }
.st-stamp-all.active {
  border-color: var(--ink-2);
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.45) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #fff 0%, #f0ece3 100%);
}
.st-stamp-pending .st-stamp-num   { color: var(--amber-dark); }
.st-stamp-pending.active {
  border-color: var(--amber);
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.45) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #FFFCF0 0%, #FFEFD0 100%);
}
.st-stamp-done .st-stamp-num      { color: var(--jade-dark); }
.st-stamp-done.active {
  border-color: var(--jade);
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.45) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #F2FFF6 0%, #D4F5DF 100%);
}
.st-stamp-enterprise .st-stamp-num { color: var(--seal-dark); }
.st-stamp-enterprise.active {
  border-color: var(--seal);
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.45) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #FFF4EC 0%, #FFDCC4 100%);
}

/* ── 4. 筛选 / 搜索工具条 ── */
.st-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  background: rgba(255, 253, 248, 0.85);
  backdrop-filter: blur(6px);
  border: 1px solid var(--line-soft);
  border-radius: 22px;
  margin-bottom: 28px;
  box-shadow: 0 14px 36px -24px rgba(15, 17, 21, 0.18);
}

.st-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.st-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 15px 9px 13px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line-soft);
  font-family: var(--ff-sub);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-2);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  letter-spacing: 0.2px;
}
.st-filter-chip:hover {
  transform: translateY(-2px);
  border-color: rgba(15, 17, 21, 0.2);
  box-shadow: 0 8px 18px -14px rgba(15, 17, 21, 0.3);
}
.st-filter-chip.active {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 8px 20px -12px rgba(15, 17, 21, 0.25);
}
.st-filter-ic { opacity: 0.85; }
.st-filter-count {
  font-family: var(--ff-mono);
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--paper-2);
  color: var(--ink-3);
  min-width: 20px;
  text-align: center;
}

/* 各色调 chip */
.tone-all.active {
  background: linear-gradient(135deg, #2A2F3A, #3D4554);
  border-color: #2A2F3A;
  color: #fff;
}
.tone-all.active .st-filter-count { background: rgba(255, 255, 255, 0.18); color: #fff; }

.tone-pending.active {
  background: linear-gradient(135deg, var(--amber), #E6A836);
  border-color: var(--amber);
  color: #3D2A00;
}
.tone-pending.active .st-filter-count { background: rgba(61, 42, 0, 0.15); color: #3D2A00; }

.tone-done.active {
  background: linear-gradient(135deg, var(--jade), #18A049);
  border-color: var(--jade);
  color: #fff;
}
.tone-done.active .st-filter-count { background: rgba(255, 255, 255, 0.18); color: #fff; }

.tone-enterprise.active {
  background: linear-gradient(135deg, var(--seal), var(--seal-dark));
  border-color: var(--seal);
  color: #fff;
}
.tone-enterprise.active .st-filter-count { background: rgba(255, 255, 255, 0.18); color: #fff; }

.st-enterprise-chip {
  border-color: rgba(255, 90, 31, 0.3);
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.06), rgba(255, 255, 255, 0.8));
}

.st-tool-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.st-search {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 260px;
  max-width: 360px;
}
.st-search-ic {
  position: absolute;
  left: 14px;
  color: var(--ink-3);
  font-size: 16px;
  z-index: 1;
  opacity: 0.75;
}
.st-search-input {
  width: 100%;
  padding: 10.5px 38px 10.5px 40px;
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  background: #fff;
  font-family: var(--ff-body);
  font-size: 13px;
  color: var(--ink);
  outline: none;
  transition: all 0.2s;
}
.st-search-input::placeholder { color: rgba(42, 47, 58, 0.4); }
.st-search-input:focus {
  border-color: rgba(61, 90, 254, 0.45);
  box-shadow: 0 0 0 4px rgba(61, 90, 254, 0.09);
}
.st-search-clear {
  position: absolute;
  right: 10px;
  width: 24px; height: 24px;
  border-radius: 8px;
  border: none;
  background: var(--paper-2);
  color: var(--ink-3);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.st-search-clear:hover { background: var(--seal-soft); color: var(--seal-dark); }

.st-sort {
  padding: 10.5px 14px;
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  background: #fff;
  font-family: var(--ff-sub);
  font-size: 12.5px;
  font-weight: 500;
  color: var(--ink-2);
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
  max-width: 280px;
}
.st-sort:hover { border-color: rgba(15, 17, 21, 0.2); }
.st-sort:focus {
  border-color: rgba(61, 90, 254, 0.45);
  box-shadow: 0 0 0 4px rgba(61, 90, 254, 0.09);
}

/* ── 5. 加载态 ── */
.st-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  padding: 80px 20px;
}
.st-loading-ring {
  width: 56px; height: 56px;
  border: 4px solid var(--paper-3);
  border-top-color: var(--seal);
  border-right-color: var(--cobalt);
  border-radius: 50%;
  animation: st-spin 1s linear infinite;
  flex-shrink: 0;
}
@keyframes st-spin { to { transform: rotate(360deg); } }
.st-loading-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.st-loading-title {
  font-family: var(--ff-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
}
.st-loading-sub {
  font-family: var(--ff-sub);
  font-size: 11px;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: 0.8;
}

/* ── 6. 任务卡网格 ── */
.st-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
  margin-bottom: 32px;
}

.st-card {
  --stagger-i: 0;
  position: relative;
  padding: 22px 22px 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, #FFFCF5 100%);
  border: 1px solid var(--line);
  border-radius: 24px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 18px 42px -26px rgba(15, 17, 21, 0.28);
  transition: all 0.38s cubic-bezier(0.34, 1.56, 0.64, 1);
  opacity: 0;
  transform: translateY(16px) scale(0.98);
  animation: st-card-in 620ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(120ms + var(--stagger-i) * 55ms);
  overflow: hidden;
}
@keyframes st-card-in {
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.st-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; right: 0;
  height: 4px;
  background: linear-gradient(90deg,
    rgba(255, 90, 31, 0.0) 0%,
    rgba(255, 90, 31, 0.35) 30%,
    rgba(61, 90, 254, 0.45) 70%,
    rgba(61, 90, 254, 0.0) 100%);
  opacity: 0;
  transition: opacity 0.35s ease;
}
.st-card:hover {
  transform: translateY(-6px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 32px 56px -28px rgba(15, 17, 21, 0.32);
  border-color: rgba(255, 90, 31, 0.3);
}
.st-card:hover::before { opacity: 1; }

/* 企业任务特殊样式 */
.st-card.is-enterprise {
  background:
    linear-gradient(180deg, #FFFCF7 0%, #FFF3E8 100%);
  border-color: rgba(255, 90, 31, 0.2);
}
.st-card.is-enterprise::after {
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 200px; height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 90, 31, 0.1) 0%, transparent 65%);
  pointer-events: none;
}

/* 已提交任务 */
.st-card.is-submitted {
  background:
    linear-gradient(180deg, #FBFFF8 0%, #F0F8EB 100%);
  border-color: rgba(29, 185, 85, 0.22);
}

/* 紧急任务（≤3天） */
.st-card.is-urgent {
  border-color: rgba(244, 183, 64, 0.45);
  animation: st-card-in 620ms cubic-bezier(0.22, 1, 0.36, 1) forwards,
             st-urgent-pulse 3s ease-in-out infinite;
  animation-delay: calc(120ms + var(--stagger-i) * 55ms), 2s;
}
@keyframes st-urgent-pulse {
  0%, 100% { box-shadow: 0 18px 42px -26px rgba(15, 17, 21, 0.28), 0 0 0 0 rgba(244, 183, 64, 0); }
  50%      { box-shadow: 0 18px 42px -26px rgba(15, 17, 21, 0.28), 0 0 0 6px rgba(244, 183, 64, 0.12); }
}

/* 逾期任务 */
.st-card.is-overdue {
  background:
    linear-gradient(180deg, #FFF5F4 0%, #FFE5E2 100%);
  border-color: rgba(230, 57, 70, 0.35);
}

/* ── 7. 任务卡内部：头部（编号+企业印章） ── */
.st-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
}
.st-card-no {
  font-family: var(--ff-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--ink-3);
  padding: 4px 10px;
  background: var(--paper-2);
  border-radius: 8px;
}
.st-ep-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.12), rgba(255, 140, 80, 0.06));
  border: 1px solid rgba(255, 90, 31, 0.28);
  font-family: var(--ff-sub);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--seal-dark);
}

/* 邮票状态标（右上角） */
.st-status-stamp {
  position: absolute;
  top: 14px; right: 14px;
  width: 74px;
  padding: 8px 6px 6px;
  border-radius: 14px;
  text-align: center;
  z-index: 2;
  transition: all 0.3s ease;
}
.st-status-teeth {
  position: absolute;
  left: 2px; right: 2px; top: 2px; bottom: 2px;
  border: 1px dashed;
  border-radius: 12px;
  opacity: 0.5;
  pointer-events: none;
}
.st-status-icon {
  font-size: 18px;
  margin-bottom: 2px;
  z-index: 1;
  position: relative;
}
.st-status-text {
  font-family: var(--ff-sub);
  font-size: 8.5px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  line-height: 1;
  margin-bottom: 2px;
  z-index: 1;
  position: relative;
}
.st-status-cn {
  font-family: var(--ff-body);
  font-size: 11.5px;
  font-weight: 700;
  line-height: 1;
  z-index: 1;
  position: relative;
}

.st-status-stamp.status-pending {
  background: linear-gradient(160deg, #FFFCF0 0%, #FFEBC7 100%);
  color: var(--amber-dark);
  border: 1.5px solid var(--amber);
  transform: rotate(6deg);
}
.st-status-stamp.status-pending .st-status-teeth { border-color: var(--amber); }
.st-card:hover .st-status-stamp.status-pending { transform: rotate(0deg) scale(1.04); }

.st-status-stamp.status-done {
  background: linear-gradient(160deg, #F0FFF5 0%, #CFF3DC 100%);
  color: var(--jade-dark);
  border: 1.5px solid var(--jade);
  transform: rotate(-4deg);
}
.st-status-stamp.status-done .st-status-teeth { border-color: var(--jade); }
.st-card:hover .st-status-stamp.status-done { transform: rotate(0deg) scale(1.04); }

.st-status-stamp.status-overdue {
  background: linear-gradient(160deg, #FFF3F1 0%, #FFD4CE 100%);
  color: #C92A1B;
  border: 1.5px solid #E63946;
  transform: rotate(4deg);
}
.st-status-stamp.status-overdue .st-status-teeth { border-color: #E63946; }
.st-card:hover .st-status-stamp.status-overdue { transform: rotate(0deg) scale(1.04); }

/* ── 8. 企业 + 岗位信息条 ── */
.st-ep-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 13px;
  margin: 8px 0 14px;
  margin-top: 42px; /* 给右上角邮票留位置 */
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.08), rgba(255, 255, 255, 0.7));
  border: 1px solid rgba(255, 90, 31, 0.22);
  border-radius: 14px;
  position: relative;
  z-index: 1;
}
.st-ep-ic {
  width: 38px; height: 38px;
  border-radius: 11px;
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.15), rgba(255, 90, 31, 0.06));
  color: var(--seal-dark);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.st-ep-text {
  min-width: 0;
  flex: 1;
}
.st-ep-name {
  font-family: var(--ff-body);
  font-size: 13.5px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.st-ep-job {
  font-size: 11.5px;
  color: var(--ink-3);
  margin-top: 3px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.st-ep-badge {
  font-family: var(--ff-sub);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 4px 9px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--seal), var(--seal-dark));
  color: #fff;
  flex-shrink: 0;
}

/* 非企业任务：给右上角邮票留同样的顶部间距 */
.st-card:not(.is-enterprise) .st-card-title {
  margin-top: 42px;
}

/* ── 9. 任务内容：标题、摘要、维度胶囊 ── */
.st-card-title {
  font-family: var(--ff-display);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.005em;
  color: var(--ink);
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
  padding-right: 86px; /* 避让右上角状态标 */
}

.st-card-summary {
  font-family: var(--ff-body);
  font-size: 13px;
  line-height: 1.72;
  color: var(--ink-3);
  margin: 0 0 14px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.st-crits {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 14px;
  position: relative;
  z-index: 1;
}
.st-crit-chip {
  display: inline-flex;
  align-items: center;
  padding: 4.5px 10px 4.5px 8px;
  border-radius: 9px;
  font-family: var(--ff-sub);
  font-size: 11px;
  font-weight: 600;
  border: 1px solid;
  background: #fff;
  transition: all 0.2s ease;
}
.st-crit-chip:hover { transform: translateY(-1px); }

.tone-cobalt {
  color: var(--cobalt-dark);
  border-color: rgba(61, 90, 254, 0.28);
  background: rgba(61, 90, 254, 0.06);
}
.tone-jade {
  color: var(--jade-dark);
  border-color: rgba(29, 185, 85, 0.28);
  background: rgba(29, 185, 85, 0.07);
}
.tone-amber {
  color: var(--amber-dark);
  border-color: rgba(244, 183, 64, 0.38);
  background: rgba(244, 183, 64, 0.1);
}
.tone-violet {
  color: #6D28D9;
  border-color: rgba(139, 92, 246, 0.28);
  background: rgba(139, 92, 246, 0.07);
}
.tone-seal {
  color: var(--seal-dark);
  border-color: rgba(255, 90, 31, 0.28);
  background: rgba(255, 90, 31, 0.07);
}
.tone-ink {
  color: var(--ink-2);
  border-color: rgba(42, 47, 58, 0.2);
  background: rgba(42, 47, 58, 0.05);
}

/* 分隔装饰线 */
.st-card-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: var(--ink-3);
  opacity: 0.5;
  margin: 4px 0 14px;
  position: relative;
  z-index: 1;
}
.st-card-divider::before,
.st-card-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--line));
  margin: 0 12px;
}
.st-card-divider::after { transform: scaleX(-1); }
.st-card-divider-diamond { color: var(--seal); opacity: 0.7; }

/* ── 10. Meta 三栏 ── */
.st-card-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 14px;
  position: relative;
  z-index: 1;
}
.st-meta-item {
  padding: 10px 10px 9px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  text-align: center;
  transition: all 0.2s ease;
}
.st-meta-item:hover {
  border-color: rgba(15, 17, 21, 0.18);
  transform: translateY(-1px);
}
.st-meta-label {
  font-family: var(--ff-sub);
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: 0.85;
  margin-bottom: 5px;
}
.st-meta-value {
  font-family: var(--ff-body);
  font-size: 13px;
  font-weight: 700;
  color: var(--ink-2);
  line-height: 1.2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}
.st-meta-value.score { color: var(--seal-dark); }
.st-meta-value.date  { color: var(--cobalt-dark); }
.st-meta-value.val-urgent {
  color: var(--amber-dark);
  animation: st-blink 1.8s ease-in-out infinite;
}
.st-meta-value.val-overdue {
  color: #C92A1B;
  background: linear-gradient(135deg, rgba(230, 57, 70, 0.1), rgba(230, 57, 70, 0.05));
  border-radius: 8px;
  padding: 3px 2px;
  margin: -3px -2px;
}
.st-meta-value.val-done { color: var(--jade-dark); }
@keyframes st-blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.65; }
}

/* ── 11. 剩余天数进度条 ── */
.st-progress {
  height: 6px;
  background: var(--paper-2);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}
.st-progress-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--cobalt), #6FC3FF);
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}
.st-progress-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%);
  animation: st-shine 2.4s ease-in-out infinite;
}
@keyframes st-shine {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.st-progress-bar.is-warn {
  background: linear-gradient(90deg, var(--amber), #FFC75A);
}
.st-progress-bar.is-danger {
  background: linear-gradient(90deg, #E63946, #FF6B6B);
}

/* ── 12. 按钮组 ── */
.st-card-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}
.st-btn {
  flex: 1;
  min-width: 120px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  border-radius: 14px;
  font-family: var(--ff-sub);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.2px;
  cursor: pointer;
  border: 1.5px solid;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.st-btn-ghost {
  background: #fff;
  color: var(--ink-2);
  border-color: var(--line);
}
.st-btn-ghost:hover {
  background: var(--paper-2);
  border-color: rgba(15, 17, 21, 0.22);
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -14px rgba(15, 17, 21, 0.3);
}

.st-btn-seal {
  background: linear-gradient(135deg, var(--seal) 0%, var(--seal-dark) 55%, #A1280A 100%);
  color: #fff;
  border-color: var(--seal);
  box-shadow:
    0 12px 28px -14px rgba(255, 90, 31, 0.75),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.st-btn-seal::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 15% 20%, rgba(255, 255, 255, 0.22), transparent 45%);
  pointer-events: none;
}
.st-btn-seal:hover {
  transform: translateY(-3px);
  box-shadow:
    0 18px 38px -16px rgba(255, 90, 31, 0.85),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.st-btn-seal:active { transform: translateY(1px); }

.st-btn-cobalt {
  background: linear-gradient(135deg, var(--cobalt) 0%, var(--cobalt-dark) 55%, #0D1F85 100%);
  color: #fff;
  border-color: var(--cobalt);
  box-shadow:
    0 12px 28px -14px rgba(61, 90, 254, 0.75),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.st-btn-cobalt::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 15% 20%, rgba(255, 255, 255, 0.22), transparent 45%);
  pointer-events: none;
}
.st-btn-cobalt:hover {
  transform: translateY(-3px);
  box-shadow:
    0 18px 38px -16px rgba(61, 90, 254, 0.85),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.st-btn-cobalt:active { transform: translateY(1px); }

/* ── 13. 空态 ── */
.st-empty {
  padding: 80px 24px 60px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.st-empty-art {
  position: relative;
  width: 140px; height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.st-empty-stamp-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px dashed;
  border-color: rgba(255, 90, 31, 0.25) rgba(61, 90, 254, 0.2) rgba(29, 185, 85, 0.22) rgba(244, 183, 64, 0.3);
  animation: st-spin 28s linear infinite;
}
.st-empty-ic {
  font-size: 64px;
  color: var(--ink-3);
  opacity: 0.6;
  z-index: 1;
}
.st-empty-title {
  font-family: var(--ff-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.005em;
}
.st-empty-sub {
  font-family: var(--ff-body);
  font-size: 14px;
  line-height: 1.7;
  color: var(--ink-3);
  max-width: 480px;
  margin-bottom: 10px;
}

/* ── 14. 页脚 ── */
.st-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  background: rgba(255, 253, 248, 0.75);
  backdrop-filter: blur(4px);
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  font-family: var(--ff-sub);
  font-size: 12px;
  color: var(--ink-3);
  font-weight: 500;
}
.st-foot-left, .st-foot-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.st-foot-ic { color: var(--cobalt); font-size: 15px; opacity: 0.85; }
.st-foot-k {
  font-family: var(--ff-mono);
  font-weight: 700;
  color: var(--seal-dark);
  padding: 1px 6px;
  border-radius: 6px;
  background: var(--seal-soft);
}
.st-foot-divider { opacity: 0.5; margin: 0 2px; }

/* ── 15. 响应式 ── */
@media (max-width: 1280px) {
  .st-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 1100px) {
  .st-hero { grid-template-columns: 1fr; gap: 26px; }
  .st-stamps {
    grid-template-columns: repeat(4, 1fr);
    order: -1;
  }
  .st-stamp:nth-child(n) { transform: rotate(0deg); }
}

@media (max-width: 860px) {
  .st-page { padding: 32px 16px 60px; }
  .st-hero { gap: 22px; margin-bottom: 28px; }
  .st-hero-title { font-size: 46px; }
  .st-stamps { grid-template-columns: repeat(2, 1fr); }
  .st-toolbar { padding: 16px; gap: 14px; }
  .st-tool-right { width: 100%; }
  .st-search { flex: 1; min-width: 0; max-width: none; }
  .st-sort { flex: 1; max-width: none; }
  .st-grid { grid-template-columns: 1fr; gap: 18px; margin-bottom: 24px; }
  .st-card { padding: 20px 18px 18px; }
  .st-foot { padding: 15px 18px; font-size: 11.5px; }
}

@media (max-width: 560px) {
  .st-hero-title { font-size: 38px; }
  .st-hero-sub-en { display: block; margin: 8px 0 0; font-size: 12px; letter-spacing: 4px; }
  .st-ledger-mark { display: none; }
  .st-stamp { padding: 16px 10px 12px; }
  .st-stamp-num { font-size: 30px; }
  .st-filter-row { width: 100%; }
  .st-filter-chip { flex: 1; justify-content: center; min-width: 0; }
  .st-card-meta { grid-template-columns: 1fr; gap: 8px; }
  .st-meta-item { text-align: left; padding: 9px 12px; }
  .st-meta-value { justify-content: flex-start; }
  .st-card-actions { flex-direction: column; }
  .st-btn { width: 100%; }
  .st-status-stamp { width: 66px; padding: 6px 4px 5px; }
  .st-status-icon { font-size: 16px; }
  .st-status-cn { font-size: 11px; }
  .st-ep-row { flex-wrap: wrap; }
  .st-ep-badge { width: 100%; text-align: center; }
}
</style>