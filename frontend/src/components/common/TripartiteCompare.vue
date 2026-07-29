<template>
  <div class="tripartite page-enter">
    <!-- ══════════ 顶部：三方总分卡（三张并排，像成绩单印章戳） ══════════ -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
      <div
        v-for="p in displayParties()"
        :key="p.role"
        class="card-mag relative overflow-hidden group"
      >
        <!-- 左上角 ROLE CHIP -->
        <div class="absolute top-5 right-5 flex items-center gap-2">
          <span class="section-label !tracking-[0.18em] !text-[11px] !py-1.5" :class="roleChipClass(p.role)">
            {{ partyRoleLabel(p.role) }}
          </span>
        </div>
        <div class="flex items-start gap-4 mb-5">
          <div class="w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm flex-shrink-0"
               :class="roleIconWrap(p.role)">
            <Icon :icon="partyIcon(p.role)" class="text-3xl" :class="roleIconClass(p.role)" />
          </div>
          <div>
            <div class="text-[13px] font-medium text-ink-4 mb-1 font-sub tracking-wide">
              {{ p.label || partyDefaultLabel(p.role) }}
            </div>
            <div class="font-display text-[13px] uppercase tracking-[0.22em] text-ink-3">
              SCORE · EVAL
            </div>
          </div>
        </div>
        <!-- 分数大数字 -->
        <div class="flex items-end gap-3">
          <div class="font-display text-6xl font-black leading-none tracking-tight"
               :class="scoreClass(p.total)">
            {{ fmtScore(p.total) }}
            <span class="text-2xl font-semibold opacity-60 align-baseline">/100</span>
          </div>
          <div class="pb-2">
            <span class="chip-mag" :class="gradeChipClass(p.total)">
              {{ gradeOf(p.total) }}
            </span>
          </div>
        </div>
        <div v-if="p.comment" class="mt-5 pt-5 border-t border-line/70">
          <div class="text-[11px] font-sub uppercase tracking-[0.2em] text-ink-4 mb-2">
            — 评语总评 · comment
          </div>
          <p class="font-body text-ink-2 text-[15px] leading-[1.75] line-clamp-3">
            {{ p.comment }}
          </p>
        </div>
        <!-- 装饰角标 -->
        <div class="absolute -bottom-10 -right-10 w-40 h-40 rounded-full opacity-[.07] pointer-events-none"
             :class="roleGlowClass(p.role)"></div>
      </div>
    </div>

    <!-- ══════════ 一致性概览条（带印章红警示徽章） ══════════ -->
    <div v-if="summary" class="card-mag mb-8 flex flex-col md:flex-row md:items-center gap-5 md:gap-8">
      <div class="flex items-center gap-4 md:pr-8 md:border-r md:border-line">
        <div class="relative w-24 h-24 flex-shrink-0">
          <!-- 印章圆环 -->
          <svg viewBox="0 0 100 100" class="w-full h-full animate-[spin_18s_linear_infinite]">
            <defs>
              <path id="sealCircle" d="M 50,50 m -42,0 a 42,42 0 1,1 84,0 a 42,42 0 1,1 -84,0" />
            </defs>
            <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" stroke-width="1.5"
                    :class="summary.needs_review ? 'text-seal' : 'text-jade'" opacity=".35" />
            <text :fill="summary.needs_review ? '#FF5A1F' : '#11A367'" font-size="8"
                  font-family="JetBrains Mono, ui-monospace, monospace" letter-spacing="2">
              <textPath href="#sealCircle">
                CONFIDENTIAL · 三方评价对标 · {{ summary.needs_review ? 'NEEDS REVIEW · 建议复核' : 'CONSISTENT · 评价一致' }} · ZHI·XUN·YUN · 
              </textPath>
            </text>
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <div class="font-display text-3xl font-black leading-none"
                 :class="summary.needs_review ? 'text-seal' : 'text-jade'">
              {{ Math.round((summary.consistency_index ?? 0) * 100) }}
            </div>
            <div class="mt-1 text-[10px] font-sub uppercase tracking-[0.2em] text-ink-4">
              consistency
            </div>
          </div>
        </div>
        <div class="min-w-0">
          <div class="section-label !mb-2">OVERVIEW · 一致性指数</div>
          <h4 class="font-display text-2xl font-bold text-ink tracking-tight mb-1">
            {{ summary.needs_review ? '发现差异点，建议人工复核' : '三方评价高度一致' }}
          </h4>
          <p class="font-body text-ink-4 text-[14.5px]">
            综合分差 {{ summary.score_spread }} 分；
            最大差异维度：
            <span class="font-semibold text-ink-2">
              {{ summary.max_difference_dimension || '—' }}
            </span>
            <span v-if="summary.max_difference_dimension" class="ml-1 text-seal-dark font-bold">
              （{{ summary.max_difference }} 分差）
            </span>
          </p>
        </div>
      </div>
      <div class="grid grid-cols-3 gap-4 flex-1 min-w-0">
        <div class="p-4 rounded-xl bg-paper-2/60 border border-line/70">
          <div class="text-[11px] font-sub uppercase tracking-[0.18em] text-ink-4 mb-2">三方总分差</div>
          <div class="font-display text-2xl font-black text-ink">
            {{ summary.score_spread }}
            <span class="text-sm font-medium text-ink-4 ml-1">/40</span>
          </div>
        </div>
        <div class="p-4 rounded-xl bg-paper-2/60 border border-line/70">
          <div class="text-[11px] font-sub uppercase tracking-[0.18em] text-ink-4 mb-2">最大维度差</div>
          <div class="font-display text-2xl font-black"
               :class="summary.max_difference >= 20 ? 'text-seal' : (summary.max_difference >= 10 ? 'text-amber' : 'text-jade')">
            {{ summary.max_difference }}
            <span class="text-sm font-medium text-ink-4 ml-1">pts</span>
          </div>
        </div>
        <div class="p-4 rounded-xl bg-paper-2/60 border border-line/70">
          <div class="text-[11px] font-sub uppercase tracking-[0.18em] text-ink-4 mb-2">建议动作</div>
          <div class="font-display text-lg font-bold mt-2">
            <span v-if="summary.needs_review" class="text-seal-dark">⚠ 复核</span>
            <span v-else class="text-jade-dark">✓ 归档</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════ 维度对标明细（三列并排 + 差异≥15淡红底+⚠徽章） ══════════ -->
    <div class="card-mag overflow-hidden">
      <!-- section header -->
      <div class="px-8 py-5 border-b border-line/80 flex items-center justify-between flex-wrap gap-3">
        <div>
          <div class="section-label !mb-1.5">DIMENSION · 维度对标表</div>
          <h4 class="font-display text-xl font-bold text-ink tracking-tight">
            三方评分 · 逐维度差异
          </h4>
        </div>
        <div class="flex items-center gap-3 text-[12px]">
          <span class="chip-mag !text-jade-dark !bg-jade/10 !border-jade/30">
            ● 一致（≤10）
          </span>
          <span class="chip-mag !text-amber-dark !bg-amber/10 !border-amber/30">
            ● 留意（10~20）
          </span>
          <span class="chip-mag !text-seal-dark !bg-seal/10 !border-seal/30">
            ●⚠ 建议复核（≥20）
          </span>
        </div>
      </div>

      <!-- table head -->
      <div class="hidden md:grid grid-cols-12 gap-0 px-8 py-3 bg-paper-2/60 border-b border-line/60
                  text-[11.5px] font-sub uppercase tracking-[0.16em] text-ink-4">
        <div class="col-span-4">维度 · Dimension</div>
        <div class="col-span-2 text-center">AI 自动评价</div>
        <div class="col-span-2 text-center">教师复评</div>
        <div class="col-span-2 text-center">企业终评</div>
        <div class="col-span-2 text-center pr-2">分差 · 状态</div>
      </div>

      <!-- rows -->
      <div v-for="(row, idx) in dimensionBreakdown" :key="row.name + idx"
           class="grid grid-cols-1 md:grid-cols-12 gap-3 md:gap-0 px-8 py-5 border-b border-line/40
                  transition-colors duration-200 group"
           :class="{
             'bg-seal/[0.05] hover:bg-seal/[0.08]': row.flag === 'warning',
             'bg-amber/[0.05] hover:bg-amber/[0.08]': row.flag === 'info',
             'hover:bg-paper-2/50': row.flag === 'ok',
           }">
        <!-- name + 图标 -->
        <div class="md:col-span-4 flex items-center gap-4 min-w-0">
          <div class="relative flex-shrink-0">
            <div class="w-11 h-11 rounded-xl flex items-center justify-center font-display text-lg font-black"
                 :class="row.flag === 'warning'
                   ? 'bg-seal/15 text-seal-dark'
                   : (row.flag === 'info' ? 'bg-amber/15 text-amber-dark' : 'bg-jade/15 text-jade-dark')">
              {{ String(idx + 1).padStart(2, '0') }}
            </div>
            <div v-if="row.flag === 'warning'"
                 class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-seal text-white
                        flex items-center justify-center text-[11px] shadow-sm">
              ⚠
            </div>
          </div>
          <div class="min-w-0">
            <div class="font-sub font-bold text-ink text-[15.5px] leading-tight truncate">
              {{ row.name }}
            </div>
            <div v-if="row.warning" class="mt-1 text-[12.5px] text-seal-dark font-medium leading-snug">
              {{ row.warning }}
            </div>
          </div>
        </div>

        <!-- AI score -->
        <div class="md:col-span-2 md:text-center md:px-3 flex md:block items-center justify-between md:justify-center">
          <span class="md:hidden text-[11px] font-sub uppercase tracking-wider text-ink-4">AI:</span>
          <span v-if="row.ai_score != null"
                class="font-display font-black text-[22px] leading-none text-violet-700 tabular-nums">
            {{ Math.round(row.ai_score) }}
          </span>
          <span v-else class="text-ink-4 font-medium text-sm">—</span>
        </div>

        <!-- Teacher score -->
        <div class="md:col-span-2 md:text-center md:px-3 flex md:block items-center justify-between md:justify-center">
          <span class="md:hidden text-[11px] font-sub uppercase tracking-wider text-ink-4">教师:</span>
          <span v-if="row.teacher_score != null"
                class="font-display font-black text-[22px] leading-none text-cobalt tabular-nums">
            {{ Math.round(row.teacher_score) }}
          </span>
          <span v-else class="text-ink-4 font-medium text-sm">—</span>
        </div>

        <!-- Enterprise score -->
        <div class="md:col-span-2 md:text-center md:px-3 flex md:block items-center justify-between md:justify-center">
          <span class="md:hidden text-[11px] font-sub uppercase tracking-wider text-ink-4">企业:</span>
          <span v-if="row.enterprise_score != null"
                class="font-display font-black text-[22px] leading-none text-seal-dark tabular-nums">
            {{ Math.round(row.enterprise_score) }}
          </span>
          <span v-else class="text-ink-4 font-medium text-sm">—</span>
        </div>

        <!-- diff + status -->
        <div class="md:col-span-2 md:pr-2 md:pl-4 flex items-center justify-between md:justify-end gap-3">
          <div class="hidden md:block w-24 h-2 rounded-full bg-line overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :style="{ width: `${Math.min(100, row.max_diff * 2.5)}%` }"
              :class="row.flag === 'warning'
                ? 'bg-seal'
                : (row.flag === 'info' ? 'bg-amber' : 'bg-jade')"
            ></div>
          </div>
          <div class="text-right">
            <div class="font-display font-black tabular-nums"
                 :class="row.flag === 'warning'
                   ? 'text-seal text-xl'
                   : (row.flag === 'info' ? 'text-amber-dark text-lg' : 'text-jade-dark text-lg')">
              Δ {{ row.max_diff }}
            </div>
            <div class="text-[11px] font-sub uppercase tracking-widest text-ink-4">
              {{ row.flag === 'warning' ? 'review' : (row.flag === 'info' ? 'note' : 'ok') }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="!dimensionBreakdown || dimensionBreakdown.length === 0"
           class="px-8 py-16 text-center font-body text-ink-4">
        暂无三方评价数据，请等待 AI 自动评分、教师复评完成后再查看。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Icon } from '@iconify/vue'

