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
            <span style="position:relative;z-index:1">智讯</span>
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
          「智讯云」智能实训评价平台：把实训批改从"下载 zip → 拖 IDE → 写评语"的机械劳动，搬进一个
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

      <!-- 右：印章 + 登录卡 -->
      <div class="hero-right">
        <!-- 绯红印章分数环（对齐 demo .seal） -->
        <div class="seal-big" title="实训总评分 · 总评 A-">
          <span class="seal-tack tl"></span>
          <span class="seal-tack br"></span>
          <div class="seal-inner">
            <div class="ring-num">92·4</div>
            <div class="ring-label">Overall Grade</div>
            <div class="ring-sub">— 实训总评 · 2026 —</div>
          </div>
        </div>

        <!-- 登录卡（对齐 demo .login-card） -->
        <div class="card-mag login-card">
          <div class="head">
            <div>
              <span class="section-label" style="margin:0;letter-spacing:2px;font-size:11px">Portal / Sign in</span>
              <h3 class="card-title">进入你的工作台</h3>
            </div>
            <span class="tag co">SSO · Lv.2 加密</span>
          </div>

          <!-- 角色切换 Tabs（3 栏，对齐 demo） -->
          <div class="role-tabs">
            <button
              type="button"
              @click="loginMode = 'student'"
              :class="loginMode==='student' ? 'on' : ''"
            >
              <Icon icon="mdi:account-school-outline" class="mr-1.5" />
              学生
            </button>
            <button
              type="button"
              @click="loginMode = 'teacher'"
              :class="loginMode==='teacher' ? 'on' : ''"
            >
              <Icon icon="mdi:teacher-outline" class="mr-1.5" />
              教师
            </button>
            <button
              type="button"
              @click="loginMode = 'enterprise'"
              :class="loginMode==='enterprise' ? 'on' : ''"
            >
              <Icon icon="mdi:office-building-outline" class="mr-1.5" />
              企业
            </button>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" class="mt-3">
            <div class="field">
              <label>身份 ID / 用户名</label>
              <el-input
                v-model="form.username"
                placeholder="请输入用户名或学号/工号"
                size="large"
                clearable
              />
            </div>

            <div class="field">
              <label>密钥 / Password</label>
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password
                @keyup.enter="login"
              />
            </div>

            <div class="toggle-row">
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox" checked class="w-4 h-4 accent-seal" />
                <span>保持本次会话</span>
              </label>
              <a href="#" class="forgot-link">忘记身份？</a>
            </div>

            <div class="login-foot">
              <button
                type="button"
                @click="login"
                :disabled="loading"
                class="btn-mag"
                style="padding:12px 26px"
              >
                <span v-if="loading" class="w-5 h-5 border-2 border-paper/30 border-t-paper rounded-full animate-spin"></span>
                <Icon v-else icon="mdi:login" class="text-base" />
                <span>{{ loading ? '登录中...' : '进入工作台' }}</span>
              </button>
              <span class="meta-note">v3.0.0 · build 20260729</span>
            </div>
          </el-form>

          <div class="register-row">
            <span>还没有账号？</span>
            <el-button link type="primary" @click="showRegister = true" class="!font-sub !text-base !p-0 !h-auto">立即注册</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const showRegister = ref(false)
