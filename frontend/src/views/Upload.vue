<template>
  <!-- 整个页面：杂志编辑部 × 作品提交信封 -->
  <div class="upload-page">
    <!-- 背景装饰：柔和光晕 + 右下角印章水印 -->
    <div class="bg-glow bg-glow-seal" aria-hidden="true"></div>
    <div class="bg-glow bg-glow-cobalt" aria-hidden="true"></div>
    <div class="seal-watermark" aria-hidden="true">知训云 · 评价封缄</div>

    <div class="page-inner page-enter-stagger">

      <!-- HERO 标题区 -->
      <header class="hero-zone reveal reveal-1">
        <div class="hero-left">
          <span class="hero-chip">
            <span class="hero-chip-num">{{ currentTask ? 'STEP' : 'STEP' }}</span>
            <span class="hero-chip-text">{{ currentTask ? '02 · 提交实训成果' : '01 · 自由上传评价' }}</span>
          </span>
          <h1 class="hero-title">
            {{ currentTask ? '封缄你的作品' : '交付你的成果' }}
            <span class="hero-underline" aria-hidden="true"></span>
          </h1>
          <p class="hero-sub">
            {{ currentTask
              ? `任务《${currentTask.title}》· 上传成果物后，AI 将按评分维度进行多维度智能初评，再由教师复评${enterpriseInvolved ? '与企业终评' : ''}，形成最终评价。`
              : '自由上传模式 · 选择文件并补充实训要求，AI 会自动按四大维度为你的成果生成多维度智能评价报告。'
            }}
          </p>
          <div class="hero-meta-row">
            <div class="hero-meta">
              <div class="hero-meta-ic ic-doc"><Icon icon="mdi:file-document-multiple-outline" /></div>
              <div class="hero-meta-txt">
                <div class="hero-meta-num">{{ files.length }}</div>
                <div class="hero-meta-lbl">已投递文件</div>
              </div>
            </div>
            <div class="hero-meta">
              <div class="hero-meta-ic ic-crit"><Icon icon="mdi:layers-triple-outline" /></div>
              <div class="hero-meta-txt">
                <div class="hero-meta-num">{{ currentCriteria.length }}</div>
                <div class="hero-meta-lbl">评价维度</div>
              </div>
            </div>
            <div class="hero-meta">
              <div class="hero-meta-ic ic-eta"><Icon icon="mdi:timer-sand" /></div>
              <div class="hero-meta-txt">
                <div class="hero-meta-num">30~60s</div>
                <div class="hero-meta-lbl">预计耗时</div>
              </div>
            </div>
          </div>
        </div>
        <!-- Hero 右侧：装饰性编号标签 -->
        <aside class="hero-right" aria-hidden="true">
          <div class="hero-stamp">
            <div class="hero-stamp-no">№ {{ uploadNo }}</div>
            <div class="hero-stamp-divider"></div>
            <div class="hero-stamp-sub">ZHI XUN YUN · SUBMISSION</div>
          </div>
          <div class="hero-ornament">
            <div class="ho-ring ho-ring-1"></div>
            <div class="ho-ring ho-ring-2"></div>
            <div class="ho-ring ho-ring-3"></div>
          </div>
        </aside>
      </header>

      <!-- 三栏主区：任务简报 / 评价维度 / 文件投递口 -->
      <div class="main-grid">

        <!-- 左 · 任务简报 BRIEFING -->
        <section class="brief-card card-mag reveal reveal-2">
          <div class="card-top card-top-seal">
            <div class="card-eyebrow">
              <span class="card-eyebrow-num">01</span>
              <span class="card-eyebrow-text">BRIEFING · 任务简报</span>
            </div>
            <Icon icon="mdi:newspaper-variant-outline" class="card-top-ic" />
          </div>

          <div class="brief-body">
            <template v-if="currentTask">
              <div class="brief-title-block">
                <div class="brief-label">TASK TITLE</div>
                <h3 class="brief-title">{{ currentTask.title }}</h3>
              </div>
              <div class="brief-divider" aria-hidden="true">
                <span>❖</span>
              </div>
              <div class="brief-req-block">
                <div class="brief-label">REQUIREMENTS · 任务要求</div>
                <textarea
                  v-model="form.task_requirements"
                  :rows="7"
                  disabled
                  class="brief-req"
                ></textarea>
              </div>
            </template>
            <template v-else>
              <div class="brief-title-block">
                <div class="brief-label">FREE SUBMIT · 自由上传</div>
                <h3 class="brief-title">补充你的实训要求</h3>
              </div>
              <div class="brief-divider" aria-hidden="true">
                <span>❖</span>
              </div>
              <div class="brief-req-block">
                <div class="brief-label">REQUIREMENTS · 作为 AI 评判依据</div>
                <textarea
                  v-model="form.task_requirements"
                  :rows="7"
                  placeholder="请输入实训任务背景、功能要求、交付说明等，作为 AI 评判的参考依据..."
                  class="brief-req is-editable"
                ></textarea>
              </div>
            </template>
          </div>
        </section>

        <!-- 中 · 评价维度 CRITERIA -->
        <section class="crit-card card-mag reveal reveal-3">
          <div class="card-top card-top-cobalt">
            <div class="card-eyebrow">
              <span class="card-eyebrow-num">02</span>
              <span class="card-eyebrow-text">CRITERIA · 评价维度</span>
            </div>
            <Icon icon="mdi:scale-balance" class="card-top-ic" />
          </div>

          <div class="crit-body">
            <div class="crit-hint">
              AI 初评 + 教师复评{{ enterpriseInvolved ? ' + 企业终评' : '' }} 均会按照以下维度加权评分
            </div>
            <div class="crit-list"
                 :class="{'is-scrollable': currentCriteria.length > 5}">
              <div v-for="(c, i) in currentCriteria" :key="c"
                   class="crit-row"
                   :class="`crit-row-${criteriaColorKey(i)}`">
                <div class="crit-ic">
                  <Icon :icon="criteriaIcon(i)" />
                </div>
                <div class="crit-text">
                  <div class="crit-name">{{ c }}</div>
                  <div class="crit-desc">{{ criteriaDesc(i) }}</div>
                </div>
                <div class="crit-weight" title="维度权重（默认均分）">{{ defaultWeight(i) }}</div>
              </div>
            </div>
            <!-- 溢出滚动提示（维度>5时显示） -->
            <div v-if="currentCriteria.length > 5" class="crit-scroll-hint">
              <Icon icon="mdi:chevron-double-down" class="crit-scroll-ic" />
              <span>共 {{ currentCriteria.length }} 个维度 · 向下滚动查看全部</span>
            </div>
            <div class="crit-foot">
              <Icon icon="mdi:information-outline" class="crit-foot-ic" />
              <span class="crit-foot-text">最终分数按维度加权得出 · 三栏分差 ≥ 6 分会触发复核标记</span>
            </div>
          </div>
        </section>

        <!-- 右 · 文件投递口 DELIVERY（主视觉） -->
        <section class="delivery-card card-mag reveal reveal-4"
                 :class="{'is-drag-over': isDragOver}">
          <div class="card-top card-top-amber">
            <div class="card-eyebrow">
              <span class="card-eyebrow-num">03</span>
              <span class="card-eyebrow-text">DELIVERY · 作品投递口</span>
            </div>
            <Icon icon="mdi:inbox-arrow-down" class="card-top-ic" />
          </div>

          <div class="delivery-body">
            <!-- 上传区 -->
            <div class="delivery-zone"
                 :class="{'is-hover': isDragOver}">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                multiple
                :on-change="onFileChangeWrap"
                :on-remove="handleRemove"
                accept=".docx,.pdf,.png,.jpg,.jpeg,.py,.java,.cpp,.c,.h,.zip"
                drag
                class="delivery-upload"
              >
                <div class="dz-inner"
                     @dragenter.prevent="isDragOver = true"
                     @dragover.prevent="isDragOver = true"
                     @dragleave.prevent="isDragOver = false"
                     @drop.prevent="isDragOver = false">
                  <div class="dz-ornament-top" aria-hidden="true">
                    <span></span><span></span><span></span><span></span><span></span>
                  </div>
                  <div class="dz-stamp" aria-hidden="true">
                    <Icon icon="mdi:stamper" />
                  </div>
                  <div class="dz-ic">
                    <Icon icon="mdi:cloud-upload-outline" />
                  </div>
                  <div class="dz-title">投递你的作品</div>
                  <div class="dz-sub">
                    将文件拖入虚线框内，<span class="dz-kbd">或点击此处</span> 选择文件
                  </div>
                  <div class="dz-formats">
                    <span class="dz-format">.PDF</span>
                    <span class="dz-format">.DOCX</span>
                    <span class="dz-format">.PNG / .JPG</span>
                    <span class="dz-format">.PY · .JAVA · .CPP</span>
                    <span class="dz-format">.ZIP</span>
                  </div>
                  <div class="dz-ornament-bottom" aria-hidden="true">
                    <span></span><span></span><span></span><span></span><span></span>
                  </div>
                </div>
              </el-upload>
            </div>

            <!-- 已上传文件列表（信封样式） -->
            <transition-group name="file-list" tag="div" class="file-stack">
              <div v-for="(f, i) in files" :key="f.uid"
                   class="file-card"
                   :style="{'--stack-i': i}">
                <div class="file-stamp" :class="`file-stamp-${criteriaColorKey(i % 6)}`" aria-hidden="true">
                  № {{ String(i + 1).padStart(2, '0') }}
                </div>
                <div class="file-ic" :class="`file-ic-${fileExtTone(f.name)}`">
                  <Icon :icon="fileIcon(f.name)" />
                </div>
                <div class="file-info">
                  <div class="file-name" :title="f.name">{{ f.name }}</div>
                  <div class="file-meta">
                    <span class="file-size">{{ formatSize(f.size) }}</span>
                    <span class="file-dot">·</span>
                    <span class="file-ext">{{ fileExt(f.name) }}</span>
                  </div>
                </div>
                <button class="file-del"
                        @click="handleRemove(f)"
                        :title="`移除 ${f.name}`"
                        type="button">
                  <Icon icon="mdi:close" />
                </button>
              </div>
            </transition-group>

            <div v-if="files.length === 0" class="delivery-empty">
              <Icon icon="mdi:email-fast-outline" class="delivery-empty-ic" />
              <span>尚无作品投递 · 请先上传至少一个文件</span>
            </div>
          </div>
        </section>
      </div>

      <!-- 底部：提交动作区 -->

        <div class="action-btns">
          <button
            type="button"
            class="submit-btn"
            :class="{
              'is-disabled': files.length === 0 || submitting,
              'is-loading': submitting
            }"
            :disabled="files.length === 0 || submitting"
            @click="submitEvaluate"
          >
            <span v-if="submitting" class="submit-spinner" aria-hidden="true"></span>
            <Icon v-else icon="mdi:seal-variant" class="submit-ic" />
            <span class="submit-text">
              {{ submitting ? '正在创建评分任务…' : (currentTask ? '提交作业 · 开始评价' : '封缄并开始智能评价') }}
            </span>
            <span class="submit-arrow" aria-hidden="true">→</span>
          </button>
          
        </div>

    </div>

    <!-- G1-2: 异步 5 步评分进度（SSE 流式推送） -->
    <EvaluationProgress
      :visible="showProgress"
      :job-id="currentJobId"
      :mode="currentMode"
      @close="showProgress = false"
      @done="onEvalDone"
      @failed="onEvalFailed"
      @retry="submitting = false"
    />
  </div>