/** ---- Types：严格对齐后端 /evaluations/compare/{id} 返回 ---- */
interface PartyScore {
  role: 'ai' | 'teacher' | 'enterprise'
  label?: string
  total: number
  comment?: string
}
interface DimensionRow {
  name: string
  ai_score?: number | null
  teacher_score?: number | null
  enterprise_score?: number | null
  max_diff: number
  flag: 'ok' | 'info' | 'warning'
  warning?: string | null
}
interface Summary {
  score_spread: number
  consistency_index?: number
  max_difference_dimension?: string | null
  max_difference: number
  needs_review?: boolean
}

const props = defineProps<{
  parties?: PartyScore[]
  dimensionBreakdown?: DimensionRow[]
  summary?: Summary
}>()

const defaultParties: PartyScore[] = [
  { role: 'ai',        total: 0 },
  { role: 'teacher',   total: 0 },
  { role: 'enterprise',total: 0 },
]
const displayParties = () => {
  if (props.parties && props.parties.length > 0) {
    const filled = [...props.parties]
    // 补齐三方（缺失的补 0 pending）
    for (const need of ['ai','teacher','enterprise'] as const) {
      if (!filled.find(p => p.role === need)) {
        filled.push({ role: need, total: 0, comment: '(尚未评价)' })
      }
    }
    return filled
  }
  return defaultParties
}

