<template>
  <!-- ══════════════════════════════════════
       LOGIN · Magazine × Paper × Seal Design
       严格对齐 frontend_ui_demo.html Hero 区
       ══════════════════════════════════════ -->
  <div class="shell-login">

    <!-- ═══ 复用 Demo 同款 Topbar ═══ -->
    <div class="topbar-mag">
      <div class="topbar-inner-mag">
        <div class="brand-mag">
          <div class="brand-mark-mag">
            <span style="position:relative;z-index:1">知训云</span>
          </div>
          <div class="brand-text-mag">
            <b>ZHI · XUN · YUN</b>
            <span>Software Training Intelligence Platform</span>
          </div>
        </div>
        <nav class="nav-mag">
          <a href="#hero" class="nav-link-mag">首页</a>
          <a href="#feat" class="nav-link-mag">功能</a>
          <a href="#about" class="nav-link-mag">关于</a>
          <router-link to="/landing" class="nav-pill-mag">查看演示 →</router-link>
        </nav>
      </div>
      <!-- Chip anchor row -->
      <div class="chip-nav-mag">
        <a href="#hero" class="chip-mag active"><b>00</b>封面 · 登录</a>
        <a href="#feat" class="chip-mag"><b>01</b>核心能力</a>
        <a href="#about" class="chip-mag"><b>02</b>平台介绍</a>
      </div>
    </div>

    <!-- ═══ HERO 区（对齐 demo 左 Hero + 右 Seal + 登录卡）════ -->
    <section id="hero" class="hero-sec">
      <!-- 左：Hero 文案 + 统计 -->
      <div class="hero-left">
        <span class="section-label">Portal · Sign in · v3.0</span>
        <h1 class="hero-title">
          给代码实训<br/>
          一枚诚实的<br/>
          <em class="accent-text">印章</em>。
        </h1>
        <p class="hero-sub">
          「知训云」智能实训评价平台：把实训批改从"下载 zip → 拖 IDE → 写评语"的机械劳动，搬进一个
          <b class="hero-bold">编辑杂志式 × 科技可视化</b> 的操作台。学生按步骤提交证据，AI 给每条步骤打分；老师和企业方只需聚焦差异点。
        </p>

        <!-- 4 项核心数据卡（对齐 demo hstat） -->
        <div class="hero-stats">
          <div class="hstat">
            <div class="n">98<small>%</small></div>
            <div class="l">步骤判定准确率<br/><span>规则 + AI 双校验</span></div>
          </div>
          <div class="hstat">
            <div class="n">47<small>s</small></div>
            <div class="l">平均批改耗时<br/><span>原人工 9 min / 份</span></div>
          </div>
          <div class="hstat">
            <div class="n">3<small>方</small></div>
            <div class="l">AI · 教师 · 企业<br/><span>对标评价一键同屏</span></div>
          </div>
          <div class="hstat">
            <div class="n">24<small>项</small></div>
            <div class="l">静态代码指标<br/><span>抄袭检测敏感度 0.85</span></div>
          </div>
        </div>

        <div class="cta-row">
          <a href="#feat" class="btn-mag accent">了解功能 <span class="arrow">→</span></a>
          <router-link to="/landing" class="btn-mag ghost">查看演示 <span class="arrow">→</span></router-link>
        </div>
      </div>

      <!-- 右：三栏身份选择 + 选中角色专属登录表单（角色隔离） -->
      <div class="hero-right">
        <!-- ① 身份选择（三张大卡堆叠式，可切换；URL hash 直达：#student / #teacher / #enterprise） -->
        <div class="role-selector" :class="{'is-chosen': chosenRole !== null}">
          <div
            v-for="role in roles"
            :key="role.key"
            class="role-card"
            :class="['role-'+role.key, {'active': chosenRole === role.key, 'inactive': chosenRole !== null && chosenRole !== role.key}]"
            @click="chooseRole(role.key, $event)"
          >
            <div class="role-head">
              <div class="role-ico" aria-hidden="true">
                <!-- SVG 角色图标（内嵌，无外部资源） -->
                <svg v-if="role.key === 'student'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 8.5l9-4.5 9 4.5-9 4.5-9-4.5z"/><path d="M6.5 10.5v4.6c0 1.2 2.5 2.2 5.5 2.4"/><path d="M17.5 10.5v1.8"/><path d="M21 8.5v4"/></svg>
                <svg v-else-if="role.key === 'teacher'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 6h13v12H4z"/><path d="M17 9h3v9h-3"/><path d="M7 9h6M7 12h6M7 15h4"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20h16V10H4zM3 20h1v-9H3zM20 20h1v-9h-1zM8 10V7l2-3h4l2 3v3"/><path d="M8 14h2M14 14h2M8 17h2M14 17h2"/></svg>
              </div>
              <div class="role-text">
                <div class="role-chip">{{ role.chip }}</div>
                <div class="role-title">{{ role.title }}</div>
              </div>
              <div class="role-mark">
                <span v-if="chosenRole === role.key">●</span>
                <span v-else>○</span>
              </div>
            </div>
            <div class="role-slogan" :class="{'is-collapsed': chosenRole !== null && chosenRole !== role.key}">
              {{ role.slogan }}
            </div>

            <!-- ② 专属登录表单（仅选中角色展开；每个角色独立表单域独立验证逻辑；账号与角色强绑定） -->
            <Transition name="expand" appear>
              <div v-if="chosenRole === role.key" class="role-form">
                <div class="form-divider" aria-hidden="true"></div>

                <div class="form-eyebrow">
                  <span class="dot"></span>
                  <span class="eyebrow-text">{{ role.eyebrow }}</span>
                </div>

                <el-form
                  :model="formByRole[role.key]"
                  :rules="rules"
                  :ref="(el: any) => setFormRef(role.key, el)"
                  class="mt-3"
                  @submit.prevent="submitLogin(role.key)"
                >
                  <div class="field">
                    <label>{{ role.usernameLabel }}</label>
                    <el-input
                      v-model="formByRole[role.key].username"
                      :placeholder="role.usernamePlaceholder"
                      size="large"
                      clearable
                      :ref="(el: any) => setUsernameInputRef(role.key, el)"
                    />
                  </div>

                  <div class="field">
                    <label>{{ role.passwordLabel }}</label>
                    <el-input
                      v-model="formByRole[role.key].password"
                      type="password"
                      placeholder="请输入密码"
                      size="large"
                      show-password
                      @keyup.enter="submitLogin(role.key)"
                    />
                  </div>

                  <div class="toggle-row">
                    <label class="flex items-center gap-2 cursor-pointer select-none">
                      <input type="checkbox" v-model="keepSession" class="w-4 h-4" :style="{accentColor: role.accent}" />
                      <span>保持本次会话</span>
                    </label>
                    <a href="#" class="forgot-link">忘记密码？</a>
                  </div>

                  <div class="login-foot">
                    <button
                      type="button"
                      @click="submitLogin(role.key)"
                      :disabled="loadingByRole[role.key]"
                      class="btn-mag btn-role"
                      :style="{'--btn-bg': role.accent}"
                    >
                      <span v-if="loadingByRole[role.key]" class="w-5 h-5 border-2 border-paper/30 border-t-paper rounded-full animate-spin"></span>
                      <Icon v-else icon="mdi:login" class="text-base" />
                      <span>{{ loadingByRole[role.key] ? '正在验证...' : role.ctaText }}</span>
                    </button>
                    <span class="meta-note">v3.0 · 仅限{{ role.title }}账号</span>
                  </div>
                </el-form>

                <div class="register-row">
                  <span>还没有{{ role.title }}账号？</span>
                  <el-button link type="primary" @click="openRegister(role.key)" class="!font-sub !text-base !p-0 !h-auto role-link" :style="{color: role.accent}">
                    立即注册 →
                  </el-button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ 功能介绍区 ═══ -->
    <section id="feat" class="feat-sec">
      <div class="text-center mb-14">
        <span class="section-label" style="justify-content:center">Features · 能力矩阵</span>
        <h2 class="font-display text-center text-ink" style="font-size:clamp(32px,4.4vw,48px);line-height:1.05;margin-top:6px">
          一份批改，输出 <em class="accent-text">24 项指标</em> 的体检。
        </h2>
        <p class="hero-sub text-center mx-auto mt-3">
          从代码静态分析 → 抄袭雷同检测 → 分步实训判定 → AI/教师/企业三方对标，全链路打通。
        </p>
      </div>

      <div class="feat-grid">
        <div class="card-mag feat-card">
          <div class="feat-ico co"><Icon icon="mdi:file-code-outline" class="text-2xl" /></div>
          <span class="section-label" style="margin:0;letter-spacing:2px;font-size:11px">D1 · Code Analysis</span>
          <h4 class="feat-title">代码质量体检</h4>
          <p class="feat-desc">LOC / 注释率 / 圈复杂度 / TODO 数 / 函数计数，单文件与整包 zip 全支持。</p>
        </div>
        <div class="card-mag feat-card">
          <div class="feat-ico bad"><Icon icon="mdi:alert-octagon-outline" class="text-2xl" /></div>
          <span class="section-label" style="margin:0;letter-spacing:2px;font-size:11px">D1 · Plagiarism</span>
          <h4 class="feat-title">雷同抄袭检测</h4>
          <p class="feat-desc">基于结构 Token 的 Jaccard 相似度，阈值 0.85 自动告警，支持 TOP-N 匹配。</p>
        </div>
        <div class="card-mag feat-card">
          <div class="feat-ico ok"><Icon icon="mdi:clipboard-check-outline" class="text-2xl" /></div>
          <span class="section-label" style="margin:0;letter-spacing:2px;font-size:11px">E1 · Step Mode</span>
          <h4 class="feat-title">分步实训提交</h4>
          <p class="feat-desc">每一步独立提交代码/截图/说明，AI 实时打分 + 规则兜底，累计出总分。</p>
        </div>
        <div class="card-mag feat-card">
          <div class="feat-ico ac"><Icon icon="mdi:scale-balance" class="text-2xl" /></div>
          <span class="section-label" style="margin:0;letter-spacing:2px;font-size:11px">A3 · 3-Way Compare</span>
          <h4 class="feat-title">三方对标同屏</h4>
          <p class="feat-desc">AI 初评 / 教师复评 / 企业终评 三栏并列，差异点高亮，一键生成报告。</p>
        </div>
      </div>
    </section>

    <!-- ═══ Footer ═══ -->
    <footer class="foot">
      <div class="lft">
        <b>ZHI · XUN · YUN</b>
        软件实训智能评价平台 · 第十五届中国软件杯
      </div>
      <div class="rgt">© 2026 · All Rights Reserved · v3.0-concept</div>
    </footer>

    <!-- ═══ 注册弹窗（保留原有逻辑，仅视觉升级）════ -->
    <el-dialog v-model="showRegister" title="注册账号" width="520px" class="mag-dialog">
      <el-form :model="regForm" :rules="regRules" ref="regFormRef" label-position="top">
        <el-form-item label="角色类型" prop="role">
          <el-radio-group v-model="regForm.role" class="w-full flex gap-2">
            <el-radio-button value="student" class="flex-1">
              <span class="inline-flex items-center gap-1.5"><Icon icon="mdi:account-school-outline" /> 学生</span>
            </el-radio-button>
            <el-radio-button value="teacher" class="flex-1">
              <span class="inline-flex items-center gap-1.5"><Icon icon="mdi:teacher-outline" /> 教师</span>
            </el-radio-button>
            <el-radio-button value="enterprise" class="flex-1">
              <span class="inline-flex items-center gap-1.5"><Icon icon="mdi:office-building-outline" /> 企业</span>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="登录用户名" prop="username">
            <el-input v-model="regForm.username" placeholder="请输入用户名" clearable />
          </el-form-item>
          <el-form-item label="登录密码" prop="password">
            <el-input v-model="regForm.password" type="password" placeholder="请输入密码" show-password />
          </el-form-item>
        </div>
        <el-form-item :label="regForm.role === 'enterprise' ? '企业负责人姓名' : '真实姓名'" prop="real_name">
          <el-input v-model="regForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item
          :label="
            regForm.role === 'enterprise' ? '统一社会信用代码'
              : regForm.role === 'student' ? '学号'
              : '教师工号'
          "
          prop="user_number"
        >
          <el-input
            v-model="regForm.user_number"
            :placeholder="
              regForm.role === 'enterprise' ? '请输入统一社会信用代码'
                : regForm.role === 'student' ? '请输入学号'
                : '请输入工号'
            "
          />
        </el-form-item>
        <template v-if="regForm.role === 'enterprise'">
          <div class="grid grid-cols-2 gap-4">
            <el-form-item label="企业名称" prop="enterprise_name">
              <el-input v-model="regForm.enterprise_name" placeholder="如：北京字节跳动科技有限公司" />
            </el-form-item>
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="regForm.contact_phone" placeholder="HR 联系电话" />
            </el-form-item>
          </div>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false" class="btn-mag ghost !py-2">取消</el-button>
        <el-button type="primary" @click="register" :loading="regLoading" class="btn-mag accent !py-2 !border-0">注册账号</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

