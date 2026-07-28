<template>
  <div class="min-h-screen bg-gradient-main relative overflow-hidden flex items-center justify-center">
    <div id="particles" class="particles"></div>
    
    <!-- 装饰元素 -->
    <div class="absolute top-20 left-10 w-96 h-96 bg-primary-400/20 rounded-full blur-[120px] animate-float"></div>
    <div class="absolute bottom-10 right-10 w-[500px] h-[500px] bg-accent-400/15 rounded-full blur-[120px] animate-float" style="animation-delay: -3s;"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary-600/5 rounded-full blur-[150px]"></div>
    
    <!-- 核心容器：优化最大宽度，适配大屏 -->
    <div class="relative z-10 w-full max-w-7xl mx-auto px-6">
      <!-- 布局优化：从对半分改为7:5黄金比例，解决位置不协调 -->
      <div class="grid lg:grid-cols-12 gap-8 lg:gap-16 items-center">
        <!-- 左侧品牌区（占7列，优化垂直间距，解决标语排版问题） -->
        <div class="lg:col-span-7 text-white mb-8 lg:mb-0 animate-slide-up">
          <div class="flex items-center gap-3 mb-10">
            <div class="w-24 h-24 rounded-full overflow-hidden shadow-lg shadow-primary-500/50 transition-all duration-500 group-hover:scale-125">
                <img 
                  src="@/img/logo.png" 
                  alt="知训云" 
                  class="w-full h-full object-cover"
                >
              </div>
            <span class="text-2xl font-bold">智能化实训系统</span>
          </div>
          
          <h1 class="text-5xl lg:text-6xl font-bold mb-8 leading-tight">
            基于大模型的<br/>
            <span class="bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">智能化实训评价</span>
          </h1>
          
          <!-- 优化标语行高和间距，排版更协调 -->
          <p class="text-xl lg:text-2xl text-white/85 mb-4 leading-relaxed">
            自动解析实训成果，多维度智能评分
          </p>
          <p class="text-xl lg:text-2xl text-white/85 mb-12 leading-relaxed">
            一键生成可视化报表，大幅提升教学效率
          </p>
          
          <!-- 优化功能卡片间距，适配不同屏幕 -->
          <div class="grid grid-cols-3 gap-6 max-w-xl">
            <div class="glass rounded-2xl p-6 text-center">
              <Icon icon="mdi:file-document-check" class="text-4xl mb-3" />
              <div class="font-semibold text-lg">智能解析</div>
            </div>
            <div class="glass rounded-2xl p-6 text-center">
              <Icon icon="mdi:star-check" class="text-4xl mb-3" />
              <div class="font-semibold text-lg">多维评价</div>
            </div>
            <div class="glass rounded-2xl p-6 text-center">
              <Icon icon="mdi:chart-box" class="text-4xl mb-3" />
              <div class="font-semibold text-lg">报表生成</div>
            </div>
          </div>
        </div>

        <!-- 右侧登录表单（占5列，优化窗口宽度和输入框适配） -->
        <div class="lg:col-span-5 animate-slide-up" style="animation-delay: 0.2s;">
          <div class="glass rounded-3xl p-8 lg:p-12 shadow-2xl w-full max-w-xl mx-auto border border-white/30 backdrop-blur-2xl">
            <div class="text-center mb-10">
              <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/20">
                <Icon icon="mdi:shield-account" class="text-3xl text-white" />
              </div>
              <h2 class="text-3xl font-bold text-surface-800 mb-2">欢迎回来</h2>
              <p class="text-surface-500 text-base">教师 / 学生登录</p>
            </div>
            
            <!-- 登录表单：优化输入框宽度，100%占满窗口，解决不协调问题 -->
            <el-form :model="form" :rules="rules" ref="formRef" class="w-full">
              <el-form-item prop="username" class="mb-5">
                <div class="relative w-full">
                  <Icon icon="mdi:account-outline" class="absolute left-4 top-1/2 -translate-y-1/2 text-xl text-gray-400 z-10" />
                  <!-- 强制输入框100%宽度，优化内边距，和窗口完美适配 -->
                  <el-input 
                    v-model="form.username" 
                    placeholder="用户名" 
                    size="large" 
                    class="w-full pl-12"
                  />
                </div>
              </el-form-item>
              
              <el-form-item prop="password" class="mb-6">
                <div class="relative w-full">
                  <Icon icon="mdi:lock-outline" class="absolute left-4 top-1/2 -translate-y-1/2 text-xl text-gray-400 z-10" />
                  <el-input 
                    v-model="form.password" 
                    type="password" 
                    placeholder="密码" 
                    size="large" 
                    show-password 
                    class="w-full pl-12"
                  />
                </div>
              </el-form-item>
              
              <el-form-item class="mb-4">
                <button
                  type="button"
                  @click="login"
                  :disabled="loading"
                  class="w-full btn-primary text-white font-bold py-3.5 rounded-xl text-base flex items-center justify-center gap-2 ripple tracking-wide"
                >
                  <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  <Icon v-else icon="mdi:login" class="text-lg" />
                  <span>{{ loading ? '登录中...' : '登 录' }}</span>
                </button>
              </el-form-item>
            </el-form>

            <div class="text-center">
              <el-button link type="primary" @click="showRegister = true" class="text-base">没有账号？立即注册</el-button>
            </div>
          </div>
          
          <p class="text-center text-white/60 text-sm mt-6">
            © 2026 实训教学评价系统 | 第十五届中国软件杯大赛
          </p>
        </div>
      </div>
    </div>

    <!-- 注册弹窗（完全保留你的原有逻辑，无任何改动） -->
    <el-dialog v-model="showRegister" title="注册账号" width="420px">
      <el-form :model="regForm" :rules="regRules" ref="regFormRef">
        <el-form-item prop="username">
          <el-input v-model="regForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="regForm.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-form-item prop="real_name">
          <el-input v-model="regForm.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item prop="role">
          <el-radio-group v-model="regForm.role">
            <el-radio value="student">学生</el-radio>
            <el-radio value="teacher">教师</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item prop="user_number">
          <el-input v-model="regForm.user_number" :placeholder="regForm.role === 'student' ? '请输入学号' : '请输入工号'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" @click="register" :loading="regLoading">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 【完全保留你原有的所有业务逻辑，一个字都没改！】
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const loading = ref(false)
const showRegister = ref(false)
const regLoading = ref(false)
const formRef = ref()
const regFormRef = ref()

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const regForm = reactive({
  username: '',
  password: '',
  role: 'student',
  real_name: '',
  user_number: ''
})

const regRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  user_number: [{ required: true, message: '请输入学号/工号', trigger: 'blur' }]
}

const login = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/auth/login`, form)
    if (res.data.success) {
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      ElMessage.success(`欢迎，${res.data.user.real_name || res.data.user.username}`)
      router.push('/app')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

const register = async () => {
  const valid = await regFormRef.value.validate().catch(() => false)
  if (!valid) return

  regLoading.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/auth/register`, regForm)
    if (res.data.success) {
      ElMessage.success('注册成功，请登录')
      showRegister.value = false
      form.username = regForm.username
      regForm.username = ''
      regForm.password = ''
      regForm.real_name = ''
      regForm.user_number = ''
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  } finally {
    regLoading.value = false
  }
}

// 粒子背景
onMounted(() => {
  const dom = document.getElementById('particles')!
  const sizes = ['w-1 h-1', 'w-1.5 h-1.5', 'w-2 h-2']
  const opacities = ['bg-white/60', 'bg-white/40', 'bg-white/25']
  for (let i = 0; i < 60; i++) {
    const p = document.createElement('div')
    const sizeClass = sizes[i % 3]
    const opacityClass = opacities[i % 3]
    p.className = `absolute ${sizeClass} ${opacityClass} rounded-full animate-pulse-soft`
    p.style.left = Math.random() * 100 + '%'
    p.style.top = Math.random() * 100 + '%'
    p.style.animationDelay = Math.random() * 6 + 's'
    p.style.animationDuration = (2 + Math.random() * 4) + 's'
    dom.appendChild(p)
  }
})
</script>

<style scoped>
/* 只保留必要的动画样式，其他全用Tailwind CSS */
.particles { @apply absolute w-full h-full overflow-hidden; }

/* 强制Element Plus输入框宽度100%适配 */
:deep(.el-input) {
  width: 100%;
}
</style>