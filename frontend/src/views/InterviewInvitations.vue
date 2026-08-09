<template>
  <div class="min-h-full page-enter">
    <!-- ============ 顶部：标题 + 状态统计 ============ -->
    <section class="mb-6">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <span class="text-[11px] font-mono tracking-[0.2em] uppercase text-ink-4 opacity-80">Invitation Center · 01</span>
          </div>
          <h1 class="font-display text-3xl font-black text-ink tracking-tight">
            面试邀约中心
            <span class="inline-block h-1 w-12 rounded-full bg-gradient-to-r from-seal via-amber-500 to-cobalt align-middle ml-3"></span>
          </h1>
          <p class="mt-2 text-[13.5px] text-ink-3 leading-relaxed max-w-2xl">
            企业导师向你发出的所有面试邀请都将在此统一管理。请及时查看邀约详情，
            <span class="text-seal-dark font-semibold">接受 / 拒绝</span>
            或补充你的回复留言。
          </p>
        </div>
      </div>

      <!-- 4 枚状态印章 -->
      <div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="inv-stat-stamp tone-amber" :style="{ '--r': '-1.2deg' }">
          <div class="holes"></div>
          <div class="lbl">PENDING</div>
          <div class="ic">
            <Icon icon="mdi:clock-outline" />
          </div>
          <div class="num">{{ statCount('pending') }}</div>
          <div class="cn">待你回复</div>
        </div>
        <div class="inv-stat-stamp tone-emerald" :style="{ '--r': '0.8deg' }">
          <div class="holes"></div>
          <div class="lbl">ACCEPTED</div>
          <div class="ic">
            <Icon icon="mdi:check-circle-outline" />
          </div>
          <div class="num">{{ statCount('accepted') }}</div>
          <div class="cn">已接受</div>
        </div>
        <div class="inv-stat-stamp tone-rose" :style="{ '--r': '-0.6deg' }">
          <div class="holes"></div>
          <div class="lbl">DECLINED</div>
          <div class="ic">
            <Icon icon="mdi:close-circle-outline" />
          </div>
          <div class="num">{{ statCount('declined') }}</div>
          <div class="cn">已拒绝</div>
        </div>
        <div class="inv-stat-stamp tone-slate" :style="{ '--r': '1.4deg' }">
          <div class="holes"></div>
          <div class="lbl">TOTAL</div>
          <div class="ic">
            <Icon icon="mdi:email-outline" />
          </div>
          <div class="num">{{ invitations.length }}</div>
          <div class="cn">邀约总数</div>
        </div>
      </div>
    </section>

    <!-- ============ 统一大卡片：Tab 切换 + 列表 ============ -->
    <section class="sp-unified">
      <div class="spu-head">
        <div class="spu-head-l">
          <h2 class="spu-title">
            <Icon icon="mdi:calendar-multiple-check" class="spu-ic spu-ic-seal" />
            我的面试邀约
          </h2>
          <p class="spu-sub text-[12.5px] text-ink-4 mt-1.5">
            共 <b class="text-ink">{{ invitations.length }}</b> 条邀约 ·
            待回复 <b class="text-amber-700">{{ statCount('pending') }}</b> 条 ·
            已响应 <b class="text-emerald-700">{{ statCount('accepted') + statCount('declined') }}</b> 条
          </p>
        </div>

        <!-- Tab 切换（全部 / 待回复 / 已接受 / 已拒绝 / 已撤回） -->
        <div class="spu-tabs" role="tablist">
          <button
            v-for="tab in tabList"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="['spu-tab', { active: activeTab === tab.key }]"
            role="tab"
          >
            <Icon :icon="tab.icon" class="mr-1" inline width="14" />
            {{ tab.label }}
            <span v-if="tab.countFn()" class="ml-1.5 text-[10.5px] font-mono px-1.5 py-0.5 rounded-md"
              :class="tab.badgeClass">
              {{ tab.countFn() }}
            </span>
          </button>
        </div>
      </div>

      <div class="spu-divider"></div>

      <!-- Tab 内容：邀约列表 -->
      <div class="spu-section">
        <div v-if="loading" class="py-20 text-center text-ink-3 text-[13px]">
          <Icon icon="mdi:loading" class="animate-spin text-3xl mb-3 text-seal" />
          <p>正在加载面试邀约…</p>
        </div>

        <div v-else-if="!filteredInvitations.length" class="py-20 text-center text-ink-3 text-[13px] p-8">
          <div class="w-20 h-20 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
            <Icon :icon="activeTab==='pending' ? 'mdi:email-open-outline' : 'mdi:calendar-blank-outline'" class="text-4xl text-ink-4" />
          </div>
          <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">
            {{ emptyTitle }}
          </p>
          <p>{{ emptySubtitle }}</p>
        </div>

        <!-- 邀约列表：紧凑纵向排布 -->
        <div v-else class="space-y-3">
          <div
            v-for="inv in filteredInvitations"
            :key="inv.id"
            class="inv-row"
            :class="`inv-row-${inv.status}`"
          >
            <!-- 左侧：状态色条 + 日期印章 -->
            <div class="inv-row-left">
              <div class="inv-status-bar" :class="`sb-${inv.status}`"></div>
              <div class="inv-date-seal">
                <div class="ids-month">{{ monthOf(inv.interview_time) }}</div>
                <div class="ids-day">{{ dayOf(inv.interview_time) }}</div>
                <div class="ids-week">{{ weekdayOf(inv.interview_time) }}</div>
              </div>
            </div>

            <!-- 中间：主体信息 -->
            <div class="inv-row-body">
              <div class="irb-head">
                <div class="flex items-center gap-2.5 flex-wrap min-w-0">
                  <!-- 岗位标题 + 级别 -->
                  <h3 class="irb-job-title truncate">
                    {{ inv.job?.title || '未关联岗位' }}
                  </h3>
                  <span v-if="inv.job?.level" class="irb-chip irb-chip-level">{{ inv.job.level }}</span>
                  <!-- 状态徽章 -->
                  <span class="irb-chip" :class="statusChipClass(inv.status)">
                    {{ statusLabel(inv.status) }}
                  </span>
                  <!-- 线上/线下 -->
                  <span class="irb-chip irb-chip-type" :class="inv.interview_type === 'online' ? 'type-online' : 'type-onsite'">
                    <Icon :icon="inv.interview_type === 'online' ? 'mdi:video-outline' : 'mdi:map-marker-outline'" class="mr-0.5" inline width="13" />
                    {{ inv.interview_type === 'online' ? '线上面试' : '线下面试' }}
                  </span>
                </div>
              </div>

              <!-- 关键信息行：3 列 -->
              <div class="irb-meta">
                <div class="irb-meta-item">
                  <Icon icon="mdi:clock-outline" class="mi-cobalt" inline width="15" />
                  <span class="irb-meta-k">面试时间</span>
                  <span class="irb-meta-v font-mono">{{ fmtDateTime(inv.interview_time) }}</span>
                </div>
                <div class="irb-meta-item">
                  <Icon :icon="inv.interview_type === 'online' ? 'mdi:link-variant' : 'mdi:map-marker-radius-outline'" class="mi-seal" inline width="15" />
                  <span class="irb-meta-k">{{ inv.interview_type === 'online' ? '会议链接' : '面试地点' }}</span>
                  <span class="irb-meta-v truncate" :title="inv.location">{{ inv.location || '—' }}</span>
                </div>
                <div class="irb-meta-item">
                  <Icon icon="mdi:domain" class="mi-emerald" inline width="15" />
                  <span class="irb-meta-k">发起企业 · 导师</span>
                  <span class="irb-meta-v">
                    {{ inv.enterprise?.name || '企业' }}
                    <template v-if="inv.mentor?.real_name"> · {{ inv.mentor.real_name }}</template>
                    <template v-if="inv.mentor?.title">（{{ inv.mentor.title }}）</template>
                  </span>
                </div>
              </div>

              <!-- 留言区：企业留言 + 学生回复（如果有） -->
              <div class="irb-messages" v-if="inv.message || inv.student_reply">
                <div v-if="inv.message" class="msg-bubble msg-enterprise">
                  <div class="mb-sender">
                    <Icon icon="mdi:message-text-outline" inline width="13" />
                    <span>企业邀约留言</span>
                  </div>
                  <div class="mb-text">{{ inv.message }}</div>
                </div>
                <div v-if="inv.student_reply" class="msg-bubble msg-student">
                  <div class="mb-sender">
                    <Icon icon="mdi:message-reply-outline" inline width="13" />
                    <span>我的回复</span>
                  </div>
                  <div class="mb-text">{{ inv.student_reply }}</div>
                </div>
              </div>

              <!-- 操作区：仅 pending 状态可响应 -->
              <div v-if="inv.status === 'pending'" class="irb-actions">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                  <input
                    v-model="replyDrafts[inv.id]"
                    :placeholder="'留言（可选）：补充你方便的时间段、简历链接或其他问题…'"
                    class="reply-input flex-1 min-w-[240px]"
                    maxlength="300"
                  />
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button
                    @click="openRespondDialog(inv, false)"
                    :disabled="submittingId === inv.id"
                    class="btn-mag btn-mag-ghost !py-2 !px-3 !text-[12.5px]"
                  >
                    <Icon icon="mdi:close-thick" class="mr-1" />
                    婉拒邀约
                  </button>
                  <button
                    @click="openRespondDialog(inv, true)"
                    :disabled="submittingId === inv.id"
                    class="btn-mag btn-mag-primary !py-2 !px-4 !text-[12.5px]"
                  >
                    <Icon v-if="submittingId === inv.id" icon="mdi:loading" class="mr-1 animate-spin" />
                    <Icon v-else icon="mdi:check-bold" class="mr-1" />
                    确认参加
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============ 响应确认弹窗 ============ -->
    <transition name="fade-in-down">
      <div v-if="respondVisible" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink/50 backdrop-blur-sm" @click.self="closeRespondDialog"></div>
        <div class="relative w-full max-w-lg card-mag !p-0 !rounded-3xl shadow-2xl overflow-hidden z-10">
          <!-- 顶条 -->
          <div
            class="px-7 py-5 border-b border-line/70"
            :class="respondAccept ? 'bg-emerald-500/[0.07]' : 'bg-rose-500/[0.07]'"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div
                  class="w-11 h-11 rounded-2xl text-white shadow-md grid place-items-center"
                  :class="respondAccept ? 'bg-gradient-to-br from-jade to-emerald-600' : 'bg-gradient-to-br from-rose-500 to-rose-700'"
                >
                  <Icon :icon="respondAccept ? 'mdi:check-bold' : 'mdi:close-thick'" class="text-2xl" />
                </div>
                <div>
                  <h3 class="font-display font-black text-ink text-xl leading-tight">
                    {{ respondAccept ? '确认参加面试？' : '确认婉拒邀约？' }}
                  </h3>
                  <p class="text-[12.5px] text-ink-3 mt-1">
                    {{ respondAccept ? '接受后企业导师将收到通知，请准时参加' : '婉拒后该邀约将被标记为已拒绝' }}
                  </p>
                </div>
              </div>
              <button @click="closeRespondDialog" class="w-9 h-9 rounded-xl hover:bg-ink/5 flex items-center justify-center text-ink-3 hover:text-ink transition-colors">
                <Icon icon="mdi:close" class="text-xl" />
              </button>
            </div>
          </div>

          <!-- 邀约摘要 -->
          <div v-if="respondTarget" class="px-7 py-4 bg-line/20 border-b border-line/70">
            <div class="text-[12px] text-ink-4 font-mono tracking-widest mb-2">INVITATION · PREVIEW</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-y-1.5 gap-x-5 text-[12.5px]">
              <div class="flex items-center gap-2">
                <Icon icon="mdi:briefcase-outline" class="text-cobalt" inline width="14" />
                <span class="text-ink-3">岗位：</span>
                <b class="text-ink">{{ respondTarget.job?.title || '—' }}</b>
                <span v-if="respondTarget.job?.level" class="chip-mag !text-[10.5px] !py-0.5 !px-2">{{ respondTarget.job.level }}</span>
              </div>
              <div class="flex items-center gap-2">
                <Icon icon="mdi:clock-outline" class="text-seal" inline width="14" />
                <span class="text-ink-3">时间：</span>
                <b class="text-ink font-mono">{{ fmtDateTime(respondTarget.interview_time) }}</b>
              </div>
              <div class="flex items-center gap-2 md:col-span-2 min-w-0">
                <Icon :icon="respondTarget.interview_type==='onsite'?'mdi:map-marker-outline':'mdi:link-variant'" class="text-amber-600" inline width="14" />
                <span class="text-ink-3 flex-shrink-0">{{ respondTarget.interview_type==='onsite'?'地点：':'链接：' }}</span>
                <span class="text-ink truncate" :title="respondTarget.location">{{ respondTarget.location || '—' }}</span>
              </div>
            </div>
          </div>

          <!-- 回复留言 -->
          <div class="px-7 py-5">
            <label class="block text-[13px] font-sub font-semibold text-ink mb-1.5">
              回复留言 <span class="text-ink-3 text-[11.5px] font-normal ml-1">（可选，最多 300 字）</span>
            </label>
            <textarea
              v-model="respondReply"
              rows="4"
              :placeholder="respondAccept
                ? '留言（可选）：如「好的，我会准时参加！如有需要请联系我 13xxxx…」'
                : '留言（可选）：如「抱歉，时间冲突无法参加，感谢邀请。」'"
              maxlength="300"
              class="w-full px-3.5 py-2.5 rounded-xl border border-line bg-white text-[13.5px] text-ink leading-relaxed focus:outline-none focus:ring-4 transition-all resize-none"
              :class="respondAccept ? 'focus:border-emerald-500 focus:ring-emerald-500/10' : 'focus:border-rose-500 focus:ring-rose-500/10'"
            ></textarea>
            <div class="mt-1 text-right text-[11px] text-ink-3 font-mono">
              {{ respondReply.length }}/300
            </div>
          </div>

          <!-- 底部按钮 -->
          <div class="px-7 py-4 bg-line/30 border-t border-line/70 flex items-center justify-end gap-3">
            <button @click="closeRespondDialog" :disabled="submitting" class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">取消</button>
            <button
              @click="submitRespond"
              :disabled="submitting"
              class="btn-mag px-5 py-2.5 text-[13px] min-w-[110px]"
              :class="respondAccept ? 'btn-mag-primary' : '!bg-rose-600 !border-rose-600 hover:!bg-rose-700 hover:!border-rose-700 text-white'"
            >
              <Icon v-if="submitting" icon="mdi:loading" class="mr-1 animate-spin" />
              <Icon v-else :icon="respondAccept ? 'mdi:check-bold' : 'mdi:close-thick'" class="mr-1" />
              {{ submitting ? '提交中…' : (respondAccept ? '确认参加' : '确认婉拒') }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'

/* ========== 状态 ========== */
const loading = ref(false)
const invitations = ref<any[]>([])
const activeTab = ref<'all' | 'pending' | 'accepted' | 'declined' | 'cancelled'>('all')
const replyDrafts = reactive<Record<number, string>>({})

/* ========== 响应弹窗 ========== */
const respondVisible = ref(false)
const respondAccept = ref(true)
const respondTarget = ref<any>(null)
const respondReply = ref('')
const submitting = ref(false)
const submittingId = ref<number | null>(null)

/* ========== Tab 配置 ========== */
const tabList = computed(() => [
  { key: 'all' as const,      label: '全部',    icon: 'mdi:view-list-outline',  badgeClass: 'bg-ink/10 text-ink-2', countFn: () => invitations.value.length },
  { key: 'pending' as const,  label: '待回复',  icon: 'mdi:clock-outline',       badgeClass: 'bg-amber-500/15 text-amber-800', countFn: () => statCount('pending') },
  { key: 'accepted' as const, label: '已接受',  icon: 'mdi:check-circle-outline',badgeClass: 'bg-emerald-500/15 text-emerald-800', countFn: () => statCount('accepted') },
  { key: 'declined' as const, label: '已拒绝',  icon: 'mdi:close-circle-outline',badgeClass: 'bg-rose-500/15 text-rose-800', countFn: () => statCount('declined') },
  { key: 'cancelled' as const,label: '已撤回',  icon: 'mdi:cancel',              badgeClass: 'bg-slate-500/15 text-slate-700', countFn: () => statCount('cancelled') },
])

const filteredInvitations = computed(() => {
  if (activeTab.value === 'all') return invitations.value
  return invitations.value.filter(i => i.status === activeTab.value)
})

const emptyTitle = computed(() => {
  switch (activeTab.value) {
    case 'pending': return '当前没有待回复的邀约'
    case 'accepted': return '你还没有接受任何邀约'
    case 'declined': return '你还没有拒绝任何邀约'
    case 'cancelled': return '暂无被撤回的邀约'
    default: return '暂时没有面试邀约'
  }
})
const emptySubtitle = computed(() => {
  if (activeTab.value === 'all') return '企业导师认可你的实训表现后，会在此向你发送面试邀请。'
  if (activeTab.value === 'pending') return '有新邀约时会立即出现在这里。'
  return '切换到其它 Tab 查看更多邀约记录。'
})

/* ========== Helpers ========== */
// Token：Header + URL 双保险（后端 _extract_token 同时支持两种方式）
const TOKEN: string = (() => {
  const t = localStorage.getItem('token')
  return t ? String(t).trim() : ''
})()
function authConfig(cfg: any = {}): any {
  const headers: any = cfg.headers ? { ...cfg.headers } : {}
  const params: any = cfg.params ? { ...cfg.params } : {}
  if (TOKEN) {
    headers.Authorization = `Bearer ${TOKEN}`
    // 双保险：URL 查询参数也带 token（部分浏览器/代理对 header 大小写敏感时兜底）
    params.token = TOKEN
  }
  return { ...cfg, headers, params }
}
function statCount(s: string): number {
  return invitations.value.filter(i => i.status === s).length
}
function statusLabel(s: string): string {
  switch (s) {
    case 'pending': return '待你回复'
    case 'accepted': return '已接受'
    case 'declined': return '已拒绝'
    case 'cancelled': return '企业撤回'
    case 'completed': return '已完成'
    default: return s
  }
}
function statusChipClass(s: string): string {
  switch (s) {
    case 'pending':   return 'st-pending'
    case 'accepted':  return 'st-accepted'
    case 'declined':  return 'st-declined'
    case 'cancelled': return 'st-cancelled'
    case 'completed': return 'st-completed'
    default:          return 'st-cancelled'
  }
}
function fmtDateTime(v: any): string {
  if (!v) return '—'
  const d = new Date(v)
  if (isNaN(d.getTime())) return String(v).slice(0, 16).replace('T', ' ')
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}
function monthOf(v: any): string {
  const d = new Date(v)
  if (isNaN(d.getTime())) return '—'
  return `${d.getMonth() + 1}月`
}
function dayOf(v: any): string {
  const d = new Date(v)
  if (isNaN(d.getTime())) return '—'
  return String(d.getDate()).padStart(2, '0')
}
function weekdayOf(v: any): string {
  const d = new Date(v)
  if (isNaN(d.getTime())) return '—'
  return ['周日','周一','周二','周三','周四','周五','周六'][d.getDay()]
}

/* ========== 加载 ========== */
async function loadInvitations(force = false) {
  loading.value = true
  try {
    if (!TOKEN) {
      // 无 token：直接跳登录（避免 401 反复弹错）
      ;(await import('element-plus')).ElMessage.warning('请先登录学生账号')
      const { useRouter } = await import('vue-router')
      useRouter().push({ path: '/login', query: { redirect: '/app/interview-invitations' } })
      return
    }
    const res = await axios.get(`${API_BASE}/api/student/interview-invitations`, authConfig({
      params: { page_size: 200 },
    }))
    if (res.data?.success) {
      invitations.value = res.data.list || []
      // 初始化所有待回复邀约的草稿默认值（避免 v-model 绑到 undefined）
      invitations.value.forEach(inv => {
        if (inv.status === 'pending' && replyDrafts[inv.id] === undefined) {
          replyDrafts[inv.id] = ''
        }
      })
    } else if (res.data?.success === false) {
      throw new Error(res.data?.detail || res.data?.error || res.data?.message || '接口返回失败')
    }
  } catch (e: any) {
    const is401 = e?.response?.status === 401 || (e?.message || '').indexOf('401') >= 0
    let msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '加载失败'
    if (is401) msg = '登录状态已过期或 Token 无效，请重新登录学生账号'
    ;(await import('element-plus')).ElMessage.error(`加载邀约列表失败：${msg}`)
    invitations.value = []
    if (is401) {
      const { useRouter } = await import('vue-router')
      setTimeout(() => useRouter().push({ path: '/login', query: { redirect: '/app/interview-invitations' } }), 600)
    }
  } finally {
    loading.value = false
  }
}

/* ========== 响应邀约 ========== */
function openRespondDialog(inv: any, accept: boolean) {
  respondTarget.value = inv
  respondAccept.value = accept
  respondReply.value = replyDrafts[inv.id] || ''
  respondVisible.value = true
}
function closeRespondDialog() {
  if (submitting.value) return
  respondVisible.value = false
  respondTarget.value = null
}
async function submitRespond() {
  if (!respondTarget.value) return
  submitting.value = true
  submittingId.value = respondTarget.value.id
  try {
    const res = await axios.patch(
      `${API_BASE}/api/student/interview-invitations/${respondTarget.value.id}/respond`,
      {
        accept: respondAccept.value,
        reply: respondReply.value.trim(),
      },
      authConfig(),
    )
    if (res.data?.success) {
      // 同步回复留言到草稿 & 更新列表本地记录
      replyDrafts[respondTarget.value.id] = respondReply.value
      ;(await import('element-plus')).ElMessage.success(
        respondAccept.value ? '已确认参加，企业导师将收到通知' : '已婉拒邀约'
      )
      closeRespondDialog()
      await loadInvitations(true)
    } else {
      throw new Error(res.data?.detail || res.data?.message || '提交失败')
    }
  } catch (e: any) {
    const is401 = e?.response?.status === 401
    let msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '响应失败，请稍后重试'
    if (is401) msg = '登录状态已过期，请重新登录学生账号'
    ;(await import('element-plus')).ElMessage.error(msg)
    if (is401) {
      const { useRouter } = await import('vue-router')
      setTimeout(() => useRouter().push('/login'), 500)
    }
  } finally {
    submitting.value = false
    submittingId.value = null
  }
}

/* ========== Init ========== */
onMounted(() => loadInvitations())
</script>

<style scoped>
/* ==============================
   学生端面试邀约页 · 简约风格
   白灰主色 + 4 状态色（绿/红/橙/蓝）
   ============================== */

/* ---- 状态印章 ---- */
.inv-stat-stamp {
  position: relative;
  background: var(--paper, #FFFDF7);
  border: 1px solid var(--line, #E7E1CF);
  border-radius: 16px;
  padding: 14px 14px 12px;
  transform: rotate(var(--r, 0deg));
  transition: transform .25s ease, box-shadow .25s ease;
  box-shadow: 0 1px 0 rgba(0,0,0,0.03);
  overflow: hidden;
}
.inv-stat-stamp:hover {
  transform: rotate(0deg) translateY(-2px);
  box-shadow: 0 10px 24px -12px rgba(44,36,24,0.18);
}
.inv-stat-stamp .holes {
  position: absolute;
  top: 8px; right: 10px;
  display: flex; gap: 3px;
}
.inv-stat-stamp .holes::before,
.inv-stat-stamp .holes::after {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #E7E1CF;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.04);
}
.inv-stat-stamp .lbl {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--ink-3, #8A7F68);
  font-weight: 700;
}
.inv-stat-stamp .ic {
  width: 32px; height: 32px;
  border-radius: 10px;
  display: grid; place-items: center;
  font-size: 16px;
  margin: 8px 0 6px;
  color: #fff;
}
.inv-stat-stamp .num {
  font-family: var(--ff-display), "Noto Serif SC", Georgia, serif;
  font-size: 30px;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--ink, #2C2418);
}
.inv-stat-stamp .cn {
  margin-top: 3px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-2, #4B4235);
  font-family: var(--ff-sub), -apple-system, BlinkMacSystemFont, sans-serif;
}
.tone-amber    .ic { background: linear-gradient(135deg, #F59E0B, #B45309); }
.tone-amber    .num { color: #B45309; }
.tone-emerald  .ic { background: linear-gradient(135deg, #10B981, #047857); }
.tone-emerald  .num { color: #047857; }
.tone-rose     .ic { background: linear-gradient(135deg, #F43F5E, #9F1239); }
.tone-rose     .num { color: #9F1239; }
.tone-slate    .ic { background: linear-gradient(135deg, #64748B, #334155); }
.tone-slate    .num { color: #334155; }

/* ---- 复用学生画像统一卡片样式 ---- */
.sp-unified {
  background: var(--paper, #F4F1EA);
  border: 1px solid var(--line, #DED6C7);
  border-radius: 16px;
  padding: 22px 26px 26px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
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
  font-size: 22px;
  letter-spacing: 0.01em;
  color: var(--ink, #2C2418);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.spu-ic { width: 22px; height: 22px; }
.spu-ic-seal { color: #FF5A1F; }
.spu-sub { margin: 0; }
.spu-tabs {
  display: inline-flex;
  padding: 4px;
  background: rgba(222, 214, 199, 0.35);
  border: 1px solid var(--line, #DED6C7);
  border-radius: 12px;
  gap: 4px;
  flex-shrink: 0;
  overflow-x: auto;
  max-width: 100%;
}
.spu-tab {
  appearance: none;
  border: none;
  background: transparent;
  padding: 8px 14px;
  border-radius: 9px;
  font-size: 12.5px;
  font-family: inherit;
  font-weight: 600;
  color: var(--ink-4, #8A7F68);
  cursor: pointer;
  transition: all .2s ease;
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
}
.spu-tab:hover { color: var(--ink-2, #4B4235); background: rgba(255,255,255,.4); }
.spu-tab.active {
  background: var(--ink, #2C2418);
  color: #fff;
  box-shadow: 0 4px 12px -4px rgba(44,36,24,0.4);
}
.spu-divider {
  margin: 18px 0 4px;
  border-top: 1px dashed rgba(222,214,199,0.9);
}
.spu-section { padding: 12px 4px 4px; }

/* ---- 邀约行 ---- */
.inv-row {
  display: flex;
  gap: 14px;
  background: rgba(255,255,255,.5);
  border: 1px solid rgba(222,214,199,0.9);
  border-radius: 14px;
  padding: 14px;
  transition: all .2s ease;
  position: relative;
  overflow: hidden;
}
.inv-row:hover {
  background: #fff;
  border-color: rgba(255,90,31,0.3);
  box-shadow: 0 6px 18px -10px rgba(44,36,24,0.15);
  transform: translateY(-1px);
}
.inv-row-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  padding-right: 12px;
  border-right: 1px dashed rgba(222,214,199,0.9);
  width: 76px;
}
.inv-status-bar {
  width: 4px;
  height: 100%;
  min-height: 90px;
  border-radius: 99px;
  position: absolute;
  left: 0; top: 0;
}
.sb-pending   { background: linear-gradient(180deg, #F59E0B, #D97706); }
.sb-accepted  { background: linear-gradient(180deg, #10B981, #047857); }
.sb-declined  { background: linear-gradient(180deg, #F43F5E, #9F1239); }
.sb-cancelled { background: linear-gradient(180deg, #94A3B8, #475569); }
.sb-completed { background: linear-gradient(180deg, #3B82F6, #1D4ED8); }

.inv-date-seal {
  width: 60px;
  text-align: center;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--line, #DED6C7);
  padding: 8px 4px 6px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.04);
}
.ids-month {
  font-size: 11px;
  font-weight: 700;
  color: #FF5A1F;
  letter-spacing: 0.05em;
}
.ids-day {
  font-family: var(--ff-display), "Noto Serif SC", Georgia, serif;
  font-size: 26px;
  font-weight: 900;
  color: var(--ink, #2C2418);
  line-height: 1.05;
  margin: 2px 0;
}
.ids-week {
  font-size: 10.5px;
  color: var(--ink-3, #8A7F68);
  font-weight: 600;
}

.inv-row-body { flex: 1; min-width: 0; }

.irb-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}
.irb-job-title {
  font-family: var(--ff-display), "Noto Serif SC", Georgia, serif;
  font-size: 17px;
  font-weight: 900;
  color: var(--ink, #2C2418);
  margin: 0;
  line-height: 1.3;
}
.irb-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-family: var(--ff-sub), -apple-system, sans-serif;
}
.irb-chip-level {
  background: rgba(61,90,254,0.08);
  border-color: rgba(61,90,254,0.2);
  color: #1D4ED8;
}
.irb-chip-type {
  background: #fff;
  border-color: var(--line, #DED6C7);
  color: var(--ink-2, #4B4235);
}
.irb-chip-type.type-online {
  background: rgba(61,90,254,0.05);
  border-color: rgba(61,90,254,0.2);
  color: #1D4ED8;
}
.irb-chip-type.type-onsite {
  background: rgba(255,90,31,0.05);
  border-color: rgba(255,90,31,0.2);
  color: #C2410C;
}
.st-pending   { background: rgba(245,158,11,0.10); border-color: rgba(245,158,11,0.28); color: #92400E; }
.st-accepted  { background: rgba(16,185,129,0.10); border-color: rgba(16,185,129,0.28); color: #065F46; }
.st-declined  { background: rgba(244,63,94,0.10);  border-color: rgba(244,63,94,0.28);  color: #9F1239; }
.st-cancelled { background: rgba(148,163,184,0.12);border-color: rgba(148,163,184,0.32);color: #475569; }
.st-completed { background: rgba(59,130,246,0.10); border-color: rgba(59,130,246,0.28); color: #1E40AF; }

.irb-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 7px 18px;
  padding: 10px 12px;
  background: rgba(222,214,199,0.22);
  border-radius: 10px;
  margin-bottom: 10px;
}
@media (min-width: 860px) {
  .irb-meta { grid-template-columns: 1.1fr 1.4fr 1.5fr; }
}
.irb-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  min-width: 0;
}
.irb-meta-k {
  color: var(--ink-3, #8A7F68);
  font-weight: 600;
  flex-shrink: 0;
}
.irb-meta-v {
  color: var(--ink-2, #4B4235);
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mi-cobalt  { color: #1D4ED8; flex-shrink: 0; }
.mi-seal    { color: #C2410C; flex-shrink: 0; }
.mi-emerald { color: #047857; flex-shrink: 0; }

.irb-messages {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.msg-bubble {
  padding: 9px 12px;
  border-radius: 11px;
  font-size: 12.5px;
  line-height: 1.6;
}
.msg-bubble.msg-enterprise {
  background: rgba(61,90,254,0.06);
  border: 1px solid rgba(61,90,254,0.15);
  border-left: 3px solid #3D5AFE;
}
.msg-bubble.msg-student {
  background: rgba(255,90,31,0.06);
  border: 1px solid rgba(255,90,31,0.15);
  border-left: 3px solid #FF5A1F;
}
.mb-sender {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-3, #8A7F68);
  margin-bottom: 3px;
  letter-spacing: 0.02em;
}
.msg-enterprise .mb-sender { color: #1D4ED8; }
.msg-student    .mb-sender { color: #C2410C; }
.mb-text { color: var(--ink-2, #4B4235); }

.irb-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(245,158,11,0.06);
  border: 1px dashed rgba(245,158,11,0.3);
  border-radius: 11px;
  flex-wrap: wrap;
}
.reply-input {
  height: 36px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1px solid var(--line, #DED6C7);
  background: #fff;
  font-size: 12.5px;
  color: var(--ink, #2C2418);
  outline: none;
  transition: all .2s ease;
  font-family: inherit;
}
.reply-input:focus {
  border-color: #FF5A1F;
  box-shadow: 0 0 0 3px rgba(255,90,31,0.10);
}

/* ---- 响应式 ---- */
@media (max-width: 720px) {
  .inv-stat-stamp .num { font-size: 24px; }
  .inv-row { flex-direction: column; }
  .inv-row-left {
    flex-direction: row;
    width: 100%;
    padding-right: 0;
    padding-bottom: 10px;
    border-right: none;
    border-bottom: 1px dashed rgba(222,214,199,0.9);
  }
  .inv-date-seal { width: 56px; }
  .irb-meta { grid-template-columns: 1fr; }
}
</style>