</template>

<script setup lang="ts">
// 【G1-2 + 保留兜底】
// 主链路: POST /api/upload-eval/async -> job_id -> EvaluationProgress (SSE) -> onEvalDone 跳结果页
// 兜底链路: async 端点失败 -> 回退老同步 POST /api/upload-eval/
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Loading, UploadFilled } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'
import EvaluationProgress from '../components/EvaluationProgress.vue'

const router = useRouter()
const submitting = ref(false)  // 替换原来的 loading（和 ElementPlus loading 变量不冲突）
const fallbackLoading = ref(false)
const showProgress = ref(false)
const currentJobId = ref('')
const currentMode = ref<'code' | 'doc' | 'auto'>('auto')
const files = ref<any[]>([])
const currentTask = ref<any>(null)
const uploadRef = ref<any>(null)

// 新增：拖拽态 / 页面装饰性编号
const isDragOver = ref(false)
const uploadNo = computed(() => {
  const t = Date.now() % 9999
  return String(t).padStart(4, '0')
})

// 新增：是否企业参与（影响 Hero 与维度区的文案）
const enterpriseInvolved = computed<boolean>(() => {
  const t = currentTask.value
  if (!t) return false
  if (typeof t.enterprise_involved === 'boolean') return t.enterprise_involved
  if (typeof t.enterprise_id === 'number' && t.enterprise_id > 0) return true
  if (typeof t.enterprise_job_id === 'number' && t.enterprise_job_id > 0) return true
  return !!t.enterprise_name
})

const form = reactive({
  task_requirements: '实训任务：实现登录模块，包含用户名密码输入框、登录按钮。要求：输入为空时提示用户、密码掩码显示、验证成功跳转主页、验证失败提示错误、代码有注释、界面美观。',
  task_id: 0
})

const currentCriteria = computed(() => {
  const taskCriteria = localStorage.getItem('current_task_criteria')
  if (taskCriteria) {
    return taskCriteria.split(',').map((c: string) => c.trim())
  }
  const saved = localStorage.getItem('criteria_config')
  if (saved) {
    return JSON.parse(saved).map((c: any) => c.name)
  }
  return ['代码质量', '功能完整性', '文档规范性', '界面设计']
})

