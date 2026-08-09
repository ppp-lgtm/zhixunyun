<template>
  <!-- EvaluationProgress.vue (G1-2)：5 步 AI 评价进度条 + 日志 + 总进度圆环 -->
  <Transition name="fade-scale">
    <div v-if="visible" class="fixed inset-0 z-[80] bg-ink/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-paper rounded-[28px] w-full max-w-2xl shadow-[0_40px_100px_-24px_rgba(15,23,42,0.45)] ring-1 ring-line ring-opacity-60 overflow-hidden animate-[scaleIn_.25s_ease-out]">
        <!-- 顶部 -->
        <div class="relative px-8 py-6 border-b border-line/70">
          <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cobalt via-seal to-violet-600"
               :style="{ width: overallPercent + '%', transition: 'width .35s ease-out' }"></div>
          <div class="flex items-center gap-4">
            <div class="relative w-16 h-16 flex-shrink-0">
              <svg viewBox="0 0 36 36" class="w-full h-full -rotate-90">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="#E2E8F0" stroke-width="3"/>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      :stroke="status==='failed' ? '#EF4444' : (status==='done' ? '#10B981' : '#FF5A1F')"
                      stroke-width="3" stroke-linecap="round"
                      stroke-dasharray="100, 100"
                      :stroke-dashoffset="100 - overallPercent"
                      style="transition: stroke-dashoffset .35s ease-out"/>
              </svg>
              <div class="absolute inset-0 flex items-center justify-center font-display font-black text-ink text-[17px]">
                <span v-if="status === 'failed'"><Icon icon="mdi:alert-circle-outline" class="text-red-500 text-2xl" /></span>
                <span v-else-if="status === 'done'"><Icon icon="mdi:check-circle-outline" class="text-jade-dark text-2xl" /></span>
                <span v-else>{{ overallPercent }}%</span>
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <Icon icon="mdi:robot-outline" class="text-cobalt text-xl" />
                <h3 class="font-display font-black text-ink text-[20px] tracking-tight">
                  {{ status === 'failed' ? '评价失败' : (status === 'done' ? '评价完成！' : 'AI 正在评价你的成果') }}
                </h3>
              </div>
              <p class="text-[13px] text-ink-3 font-body leading-relaxed">
                <template v-if="status === 'failed'">{{ lastError || '请检查文件格式后重新提交' }}</template>
                <template v-else-if="status === 'done'">正在整理最终报告，即将跳转结果页…</template>
                <template v-else>每一步都在实时推送，当前进度会比传统上传快 30%（SSE 流 + 后台异步）。请不要关闭此窗口。</template>
              </p>
            </div>
            <button @click="$emit('close')"
                    v-if="status === 'done' || status === 'failed'"
                    class="w-9 h-9 rounded-xl hover:bg-line/50 flex items-center justify-center text-ink-3 hover:text-ink transition-colors">
              <Icon icon="mdi:close" class="text-xl" />
            </button>
          </div>
        </div>

        <!-- 5 步 -->
        <div class="px-8 py-6">
          <div class="grid grid-cols-5 gap-2 mb-6">
            <div v-for="(s, i) in STEP_META" :key="s.key"
                 class="relative flex flex-col items-center text-center">
              <div class="relative">
                <div class="w-11 h-11 rounded-2xl flex items-center justify-center border transition-all duration-300"
                     :class="stepClass(i)">
                  <Icon v-if="currentStep > i+1" icon="mdi:check" class="text-white text-[18px]" />
                  <span v-else class="font-display font-black text-[14px]" :class="currentStep === i+1 ? 'text-white' : ''">
                    {{ i + 1 }}
                  </span>
                </div>
                <!-- 进度条（在 step 内部显示一个半弧 or 条） -->
                <div v-if="currentStep === i+1 && (stepProgress[i] ?? 0) > 0"
                     class="absolute -bottom-1 left-0 right-0 h-1 rounded-full bg-line/40 overflow-hidden mx-1">
                  <div class="h-full bg-gradient-to-r from-cobalt to-seal"
                       :style="{ width: (stepProgress[i] ?? 0) + '%', transition: 'width .2s ease-out' }"></div>
                </div>
              </div>
              <!-- 连接线 -->
              <div v-if="i < STEP_META.length - 1"
                   class="hidden md:block absolute top-[22px] left-[calc(50%+22px)] right-[calc(-50%+22px)] h-0.5 -z-0"
                   :class="currentStep > i+1 ? 'bg-jade' : 'bg-line'"></div>

              <div class="mt-3 text-[12.5px] font-semibold tracking-wide"
                   :class="currentStep >= i+1 ? 'text-ink' : 'text-ink-4'">
                {{ s.label }}
              </div>
              <div class="text-[11.5px] text-ink-4 mt-0.5 leading-tight" v-show="currentStep >= i+1">
                {{ stepDetail[i] || s.hint }}
              </div>
            </div>
          </div>

          <!-- 详细日志 -->
          <div class="rounded-2xl bg-gradient-to-b from-paper-2/60 to-transparent border border-line/70 overflow-hidden">
            <div class="px-4 py-2.5 border-b border-line/60 flex items-center justify-between text-[11.5px] uppercase tracking-[0.12em] font-sub font-bold text-ink-4">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full" :class="status==='done' ? 'bg-jade' : (status==='failed' ? 'bg-red-500' : 'bg-seal animate-pulse')"></span>
                实时日志
              </div>
              <button @click="showLog = !showLog"
                      class="text-[11px] text-cobalt hover:text-violet-700 font-bold normal-case tracking-normal">
                {{ showLog ? '隐藏' : '展开' }}
                <Icon :icon="showLog ? 'mdi:chevron-up' : 'mdi:chevron-down'" inline width="12" class="ml-0.5" />
              </button>
            </div>
            <Transition name="slide-fade">
              <div v-show="showLog" ref="logBoxRef" class="max-h-40 overflow-y-auto px-4 py-2.5 font-mono text-[11.5px] text-ink-2 leading-relaxed space-y-0.5 bg-paper-2/30">
                <div v-if="!logs.length" class="italic text-ink-4">等待 AI 第一步反馈…</div>
                <div v-for="(l, idx) in logs" :key="idx" class="flex gap-2">
                  <span class="text-ink-4 select-none min-w-[6ch]">{{ String(idx+1).padStart(3,'0') }}</span>
                  <span class="break-all" v-html="colorizeLog(l)"></span>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 底部操作 -->
          <div class="mt-6 flex items-center justify-between">
            <div class="text-[11.5px] text-ink-4 font-mono">
              job_id: <span class="text-ink-2">{{ jobId || '—' }}</span>
              <span class="mx-2 text-ink-4/40">·</span>
              mode: <span class="text-ink-2">{{ mode || 'auto' }}</span>
              <span v-if="pollingAsFallback" class="ml-2 !text-seal-dark bg-seal/8 rounded-md px-2 py-0.5 !font-semibold !font-body">
                <Icon icon="mdi:sync-alert" inline width="11" class="mr-0.5" /> SSE 不可用 · 已切换轮询
              </span>
            </div>
            <div class="flex gap-2">
              <button v-if="status === 'failed'" @click="retryEmit"
                      class="btn-mag btn-mag-danger !px-4 !py-2 text-[12.5px]">
                <Icon icon="mdi:refresh" class="mr-1" inline width="13" /> 关闭并重试
              </button>
              <button v-if="status === 'done'" @click="$emit('close')"
                      class="btn-mag btn-mag-primary !px-5 !py-2 text-[12.5px]">
                查看结果 <Icon icon="mdi:arrow-right" inline width="13" class="ml-1" />
              </button>
              <button v-else disabled
                      class="btn-mag btn-mag-ghost !px-4 !py-2 text-[12.5px] opacity-70 cursor-not-allowed">
                请等待 5 步完成…
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'