const regLoading = ref(false)
const formRef = ref()
const regFormRef = ref()
const loginMode = ref<'student' | 'teacher' | 'enterprise'>('student')

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const regForm = reactive({
  username: '',
  password: '',
  role: 'student' as 'student' | 'teacher' | 'enterprise',
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

const login = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const url = loginMode.value === 'enterprise'
      ? `${API_BASE}/api/enterprise/login`
      : `${API_BASE}/api/auth/login`

    const payload: Record<string, string> = {
      username: form.username,
      password: form.password,
    }

    const res = await axios.post(url, payload)
    if (res.data.success) {
      localStorage.setItem('token', res.data.token)
      const user = {
        ...(res.data.user || {}),
        ...(res.data.enterprise ? { enterprise: res.data.enterprise } : {}),
      } as any
      if (!user.role) user.role = loginMode.value
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
      msg = '无法连接后端服务，请确认 127.0.0.1:8000 是否启动（响应体为空）'
    } else if (status === 422) {
      msg = `提交字段与后端不一致（HTTP 422）：${
        Array.isArray(err.response.data?.detail)
          ? err.response.data.detail.map((x: any) => x.msg || JSON.stringify(x)).join('; ')
          : detail || JSON.stringify(err.response.data)
      }`
    } else if (detail) {
      msg = detail
    } else if (err.message) {
      msg = err.message
    }
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

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
      form.username = regForm.username
      loginMode.value = regForm.role
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
      msg = '无法连接后端服务（响应体为空），请启动后端 127.0.0.1:8000'
    } else if (status === 422) {
      msg = `提交字段与后端不一致（HTTP 422）：${
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

// 简单的进场动画：页面加载后给所有 hstat/feat-card 加 .on 类
onMounted(() => {
  setTimeout(() => {
    document.querySelectorAll('.hstat, .feat-card, .hero-title, .seal-big, .login-card').forEach((el, i) => {
      (el as HTMLElement).style.animationDelay = (i * 80) + 'ms'
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
.section-label::before { content: ""; width: 28px; height: 2px; background: var(--seal); }

/* ── Hero 主视觉 ── */
.hero-sec {
  max-width: 1240px; margin: 0 auto;
  padding: 40px 28px 56px;
  display: grid;
  grid-template-columns: 1.55fr 1fr;
  gap: 44px;
  align-items: start;
}

.hero-left { padding: 22px 0 40px; }
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

/* ── Right column: Seal + Login card ── */
.hero-right {
  display: flex; flex-direction: column; align-items: center;
}

/* Seal 印章 */
.seal-big {
  position: relative;
  aspect-ratio: 1 / 1;
  border-radius: 50%;
  width: min(260px, 78%);
  margin-left: auto;
  margin-right: auto;
  background: radial-gradient(circle at 30% 28%, #FF8A5C 0%, var(--seal) 55%, var(--seal-dark) 100%);
  color: white;
  display: grid; place-items: center; text-align: center;
  box-shadow: var(--shadow-3), inset 0 0 0 2px rgba(255,255,255,.35), inset 0 0 40px rgba(0,0,0,.22);
  transform: rotate(-6deg);
  opacity: 0; transform: rotate(-6deg) scale(0.9);
  animation: sealPop 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s forwards;
}
.seal-big::before {
  content: ""; position: absolute; inset: 10%;
  border-radius: 50%;
  border: 1.5px dashed rgba(255,255,255,.6);
}
.seal-tack {
  position: absolute; width: 16px; height: 16px; border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #fff 0%, #aaa 40%, #444 100%);
  box-shadow: 0 2px 4px rgba(0,0,0,.4);
}
.seal-tack.tl { top: -8px; left: 28%; }
.seal-tack.br { bottom: -6px; right: 30%; }
.ring-num { font-family: var(--ff-display); font-size: 72px; line-height: 1; letter-spacing: 2px; }
.ring-label { font-family: var(--ff-sub); font-size: 13px; letter-spacing: 4px; text-transform: uppercase; opacity: .92; margin-top: 4px; }
.ring-sub { font-family: var(--ff-body); font-style: italic; opacity: .85; margin-top: 2px; }

/* Login card */
.login-card {
  width: 100%;
  margin-top: -40px;
  position: relative;
  z-index: 2;
  opacity: 0; transform: translateY(14px);
  animation: revealIn 0.6s ease 0.2s forwards;
}
.head {
  display: flex; justify-content: space-between;
  align-items: flex-end; margin-bottom: 14px; gap: 12px;
}
.card-title {
  font-family: var(--ff-display);
  letter-spacing: 1px;
  font-size: 22px;
  margin-top: 2px;
  color: var(--ink);
}

/* Tag */
.tag {
  display: inline-flex; align-items: center;
  font-family: var(--ff-mono); font-size: 11px;
  padding: 3px 8px; border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper-2); color: var(--ink-3);
}
.tag.co { background: var(--cobalt-soft); color: var(--cobalt-dark); border-color: #B8C4F5; }

/* Role tabs */
.role-tabs {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 8px; margin-top: 16px;
}
.role-tabs button {
  all: unset; cursor: pointer; text-align: center;
  padding: 10px 8px; border-radius: var(--r-md);
  border: 1px solid var(--line); background: var(--paper);
  font-family: var(--ff-sub); font-size: 13px;
  color: var(--ink-3); transition: all .2s;
  display: inline-flex; align-items: center; justify-content: center;
}
.role-tabs button:hover {
  border-color: var(--seal); background: white;
}
.role-tabs button.on {
  background: var(--ink); color: var(--paper);
  border-color: var(--ink); box-shadow: var(--shadow-1);
}

/* Form fields */
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

/* Card mag (replicated) */
.card-mag {
  background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.78));
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 22px;
  box-shadow: var(--shadow-2);
  backdrop-filter: blur(6px);
  position: relative;
  overflow: hidden;
}
.card-mag::after {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, var(--seal), transparent 60%);
  opacity: .7;
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
@keyframes sealPop {
  0%   { opacity: 0; transform: rotate(-6deg) scale(0.8); }
  60%  { opacity: 1; transform: rotate(-6deg) scale(1.04); }
  100% { opacity: 1; transform: rotate(-6deg) scale(1); }
}

/* ── Responsive ── */
@media (max-width: 980px) {
  .hero-sec { grid-template-columns: 1fr; gap: 24px; padding: 30px 20px; }
  .seal-big { margin: 20px auto 0; }
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