/* ---- helpers ---- */
function fmtScore(v: any) {
  if (v == null || isNaN(Number(v))) return '—'
  return Math.round(Number(v))
}
function gradeOf(v: any) {
  const n = Number(v); if (isNaN(n)) return '—'
  if (n >= 90) return 'S · 优秀'
  if (n >= 80) return 'A · 良好'
  if (n >= 70) return 'B · 中等'
  if (n >= 60) return 'C · 合格'
  return 'D · 待改进'
}
function scoreClass(v: any) {
  const n = Number(v); if (isNaN(n)) return 'text-ink-4'
  if (n >= 90) return 'text-jade-dark'
  if (n >= 80) return 'text-cobalt'
  if (n >= 60) return 'text-amber-dark'
  return 'text-seal-dark'
}
function gradeChipClass(v: any) {
  const n = Number(v); if (isNaN(n)) return ''
  if (n >= 90) return '!bg-jade/15 !text-jade-dark !border-jade/30'
  if (n >= 80) return '!bg-cobalt/12 !text-cobalt !border-cobalt/30'
  if (n >= 60) return '!bg-amber/15 !text-amber-dark !border-amber/30'
  return '!bg-seal/12 !text-seal-dark !border-seal/30'
}

function partyIcon(r: string) {
  if (r === 'ai') return 'mdi:robot-happy-outline'
  if (r === 'teacher') return 'mdi:account-tie-outline'
  return 'mdi:domain'
}
function partyRoleLabel(r: string) {
  if (r === 'ai') return 'AI · 初评'
  if (r === 'teacher') return '教师 · 复评'
  return '企业 · 终评'
}
function partyDefaultLabel(r: string) {
  if (r === 'ai') return 'DeepSeek + 规则引擎 自动评价'
  if (r === 'teacher') return '授课教师复评'
  return '企业导师终评'
}
function roleChipClass(r: string) {
  if (r === 'ai')       return '!bg-violet-500/10 !text-violet-700 !border-violet-400/30'
  if (r === 'teacher')  return '!bg-cobalt/12 !text-cobalt !border-cobalt/30'
  return '!bg-seal/12 !text-seal-dark !border-seal/30'
}
function roleIconWrap(r: string) {
  if (r === 'ai')       return 'bg-violet-500/10 border border-violet-400/25'
  if (r === 'teacher')  return 'bg-cobalt/10 border border-cobalt/25'
  return 'bg-seal/10 border border-seal/25'
}
function roleIconClass(r: string) {
  if (r === 'ai')       return 'text-violet-700'
  if (r === 'teacher')  return 'text-cobalt'
  return 'text-seal-dark'
}
function roleGlowClass(r: string) {
  if (r === 'ai')       return 'bg-violet-500'
  if (r === 'teacher')  return 'bg-cobalt'
  return 'bg-seal'
}
</script>

<style scoped>
/* 杂志风下的小微调：Element Plus 不会干涉这里，全部用 global.css 已定义 token */
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