/* ---------- 新增：评价维度视觉辅助函数 ---------- */
const CRIT_COLORS = ['cobalt', 'jade', 'amber', 'violet', 'seal', 'ink'] as const
function criteriaColorKey(i: number): typeof CRIT_COLORS[number] {
  return CRIT_COLORS[i % CRIT_COLORS.length]
}
function criteriaIcon(i: number): string {
  const name = (currentCriteria.value[i] || '').toLowerCase()
  if (name.includes('代码') || name.includes('code') || name.includes('质量')) return 'mdi:code-tags'
  if (name.includes('功能') || name.includes('完整') || name.includes('function')) return 'mdi:check-decagram-outline'
  if (name.includes('文档') || name.includes('规范') || name.includes('doc')) return 'mdi:notebook-outline'
  if (name.includes('界面') || name.includes('ui') || name.includes('设计')) return 'mdi:palette-outline'
  if (name.includes('岗位') || name.includes('匹配')) return 'mdi:briefcase-outline'
  if (name.includes('注释') || name.includes('可读')) return 'mdi:tooltip-text-outline'
  const fallbacks = ['mdi:star-four-points-outline', 'mdi:target', 'mdi:lightbulb-on-outline', 'mdi:rocket-launch-outline', 'mdi:certificate-outline', 'mdi:compass-outline']
  return fallbacks[i % fallbacks.length]
}
function criteriaDesc(i: number): string {
  const name = currentCriteria.value[i] || ''
  if (name.includes('代码') || name.includes('质量')) return '结构、可读性、注释、错误处理'
  if (name.includes('功能') || name.includes('完整')) return '需求覆盖度 · 边界场景 · 无严重 bug'
  if (name.includes('文档') || name.includes('规范')) return 'README / 注释 / 目录结构规范性'
  if (name.includes('界面') || name.includes('设计')) return 'UI 审美 · 交互逻辑 · 响应式表现'
  if (name.includes('岗位') || name.includes('匹配')) return '与目标岗位技能门槛的对齐程度'
  return 'AI + 教师两方综合评定加权'
}
function defaultWeight(i: number): string {
  const total = currentCriteria.value.length || 1
  const pct = Math.round(100 / total)
  // 最后一个承担余项，保证视觉和为 100
  if (i === total - 1) {
    const rest = 100 - pct * (total - 1)
    return `${rest}%`
  }
  return `${pct}%`
}

/* ---------- 新增：文件卡辅助函数 ---------- */
function fileExt(name: string): string {
  const m = (name || '').match(/\.([^.]+)$/)
  return m ? m[1].toUpperCase() : 'FILE'
}
function fileExtTone(name: string): string {
  const ext = fileExt(name).toLowerCase()
  if (['pdf'].includes(ext)) return 'seal'
  if (['docx', 'doc'].includes(ext)) return 'cobalt'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'jade'
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'amber'
  if (['py', 'java', 'cpp', 'c', 'h', 'hpp', 'js', 'ts', 'tsx', 'jsx', 'go', 'rs', 'rb', 'php'].includes(ext)) return 'violet'
  return 'ink'
}
function fileIcon(name: string): string {
  const ext = fileExt(name).toLowerCase()
  if (['pdf'].includes(ext)) return 'mdi:file-pdf-box'
  if (['docx', 'doc'].includes(ext)) return 'mdi:file-word-box'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'mdi:file-image-outline'
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'mdi:folder-zip-outline'
  if (['py'].includes(ext)) return 'mdi:language-python'
  if (['java'].includes(ext)) return 'mdi:language-java'
  if (['cpp', 'c', 'h', 'hpp'].includes(ext)) return 'mdi:language-cpp'
  if (['js', 'ts', 'tsx', 'jsx'].includes(ext)) return 'mdi:language-javascript'
  return 'mdi:file-document-outline'
}
function formatSize(bytes: number | undefined | null): string {
  if (!bytes || typeof bytes !== 'number' || !Number.isFinite(bytes)) return '— KB'
  const units = ['B', 'KB', 'MB', 'GB']
  let b = bytes, u = 0
  while (b >= 1024 && u < units.length - 1) { b /= 1024; u++ }
  return `${b.toFixed(b >= 10 || u === 0 ? 0 : 1)} ${units[u]}`
}

/* ---------- 新增：文件变化包装（复用旧 handleFileChange 语义）---------- */
function onFileChangeWrap(uploadFile: any) {
  // 手动关掉拖拽态（防止某些浏览器 dragleave 不触发）
  isDragOver.value = false
  handleFileChange(uploadFile)
}

function clearAllFiles() {
  files.value = []
  try { uploadRef.value?.clearFiles?.() } catch {}
  ElMessage.info('已清空所有待投递文件')
}

onMounted(() => {
  const taskData = localStorage.getItem('current_task')
  if (taskData) {
    const task = JSON.parse(taskData)
    currentTask.value = task
    form.task_requirements = task.requirements
    form.task_id = task.id
    if (task.criteria) {
      localStorage.setItem('current_task_criteria', task.criteria)
    }
  }
})

const handleFileChange = (uploadFile: any) => {
  files.value.push(uploadFile)
}

const handleRemove = (uploadFile: any) => {
  const idx = files.value.findIndex((f: any) => f.uid === uploadFile.uid)
  if (idx > -1) files.value.splice(idx, 1)
}

function buildFormData(): FormData {
  const saved = localStorage.getItem('criteria_config')
  const criteriaNames = saved
    ? JSON.parse(saved).map((c: any) => c.name).join(',')
    : '代码质量,功能完整性,文档规范性,界面设计'
  const formData = new FormData()
  files.value.forEach((f: any) => { formData.append('files', f.raw) })
  formData.append('task_requirements', form.task_requirements)
  formData.append('criteria', criteriaNames)
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  formData.append('student_id', String(user.id || 0))
  if (form.task_id > 0) formData.append('task_id', String(form.task_id))
  return formData
}

function detectModeFromFiles(): 'code' | 'doc' {
  const CODE_EXT = ['.py', '.java', '.cpp', '.cc', '.cxx', '.c++', '.c', '.h', '.hpp', '.hh', '.hxx', '.zip']
  const DOC_EXT = ['.docx', '.pdf', '.doc']
  let code = 0, doc = 0
  for (const f of files.value) {
    const low = (f.name || '').toLowerCase()
    if (CODE_EXT.some(ext => low.endsWith(ext))) code++
    if (DOC_EXT.some(ext => low.endsWith(ext))) doc++
  }
  return code >= doc ? 'code' : 'doc'
}