type RoleKey = 'student' | 'teacher' | 'enterprise'

const router = useRouter()
const route = useRoute()

// ============================================================
// 三个角色：独立配置（颜色、图标、占位符、文案）
// ============================================================
const roles = [
  {
    key: 'student' as RoleKey,
    chip: '01 · STUDENT',
    title: '学生',
    accent: '#C99A2E',        // 琥珀金（杂志风）
    slogan: '交作业 · 看批改 · 追进度 —— 提交即得 AI 即时反馈',
    eyebrow: '学生端入口 · STUDENT PORTAL',
    usernameLabel: '学号 / 用户名',
    usernamePlaceholder: '请输入学号或登录用户名',
    passwordLabel: '登录密码',
    ctaText: '进入实训工作台',
  },
  {
    key: 'teacher' as RoleKey,
    chip: '02 · TEACHER',
    title: '教师',
    accent: '#3D5AFE',        // 冷钴蓝
    slogan: '发任务 · 评作业 · 出报表 —— AI 初评 + 教师人工复评',
    eyebrow: '教师端入口 · FACULTY PORTAL',
    usernameLabel: '工号 / 用户名',
    usernamePlaceholder: '请输入工号或登录用户名',
    passwordLabel: '登录密码',
    ctaText: '进入教学管理台',
  },
  {
    key: 'enterprise' as RoleKey,
    chip: '03 · ENTERPRISE',
    title: '企业',
    accent: '#FF5A1F',        // 绯红印章
    slogan: '发岗位 · 挖人才 · 做终评 —— 企业方导师独立视角',
    eyebrow: '企业端入口 · ENTERPRISE PORTAL',
    usernameLabel: 'HR 账号 / 邮箱',
    usernamePlaceholder: '请输入企业 HR 账号或邮箱',
    passwordLabel: '登录密码',
    ctaText: '进入企业招聘台',
  },
]