interface Props {
  visible: boolean
  jobId: string
  mode?: string
  onCloseWhenDone?: boolean
  pollFallbackTimeoutMs?: number
}
const props = withDefaults(defineProps<Props>(), {
  mode: 'code',
  onCloseWhenDone: true,
  pollFallbackTimeoutMs: 4500,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'done', result: any): void
  (e: 'failed', error: string): void
  (e: 'retry'): void
  (e: 'step-change', step: number): void
}>()

const STEP_META = [
  { key: 'parse', label: '文件解析', hint: 'docx/pdf/图片/代码zip' },
  { key: 'analyze', label: '静态分析', hint: '指标/抄袭/要求匹配' },
  { key: 'ai_score', label: 'AI 评分', hint: '大模型多维度评价' },
  { key: 'save', label: '写入数据库', hint: 'submission + evaluation' },
  { key: 'done', label: '生成报告', hint: '即将跳转结果页' },
]

const status = ref<'queued' | 'running' | 'done' | 'failed'>('queued')
const currentStep = ref(0)
const stepProgress = reactive<Record<number, number>>({ 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 })
const stepDetail = reactive<Record<number, string>>({ 0: '', 1: '', 2: '', 3: '', 4: '' })
const logs = ref<string[]>([])
const showLog = ref(true)
const lastError = ref('')
const pollingAsFallback = ref(false)
const logBoxRef = ref<HTMLElement | null>(null)

