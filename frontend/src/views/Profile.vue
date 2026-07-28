<template>
  <div class="min-h-screen bg-gradient-main relative overflow-hidden">
    <!-- 背景装饰元素 -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
      <div class="absolute top-[-10%] left-[-5%] w-[500px] h-[500px] bg-primary-500/10 rounded-full blur-[100px]"></div>
      <div class="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] bg-ai-500/10 rounded-full blur-[100px]"></div>
    </div>

    <!-- 主内容容器 -->
    <div class="relative z-10 max-w-7xl mx-auto px-6 py-12">
      <!-- 页面标题 -->
      <div class="mb-10 animate-fade-in">
        <h1 class="text-4xl font-bold text-white mb-2">个人中心</h1>
        <p class="text-white/70">管理你的个人信息、账号安全</p>
      </div>

      <!-- 顶部个人信息头图 -->
      <div class="glass rounded-3xl p-8 mb-10 animate-slide-up backdrop-blur-xl" v-if="user">
        <div class="flex flex-col md:flex-row items-center md:items-end gap-8">
          <!-- 头像上传 -->
          <el-upload
            :show-file-list="false"
            :before-upload="beforeAvatar"
            :http-request="uploadAvatar"
            accept=".png,.jpg,.jpeg,.gif"
            class="cursor-pointer"
          >
            <div class="relative group">
              <div class="w-32 h-32 rounded-full bg-gradient-to-br from-primary-500 to-ai-500 p-1.5 group-hover:scale-105 transition-transform duration-300">
                <el-avatar :size="120" :src="avatarUrl" class="bg-white/10 text-white text-4xl border-2 border-white/20">
                  {{ (user?.real_name || user?.username || '').charAt(0).toUpperCase() }}
                </el-avatar>
              </div>
              <div class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div class="text-center">
                  <Icon icon="mdi:camera" class="text-white text-3xl mb-1" />
                  <p class="text-white text-xs font-medium">更换头像</p>
                </div>
              </div>
            </div>
          </el-upload>

          <!-- 个人核心信息 -->
          <div class="flex-1 text-center md:text-left">
            <div class="flex flex-col md:flex-row md:items-end gap-4 mb-3">
              <h2 class="text-3xl font-bold text-white">{{ user?.real_name || user?.username }}</h2>
              <span :class="user?.role === 'teacher' ? 'bg-orange-500/20 text-orange-300' : 'bg-green-500/20 text-green-300'"
                class="px-4 py-1 rounded-full text-sm font-medium border border-white/10">
                {{ user?.role === 'teacher' ? '教师账号' : '学生账号' }}
              </span>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl">
              <div class="text-white/80">
                <p class="text-xs text-white/50 mb-1">用户名</p>
                <p class="font-medium">{{ user?.username }}</p>
              </div>
              <div class="text-white/80">
                <p class="text-xs text-white/50 mb-1">{{ user?.role === 'student' ? '学号' : '工号' }}</p>
                <p class="font-medium">{{ profile?.user_number || '未填写' }}</p>
              </div>
              <div class="text-white/80">
                <p class="text-xs text-white/50 mb-1">邮箱</p>
                <p class="font-medium">{{ profile?.email || '未填写' }}</p>
              </div>
              <div class="text-white/80">
                <p class="text-xs text-white/50 mb-1">注册时间</p>
                <p class="font-medium">{{ profile?.created_at?.split('T')[0] || '-' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 下方功能卡片区 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8" v-if="user">
        <!-- 左侧：编辑资料卡片 -->
        <div class="lg:col-span-2 space-y-8">
          <!-- 编辑资料卡片 -->
          <div class="bg-white/90 backdrop-blur-md rounded-3xl p-8 shadow-xl animate-slide-up" style="animation-delay: 0.1s;">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                <Icon icon="mdi:account-edit" class="text-xl text-primary-500" />
              </div>
              <h3 class="text-2xl font-bold text-gray-800">编辑资料</h3>
            </div>

            <el-form :model="editForm" label-width="100px" class="modern-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="真实姓名">
                    <el-input v-model="editForm.real_name" placeholder="请输入真实姓名" size="large" class="modern-input" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="user?.role === 'student' ? '学号' : '工号'">
                    <el-input v-model="editForm.user_number" :placeholder="user?.role === 'student' ? '请输入学号' : '请输入工号'" size="large" class="modern-input" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="邮箱">
                <el-input v-model="editForm.email" placeholder="请输入邮箱" size="large" class="modern-input" />
              </el-form-item>
              <el-form-item>
                <button type="button" class="btn-primary text-white px-8 py-3 rounded-xl font-medium text-lg hover:shadow-lg hover:shadow-primary-500/30 transition-all"
                  @click="saveProfile" :disabled="saving">
                  <span v-if="saving" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
                  保存资料
                </button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 修改密码卡片 -->
          <div class="bg-white/90 backdrop-blur-md rounded-3xl p-8 shadow-xl animate-slide-up" style="animation-delay: 0.2s;">
            <div class="flex items-center gap-3 mb-6">
              <div class="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center">
                <Icon icon="mdi:lock-reset" class="text-xl text-orange-500" />
              </div>
              <h3 class="text-2xl font-bold text-gray-800">修改密码</h3>
            </div>

            <el-form :model="pwdForm" label-width="110px" class="modern-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="旧密码">
                    <el-input v-model="pwdForm.old_password" type="password" show-password size="large" class="modern-input" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="新密码">
                    <el-input v-model="pwdForm.new_password" type="password" show-password size="large" class="modern-input" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="确认新密码">
                <el-input v-model="pwdForm.confirm_password" type="password" show-password size="large" class="modern-input" />
              </el-form-item>
              <el-form-item>
                <button type="button" class="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-3 rounded-xl font-medium text-lg hover:shadow-lg hover:shadow-orange-500/30 transition-all"
                  @click="changePassword" :disabled="changingPwd">
                  <span v-if="changingPwd" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
                  修改密码
                </button>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 右侧：账号安全/危险操作 -->
        <div class="space-y-8">
          <!-- 账号安全卡片 -->
          <div class="bg-white/90 backdrop-blur-md rounded-3xl p-8 shadow-xl animate-slide-up" style="animation-delay: 0.3s;">
            <h3 class="text-xl font-bold text-gray-800 mb-6">账号安全</h3>
            <div class="space-y-6">
              <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center">
                    <Icon icon="mdi:shield-check" class="text-green-500" />
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">登录状态</p>
                    <p class="text-xs text-gray-500">当前已登录</p>
                  </div>
                </div>
                <span class="px-2 py-1 bg-green-50 text-green-500 rounded-full text-xs font-medium">正常</span>
              </div>

              <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                    <Icon icon="mdi:calendar" class="text-blue-500" />
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">注册时间</p>
                    <p class="text-xs text-gray-500">{{ profile?.created_at?.split('T')[0] || '-' }}</p>
                  </div>
                </div>
              </div>

              <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center">
                    <Icon icon="mdi:id-card" class="text-primary-500" />
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">账号ID</p>
                    <p class="text-xs text-gray-500">{{ user?.id || '-' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 危险操作卡片 -->
          <div class="bg-red-50/90 backdrop-blur-md rounded-3xl p-8 shadow-xl border border-red-200 animate-slide-up" style="animation-delay: 0.4s;">
            <div class="flex items-center gap-3 mb-4">
              <Icon icon="mdi:alert-octagon" class="text-2xl text-red-500" />
              <h3 class="text-xl font-bold text-red-700">危险操作</h3>
            </div>
            <p class="text-red-600 text-sm mb-6">注销后不可恢复，所有数据将被永久删除，请谨慎操作。</p>
            <button type="button" class="w-full bg-red-500 text-white px-6 py-3 rounded-xl font-medium hover:bg-red-600 hover:shadow-lg hover:shadow-red-500/30 transition-all"
              @click="deleteAccount">
              注销账号
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 【完全保留你原有的所有业务逻辑，一行未改！】
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const user = ref<any>(null)
const profile = ref<any>({})
const saving = ref(false)
const changingPwd = ref(false)

const avatarUrl = computed(() => {
  if (profile.value?.avatar) {
    return `${API_BASE}/uploads/avatars/${profile.value.avatar}`
  }
  const saved = localStorage.getItem('user_avatar')
  if (saved) return `${API_BASE}/uploads/avatars/${saved}`
  return ''
})

const editForm = reactive({ real_name: '', email: '', user_number: '' })
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

onMounted(async () => {
  const data = localStorage.getItem('user')
  if (!data) { router.push('/login'); return }
  user.value = JSON.parse(data)

  try {
    const res = await axios.get(`${API_BASE}/api/user/profile/${user.value.id}`)
    if (res.data.success) {
      profile.value = res.data.data
      editForm.real_name = res.data.data.real_name || ''
      editForm.email = res.data.data.email || ''
      editForm.user_number = res.data.data.user_number || ''
    }
  } catch {}
})

const saveProfile = async () => {
  saving.value = true
  try {
    await axios.put(`${API_BASE}/api/user/profile/${user.value.id}`, {
      real_name: editForm.real_name,
      email: editForm.email,
      user_number: editForm.user_number
    })
    ElMessage.success('资料已更新')

    if (editForm.real_name) {
      user.value.real_name = editForm.real_name
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

const changePassword = async () => {
  if (!pwdForm.old_password || !pwdForm.new_password) {
    ElMessage.warning('请填写完整密码信息'); return
  }
  if (pwdForm.new_password !== pwdForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致'); return
  }
  changingPwd.value = true
  try {
    await axios.put(`${API_BASE}/api/user/password/${user.value.id}`, {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password
    })
    ElMessage.success('密码已修改，请重新登录')
    pwdForm.old_password = ''; pwdForm.new_password = ''; pwdForm.confirm_password = ''
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  } finally { changingPwd.value = false }
}

const beforeAvatar = (file: File) => {
  const isValid = ['image/png', 'image/jpeg', 'image/gif'].includes(file.type)
  if (!isValid) ElMessage.error('仅支持 PNG/JPG/GIF 格式')
  return isValid
}

const uploadAvatar = async (options: any) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await axios.post(`${API_BASE}/api/user/avatar/${user.value.id}`, formData)
    if (res.data.success) {
      localStorage.setItem('user_avatar', res.data.avatar)
      ElMessage.success('头像已更新，即将刷新页面')
      setTimeout(() => window.location.reload(), 500)
    }
  } catch { ElMessage.error('上传失败') }
}

const deleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '确定注销账号？此操作不可撤销。', '最后确认',
      { type: 'error', confirmButtonText: '确认注销', cancelButtonText: '取消' }
    )
    await axios.delete(`${API_BASE}/api/user/account/${user.value.id}`)
    localStorage.clear()
    ElMessage.success('账号已注销')
    router.push('/login')
  } catch {}
}
</script>

<style scoped>
/* 玻璃态核心样式 */
.glass {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

/* 表单输入框美化 */
.modern-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
}
.modern-input :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}
.modern-input :deep(.el-input__wrapper):hover {
  border-color: #165DFF;
}
.modern-input :deep(.el-input__wrapper.is-focus) {
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}

/* 渐变背景 */
.bg-gradient-main {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

/* 动画 */
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}
.animate-slide-up {
  animation: slideUp 0.6s ease-out backwards;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>