// ============================================================
// 状态：每个角色独立表单 / 独立 loading / 独立 ref
// ============================================================
const chosenRole = ref<RoleKey | null>(null)
const keepSession = ref(true)

const formByRole = reactive<Record<RoleKey, { username: string; password: string }>>({
  student:   { username: '', password: '' },
  teacher:   { username: '', password: '' },
  enterprise:{ username: '', password: '' },
})
const loadingByRole = reactive<Record<RoleKey, boolean>>({
  student: false,
  teacher: false,
  enterprise: false,
})
const formRefs: Partial<Record<RoleKey, any>> = {}
const setFormRef = (k: RoleKey, el: any) => { if (el) formRefs[k] = el }
// username 输入框的 element-plus 组件实例（不是 native input），
// 用它的 .focus() 最稳定，避免 document.querySelector 选择器乱抢第一个 INPUT
const usernameInputRefs: Partial<Record<RoleKey, any>> = {}
const setUsernameInputRef = (k: RoleKey, el: any) => { if (el) usernameInputRefs[k] = el }

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册弹窗复用原逻辑（根据点击的角色预填）
const showRegister = ref(false)
const regLoading = ref(false)
const regFormRef = ref()
const regForm = reactive({
  username: '',
  password: '',
  role: 'student' as RoleKey,
  real_name: '',
  user_number: '',
  enterprise_name: '',
  contact_phone: ''
})
const regRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  user_number: [{
    required: true,
    message: () => {
      if (regForm.role === 'enterprise') return '请输入统一社会信用代码'
      if (regForm.role === 'student') return '请输入学号'
      return '请输入工号'
    },
    trigger: 'blur'
  }],
  enterprise_name: [{
    required: true,
    validator: (_rule: any, value: string, cb: (err?: any) => void) => {
      if (regForm.role === 'enterprise' && !value?.trim()) cb(new Error('请输入企业名称'))
      else cb()
    },
    trigger: 'blur'
  }],
  contact_phone: [{
    required: true,
    validator: (_rule: any, value: string, cb: (err?: any) => void) => {
      if (regForm.role === 'enterprise' && !value?.trim()) cb(new Error('请输入联系电话'))
      else cb()
    },
    trigger: 'blur'
  }]
}