const submitEvaluate = async () => {
  if (files.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }

  // 确认弹窗
  try {
    const saved = localStorage.getItem('criteria_config')
    const criteriaNames = saved
      ? JSON.parse(saved).map((c: any) => c.name).join(',')
      : '代码质量,功能完整性,文档规范性,界面设计'

    await ElMessageBox.confirm(
      `文件：${files.value.map(f => f.name).join(', ')}\n\n实训要求：${form.task_requirements.substring(0, 60)}...\n\n评价维度：${criteriaNames}\n\n提交后AI将自动评分，确认无误？`,
      '确认提交',
      { confirmButtonText: '确认提交', cancelButtonText: '取消', type: 'info' }
    )
  } catch {
    return
  }

  const mode = detectModeFromFiles()
  currentMode.value = mode

  // ------ 主链路: async + SSE ------
  submitting.value = true
  let jobId = ''
  try {
    const formData = buildFormData()
    formData.append('check_plagiarism', 'true')
    formData.append('mode', mode)
    const resp = await axios.post(`${API_BASE}/api/upload-eval/async`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (resp.data?.success && resp.data?.job_id) {
      jobId = resp.data.job_id
      currentJobId.value = jobId
      showProgress.value = true
      // submitting 保持 true，避免用户重复点击（onDone/onFailed 会释放）
      return
    }
  } catch (err: any) {
    ElMessage.warning('异步接口不可用，自动降级为同步评分模式（' + (err.message || '未知错误') + '）')
  }

  // ------ 兜底链路: 同步 POST /api/upload-eval/ ------
  await runSyncFallback(mode)
}

async function runSyncFallback(_mode: string) {
  fallbackLoading.value = true
  try {
    const formData = buildFormData()
    const res = await axios.post(`${API_BASE}/api/upload-eval/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data?.success) {
      localStorage.setItem('eval_result', JSON.stringify(res.data))
      localStorage.removeItem('current_task')
      localStorage.removeItem('current_task_criteria')
      ElMessage.success(currentTask.value ? '作业提交成功！' : '评价完成！')
      router.replace('/app/result/latest')
    } else {
      ElMessage.error(res.data?.error || '评价失败')
    }
  } catch (err: any) {
    ElMessage.error('请求失败：' + (err.message || '未知错误'))
  } finally {
    submitting.value = false
    fallbackLoading.value = false
  }
}

function onEvalDone(result: any) {
  // 把 SSE done 里的结果按老同步接口的形状存一份，保证 Result.vue 无感
  const payload = {
    success: true,
    submission_id: result.submission_id,
    evaluation_id: result.evaluation_id,
    filename: result.filename,
    content: result.content,
    evaluation: result.evaluation,
    completeness: result.completeness,
    code_analysis: result.code_analysis,
  }
  localStorage.setItem('eval_result', JSON.stringify(payload))
  localStorage.setItem('last_submission_id', String(result.submission_id))
  localStorage.removeItem('current_task')
  localStorage.removeItem('current_task_criteria')
  submitting.value = false
  ElMessage.success(currentTask.value ? '作业提交成功！' : '评价完成！')
  setTimeout(() => {
    showProgress.value = false
    router.replace(result.submission_id ? `/app/result/${result.submission_id}` : '/app/result/latest')
  }, 900)
}

function onEvalFailed(err: string) {
  submitting.value = false
  ElMessage.error('评价失败：' + err)
}
</script>

<style scoped>
/* ============================================================
   Upload Page · 编辑部作品提交信封
   美学：Editorial Magazine × Paper Envelope × Seal
   ============================================================ */

/* ── 1. 页面整体与背景 ── */
.upload-page {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  padding: 56px 24px 80px;
  background:
    linear-gradient(180deg, rgba(255, 246, 238, 0.9) 0%, var(--paper) 35%, var(--paper) 100%);
}

.bg-glow {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  filter: blur(100px);
  opacity: 0.55;
  border-radius: 50%;
}
.bg-glow-seal {
  top: -160px; left: -80px;
  width: 520px; height: 520px;
  background: radial-gradient(circle, var(--seal) 0%, transparent 65%);
}
.bg-glow-cobalt {
  top: 10%; right: -140px;
  width: 480px; height: 480px;
  background: radial-gradient(circle, var(--cobalt) 0%, transparent 65%);
  opacity: 0.32;
}
.seal-watermark {
  position: fixed;
  right: -30px; bottom: 12%;
  z-index: 0;
  pointer-events: none;
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 130px;
  letter-spacing: 10px;
  color: transparent;
  -webkit-text-stroke: 2px rgba(255, 90, 31, 0.08);
  transform: rotate(-14deg);
  white-space: nowrap;
}

.page-inner {
  position: relative;
  z-index: 2;
  max-width: 1340px;
  margin: 0 auto;
}

/* ── 2. 入场交错揭示 ── */
.page-enter-stagger .reveal {
  opacity: 0;
  transform: translateY(18px);
  animation: reveal 700ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.reveal-1 { animation-delay: 40ms; }
.reveal-2 { animation-delay: 140ms; }
.reveal-3 { animation-delay: 220ms; }
.reveal-4 { animation-delay: 300ms; }
.reveal-5 { animation-delay: 380ms; }

@keyframes reveal {
  to { opacity: 1; transform: translateY(0); }
}

/* ── 3. HERO 标题区 ── */
.hero-zone {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
  gap: 36px;
  align-items: stretch;
  margin-bottom: 44px;
}
.hero-left { position: relative; }
.hero-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 8px 10px;
  border: 1px solid rgba(255, 90, 31, 0.35);
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.12), rgba(255, 140, 80, 0.05));
  border-radius: 999px;
  margin-bottom: 22px;
}
.hero-chip-num {
  font-family: var(--ff-mono);
  font-weight: 700;
  font-size: 10.5px;
  letter-spacing: 2px;
  color: #fff;
  background: linear-gradient(135deg, var(--seal), var(--seal-dark));
  padding: 4px 10px;
  border-radius: 999px;
  box-shadow: 0 6px 14px -8px rgba(255, 90, 31, 0.8);
}
.hero-chip-text {
  font-family: var(--ff-sub);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--seal-dark);
}

.hero-title {
  font-family: var(--ff-display);
  font-size: clamp(42px, 5.6vw, 78px);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin-bottom: 20px;
  position: relative;
  display: inline-block;
}
.hero-underline {
  position: absolute;
  left: 0; right: -8px; bottom: -12px;
  height: 14px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255, 90, 31, 0.35) 12%,
    rgba(255, 90, 31, 0.55) 50%,
    rgba(61, 90, 254, 0.35) 88%,
    transparent 100%);
  border-radius: 999px;
  z-index: -1;
  filter: blur(1px);
}

.hero-sub {
  font-family: var(--ff-body);
  font-size: 16px;
  line-height: 1.75;
  color: var(--ink-3);
  max-width: 680px;
  margin: 24px 0 32px;
  font-weight: 400;
  letter-spacing: 0.005em;
}

.hero-meta-row {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}
.hero-meta {
  flex: 1;
  min-width: 150px;
  max-width: 220px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: rgba(255, 253, 248, 0.8);
  backdrop-filter: blur(6px);
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  transition: all 0.25s ease;
}
.hero-meta:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 90, 31, 0.3);
  box-shadow: 0 12px 28px -16px rgba(15, 17, 21, 0.2);
}
.hero-meta-ic {
  width: 44px; height: 44px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.hero-meta-ic.ic-doc { background: rgba(61, 90, 254, 0.12); color: var(--cobalt); }
.hero-meta-ic.ic-crit { background: rgba(29, 185, 85, 0.12); color: var(--jade-dark); }
.hero-meta-ic.ic-eta { background: rgba(244, 183, 64, 0.15); color: var(--amber-dark); }
.hero-meta-num {
  font-family: var(--ff-display);
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
  color: var(--ink);
  letter-spacing: -0.02em;
}
.hero-meta-lbl {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: 0.85;
  margin-top: 5px;
}

/* Hero 右侧：装饰印章卡 */
.hero-right {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-stamp {
  position: relative;
  z-index: 2;
  width: 260px;
  aspect-ratio: 3/4;
  border-radius: 28px;
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.4) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #fff 0%, #fdf7ed 55%, #fbe6d4 100%);
  border: 2px solid var(--seal);
  box-shadow:
    0 30px 60px -20px rgba(15, 17, 21, 0.22),
    inset 0 0 0 6px rgba(255, 90, 31, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 26px;
  transform: rotate(2deg);
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.hero-stamp:hover { transform: rotate(-1deg) translateY(-4px) scale(1.01); }
.hero-stamp-no {
  font-family: var(--ff-display);
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
  color: var(--seal);
  letter-spacing: 3px;
}
.hero-stamp-divider {
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--seal) 20%, var(--seal) 80%, transparent);
  opacity: 0.45;
  margin: 18px 0 14px;
  position: relative;
}
.hero-stamp-divider::before,
.hero-stamp-divider::after {
  content: '❖';
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: #fdf5e9;
  padding: 0 6px;
  font-size: 11px;
  color: var(--seal);
}
.hero-stamp-divider::before { left: 20%; }
.hero-stamp-divider::after { right: 20%; }
.hero-stamp-sub {
  font-family: var(--ff-sub);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3.5px;
  text-transform: uppercase;
  color: var(--seal-dark);
  text-align: center;
  line-height: 1.8;
  opacity: 0.85;
}

/* Hero 装饰：三圈同心圆环 */
.hero-ornament {
  position: absolute;
  inset: auto -10px -20px auto;
  width: 240px; height: 240px;
  z-index: 1;
}
.ho-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed;
  inset: 0;
  margin: auto;
}
.ho-ring-1 { width: 80px;  height: 80px;  border-color: rgba(61, 90, 254, 0.3);  animation: spin 32s linear infinite; }
.ho-ring-2 { width: 150px; height: 150px; border-color: rgba(255, 90, 31, 0.22); animation: spin 48s linear infinite reverse; }
.ho-ring-3 { width: 230px; height: 230px; border-color: rgba(15, 17, 21, 0.08); animation: spin 72s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 4. 通用卡片头部（三卡共用） ── */
.main-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
  margin-bottom: 36px;
  align-items: stretch; /* 三卡等高关键 */
}

.card-mag {
  overflow: hidden;
  display: flex;          /* 配合等高 */
  flex-direction: column; /* 从上到下 */
  min-height: 0;          /* flex子项滚动关键 */
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0; /* 防止压缩头部 */
}
.card-top::before {
  content: '';
  position: absolute;
  left: 0; top: 0; right: 0;
  height: 4px;
}
.card-top-seal::before   { background: linear-gradient(90deg, var(--seal), #FF8A5C); }
.card-top-cobalt::before { background: linear-gradient(90deg, var(--cobalt), #6FC3FF); }
.card-top-amber::before  { background: linear-gradient(90deg, var(--amber), #FFD583); }

.card-top::after {
  content: '';
  position: absolute;
  right: -60px; top: -60px;
  width: 180px; height: 180px;
  border-radius: 50%;
  opacity: 0.08;
  pointer-events: none;
}
.card-top-seal::after   { background: radial-gradient(circle, var(--seal), transparent 60%); }
.card-top-cobalt::after { background: radial-gradient(circle, var(--cobalt), transparent 60%); }
.card-top-amber::after  { background: radial-gradient(circle, var(--amber), transparent 60%); }

.card-eyebrow { display: inline-flex; align-items: baseline; gap: 10px; }
.card-eyebrow-num {
  font-family: var(--ff-mono);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1px;
  width: 26px; height: 26px;
  border-radius: 9px;
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.card-top-seal   .card-eyebrow-num { background: linear-gradient(135deg, var(--seal), var(--seal-dark)); }
.card-top-cobalt .card-eyebrow-num { background: linear-gradient(135deg, var(--cobalt), var(--cobalt-dark)); }
.card-top-amber  .card-eyebrow-num { background: linear-gradient(135deg, var(--amber), var(--amber-dark)); color: var(--ink); }

.card-eyebrow-text {
  font-family: var(--ff-sub);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--ink-3);
}
.card-top-ic {
  font-size: 22px;
  opacity: 0.65;
  z-index: 1;
}
.card-top-seal   .card-top-ic { color: var(--seal-dark); }
.card-top-cobalt .card-top-ic { color: var(--cobalt-dark); }
.card-top-amber  .card-top-ic { color: var(--amber-dark); }

/* ── 5. 左 · 任务简报卡 ── */
.brief-body {
  padding: 6px 24px 26px;
  flex: 1;           /* 配合等高：占满卡片剩余空间 */
  min-height: 0;     /* flex 子项滚动关键 */
  display: flex;
  flex-direction: column;
}
.brief-title-block {
  margin-bottom: 18px;
  flex-shrink: 0;
}
.brief-label {
  font-family: var(--ff-sub);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--seal-dark);
  margin-bottom: 8px;
}
.brief-title {
  font-family: var(--ff-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.25;
  letter-spacing: -0.005em;
}

.brief-divider {
  text-align: center;
  font-size: 12px;
  color: var(--seal);
  opacity: 0.6;
  margin: 14px 0 16px;
  position: relative;
  flex-shrink: 0;
}
.brief-divider::before,
.brief-divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: calc(50% - 20px);
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--line));
}
.brief-divider::before { left: 0; }
.brief-divider::after  { right: 0; transform: scaleX(-1); }

.brief-req-block {
  position: relative;
  flex: 1;           /* textarea 区撑满剩下空间 */
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.brief-req {
  width: 100%;
  display: block;
  flex: 1;          /* 高度自适应 */
  min-height: 220px; /* 保底高度 */
  max-height: 100%;
  padding: 16px 18px;
  background:
    repeating-linear-gradient(transparent 0 27px, rgba(61, 90, 254, 0.06) 27px 28px),
    #FFFCF5;
  border: 1px solid var(--line-soft);
  border-left: 3px solid var(--seal);
  border-radius: 14px;
  font-family: var(--ff-body);
  font-size: 14px;
  line-height: 28px;
  color: var(--ink-2);
  resize: none;
  outline: none;
  transition: all 0.2s;
  cursor: default;
  overflow-y: auto;
}
/* 任务要求 textarea 自定义滚动条 */
.brief-req::-webkit-scrollbar {
  width: 6px;
}
.brief-req::-webkit-scrollbar-track {
  background: var(--paper-2);
  border-radius: 999px;
  margin: 8px 0;
}
.brief-req::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--seal), var(--amber));
  border-radius: 999px;
  opacity: 0.6;
}
.brief-req::-webkit-scrollbar-thumb:hover {
  opacity: 1;
  background: linear-gradient(180deg, var(--seal-dark), var(--amber-dark));
}
.brief-req.is-editable {
  cursor: text;
  border-left-color: var(--cobalt);
  background:
    repeating-linear-gradient(transparent 0 27px, rgba(61, 90, 254, 0.045) 27px 28px),
    #fff;
}
.brief-req.is-editable:focus {
  border-color: rgba(61, 90, 254, 0.45);
  box-shadow: 0 0 0 4px rgba(61, 90, 254, 0.1);
}
.brief-req::placeholder { color: rgba(42, 47, 58, 0.4); font-style: italic; }

/* ── 6. 中 · 评价维度卡 ── */
.crit-body {
  padding: 4px 22px 22px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.crit-hint {
  font-size: 12px;
  color: var(--ink-3);
  margin: 0 4px 16px;
  line-height: 1.7;
  flex-shrink: 0;
}
.crit-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
  max-height: 352px;  /* ≈ 5个 crit-row (62px ×5 + gap10px ×4 = 350px) */
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  margin-right: -6px;
  min-height: 0; /* flex 容器滚动关键 */
  flex-shrink: 0;
}
/* 自定义滚动条 - 评价维度列表 */
.crit-list::-webkit-scrollbar {
  width: 6px;
}
.crit-list::-webkit-scrollbar-track {
  background: var(--paper-2);
  border-radius: 999px;
  margin: 4px 0;
}
.crit-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--cobalt), var(--seal));
  border-radius: 999px;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.crit-list::-webkit-scrollbar-thumb:hover {
  opacity: 1;
  background: linear-gradient(180deg, var(--cobalt-dark), var(--seal-dark));
}
.crit-list.is-scrollable {
  -webkit-mask-image: linear-gradient(180deg, #000 0%, #000 calc(100% - 24px), transparent 100%);
  mask-image: linear-gradient(180deg, #000 0%, #000 calc(100% - 24px), transparent 100%);
  padding-bottom: 6px;
}
/* 溢出提示条 */
.crit-scroll-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 7px 12px;
  margin: -2px 0 10px;
  border-radius: 10px;
  background: linear-gradient(90deg, rgba(61, 90, 254, 0.08), rgba(139, 92, 246, 0.08));
  border: 1px solid rgba(61, 90, 254, 0.2);
  font-size: 11px;
  font-family: var(--ff-sub);
  font-weight: 600;
  color: var(--cobalt-dark);
  letter-spacing: 0.2px;
  animation: crit-scroll-pulse 2.2s ease-in-out infinite;
}
.crit-scroll-ic {
  font-size: 14px;
  animation: crit-scroll-bounce 1.4s ease-in-out infinite;
}
@keyframes crit-scroll-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(61, 90, 254, 0.22); }
  50%      { box-shadow: 0 0 0 5px rgba(61, 90, 254, 0.04); }
}
@keyframes crit-scroll-bounce {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(3px); }
}
.crit-row {
  display: grid;
  grid-template-columns: 42px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 11px 12px 11px 10px;
  border-radius: 14px;
  background: #FFFCF5;
  border: 1px solid var(--line-soft);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  flex-shrink: 0; /* 防止滚动时被压缩 */
}
.crit-row::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  opacity: 0.85;
}
.crit-row:hover { transform: translateX(3px); box-shadow: 0 8px 18px -14px rgba(15, 17, 21, 0.25); }

.crit-row-cobalt::before { background: var(--cobalt); }
.crit-row-jade::before   { background: var(--jade); }
.crit-row-amber::before  { background: var(--amber); }
.crit-row-violet::before { background: #8B5CF6; }
.crit-row-seal::before   { background: var(--seal); }
.crit-row-ink::before    { background: var(--ink-3); }

.crit-ic {
  width: 42px; height: 42px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  z-index: 1;
}
.crit-row-cobalt .crit-ic { background: rgba(61, 90, 254, 0.1); color: var(--cobalt); }
.crit-row-jade   .crit-ic { background: rgba(29, 185, 85, 0.12); color: var(--jade-dark); }
.crit-row-amber  .crit-ic { background: rgba(244, 183, 64, 0.18); color: var(--amber-dark); }
.crit-row-violet .crit-ic { background: rgba(139, 92, 246, 0.1); color: #6D28D9; }
.crit-row-seal   .crit-ic { background: rgba(255, 90, 31, 0.1); color: var(--seal-dark); }
.crit-row-ink    .crit-ic { background: rgba(42, 47, 58, 0.08); color: var(--ink-2); }

.crit-name {
  font-family: var(--ff-body);
  font-weight: 600;
  font-size: 15px;
  color: var(--ink);
  line-height: 1.25;
}
.crit-desc {
  font-size: 11.5px;
  color: var(--ink-3);
  margin-top: 3px;
  line-height: 1.5;
}
.crit-weight {
  font-family: var(--ff-mono);
  font-weight: 700;
  font-size: 13px;
  padding: 5px 10px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line-soft);
  color: var(--ink-2);
}
.crit-row-cobalt .crit-weight { color: var(--cobalt-dark); border-color: rgba(61, 90, 254, 0.25); background: rgba(61, 90, 254, 0.05); }
.crit-row-jade   .crit-weight { color: var(--jade-dark);   border-color: rgba(29, 185, 85, 0.25); background: rgba(29, 185, 85, 0.06); }
.crit-row-amber  .crit-weight { color: var(--amber-dark);  border-color: rgba(244, 183, 64, 0.35); background: rgba(244, 183, 64, 0.1); }
.crit-row-violet .crit-weight { color: #6D28D9;            border-color: rgba(139, 92, 246, 0.25); background: rgba(139, 92, 246, 0.06); }
.crit-row-seal   .crit-weight { color: var(--seal-dark);   border-color: rgba(255, 90, 31, 0.25); background: rgba(255, 90, 31, 0.05); }

.crit-foot {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  background: linear-gradient(90deg, rgba(61, 90, 254, 0.05), rgba(255, 90, 31, 0.05));
  border-radius: 12px;
  border: 1px solid var(--line-soft);
  font-size: 11.5px;
  color: var(--ink-3);
  line-height: 1.7;
}
.crit-foot-ic { flex-shrink: 0; font-size: 15px; margin-top: 1px; color: var(--cobalt-dark); }

/* ── 7. 右 · 文件投递口卡 ── */
.delivery-body {
  padding: 4px 22px 24px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.delivery-zone {
  position: relative;
  margin-bottom: 18px;
  transition: transform 0.3s ease;
  flex-shrink: 0; /* 上传区不压缩 */
}
.delivery-zone.is-hover { transform: scale(1.005); }

.delivery-card.is-drag-over {
  border-color: rgba(255, 90, 31, 0.55);
  box-shadow:
    0 20px 60px -22px rgba(255, 90, 31, 0.35),
    0 0 0 4px rgba(255, 90, 31, 0.08);
}

.delivery-upload { width: 100%; }
.delivery-upload :deep(.el-upload-dragger) {
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
  width: 100% !important;
}
.delivery-upload :deep(.el-upload-dragger:hover) {
  background: transparent !important;
}

.dz-inner {
  position: relative;
  padding: 42px 20px 34px;
  border: 2px dashed #D9C9A8;
  border-radius: 22px;
  background:
    repeating-linear-gradient(90deg, transparent 0 10px, rgba(217, 210, 192, 0.25) 10px 11px),
    repeating-linear-gradient(0deg,  transparent 0 10px, rgba(217, 210, 192, 0.18) 10px 11px),
    linear-gradient(180deg, #FFFCF3 0%, #FFF7E8 100%);
  text-align: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
}
.delivery-zone.is-hover .dz-inner,
.dz-inner:hover {
  border-color: var(--seal);
  background:
    repeating-linear-gradient(90deg, transparent 0 10px, rgba(255, 90, 31, 0.15) 10px 11px),
    repeating-linear-gradient(0deg,  transparent 0 10px, rgba(255, 90, 31, 0.08) 10px 11px),
    linear-gradient(180deg, #FFF5EC 0%, #FFEED6 100%);
  transform: translateY(-2px);
  box-shadow: 0 18px 40px -22px rgba(255, 90, 31, 0.35);
}

/* 虚线框四角装饰 */
.dz-ornament-top, .dz-ornament-bottom {
  position: absolute;
  left: 10px; right: 10px;
  height: 0;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}
.dz-ornament-top { top: 10px; }
.dz-ornament-bottom { bottom: 10px; }
.dz-ornament-top span, .dz-ornament-bottom span {
  width: 10px; height: 10px;
  border: 2px solid var(--seal);
  opacity: 0.55;
}
.dz-ornament-top span:nth-child(1) { border-right: none; border-bottom: none; border-top-left-radius: 6px; }
.dz-ornament-top span:nth-child(2) { border: none; border-top: 2px solid var(--seal); opacity: 0.25; }
.dz-ornament-top span:nth-child(3) { border: none; border-top: 2px solid var(--amber); opacity: 0.35; }
.dz-ornament-top span:nth-child(4) { border: none; border-top: 2px solid var(--cobalt); opacity: 0.25; }
.dz-ornament-top span:nth-child(5) { border-left: none; border-bottom: none; border-top-right-radius: 6px; border-color: var(--cobalt); opacity: 0.55; }

.dz-ornament-bottom span:nth-child(1) { border-right: none; border-top: none; border-bottom-left-radius: 6px; }
.dz-ornament-bottom span:nth-child(2) { border: none; border-bottom: 2px solid var(--seal); opacity: 0.25; }
.dz-ornament-bottom span:nth-child(3) { border: none; border-bottom: 2px solid var(--amber); opacity: 0.35; }
.dz-ornament-bottom span:nth-child(4) { border: none; border-bottom: 2px solid var(--cobalt); opacity: 0.25; }
.dz-ornament-bottom span:nth-child(5) { border-left: none; border-top: none; border-bottom-right-radius: 6px; border-color: var(--cobalt); opacity: 0.55; }

.dz-stamp {
  position: absolute;
  top: 14px; right: 18px;
  font-size: 14px;
  color: var(--seal);
  opacity: 0.35;
  transform: rotate(12deg);
}

.dz-ic {
  width: 78px; height: 78px;
  margin: 4px auto 16px;
  border-radius: 24px;
  background: linear-gradient(145deg, #fff 0%, #fff3e2 100%);
  border: 1px solid rgba(255, 90, 31, 0.2);
  box-shadow:
    0 14px 34px -20px rgba(255, 90, 31, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  display: flex; align-items: center; justify-content: center;
  font-size: 36px;
  color: var(--seal);
  animation: float 5s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-6px); }
}

.dz-title {
  font-family: var(--ff-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.005em;
  margin-bottom: 8px;
}
.dz-sub {
  font-size: 14px;
  color: var(--ink-3);
  line-height: 1.6;
}
.dz-kbd {
  display: inline-block;
  padding: 2px 8px;
  font-family: var(--ff-mono);
  font-size: 12px;
  color: var(--seal-dark);
  background: rgba(255, 90, 31, 0.1);
  border: 1px solid rgba(255, 90, 31, 0.25);
  border-radius: 6px;
  margin: 0 2px;
}

.dz-formats {
  margin-top: 22px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.dz-format {
  display: inline-block;
  padding: 5px 12px;
  font-family: var(--ff-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: var(--ink-3);
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  transition: all 0.2s;
}
.dz-format:hover {
  color: var(--seal-dark);
  border-color: rgba(255, 90, 31, 0.3);
  background: rgba(255, 90, 31, 0.06);
  transform: translateY(-1px);
}

/* 文件堆叠卡片（信封样式） */
.file-stack {
  position: relative;
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;  /* ≈ 5个 file-card (≈72px ×5 + gap10px ×4) = 400px */
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 6px;
  margin-right: -6px;
  min-height: 0;
  flex: 1;
}
/* 文件列表自定义滚动条 */
.file-stack::-webkit-scrollbar {
  width: 6px;
}
.file-stack::-webkit-scrollbar-track {
  background: var(--paper-2);
  border-radius: 999px;
  margin: 4px 0;
}
.file-stack::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--amber), var(--seal));
  border-radius: 999px;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.file-stack::-webkit-scrollbar-thumb:hover {
  opacity: 1;
  background: linear-gradient(180deg, var(--amber-dark), var(--seal-dark));
}

.file-card {
  position: relative;
  display: grid;
  grid-template-columns: 44px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 12px 12px 12px 52px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  box-shadow:
    0 1px 0 #fff inset,
    0 8px 22px -18px rgba(15, 17, 21, 0.35);
  transition: all 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: translateY(calc(var(--stack-i, 0) * 0px));
  overflow: hidden;
  flex-shrink: 0; /* 滚动时不压缩 */
}
.file-card::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 30px;
  background:
    linear-gradient(180deg, rgba(61, 90, 254, 0.06), transparent 70%),
    repeating-linear-gradient(90deg, transparent 0 18px, rgba(15, 17, 21, 0.035) 18px 19px);
  pointer-events: none;
}
.file-card:hover {
  transform: translateY(-3px) translateX(2px);
  box-shadow: 0 16px 30px -18px rgba(15, 17, 21, 0.4);
  border-color: rgba(255, 90, 31, 0.35);
}

.file-stamp {
  position: absolute;
  top: -2px; left: -2px;
  font-family: var(--ff-mono);
  font-size: 10px;
  font-weight: 700;
  padding: 5px 9px;
  color: #fff;
  border-bottom-right-radius: 12px;
  letter-spacing: 0.4px;
}
.file-stamp-cobalt { background: linear-gradient(135deg, var(--cobalt), #5E7CFF); }
.file-stamp-jade   { background: linear-gradient(135deg, var(--jade), #39D179); }
.file-stamp-amber  { background: linear-gradient(135deg, var(--amber), #FFC75A); color: var(--ink); }
.file-stamp-violet { background: linear-gradient(135deg, #8B5CF6, #A855F7); }
.file-stamp-seal   { background: linear-gradient(135deg, var(--seal), #FF7E40); }
.file-stamp-ink    { background: linear-gradient(135deg, var(--ink-2), var(--ink-3)); }

.file-ic {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  background: #fff;
  border: 1px solid var(--line-soft);
  z-index: 1;
}
.file-ic-seal   { background: rgba(255, 90, 31, 0.1);  color: var(--seal-dark); border-color: rgba(255, 90, 31, 0.2); }
.file-ic-cobalt { background: rgba(61, 90, 254, 0.1);  color: var(--cobalt-dark); border-color: rgba(61, 90, 254, 0.22); }
.file-ic-jade   { background: rgba(29, 185, 85, 0.12); color: var(--jade-dark);   border-color: rgba(29, 185, 85, 0.22); }
.file-ic-amber  { background: rgba(244, 183, 64, 0.18); color: var(--amber-dark); border-color: rgba(244, 183, 64, 0.3); }
.file-ic-violet { background: rgba(139, 92, 246, 0.1); color: #6D28D9;            border-color: rgba(139, 92, 246, 0.2); }
.file-ic-ink    { background: rgba(42, 47, 58, 0.06);  color: var(--ink-2);       border-color: var(--line-soft); }

.file-name {
  font-family: var(--ff-body);
  font-weight: 600;
  font-size: 14px;
  color: var(--ink);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}
.file-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 11.5px;
  color: var(--ink-3);
  font-family: var(--ff-mono);
}
.file-dot { opacity: 0.5; }
.file-ext {
  padding: 1px 6px;
  border-radius: 5px;
  background: rgba(15, 17, 21, 0.05);
  font-weight: 700;
  letter-spacing: 0.3px;
}

.file-del {
  width: 34px; height: 34px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--line-soft);
  color: var(--signal-dark);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.file-del:hover {
  background: linear-gradient(135deg, var(--signal), var(--signal-dark));
  color: #fff;
  border-color: var(--signal);
  transform: rotate(12deg) scale(1.05);
  box-shadow: 0 8px 18px -8px rgba(230, 57, 70, 0.55);
}

/* 文件卡入场动画 */
.file-list-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.file-list-leave-active {
  transition: all 0.3s ease;
  position: absolute;
}
.file-list-enter-from { opacity: 0; transform: translateX(-22px) scale(0.92); }
.file-list-leave-to   { opacity: 0; transform: translateX(30px) scale(0.9) rotate(4deg); }
.file-list-move       { transition: transform 0.35s ease; }

/* 空态 */
.delivery-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 18px;
  margin-top: 14px;
  border-radius: 14px;
  background: linear-gradient(90deg, rgba(244, 183, 64, 0.08), rgba(255, 90, 31, 0.06));
  border: 1px dashed rgba(244, 183, 64, 0.45);
  color: var(--amber-dark);
  font-size: 12.5px;
  font-weight: 500;
  flex-shrink: 0;
}
.delivery-empty-ic { font-size: 17px; flex-shrink: 0; }

/* ── 8. 底部动作区 ── */
.action-zone {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.2fr);
  gap: 20px;
  align-items: center;
  padding: 22px 28px;
  background: linear-gradient(135deg, rgba(255, 253, 248, 0.92), rgba(255, 246, 232, 0.92));
  backdrop-filter: blur(8px);
  border: 1px solid var(--line);
  border-radius: 26px;
  box-shadow: 0 20px 50px -30px rgba(15, 17, 21, 0.22);
  position: relative;
  overflow: hidden;
}
.action-zone::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--seal), var(--amber) 45%, var(--cobalt));
}

.action-hint {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: #fff;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
}
.action-hint-ic {
  flex-shrink: 0;
  width: 48px; height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(61, 90, 254, 0.12), rgba(139, 92, 246, 0.1));
  color: var(--cobalt-dark);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
}
.action-hint-title {
  font-family: var(--ff-sub);
  font-size: 12.5px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--ink);
  margin-bottom: 6px;
}
.action-hint-list {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 11.5px;
  font-family: var(--ff-mono);
  color: var(--ink-3);
  font-weight: 500;
}
.ah-line {
  display: inline-block;
  color: var(--seal);
  opacity: 0.6;
  font-weight: 700;
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 14px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.submit-btn {
  flex: 1;
  min-width: 360px;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 17px 28px;
  font-family: var(--ff-display);
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.005em;
  color: #fff;
  border-radius: 18px;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, var(--seal) 0%, var(--seal-dark) 55%, #A1280A 100%);
  box-shadow:
    0 18px 38px -16px rgba(255, 90, 31, 0.75),
    0 4px 0 rgba(180, 54, 15, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}
.submit-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 15% 20%, rgba(255, 255, 255, 0.22), transparent 45%);
  pointer-events: none;
}
.submit-btn:hover:not(.is-disabled):not(.is-loading) {
  transform: translateY(-3px);
  box-shadow:
    0 26px 48px -18px rgba(255, 90, 31, 0.85),
    0 6px 0 rgba(180, 54, 15, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.submit-btn:active:not(.is-disabled):not(.is-loading) {
  transform: translateY(2px);
  box-shadow:
    0 10px 20px -10px rgba(255, 90, 31, 0.6),
    0 2px 0 rgba(180, 54, 15, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.submit-btn.is-disabled {
  cursor: not-allowed;
  background: linear-gradient(135deg, #B9B099, #9A9280);
  box-shadow: 0 6px 16px -12px rgba(15, 17, 21, 0.25);
  opacity: 0.85;
}

.submit-btn.is-loading { cursor: progress; }

.submit-ic {
  font-size: 22px;
  z-index: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}
.submit-text { z-index: 1; }
.submit-arrow {
  font-family: var(--ff-mono);
  font-size: 22px;
  z-index: 1;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.submit-btn:hover:not(.is-disabled) .submit-arrow { transform: translateX(6px); }

.submit-spinner {
  width: 22px; height: 22px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  z-index: 1;
}

/* ── 9. 响应式 ── */
@media (max-width: 1180px) {
  .hero-zone { grid-template-columns: 1fr; }
  .hero-right { order: -1; justify-content: flex-start; }
  .hero-stamp {
    width: 200px; aspect-ratio: auto; height: 160px;
    transform: rotate(-1deg);
  }
  .main-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .delivery-card { grid-column: 1 / -1; }
}
@media (max-width: 820px) {
  .upload-page { padding: 32px 16px 60px; }
  .hero-zone { gap: 22px; margin-bottom: 28px; }
  .hero-title { font-size: 44px; }
  .hero-meta-row { gap: 10px; }
  .hero-meta { min-width: 140px; flex: 1 1 calc(50% - 10px); max-width: none; }
  .main-grid { grid-template-columns: 1fr; gap: 18px; margin-bottom: 22px; }
  .action-zone { grid-template-columns: 1fr; padding: 18px; gap: 16px; }
  .action-btns { justify-content: stretch; }
  .submit-btn { min-width: 0; width: 100%; font-size: 16px; padding: 15px 20px; }
  .action-btns .btn-mag { width: 100%; }
}
@media (max-width: 520px) {
  .hero-title { font-size: 36px; }
  .hero-right { display: none; }
  .hero-meta { flex: 1 1 100%; }
  .crit-row { grid-template-columns: 38px 1fr; }
  .crit-weight { grid-column: 1 / -1; justify-self: start; margin-top: 4px; }
  .file-card { grid-template-columns: 40px 1fr; padding-left: 46px; }
  .file-del  { grid-column: 1 / -1; justify-self: end; margin-top: 4px; }
  .action-hint-list { font-size: 10.5px; }
}
</style>