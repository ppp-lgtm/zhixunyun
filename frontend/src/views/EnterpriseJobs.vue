<template>
  <div class="min-h-full page-enter">
    <!-- 顶部 Header -->
    <div class="mb-8">
      <div class="flex items-end md:items-center justify-between flex-wrap gap-4 mb-5">
        <div>
          <h1 class="font-display text-3xl font-black text-ink tracking-tight">岗位管理</h1>
          <p class="text-ink-3 mt-1 text-[13.5px] font-body">发布和管理招聘岗位，配置技能门槛与绑定班级后，可在「岗位匹配榜」中自动匹配优秀学生。</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="loadJobs" :disabled="loading" class="btn-mag btn-mag-ghost px-4 py-2.5 text-[13px]">
            <Icon icon="mdi:refresh" class="mr-1" :class="{'animate-spin': loading}" /> 刷新
          </button>
          <button @click="openCreate" class="btn-mag btn-mag-primary px-4 py-2.5 text-[13px]">
            <Icon icon="mdi:plus" class="mr-1" /> 新建岗位
          </button>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="card-mag px-6 py-4 flex items-center gap-3 flex-wrap">
        <div class="relative w-72">
          <Icon icon="mdi:magnify" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-4" />
          <input v-model="keyword" @input="loadJobs" placeholder="搜索岗位名称 / 城市 / 标签…"
                 class="w-full h-10 rounded-xl border border-line bg-paper px-10 font-body text-[13.5px] text-ink outline-none focus:border-seal/40 focus:shadow-[0_0_0_4px_rgba(255,90,31,0.08)]" />
        </div>
        <select v-model="statusFilter" @change="loadJobs"
                class="h-10 rounded-xl border border-line bg-paper px-3 text-ink text-[13px] outline-none focus:border-seal/40">
          <option value="">全部状态</option>
          <option value="open">招聘中 (open)</option>
          <option value="paused">暂停 (paused)</option>
          <option value="closed">已截止 (closed)</option>
        </select>
        <div class="ml-auto text-[12.5px] text-ink-3">
          共 <b class="font-display text-ink text-[16px]">{{ total }}</b> 个岗位
        </div>
      </div>

      <!-- 接口错误提示 -->
      <div v-if="loadError" class="mt-5 rounded-2xl border-2 border-seal/30 bg-seal/[0.06] px-5 py-4 flex items-start gap-3">
        <Icon icon="mdi:alert-circle-outline" class="text-seal text-xl flex-shrink-0 mt-0.5" />
        <div class="text-[13.5px] text-seal-dark leading-[1.7] flex-1">{{ loadError }}</div>
        <button @click="loadJobs" class="chip-mag !text-[12px] !py-1 !px-3 flex-shrink-0">
          <Icon icon="mdi:refresh" class="mr-1" inline width="12" /> 重试
        </button>
      </div>
    </div>

    <!-- 岗位卡片列表 -->
    <div v-if="loading && !jobs.length" class="py-20 text-center text-ink-3 text-sm">
      <Icon icon="mdi:loading" class="text-4xl animate-spin mb-3 block mx-auto opacity-60" />
      正在加载岗位列表…
    </div>

    <div v-else-if="!jobs.length" class="py-20 text-center">
      <div class="w-24 h-24 rounded-2xl bg-line/50 flex items-center justify-center mx-auto mb-4">
        <Icon icon="mdi:briefcase-off-outline" class="text-5xl text-ink-4" />
      </div>
      <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">暂无岗位</p>
      <p class="text-[12.5px] text-ink-4 mb-5">点击右上角「新建岗位」创建第一个招聘岗位。</p>
      <button @click="openCreate" class="btn-mag btn-mag-primary px-5 py-2.5 text-[13px]">
        <Icon icon="mdi:plus" class="mr-1" /> 新建岗位
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="j in jobs" :key="j.id"
           class="card-mag p-0 overflow-hidden hover:-translate-y-0.5 hover:shadow-[0_12px_40px_-18px_rgba(15,23,42,0.2)] transition-all duration-200">
        <div class="h-2" :class="statusBarClass(j.status)"></div>
        <div class="p-6">
          <!-- 头部信息 -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-start gap-3 min-w-0">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-cobalt/15 to-violet-600/15 text-cobalt flex items-center justify-center flex-shrink-0">
                <Icon icon="mdi:briefcase-outline" class="text-2xl" />
              </div>
              <div class="min-w-0">
                <h3 class="font-display font-bold text-ink text-[17px] tracking-tight truncate">{{ j.title }}</h3>
                <p class="text-[12px] text-ink-3 mt-0.5">{{ j.job_type || '技术岗' }} · {{ j.level || '初级' }} · {{ j.city || '远程' }}</p>
              </div>
            </div>
            <span :class="statusChipClass(j.status)" class="chip-mag !text-[11px] !py-0.5 !px-2 flex-shrink-0">
              {{ statusLabel(j.status) }}
            </span>
          </div>

          <!-- 薪资 -->
          <div class="mb-4">
            <span class="font-display text-2xl font-black text-seal">{{ j.salary_range || '面议' }}</span>
            <span v-if="j.salary_range" class="text-[12px] text-ink-4 ml-2">· 月薪</span>
          </div>

          <!-- 关键信息 -->
          <div class="space-y-1.5 mb-4 text-[12.5px] text-ink-2">
            <div class="flex items-center gap-2" v-if="j.enterprise_name">
              <Icon icon="mdi:domain" class="text-cobalt" inline width="14" /> {{ j.enterprise_name }}
            </div>
            <div class="flex items-center gap-2" v-if="j.linked_class_ids?.length">
              <Icon icon="mdi:google-classroom" class="text-cobalt" inline width="14" />
              绑定班级：{{ j.linked_class_ids.length }} 个 · {{ j.tag_list?.length || 0 }} 技能标签
            </div>
            <div class="flex items-center gap-2">
              <Icon icon="mdi:calendar-outline" class="text-cobalt" inline width="14" />
              更新：{{ fmtDate(j.updated_at || j.created_at) }}
            </div>
          </div>

          <!-- 技能门槛 -->
          <div v-if="j.skill_requirements?.length" class="flex flex-wrap gap-1.5 mb-4">
            <span v-for="s in j.skill_requirements.slice(0, 5)" :key="s.name"
                  class="text-[11px] px-2 py-1 rounded-lg font-mono flex items-center gap-1"
                  :class="s.must ? 'bg-seal/10 text-seal-dark border border-seal/25' : 'bg-cobalt/10 text-cobalt border border-cobalt/20'">
              <span v-if="s.must"><Icon icon="mdi:shield-alert-outline" inline width="12" /></span>
              {{ s.name }} <span class="text-ink-4 opacity-80">≥{{ Math.round(s.threshold) }}</span>
            </span>
            <span v-if="j.skill_requirements.length > 5" class="text-[11px] px-2 py-1 rounded-lg bg-line/40 text-ink-4">
              +{{ j.skill_requirements.length - 5 }} …
            </span>
          </div>

          <!-- 操作按钮 -->
          <div class="flex flex-wrap gap-2 pt-4 border-t border-line/70">
            <button @click="$router.push(`/app/enterprise/matching`)"
                    class="flex-1 btn-mag btn-mag-ghost !px-3 !py-2 text-[12px]">
              <Icon icon="mdi:radar" class="mr-1" inline width="13" /> 匹配榜
            </button>
            <button @click="openEdit(j)"
                    class="flex-1 btn-mag btn-mag-primary !px-3 !py-2 text-[12px]">
              <Icon icon="mdi:pencil-outline" class="mr-1" inline width="13" /> 编辑
            </button>
            <button @click="removeJob(j)"
                    class="btn-mag btn-mag-danger !px-3 !py-2 text-[12px]">
              <Icon icon="mdi:delete-outline" inline width="13" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建 / 编辑 弹窗 -->
    <div v-if="dialog.visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-ink/50 backdrop-blur-sm" @click="dialog.visible = false"></div>
      <div class="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-paper shadow-[0_30px_80px_-20px_rgba(15,23,42,0.4)] ring-1 ring-line">
        <div class="px-8 py-6 border-b border-line/70 flex items-center justify-between">
          <div>
            <div class="section-label !mb-1 !text-[10.5px]">{{ dialog.isEdit ? 'EDIT' : 'CREATE' }}</div>
            <h2 class="font-display text-2xl font-black text-ink tracking-tight">
              {{ dialog.isEdit ? '编辑岗位' : '新建岗位' }}
            </h2>
          </div>
          <button @click="dialog.visible = false" class="w-9 h-9 rounded-xl hover:bg-line/50 flex items-center justify-center text-ink-3 hover:text-ink">
            <Icon icon="mdi:close" class="text-xl" />
          </button>
        </div>

        <div class="px-8 py-6 space-y-4">
          <!-- AI 生成需求 -->
          <div class="rounded-2xl border border-violet-500/20 bg-gradient-to-r from-violet-600/[0.06] via-violet-500/[0.05] to-cobalt/[0.06] p-4">
            <div class="flex items-center gap-3 flex-wrap">
              <div class="flex-1 min-w-[260px] flex items-center gap-2">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-cobalt text-white flex items-center justify-center flex-shrink-0 shadow-[0_8px_20px_-8px_rgba(124,58,237,0.6)]">
                  <Icon icon="mdi:star-three-points" class="text-xl" />
                </div>
                <div>
                  <div class="text-[12.5px] font-sub font-bold text-violet-900/90">AI 一键生成岗位需求</div>
                  <div class="text-[11.5px] text-violet-900/60 mt-0.5">输入岗位名称，智能生成描述、要求、职责、技能门槛与标签（可继续手动修改）</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <input v-model="aiJobTitle" placeholder="输入岗位名称，如：Python 后端工程师"
                       class="h-10 w-64 rounded-xl border border-violet-500/25 bg-paper px-3.5 text-[13px] text-ink outline-none focus:border-violet-600/50 focus:shadow-[0_0_0_4px_rgba(124,58,237,0.1)]" />
                <button type="button" @click="runAIJobGenerate" :disabled="aiGenerating"
                        class="btn-mag !py-2.5 !px-4 !text-[12.5px]"
                        :class="aiGenerating ? 'btn-mag-ghost opacity-70' : 'bg-gradient-to-r from-violet-600 to-cobalt text-white hover:opacity-95 !border-violet-600/0 shadow-[0_8px_20px_-10px_rgba(124,58,237,0.7)]'">
                  <Icon v-if="aiGenerating" icon="mdi:loading" class="mr-1 animate-spin" />
                  <Icon v-else icon="mdi:auto-fix" class="mr-1" inline width="14" />
                  {{ aiGenerating ? '生成中…' : 'AI 生成需求' }}
                </button>
              </div>
            </div>
            <div v-if="aiLastError" class="mt-3 text-[12px] text-seal-dark bg-seal/[0.06] border border-seal/20 rounded-xl px-3 py-2">
              <Icon icon="mdi:alert-circle-outline" class="mr-1 align-text-bottom" inline width="13" />
              {{ aiLastError }}
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">岗位名称 *</label>
              <input v-model="form.title" placeholder="如：初级 Python 全栈工程师" class="input-mag w-full" />
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">级别</label>
              <select v-model="form.level" class="input-mag w-full">
                <option value="实习">实习</option>
                <option value="初级">初级 (P4)</option>
                <option value="中级">中级 (P5)</option>
                <option value="高级">高级 (P6+)</option>
              </select>
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">薪资范围</label>
              <input v-model="form.salary_range" placeholder="如：12-20K" class="input-mag w-full" />
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">工作城市</label>
              <input v-model="form.city" placeholder="如：上海 / 杭州 / 远程" class="input-mag w-full" />
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">招聘状态</label>
              <select v-model="form.status" class="input-mag w-full">
                <option value="open">招聘中 open</option>
                <option value="paused">暂停 paused</option>
                <option value="closed">已截止 closed</option>
              </select>
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">标签（逗号分隔）</label>
              <input v-model="form.tags" placeholder="如：Python,FastAPI,Vue3" class="input-mag w-full" />
            </div>
          </div>

          <!-- 文本描述 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">岗位描述</label>
              <textarea v-model="form.description" rows="3" placeholder="业务方向、团队背景…" class="input-mag w-full resize-none"></textarea>
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">任职要求</label>
              <textarea v-model="form.requirements" rows="3" placeholder="学历 / 经验 / 基础要求…" class="input-mag w-full resize-none"></textarea>
            </div>
            <div>
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4 mb-1.5 block">岗位职责</label>
              <textarea v-model="form.responsibilities" rows="3" placeholder="日常工作 / 输出物…" class="input-mag w-full resize-none"></textarea>
            </div>
          </div>

          <!-- 技能门槛编辑 -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-[12px] font-sub font-bold uppercase tracking-[0.15em] text-ink-4">
                <Icon icon="mdi:shield-check-outline" class="mr-1 align-text-bottom" inline width="14" /> 技能门槛（用于匹配算法）
              </label>
              <button type="button" @click="addSkill" class="chip-mag !text-[11.5px] !py-1 !px-2.5">
                <Icon icon="mdi:plus" inline width="12" /> 新增维度
              </button>
            </div>
            <div class="rounded-xl border border-line overflow-hidden">
              <div class="grid grid-cols-[1.6fr_1fr_1fr_60px_28px] gap-2 px-4 py-2.5 bg-ink/[0.03] text-[11px] font-sub font-bold uppercase tracking-[0.1em] text-ink-4 border-b border-line/70">
                <div>维度 / 技能名</div>
                <div>权重</div>
                <div>门槛分</div>
                <div>必选</div>
                <div></div>
              </div>
              <div v-if="!form.skill_requirements.length" class="px-4 py-6 text-center text-[12.5px] text-ink-4 italic">
                暂未配置技能门槛，点击右上角「新增维度」添加
              </div>
              <div v-else class="divide-y divide-line/60">
                <div v-for="(s, idx) in form.skill_requirements" :key="idx"
                     class="grid grid-cols-[1.6fr_1fr_1fr_60px_28px] gap-2 px-4 py-2.5 items-center hover:bg-paper-2/40">
                  <input v-model="s.name" class="h-8 rounded-lg border border-line px-2.5 text-[12.5px] text-ink outline-none focus:border-seal/40" />
                  <div class="flex items-center gap-1.5">
                    <input v-model.number="s.weight" type="number" min="0" step="1" class="h-8 w-full rounded-lg border border-line px-2 text-[12px] font-mono outline-none focus:border-seal/40" />
                    <span class="text-[11px] text-ink-4 w-6">%</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <input v-model.number="s.threshold" type="number" min="0" max="100" step="1" class="h-8 w-full rounded-lg border border-line px-2 text-[12px] font-mono outline-none focus:border-seal/40" />
                    <span class="text-[11px] text-ink-4 w-6">/100</span>
                  </div>
                  <div class="flex items-center justify-center">
                    <input type="checkbox" v-model="s.must" class="w-4 h-4 accent-seal" />
                  </div>
                  <button type="button" @click="removeSkill(idx)"
                          class="w-7 h-7 rounded-lg hover:bg-seal/10 text-ink-3 hover:text-seal-dark flex items-center justify-center">
                    <Icon icon="mdi:delete-outline" class="text-base" />
                  </button>
                </div>
              </div>
            </div>
            <div class="text-[11.5px] text-ink-4 mt-1.5">
              权重合计：<b :class="weightSum === 100 ? 'text-jade-dark' : 'text-seal-dark'">{{ weightSum }}</b>
              <span v-if="weightSum !== 100" class="ml-1">（推荐 100，不影响算法）</span>
            </div>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="px-8 py-5 border-t border-line/70 flex items-center justify-end gap-3">
          <button @click="dialog.visible = false" class="btn-mag btn-mag-ghost px-5 py-2.5 text-[13px]">取消</button>
          <button @click="submitJob" :disabled="submitting" class="btn-mag btn-mag-primary px-5 py-2.5 text-[13px]">
            <Icon v-if="submitting" icon="mdi:loading" class="mr-1 animate-spin" />
            {{ submitting ? '提交中…' : (dialog.isEdit ? '保存修改' : '创建岗位') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'
import { API_BASE } from '../config'

type JobT = any
type SkillT = { name: string; weight: number; threshold: number; must: boolean }

const loading = ref(false)
const submitting = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loadError = ref('')

const jobs = ref<JobT[]>([])
const classOptions = ref<any[]>([])
const aiJobTitle = ref('')
const aiGenerating = ref(false)
const aiLastError = ref('')

const dialog = reactive({
  visible: false,
  isEdit: false,
  editingId: 0 as number,
})

const form = reactive<{
  title: string; level: string; salary_range: string; city: string;
  description: string; requirements: string; responsibilities: string;
  tags: string; linked_class_ids: number[]; status: string;
  skill_requirements: SkillT[];
}>({
  title: '', level: '初级', salary_range: '', city: '',
  description: '', requirements: '', responsibilities: '',
  tags: '', linked_class_ids: [], status: 'open',
  skill_requirements: [],
})

function resetForm() {
  form.title = ''; form.level = '初级'
  form.salary_range = ''; form.city = ''
  form.description = ''; form.requirements = ''; form.responsibilities = ''
  form.tags = ''; form.linked_class_ids = []; form.status = 'open'
  form.skill_requirements = [
    { name: '代码质量', weight: 30, threshold: 70, must: true },
    { name: '功能完整性', weight: 30, threshold: 70, must: true },
    { name: '文档规范性', weight: 15, threshold: 65, must: false },
    { name: '异常处理', weight: 15, threshold: 65, must: false },
    { name: '界面设计', weight: 10, threshold: 60, must: false },
  ]
  aiJobTitle.value = ''
  aiLastError.value = ''
}

function openCreate() {
  resetForm()
  dialog.isEdit = false
  dialog.editingId = 0
  dialog.visible = true
}

function openEdit(j: JobT) {
  resetForm()
  dialog.isEdit = true
  dialog.editingId = Number(j.id)
  form.title = j.title || ''
  aiJobTitle.value = j.title || ''
  form.level = j.level || '初级'
  form.salary_range = j.salary_range || ''
  form.city = j.city || ''
  form.description = j.description || ''
  form.requirements = j.requirements || ''
  form.responsibilities = j.responsibilities || ''
  form.tags = j.tags || ''
  form.status = j.status || 'open'
  form.linked_class_ids = [...(j.linked_class_ids || [])]
  form.skill_requirements = (j.skill_requirements || []).map((s: any) => ({
    name: s.name || '', weight: Number(s.weight) || 0,
    threshold: Number(s.threshold) || 0, must: !!s.must,
  }))
  dialog.visible = true
}

function addSkill() {
  form.skill_requirements.push({ name: '新维度', weight: 10, threshold: 60, must: false })
}
function removeSkill(idx: number) {
  form.skill_requirements.splice(idx, 1)
}

const weightSum = computed(() =>
  Math.round(form.skill_requirements.reduce((s: number, r: SkillT) => s + (Number(r.weight) || 0), 0))
)

/* API helpers */
function authHeaders(): any {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function runAIJobGenerate() {
  const t = (aiJobTitle.value || form.title || '').trim()
  if (!t) {
    alert('请先在上方输入岗位名称，再点击 AI 生成需求')
    return
  }
  aiGenerating.value = true
  aiLastError.value = ''
  try {
    const r = await axios.post(`${API_BASE}/api/enterprise/jobs/ai-generate`, { title: t }, { headers: authHeaders() })
    if (r.data?.success === false) throw new Error(r.data?.message || r.data?.error || '生成失败')
    // 兼容两种返回：后端目前平铺字段在顶层（success/title/description/.../skill_tags），
    // 也兼容未来包一层 data 的结构：优先取 r.data.data，再 fallback 到 r.data 本身
    const dataRaw = (r.data?.data && typeof r.data.data === 'object' && (r.data.data.description || r.data.data.skill_tags))
      ? r.data.data
      : r.data
    const data = dataRaw ?? {}
    form.title = (data.title as string) || t
    form.description = (data.description ?? '') as string
    form.requirements = (data.requirements ?? '') as string
    form.responsibilities = (data.responsibilities ?? '') as string
    const skillTags = Array.isArray(data.skill_tags) ? data.skill_tags : []
    if (skillTags.length) {
      const existing = (form.tags ? String(form.tags).split(',').map((x) => x.trim()).filter(Boolean) : [])
      const merged = Array.from(new Set([...existing, ...skillTags.map((s: any) => String(s).trim()).filter(Boolean)]))
      form.tags = merged.join(',')
    }
    const skillReqs = Array.isArray(data.skill_requirements) ? data.skill_requirements : []
    if (skillReqs.length) {
      const normalized = skillReqs.map((s: any) => ({
        name: String(s?.name || ''),
        weight: Number(s?.weight ?? (s?.must ? 25 : 15)) || 15,
        threshold: Number(s?.threshold ?? (s?.must ? 75 : 65)) || 65,
        must: !!s?.must,
      })).filter((s: SkillT) => s.name)
      if (normalized.length) {
        // 后端返回的 weight 可能是 0~1 之和≈1 的小数，也可能是百分比整数；这里统一归一到百分比（总和 100）
        const rawSum = normalized.reduce((a: number, b: SkillT) => a + (Number(b.weight) || 0), 0) || 1
        const scaleToPercent = rawSum > 0 && rawSum <= 1.5 // 推测是 0~1 小数
        if (scaleToPercent) {
          normalized.forEach((s: SkillT) => { s.weight = Math.max(1, Math.round((Number(s.weight) || 0) * 100)) })
        } else {
          normalized.forEach((s: SkillT) => { s.weight = Math.max(1, Math.round(Number(s.weight) || 15)) })
        }
        const totalAfter = normalized.reduce((a: number, b: SkillT) => a + (Number(b.weight) || 0), 0) || 1
        if (Math.abs(totalAfter - 100) > 0.01) {
          const ratio = 100 / totalAfter
          normalized.forEach((s: SkillT) => {
            s.weight = Math.max(1, Math.round((Number(s.weight) || 0) * ratio))
          })
          const off = normalized.reduce((a: number, b: SkillT) => a + (Number(b.weight) || 0), 0) - 100
          if (normalized[0]) normalized[0].weight = Math.max(1, (Number(normalized[0].weight) || 0) - off)
        }
        form.skill_requirements = normalized
      }
    }
    // 如果成功但核心字段仍为空，直接提示（避免用户以为自己操作错了）
    if (!form.description && !form.requirements && !form.responsibilities && !skillReqs.length) {
      aiLastError.value = 'AI 返回内容为空，可能 LLM 输出被截断或未按 JSON 格式返回；请重试或手动填写。'
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.response?.data?.message || e?.response?.data?.error || e?.message || '未知错误'
    aiLastError.value = `AI 生成失败：${msg}（请确认后端已启动并配置 LLM，可手动填写其余字段）`
  } finally {
    aiGenerating.value = false
  }
}

async function loadClassOptions() {
  try {
    const r = await axios.get(`${API_BASE}/api/enterprise/linked-classes/options`, { headers: authHeaders() })
    classOptions.value = (r.data as any)?.list || (r.data as any)?.data?.list || []
  } catch (e: any) {
    classOptions.value = []
  }
}

async function loadJobs() {
  loading.value = true
  loadError.value = ''
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const r = await axios.get(`${API_BASE}/api/enterprise/jobs`, { headers: authHeaders(), params })
    const payload: any = r.data
    jobs.value = payload.list || payload.data?.list || []
    total.value = payload.total ?? (payload.data?.total ?? jobs.value.length)
  } catch (e: any) {
    jobs.value = []
    total.value = 0
    const msg = e?.response?.data?.detail || e?.message || '接口请求失败'
    loadError.value = `岗位列表加载失败：${msg}（请确认已启动后端服务，且当前为企业导师账号）`
  } finally {
    loading.value = false
  }
}

async function submitJob() {
  if (!form.title.trim()) {
    alert('请输入岗位名称')
    return
  }
  submitting.value = true
  const payload = {
    title: form.title, level: form.level,
    salary_range: form.salary_range, city: form.city,
    description: form.description, requirements: form.requirements, responsibilities: form.responsibilities,
    tags: form.tags,
    linked_classes: '',
    status: form.status,
    skill_requirements: form.skill_requirements.map(s => ({
      name: s.name, weight: Number(s.weight) || 0,
      threshold: Number(s.threshold) || 0, must: !!s.must,
    })),
  }
  try {
    let resp: any
    if (dialog.isEdit) {
      resp = await axios.put(`${API_BASE}/api/enterprise/jobs/${dialog.editingId}`, payload, { headers: authHeaders() })
    } else {
      resp = await axios.post(`${API_BASE}/api/enterprise/jobs`, payload, { headers: authHeaders() })
    }
    if (resp.data?.success !== false) {
      dialog.visible = false
      await loadJobs()
    } else {
      alert(resp.data?.message || '提交失败')
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    alert(`提交失败：${msg}\n（如未登录请先登录企业导师账号）`)
  } finally {
    submitting.value = false
  }
}

async function removeJob(j: JobT) {
  if (!confirm(`确定删除岗位【${j.title}】吗？该操作不可撤销，所有绑定该岗位的企业评价会自动解除 matched_job 关联。`)) return
  try {
    await axios.delete(`${API_BASE}/api/enterprise/jobs/${j.id}`, { headers: authHeaders() })
    await loadJobs()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    alert(`删除失败：${msg}`)
  }
}

/* utils */
function statusLabel(s: string) {
  return s === 'open' ? '招聘中' : s === 'paused' ? '暂停' : s === 'closed' ? '已截止' : (s || '未知')
}
function statusBarClass(s: string) {
  if (s === 'open') return 'bg-gradient-to-r from-jade via-emerald-500 to-cobalt'
  if (s === 'paused') return 'bg-gradient-to-r from-amber to-orange-400'
  if (s === 'closed') return 'bg-gradient-to-r from-ink-4 to-ink-3'
  return 'bg-gradient-to-r from-cobalt to-violet-600'
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
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(async () => {
  await Promise.all([loadClassOptions(), loadJobs()])
})
</script>

<style scoped>
.input-mag {
  height: 40px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  background: #FFFDF8;
  color: #0F172A;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: all 0.18s;
}
textarea.input-mag {
  height: auto;
  padding: 10px 14px;
}
.input-mag:focus {
  border-color: rgba(255, 90, 31, 0.4);
  box-shadow: 0 0 0 4px rgba(255, 90, 31, 0.08);
}
</style>