// ============================================================
// 选择角色 + hash 直达
// ============================================================
/** 最近一次聚焦 username 输入框的 timer id（同一角色重复进入会被 clear，
 *  避免用户点击密码框时被"上一次没来得及执行的 focus 任务"抢焦点）。 */
let _focusUsernameTimer: number | null = null
/** 最近一次通过 replaceState 改 hash 写进去的角色 — 用来打破
 *  replaceState → watch(hash) → chooseRole(同一个 role) 这种无意义的自触发循环，
 *  否则每次它会额外排一个 120ms 的 focus(username)，把用户在密码框的光标抢走。 */
let _selfWrittenHashRole: RoleKey | null = null

function chooseRole(role: RoleKey, evt?: MouseEvent) {
  // ---- 短路 1：点击来源于 el-input 内部（用户在填表单），不是切角色的动作，完全忽略 ----
  if (evt?.target instanceof HTMLElement) {
    const t = evt.target as HTMLElement
    if (t.closest('.el-input') || t.closest('.role-form') || t.closest('input') || t.closest('button') || t.closest('a')) {
      return
    }
  }

  // ---- 短路 2：同一个角色没真正切换，不做任何副作用 ----
  if (chosenRole.value === role) return
  chosenRole.value = role

  // 同步更新 URL hash（用于直达链接 / 刷新后保持）。
  // 写之前先把目标角色记下来，这样紧接着触发的 watch(window.location.hash)
  // 能一眼识别"这是我自己刚刚写的，不应该再重新 chooseRole / 再排 focus"。
  if (window.location.hash.replace(/^#/, '') !== role) {
    _selfWrittenHashRole = role
    window.history.replaceState(null, '', `#${role}`)
    // 一个微任务后就清掉这个标记，避免下次用户手改 URL 直达别的角色被误忽略
    queueMicrotask(() => { if (_selfWrittenHashRole === role) _selfWrittenHashRole = null })
  }

  // 切换角色后才需要"自动聚焦 username 框"（是合理 UX）；
  // 用 setTimeout 120ms 等 expand 动画跑完，但必须：
  //   · 用 element-plus 实例 ref 调用，不做全局 document.querySelector（稳定）
  //   · 如果前一个 timer 还没执行就清掉（避免同一角色重复排队抢焦点）
  if (_focusUsernameTimer) {
    window.clearTimeout(_focusUsernameTimer)
    _focusUsernameTimer = null
  }
  _focusUsernameTimer = window.setTimeout(() => {
    const comp = usernameInputRefs[role]
    if (comp && typeof comp.focus === 'function') comp.focus()
    _focusUsernameTimer = null
  }, 120)
}

function openRegister(role: RoleKey) {
  regForm.role = role
  showRegister.value = true
}

// URL hash 变更 / 初始化自动选角色
watch(
  () => window.location.hash,
  () => {
    const h = window.location.hash.replace(/^#/, '') as RoleKey
    if (!(['student', 'teacher', 'enterprise'] as RoleKey[]).includes(h)) return
    // 短路：这个 hash 恰恰就是 chooseRole 刚刚自己 replaceState 写进去的，
    //       那就不要再重新 chooseRole —— 否则就是一次"假切换"，又会排一个
    //       focus(username)，把用户点到密码框的光标抢走。
    if (_selfWrittenHashRole === h) return
    chooseRole(h)
  }
)

// ============================================================
// 登录提交：角色强隔离
// · 学生/教师：POST /api/auth/login 带 expected_role
// · 企业：POST /api/enterprise/login（后端自带角色校验）
// 任何失败统一显示「用户名或密码错误」
// ============================================================
async function submitLogin(role: RoleKey) {
  const ref = formRefs[role]
  if (!ref) return
  const valid = await ref.validate().catch(() => false)
  if (!valid) return

  loadingByRole[role] = true
  try {
    const payload: Record<string, any> = {
      username: formByRole[role].username.trim(),
      password: formByRole[role].password,
    }
    let url: string
    if (role === 'enterprise') {
      url = `${API_BASE}/api/enterprise/login`
    } else {
      url = `${API_BASE}/api/auth/login`
      payload.expected_role = role   // 告诉后端：这个入口只允许该角色登录
    }

    const res = await axios.post(url, payload)
    if (res.data.success) {
      localStorage.setItem('token', res.data.token)
      const user = {
        ...(res.data.user || {}),
        ...(res.data.enterprise ? { enterprise: res.data.enterprise } : {}),
      } as any
      if (!user.role) user.role = role
      localStorage.setItem('user', JSON.stringify(user))
      ElMessage.success(`欢迎，${user.real_name || user.username}`)

      const redirect = route.query.redirect as string | undefined
      if (redirect) {
        router.push(redirect)
      } else if (user.role === 'enterprise') {
        router.push('/app/enterprise/dashboard')
      } else {
        router.push('/app')
      }
    }
  } catch (err: any) {
    const status = err.response?.status ?? 0
    const detail = err.response?.data?.detail
    let msg = '登录失败，请稍后重试'
    if (status === 0 || !err.response) {
      msg = '无法连接后端服务，请确认 127.0.0.1:8000 是否已启动'
    } else if (status === 422) {
      msg = `请求字段格式错误：${
        Array.isArray(err.response.data?.detail)
          ? err.response.data.detail.map((x: any) => x.msg || JSON.stringify(x)).join('; ')
          : detail || JSON.stringify(err.response.data)
      }`
    } else if (detail) {
      // ⚠️  严格按用户要求：不暴露"此账号属XX端"信息
      // 后端对所有 401 已统一输出「用户名或密码错误」，这里直接透传
      msg = String(detail)
    } else if (err.message) {
      msg = err.message
    }
    ElMessage.error(msg)
  } finally {
    loadingByRole[role] = false
  }
}

// ============================================================
// 注册：复用原逻辑（根据角色选对应 API）
// 注册成功后：自动回填选中角色表单
// ============================================================
const register = async () => {
  const valid = await regFormRef.value.validate().catch(() => false)
  if (!valid) return

  regLoading.value = true
  try {
    let url: string
    let payload: Record<string, any>
    if (regForm.role === 'enterprise') {
      url = `${API_BASE}/api/enterprise/register`
      payload = {
        username: regForm.username,
        password: regForm.password,
        real_name: regForm.real_name,
        title: '',
        enterprise_name: regForm.enterprise_name,
        enterprise_short_name: regForm.enterprise_name.trim().slice(0, 8),
        industry: '',
        scale: '',
        contact_phone: regForm.contact_phone,
        contact_email: '',
        address: '',
        description: '',
      }
    } else {
      url = `${API_BASE}/api/auth/register`
      payload = {
        username: regForm.username,
        password: regForm.password,
        role: regForm.role,
        real_name: regForm.real_name,
        user_number: regForm.user_number,
      }
    }
    const res = await axios.post(url, payload)
    if (res.data.success) {
      ElMessage.success('注册成功，请登录')
      showRegister.value = false
      // 成功后：自动切到对应角色表单，并预填账号
      chooseRole(regForm.role)
      formByRole[regForm.role].username = regForm.username
      formByRole[regForm.role].password = ''
      // 清空
      regForm.username = ''
      regForm.password = ''
      regForm.real_name = ''
      regForm.user_number = ''
      regForm.enterprise_name = ''
      regForm.contact_phone = ''
    }
  } catch (err: any) {
    const status = err.response?.status ?? 0
    const detail = err.response?.data?.detail
    let msg = '注册失败，请稍后重试'
    if (status === 0 || !err.response) {
      msg = '无法连接后端服务，请启动后端 127.0.0.1:8000'
    } else if (status === 422) {
      msg = `提交字段格式错误（HTTP 422）：${
        Array.isArray(err.response.data?.detail)
          ? err.response.data.detail.map((x: any) => x.msg || JSON.stringify(x)).join('; ')
          : detail || JSON.stringify(err.response.data)
      }`
    } else if (detail) {
      msg = detail
    }
    ElMessage.error(msg)
  } finally {
    regLoading.value = false
  }
}

// ============================================================
// onMounted：动画 + hash 直达
// ============================================================
onMounted(() => {
  // ① 处理 URL hash：#student / #teacher / #enterprise 自动选对应角色
  const hash = window.location.hash.replace(/^#/, '')
  if ((['student', 'teacher', 'enterprise'] as RoleKey[]).includes(hash as RoleKey)) {
    chooseRole(hash as RoleKey)
  } else if (!hash && !window.location.pathname.includes('/login')) {
    // 纯 /login 或 其他路径过来的 hash=hero 不选角色；让用户自己点
  }

  // ② 保留原进场动画（给 hstat/feat-card/hero-title 加延迟动画）
  setTimeout(() => {
    document.querySelectorAll('.hstat, .feat-card, .hero-title, .role-card').forEach((el, i) => {
      (el as HTMLElement).style.animationDelay = (i * 70) + 'ms'
      el.classList.add('mag-anim')
    })
  }, 50)
})
</script>

<style scoped>
/* ══════════════════════════════════════
   Login Page · Magazine styles
   对齐 frontend_ui_demo.html .hero/.seal/.login-card
   ══════════════════════════════════════ */

.shell-login {
  position: relative;
  z-index: 2;
  min-height: 100vh;
}

/* ── 复用 MainLayout 的 Topbar/Chip/Brand 样式 ── */
.topbar-mag {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: rgba(246, 243, 236, 0.72);
  border-bottom: 1px solid var(--line);
}
.topbar-inner-mag {
  max-width: 1240px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  gap: 20px;
}
.brand-mag { display: flex; align-items: center; gap: 12px; }
.brand-mark-mag {
  width: 44px; height: 44px; border-radius: 12px;
  background: var(--ink); color: var(--paper);
  display: grid; place-items: center;
  font-family: var(--ff-display); font-size: 15px; letter-spacing: 1px;
  box-shadow: var(--shadow-2), inset 0 0 0 1px rgba(255,255,255,0.08);
  position: relative; overflow: hidden;
}
.brand-mark-mag::after {
  content: ""; position: absolute; inset: auto -40% -60% auto;
  width: 80%; height: 80%;
  background: radial-gradient(closest-side, rgba(255,90,31,0.55), transparent 70%);
  filter: blur(2px);
}
.brand-text-mag { display: flex; flex-direction: column; line-height: 1.1; }
.brand-text-mag b { font-family: var(--ff-display); font-size: 17px; letter-spacing: 2px; color: var(--ink); }
.brand-text-mag span { font-family: var(--ff-sub); font-size: 10px; letter-spacing: 2.5px; color: var(--ink-3); text-transform: uppercase; margin-top: 2px; }

.nav-mag {
  display: flex; gap: 22px;
  font-family: var(--ff-sub); font-size: 14px;
  color: var(--ink-3); align-items: center;
}
.nav-link-mag {
  text-decoration: none; position: relative; padding: 6px 0;
  color: var(--ink-3); transition: color .2s;
}
.nav-link-mag::after {
  content: ""; position: absolute; left: 0; right: 100%; bottom: 0; height: 2px;
  background: var(--seal); transition: right .25s ease;
}
.nav-link-mag:hover { color: var(--ink); }
.nav-link-mag:hover::after { right: 0; }
.nav-pill-mag {
  padding: 8px 16px; border-radius: 999px;
  background: var(--ink); color: var(--paper); font-size: 13px;
  box-shadow: var(--shadow-2); transition: transform .2s ease;
  text-decoration: none; font-family: var(--ff-sub);
}
.nav-pill-mag:hover { transform: translateY(-1px); }

.chip-nav-mag {
  display: flex; gap: 8px;
  padding: 16px 28px 4px;
  max-width: 1240px; margin: 0 auto;
  overflow-x: auto; scrollbar-width: none;
}
.chip-nav-mag::-webkit-scrollbar { display: none; }
.chip-mag {
  flex: 0 0 auto; padding: 6px 12px;
  border: 1px solid var(--line); background: var(--paper-2);
  border-radius: 999px; font-family: var(--ff-sub); font-size: 12px;
  color: var(--ink-3); text-decoration: none; transition: all .2s;
  cursor: pointer;
}
.chip-mag:hover { border-color: var(--seal); color: var(--ink); background: white; }
.chip-mag b { color: var(--seal); margin-right: 6px; font-family: var(--ff-mono); font-weight: 600; }
.chip-mag.active { background: var(--ink); color: var(--paper); border-color: var(--ink); box-shadow: var(--shadow-2); }
.chip-mag.active b { color: #FF8A5C; }

/* ── Section label ── */
.section-label {
  font-family: var(--ff-sub); font-size: 12px; letter-spacing: 3px;
  text-transform: uppercase; color: var(--seal);
  display: inline-flex; align-items: center; gap: 10px; margin-bottom: 14px;
}

/* ── Hero 主视觉（移除印章后，左文右卡匀称对齐）── */
.hero-sec {
  max-width: 1240px; margin: 0 auto;
  padding: 40px 28px 56px;
  display: grid;
  grid-template-columns: 1.55fr 1fr;
  gap: 44px;
  align-items: start;
}

.hero-left { padding: 12px 0 40px; }
.hero-title {
  font-family: var(--ff-display);
  font-size: clamp(48px, 7vw, 86px);
  line-height: 1;
  margin-top: 8px;
  color: var(--ink);
  letter-spacing: .5px;
}
.accent-text { color: var(--seal); font-style: normal; }
.hero-sub {
  font-family: var(--ff-body);
  color: var(--ink-3); font-size: 15px;
  margin-top: 10px;
  max-width: 58ch;
  line-height: 1.7;
}
.hero-bold { font-family: var(--ff-sub); font-weight: 600; color: var(--ink); }

/* 4 stat cards */
.hero-stats {
  display: flex; flex-wrap: wrap; gap: 14px;
  margin-top: 26px;
}
.hstat {
  flex: 0 0 auto; min-width: 150px;
  padding: 14px 16px;
  border-radius: var(--r-md);
  background: white;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-1);
  opacity: 0; transform: translateY(14px);
  animation: revealIn 0.6s ease forwards;
}
.hstat .n {
  font-family: var(--ff-display); font-size: 30px; line-height: 1;
  color: var(--seal);
}
.hstat .n small {
  font-size: 14px; color: var(--ink-3);
  font-family: var(--ff-mono); margin-left: 4px;
}
.hstat .l {
  font-family: var(--ff-sub); font-size: 12px;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--ink-3); margin-top: 4px;
  line-height: 1.5;
}
.hstat .l span { text-transform: none; letter-spacing: normal; font-size: 11px; opacity: .85; }

/* CTA */
.cta-row {
  display: flex; gap: 12px; margin-top: 28px; flex-wrap: wrap;
}
.btn-mag {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 20px; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--ink);
  background: var(--ink); color: var(--paper);
  text-decoration: none;
  font-family: var(--ff-sub); font-size: 14px;
  box-shadow: var(--shadow-2);
  transition: transform .2s ease, box-shadow .2s ease, background .2s;
}
.btn-mag:hover { transform: translateY(-1px); box-shadow: var(--shadow-3); }
.btn-mag.ghost { background: transparent; color: var(--ink); }
.btn-mag.accent { background: var(--seal); border-color: var(--seal); }
.btn-mag .arrow { display: inline-block; transition: transform .2s ease; }
.btn-mag:hover .arrow { transform: translateX(3px); }

/* ══════════════════════════════════════
   · 右栏：身份选择器（方案 A：3 张堆叠式角色大卡）
   · 每个角色独立配色/独立 slogan/独立表单展开
   ══════════════════════════════════════ */
.role-selector {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
}

.role-card {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-1);
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease,
              border-color 0.25s ease, padding 0.25s ease,
              background 0.25s ease;
  position: relative;
  overflow: hidden;
  opacity: 0;
  transform: translateY(14px);
  animation: revealIn 0.6s ease forwards;
}
.role-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-2);
}