const overallPercent = computed(() => {
  // 各步权重 ≈ 它们在评估里的真实耗时：parse 15 / analyze 30 / ai_score 35 / save 15 / done 5
  const weights = [15, 30, 35, 15, 5]
  let total = 0
  for (let i = 0; i < 5; i++) {
    const p = currentStep.value > i + 1 ? 100 : (currentStep.value === i + 1 ? (stepProgress[i] ?? 0) : 0)
    total += weights[i] * p / 100
  }
  if (status.value === 'done') return 100
  return Math.round(total)
})

function stepClass(i: number) {
  const done = currentStep.value > i + 1
  const active = currentStep.value === i + 1
  if (status.value === 'failed' && !done && !active) {
    return 'border-line bg-paper text-ink-4'
  }
  if (done) {
    return 'bg-jade border-jade shadow-[0_8px_20px_-8px_rgba(16,185,129,0.6)]'
  }
  if (active) {
    return 'bg-gradient-to-br from-seal to-violet-600 border-transparent shadow-[0_8px_20px_-8px_rgba(255,90,31,0.7)] text-white animate-[pulseDot_1.5s_ease-in-out_infinite]'
  }
  return 'bg-paper border-line text-ink-4'
}

function colorizeLog(line: string): string {
  let escaped = line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  escaped = escaped.replace(/(\[ERROR\])/g, '<span class="text-red-500 font-bold">$1</span>')
  escaped = escaped.replace(/(\[[1-5]\/5\][^\s:]*)/g, '<span class="text-cobalt font-semibold">$1</span>')
  escaped = escaped.replace(/(done:|ok|成功|通过|passed)/g, '<span class="text-jade-dark font-semibold">$1</span>')
  return escaped
}

function pushLog(line: string) {
  logs.value.push(line)
  if (logs.value.length > 200) logs.value = logs.value.slice(-200)
  nextTick(() => {
    if (logBoxRef.value) logBoxRef.value.scrollTop = logBoxRef.value.scrollHeight
  })
}

// ---------- SSE / Poll 调度 ----------
let es: EventSource | null = null
let pollTimer: number | null = null
let sseFallbackTimer: number | null = null

function _applyStepEvent(data: any) {
  const idx = Number(data.index) || 0
  if (idx < 1 || idx > 5) return
  currentStep.value = idx
  stepProgress[idx - 1] = Number(data.percent) || 0
  if (data.detail || data.title) stepDetail[idx - 1] = data.detail || data.title || ''
  emit('step-change', idx)
}

function teardown() {
  if (es) { try { es.close() } catch {} es = null }
  if (pollTimer) { window.clearInterval(pollTimer); pollTimer = null }
  if (sseFallbackTimer) { window.clearTimeout(sseFallbackTimer); sseFallbackTimer = null }
}

async function _pollTick() {
  try {
    const r = await axios.get(`${API_BASE}/api/upload-eval/status/${props.jobId}`)
    const d = (r.data as any)?.data || r.data
    if (!d) return
    if (d.status === 'failed') {
      status.value = 'failed'
      lastError.value = d.error || '任务失败'
      pushLog(`[ERROR] ${lastError.value}`)
      emit('failed', lastError.value)
      teardown()
      return
    }
    if (d.step && d.step > currentStep.value) {
      // 轮询场景下，补一个 step 事件（百分比用 100%，因为轮询粒度粗）
      _applyStepEvent({ index: d.step, percent: 100, detail: d.step_name || '' })
    }
    if (d.result && d.status === 'done') {
      currentStep.value = 5
      status.value = 'done'
      stepProgress[4] = 100
      pushLog('[5/5] done: （轮询模式）结果已获取')
      emit('done', d.result)
      if (props.onCloseWhenDone) setTimeout(() => emit('close'), 1200)
      teardown()
    }
  } catch (_e) { /* ignore poll err */ }
}

function startPollFallback() {
  if (pollTimer) return
  pollingAsFallback.value = true
  pushLog('[fallback] SSE 未在预期时间内连接，自动切换为 1s 轮询模式')
  pollTimer = window.setInterval(_pollTick, 1000)
  _pollTick()
}