/* ——— 三色主题边框（通过左 border 2px 做角色暗示，不突兀）——— */
.role-card.role-student    { border-left: 3px solid #C99A2E; }
.role-card.role-teacher    { border-left: 3px solid #3D5AFE; }
.role-card.role-enterprise { border-left: 3px solid #FF5A1F; }

.role-card.inactive {
  padding: 10px 20px;
  opacity: 0.6;
  box-shadow: none;
}
.role-card.inactive:hover {
  opacity: 1;
  transform: none;
  box-shadow: var(--shadow-1);
}

.role-card.active {
  padding: 22px 22px 18px;
  border-color: var(--role-accent, var(--seal));
  box-shadow: var(--shadow-3), 0 0 0 4px var(--role-ring, rgba(255,90,31,0.08));
}

.role-card.role-student.active    { --role-accent: #C99A2E; --role-ring: rgba(201,154,46,0.12); }
.role-card.role-teacher.active    { --role-accent: #3D5AFE; --role-ring: rgba(61,90,254,0.12); }
.role-card.role-enterprise.active { --role-accent: #FF5A1F; --role-ring: rgba(255,90,31,0.12); }

/* —— 头部：图标 + chip + 标题 + 状态点 —— */
.role-head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
}
.role-ico {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: grid; place-items: center;
  color: white;
  box-shadow: var(--shadow-1);
}
.role-ico svg { width: 24px; height: 24px; }
.role-card.role-student    .role-ico { background: linear-gradient(135deg, #E6B757, #C99A2E); }
.role-card.role-teacher    .role-ico { background: linear-gradient(135deg, #6A84FF, #3D5AFE); }
.role-card.role-enterprise .role-ico { background: linear-gradient(135deg, #FF8A5C, #FF5A1F); }

.role-text { display: flex; flex-direction: column; line-height: 1.2; gap: 3px; }
.role-chip {
  font-family: var(--ff-mono); font-size: 10.5px; letter-spacing: 2px;
  color: var(--ink-3);
  text-transform: uppercase;
}
.role-title {
  font-family: var(--ff-display);
  font-size: 20px;
  letter-spacing: 0.5px;
  color: var(--ink);
}
.role-mark {
  font-size: 14px;
  color: var(--line);
  transition: color 0.2s;
  line-height: 1;
}
.role-card.active .role-mark { color: var(--role-accent, var(--seal)); }

/* —— 标语：未选中时折叠为 0（不占空间），选中或未选任何角色时展开 —— */
.role-slogan {
  font-family: var(--ff-sub);
  font-size: 12.5px;
  color: var(--ink-3);
  line-height: 1.6;
  margin-top: 10px;
  max-height: 60px;
  opacity: 1;
  overflow: hidden;
  transition: max-height 0.25s ease, opacity 0.2s ease, margin-top 0.25s ease;
}
.role-slogan.is-collapsed {
  max-height: 0px;
  margin-top: 0px;
  opacity: 0;
}

/* —— 展开后的专属表单 —— */
.role-form {
  margin-top: 4px;
}
.form-divider {
  height: 1px;
  background: linear-gradient(90deg, var(--line-soft), transparent);
  margin: 14px -22px 12px;
}
.form-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--ff-mono); font-size: 10.5px;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--ink-3);
  margin-top: 4px;
}
.form-eyebrow .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--seal);
  box-shadow: 0 0 0 3px var(--seal-soft);
}
.role-card.role-student    .form-eyebrow .dot { background: #C99A2E; box-shadow: 0 0 0 3px rgba(201,154,46,0.14); }
.role-card.role-teacher    .form-eyebrow .dot { background: #3D5AFE; box-shadow: 0 0 0 3px rgba(61,90,254,0.14); }
.role-card.role-enterprise .form-eyebrow .dot { background: #FF5A1F; box-shadow: 0 0 0 3px rgba(255,90,31,0.14); }

/* 表单域 + 按钮：按角色色做 focus/hover */
.role-card.role-student    .field :deep(.el-input__wrapper.is-focus) {
  border-color: #C99A2E !important;
  box-shadow: 0 0 0 4px rgba(201,154,46,0.14) !important;
}
.role-card.role-teacher    .field :deep(.el-input__wrapper.is-focus) {
  border-color: #3D5AFE !important;
  box-shadow: 0 0 0 4px rgba(61,90,254,0.14) !important;
}
.role-card.role-enterprise .field :deep(.el-input__wrapper.is-focus) {
  border-color: #FF5A1F !important;
  box-shadow: 0 0 0 4px rgba(255,90,31,0.14) !important;
}

/* 角色化 CTA 按钮 */
.btn-mag.btn-role {
  padding: 11px 22px;
  background: var(--btn-bg, var(--seal));
  border-color: var(--btn-bg, var(--seal));
  box-shadow: 0 6px 16px -6px var(--btn-bg, var(--seal));
  color: white;
}
.btn-mag.btn-role:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
  box-shadow: 0 10px 22px -8px var(--btn-bg, var(--seal));
}
.btn-mag.btn-role:disabled {
  opacity: 0.75;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.role-link {
  font-family: var(--ff-sub);
}

/* —— 过渡动画：expand（表单展开收起）—— */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.28s ease;
  overflow: hidden;
  max-height: 480px;
  opacity: 1;
  transform: translateY(0);
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
}
.expand-move { transition: transform 0.28s ease; }

/* —— 右栏布局：去掉旧的 login-card 样式（已废弃）—— */
.hero-right .login-card { display: none; }
.login-card { display: none; }
.head, .card-title, .tag, .role-tabs { display: none; }

/* ══════════════════════════════════════
   · 原样式的 Form / ToggleRow / LoginFoot（保留，供 roll-card 内复用）
   ══════════════════════════════════════ */
.field { margin-top: 12px; }
.field label {
  display: block;
  font-family: var(--ff-sub); font-size: 12px;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--ink-3); margin-bottom: 6px;
}
.field :deep(.el-input__wrapper) {
  border-radius: var(--r-md);
  box-shadow: none;
  border: 1px solid var(--line);
  background: var(--paper);
  transition: all .2s;
  font-family: var(--ff-body); font-size: 15px;
  padding: 4px 14px;
}
.field :deep(.el-input__wrapper:hover) { border-color: #C8BFA7; background: white; }
.field :deep(.el-input__wrapper.is-focus) {
  border-color: var(--seal);
  box-shadow: 0 0 0 4px rgba(255,90,31,0.14) !important;
  background: white;
}

.toggle-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 14px;
  font-size: 13px; font-family: var(--ff-sub); color: var(--ink-3);
}
.forgot-link {
  color: var(--seal); text-decoration: none;
  transition: opacity .2s;
}
.forgot-link:hover { opacity: .8; }

.login-foot {
  margin-top: 18px;
  display: flex; justify-content: space-between;
  align-items: center; gap: 10px;
}
.meta-note {
  font-family: var(--ff-mono); font-size: 11px;
  color: var(--ink-3);
}

.register-row {
  margin-top: 14px; text-align: center;
  font-family: var(--ff-sub); font-size: 13px;
  color: var(--ink-3);
  display: flex; align-items: center; justify-content: center; gap: 6px;
}

/* Card mag (replicated, 纯色化：移除渐变顶条) */
.card-mag {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 22px;
  box-shadow: var(--shadow-2);
  position: relative;
  overflow: hidden;
}

/* ── Features section ── */
.feat-sec {
  max-width: 1240px; margin: 0 auto;
  padding: 20px 28px 56px;
}
.feat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.feat-card {
  opacity: 0; transform: translateY(14px);
  animation: revealIn 0.6s ease forwards;
}
.feat-ico {
  width: 48px; height: 48px; border-radius: 14px;
  display: grid; place-items: center;
  color: white;
  margin-bottom: 12px;
  box-shadow: var(--shadow-1);
}
.feat-ico.co { background: linear-gradient(135deg, #5E7AE9, var(--cobalt)); }
.feat-ico.ok { background: linear-gradient(135deg, #46CF79, var(--jade)); }
.feat-ico.bad { background: linear-gradient(135deg, #F18A94, var(--signal)); }
.feat-ico.ac { background: linear-gradient(135deg, #FF8A5C, var(--seal)); }
.feat-title {
  font-family: var(--ff-display); font-size: 22px;
  letter-spacing: .5px; margin-top: 4px;
  color: var(--ink);
}
.feat-desc {
  font-family: var(--ff-body); font-size: 14px;
  color: var(--ink-3); margin-top: 6px; line-height: 1.6;
}

/* ── Footer ── */
.foot {
  max-width: 1240px; margin: 0 auto;
  padding: 40px 28px 60px;
  display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 14px;
  border-top: 1px solid var(--line);
  margin-top: 30px;
}
.foot .lft {
  font-family: var(--ff-sub); font-size: 13px; color: var(--ink-3);
}
.foot .lft b {
  font-family: var(--ff-display); color: var(--ink);
  letter-spacing: 1.5px; margin-right: 10px;
}
.foot .rgt {
  font-family: var(--ff-mono); font-size: 12px; color: var(--ink-3);
}

/* ── Animations ── */
.mag-anim { animation: revealIn 0.6s ease forwards; }
@keyframes revealIn {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: none; }
}

/* ── Responsive ── */
@media (max-width: 980px) {
  .hero-sec { grid-template-columns: 1fr; gap: 24px; padding: 30px 20px; }
  .hero-right { padding-top: 0; }
  .feat-sec { padding: 20px 20px 40px; }
  .nav-mag { display: none; }
}
@media (max-width: 640px) {
  .topbar-inner-mag { padding: 12px 16px; }
  .chip-nav-mag { padding: 12px 16px 4px; }
  .hero-stats .hstat { min-width: calc(50% - 7px); }
  .brand-text-mag span { display: none; }
  .login-foot { flex-direction: column; align-items: stretch; }
}
</style>