function startSSE() {
  if (!props.jobId) return
  teardown()
  // 初始化
  currentStep.value = 0
  stepProgress[0] = stepProgress[1] = stepProgress[2] = stepProgress[3] = stepProgress[4] = 0
  stepDetail[0] = stepDetail[1] = stepDetail[2] = stepDetail[3] = stepDetail[4] = ''
  logs.value = []
  status.value = 'queued'
  lastError.value = ''
  pollingAsFallback.value = false

  // Fallback 保险：若 SSE 在 N ms 内没收到第一个 step 事件，则切轮询
  sseFallbackTimer = window.setTimeout(startPollFallback, props.pollFallbackTimeoutMs || 4500)

  try {
    const url = `${API_BASE}/api/upload-eval/stream/${props.jobId}`
    es = new EventSource(url, { withCredentials: false })
    es.addEventListener('hello', (e: any) => {
      const data = JSON.parse(e.data)
      pushLog(`[hello] server_time=${new Date(data.server_time * 1000).toLocaleTimeString()}, ttl=${data.ttl_seconds}s`)
    })
    es.addEventListener('status', (e: any) => {
      const data = JSON.parse(e.data)
      if (data === 'running' || typeof data === 'string') status.value = data as any
    })
    es.addEventListener('step', (e: any) => {
      const data = JSON.parse(e.data)
      // 收到第一步 SSE 有效反馈：取消 fallback 定时器
      if (sseFallbackTimer) { window.clearTimeout(sseFallbackTimer); sseFallbackTimer = null }
      _applyStepEvent(data)
    })
    es.addEventListener('log', (e: any) => {
      const line = JSON.parse(e.data)
      if (typeof line === 'string') pushLog(line)
    })
    es.addEventListener('done', (e: any) => {
      teardown()
      const result = JSON.parse(e.data)
      currentStep.value = 5
      stepProgress[4] = 100
      status.value = 'done'
      pushLog('[5/5] done: 最终结果已送达 (SSE)')
      emit('done', result)
      if (props.onCloseWhenDone) setTimeout(() => emit('close'), 1200)
    })
    es.addEventListener('error', (e: any) => {
      const msg = JSON.parse(e.data || 'null')
      if (msg) {
        status.value = 'failed'
        lastError.value = typeof msg === 'string' ? msg : (msg?.detail || '任务失败')
        pushLog(`[ERROR] ${lastError.value}`)
        emit('failed', lastError.value)
      }
      // EventSource 自身网络错误（event=error 无 data）：切轮询
      if (!msg) {
        pushLog('[SSE] 连接异常，切换轮询兜底')
        startPollFallback()
        if (es) { try { es.close() } catch {} es = null }
      }
    })
    es.addEventListener('heartbeat', () => {
      // 心跳不打日志，保持静默（避免刷屏）
    })
    es.onerror = () => {
      pushLog('[SSE] onerror fired: 服务器可能重启或断连，切换轮询')
      startPollFallback()
      if (es) { try { es.close() } catch {} es = null }
    }
  } catch (err: any) {
    pushLog(`[SSE] init error: ${err.message}, falling back to polling`)
    startPollFallback()
  }
}

watch(() => [props.visible, props.jobId], () => {
  if (props.visible && props.jobId) {
    nextTick(startSSE)
  } else if (!props.visible) {
    teardown()
  }
}, { immediate: true, deep: false })

onBeforeUnmount(teardown)

function retryEmit() {
  emit('retry')
  emit('close')
}
</script>

<style scoped>
@keyframes scaleIn {
  0%   { transform: scale(0.94); opacity: 0; }
  100% { transform: scale(1);    opacity: 1; }
}
@keyframes pulseDot {
  0%, 100% { box-shadow: 0 8px 20px -8px rgba(255,90,31,0.6); }
  50%      { box-shadow: 0 8px 24px -4px rgba(255,90,31,0.85); }
}
.fade-scale-enter-active,
.fade-scale-leave-active { transition: opacity .2s ease-out; }
.fade-scale-enter-from,
.fade-scale-leave-to { opacity: 0; }
.slide-fade-enter-active,
.slide-fade-leave-active { transition: all .2s ease; }
.slide-fade-enter-from,
.slide-fade-leave-to { transform: translateY(-6px); opacity: 0; max-height: 0; }
</style>
