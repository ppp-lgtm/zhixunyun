<template>
  <div class="profile-page" v-if="user">
    <!-- ══════════════════════════════════════════════════════════════
         单一信息总卡片（Unified Profile Card）
         顶部：身份头部（头像 / 姓名 / 角色 / ID / 注册时间）
         主体：按功能分区，用虚线分隔，不再各自套独立 paper-card
         ══════════════════════════════════════════════════════════════ -->
    <section class="unified-card" :class="`role-${user.role}`">
      <!-- ====== 头部：身份信息 ====== -->
      <header class="uc-header">
        <div class="uc-identity">
          <el-upload
            :show-file-list="false"
            :before-upload="beforeAvatar"
            :http-request="uploadAvatar"
            accept=".png,.jpg,.jpeg,.gif"
            class="uc-avatar-upload"
          >
            <div class="uc-avatar-wrap">
              <el-avatar :size="72" :src="avatarUrl" class="uc-avatar">
                {{ initial }}
              </el-avatar>
              <span class="uc-avatar-edit" title="更换头像">
                <Icon icon="mdi:pencil" />
              </span>
            </div>
          </el-upload>

          <div class="uc-id-text">
            <div class="uc-id-row">
              <h1 class="uc-name">{{ displayName }}</h1>
              <span class="uc-role-tag">{{ roleLabel }}</span>
            </div>
            <div class="uc-meta-row">
              <span class="uc-meta">
                <Icon icon="mdi:numeric" />
                ID · {{ user.id }}
              </span>
              <span class="uc-meta">
                <Icon icon="mdi:calendar" />
                注册于 {{ joinedOn }}
              </span>
              <span class="uc-meta">
                <Icon icon="mdi:shield-check" class="ok" />
                本次会话已登录
              </span>
            </div>
          </div>
        </div>
      </header>

      <!-- ====== 分区：个人信息展示 ====== -->
      <div class="uc-section">
        <div class="uc-sec-head">
          <h3 class="uc-sec-title">
            <Icon icon="mdi:account-circle-outline" class="sh-ic ic-blue" />
            个人信息
          </h3>
        </div>

        <!-- ENTERPRISE 企业端专属字段 -->
        <template v-if="user.role === 'enterprise'">
          <div class="stat-grid four">
            <div class="stat-item">
              <p class="stat-label">企业全称</p>
              <p class="stat-value strong">{{ profile.enterprise?.name || '未完善企业信息' }}</p>
            </div>
            <div class="stat-item">
              <p class="stat-label">简称 / Brand</p>
              <p class="stat-value">{{ profile.enterprise?.short_name || '—' }}</p>
            </div>
            <div class="stat-item">
              <p class="stat-label">所属行业</p>
              <p class="stat-value">{{ profile.enterprise?.industry || '—' }}</p>
            </div>
            <div class="stat-item">
              <p class="stat-label">企业规模</p>
              <p class="stat-value">{{ profile.enterprise?.scale || '—' }}</p>
            </div>
          </div>

          <div class="uc-divider" />

          <div class="info-grid three">
            <div class="info-item">
              <Icon icon="mdi:badge-account-horizontal" class="info-ic ic-blue" />
              <div>
                <p class="info-k">HR 账号</p>
                <p class="info-v">{{ user.username }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:account-tie" class="info-ic ic-green" />
              <div>
                <p class="info-k">联系人 / HR 实名</p>
                <p class="info-v">{{ profile.enterprise?.contact_person || profile.real_name || user.real_name || '—' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:title" class="info-ic ic-orange" />
              <div>
                <p class="info-k">岗位 / 部门</p>
                <p class="info-v">{{ [profile.mentor?.title, profile.mentor?.department].filter(Boolean).join(' · ') || '—' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:phone" class="info-ic ic-blue" />
              <div>
                <p class="info-k">联系电话</p>
                <p class="info-v">{{ profile.enterprise?.contact_phone || profile.phone || '—' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:email" class="info-ic ic-green" />
              <div>
                <p class="info-k">联系邮箱</p>
                <p class="info-v">{{ profile.enterprise?.contact_email || profile.email || '—' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:map-marker" class="info-ic ic-orange" />
              <div>
                <p class="info-k">办公地址</p>
                <p class="info-v">{{ profile.enterprise?.address || '—' }}</p>
              </div>
            </div>
          </div>

          <div class="desc-box" v-if="profile.enterprise?.description">
            <Icon icon="mdi:script-text-outline" class="info-ic ic-blue" />
            <div>
              <p class="info-k">企业简介</p>
              <p class="info-v multi">{{ profile.enterprise.description }}</p>
            </div>
          </div>
        </template>

        <!-- STUDENT 学生端 -->
        <template v-else-if="user.role === 'student'">
          <div class="info-grid three">
            <div class="info-item">
              <Icon icon="mdi:badge-account" class="info-ic ic-blue" />
              <div>
                <p class="info-k">登录用户名</p>
                <p class="info-v">{{ user.username }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:id-card" class="info-ic ic-green" />
              <div>
                <p class="info-k">学号</p>
                <p class="info-v">{{ profile.user_number || '未填写' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:account" class="info-ic ic-orange" />
              <div>
                <p class="info-k">真实姓名</p>
                <p class="info-v">{{ profile.real_name || user.real_name || '—' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:email" class="info-ic ic-blue" />
              <div>
                <p class="info-k">邮箱</p>
                <p class="info-v">{{ profile.email || '未填写' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:phone" class="info-ic ic-green" />
              <div>
                <p class="info-k">手机</p>
                <p class="info-v">{{ profile.phone || '未填写' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:calendar" class="info-ic ic-orange" />
              <div>
                <p class="info-k">账号注册日</p>
                <p class="info-v">{{ joinedOn }}</p>
              </div>
            </div>
          </div>
        </template>

        <!-- TEACHER 教师端 -->
        <template v-else>
          <div class="info-grid three">
            <div class="info-item">
              <Icon icon="mdi:badge-account" class="info-ic ic-blue" />
              <div>
                <p class="info-k">登录用户名</p>
                <p class="info-v">{{ user.username }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:card-account-details" class="info-ic ic-green" />
              <div>
                <p class="info-k">工号</p>
                <p class="info-v">{{ profile.user_number || '未填写' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:account-tie" class="info-ic ic-orange" />
              <div>
                <p class="info-k">真实姓名</p>
                <p class="info-v">{{ profile.real_name || user.real_name || '—' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:email" class="info-ic ic-blue" />
              <div>
                <p class="info-k">邮箱</p>
                <p class="info-v">{{ profile.email || '未填写' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:phone" class="info-ic ic-green" />
              <div>
                <p class="info-k">手机</p>
                <p class="info-v">{{ profile.phone || '未填写' }}</p>
              </div>
            </div>
            <div class="info-item">
              <Icon icon="mdi:calendar" class="info-ic ic-orange" />
              <div>
                <p class="info-k">账号注册日</p>
                <p class="info-v">{{ joinedOn }}</p>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ====== 分区：活跃数据统计（直接嵌入，不另开卡片） ====== -->
      <div class="uc-section">
        <div class="uc-sec-head">
          <h3 class="uc-sec-title">
            <Icon icon="mdi:chart-timeline-variant" class="sh-ic ic-green" />
            活跃数据
          </h3>
        </div>

        <!-- ENTERPRISE -->
        <template v-if="user.role === 'enterprise'">
          <div class="metric-grid three">
            <div class="metric">
              <Icon icon="mdi:briefcase" class="metric-ic ic-blue" />
              <div>
                <p class="metric-num">{{ stats.job_count || 0 }}</p>
                <p class="metric-lbl">发布岗位</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:domain" class="metric-ic ic-green" />
              <div>
                <p class="metric-num">{{ stats.class_count || 0 }}</p>
                <p class="metric-lbl">可见班级</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:account-group" class="metric-ic ic-orange" />
              <div>
                <p class="metric-num">{{ stats.student_count || 0 }}</p>
                <p class="metric-lbl">覆盖学生</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:comment-check" class="metric-ic ic-blue" />
              <div>
                <p class="metric-num">{{ stats.eval_count || 0 }}</p>
                <p class="metric-lbl">企业评价</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:comment-clock" class="metric-ic ic-orange" />
              <div>
                <p class="metric-num">{{ stats.pending_eval_count || 0 }}</p>
                <p class="metric-lbl">待评</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:star-half" class="metric-ic ic-green" />
              <div>
                <p class="metric-num">{{ stats.avg_score || 0 }}</p>
                <p class="metric-lbl">评分均值</p>
              </div>
            </div>
          </div>
        </template>

        <!-- STUDENT -->
        <template v-else-if="user.role === 'student'">
          <div class="metric-grid four">
            <div class="metric">
              <Icon icon="mdi:google-classroom" class="metric-ic ic-blue" />
              <div>
                <p class="metric-num">{{ stats.class_count || 0 }}</p>
                <p class="metric-lbl">参与班级</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:file-document-multiple" class="metric-ic ic-green" />
              <div>
                <p class="metric-num">{{ stats.submission_count || 0 }}</p>
                <p class="metric-lbl">提交次数</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:comment-text" class="metric-ic ic-orange" />
              <div>
                <p class="metric-num">{{ stats.evaluation_count || 0 }}</p>
                <p class="metric-lbl">获得评价</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:star" class="metric-ic ic-blue" />
              <div>
                <p class="metric-num">{{ stats.avg_score || 0 }}</p>
                <p class="metric-lbl">评价均分</p>
              </div>
            </div>
          </div>
        </template>

        <!-- TEACHER -->
        <template v-else>
          <div class="metric-grid four">
            <div class="metric">
              <Icon icon="mdi:google-classroom" class="metric-ic ic-blue" />
              <div>
                <p class="metric-num">{{ stats.class_count || 0 }}</p>
                <p class="metric-lbl">授课班级</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:account-group" class="metric-ic ic-green" />
              <div>
                <p class="metric-num">{{ stats.student_count || 0 }}</p>
                <p class="metric-lbl">学生总数</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:comment-check" class="metric-ic ic-orange" />
              <div>
                <p class="metric-num">{{ stats.evaluation_count || 0 }}</p>
                <p class="metric-lbl">教师评价</p>
              </div>
            </div>
            <div class="metric">
              <Icon icon="mdi:star" class="metric-ic ic-blue" />
              <div>
                <p class="metric-num">{{ stats.avg_score || 0 }}</p>
                <p class="metric-lbl">评价均分</p>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ====== 分区：编辑资料 ====== -->
      <div class="uc-section">
        <div class="uc-sec-head">
          <h3 class="uc-sec-title">
            <Icon icon="mdi:pencil-outline" class="sh-ic ic-blue" />
            编辑资料
          </h3>
          <span class="uc-sec-tag">基础信息</span>
        </div>
        <el-form :model="editForm" label-width="110px" class="paper-form">
          <!-- 学生/教师通用：姓名 + 学号/工号 -->
          <el-row v-if="user.role !== 'enterprise'" :gutter="20">
            <el-col :span="12">
              <el-form-item label="真实姓名">
                <el-input v-model="editForm.real_name" placeholder="请输入真实姓名" size="large" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="user.role === 'student' ? '学号' : '工号'">
                <el-input v-model="editForm.user_number"
                  :placeholder="user.role === 'student' ? '请输入学号' : '请输入工号'" size="large" />
              </el-form-item>
            </el-col>
          </el-row>
          <!-- 企业端：联系人 + 联系电话 -->
          <el-row v-else :gutter="20">
            <el-col :span="12">
              <el-form-item label="联系人 / HR">
                <el-input v-model="editForm.real_name" placeholder="请输入联系人姓名" size="large" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联系电话">
                <el-input v-model="editForm.phone" placeholder="请输入企业联系电话" size="large" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="邮箱">
                <el-input v-model="editForm.email" placeholder="请输入邮箱" size="large" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <button type="button" class="btn-primary" @click="saveProfile" :disabled="saving">
              <Icon icon="mdi:content-save-outline" />
              <span v-if="!saving">保存修改</span>
              <span v-else>保存中…</span>
            </button>
          </el-form-item>
        </el-form>
      </div>

      <!-- ====== 分区：修改密码 ====== -->
      <div class="uc-section">
        <div class="uc-sec-head">
          <h3 class="uc-sec-title">
            <Icon icon="mdi:lock-reset" class="sh-ic ic-orange" />
            修改密码
          </h3>
          <span class="uc-sec-tag tag-orange">安全</span>
        </div>
        <el-form :model="pwdForm" label-width="110px" class="paper-form">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="旧密码">
                <el-input v-model="pwdForm.old_password" type="password" show-password size="large" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="新密码">
                <el-input v-model="pwdForm.new_password" type="password" show-password size="large" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="确认新密码">
                <el-input v-model="pwdForm.confirm_password" type="password" show-password size="large" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <button type="button" class="btn-secondary" @click="changePassword" :disabled="changingPwd">
              <Icon icon="mdi:lock-check-outline" />
              <span v-if="!changingPwd">确认修改密码</span>
              <span v-else>修改中…</span>
            </button>
          </el-form-item>
        </el-form>
      </div>

      <!-- ====== 分区：危险操作 ====== -->
      <div class="uc-section uc-danger">
        <div class="uc-sec-head">
          <h3 class="uc-sec-title danger">
            <Icon icon="mdi:alert-octagon" class="sh-ic ic-red" />
            危险操作
          </h3>
        </div>
        <p class="danger-txt">
          注销账号后数据永久删除，实训提交、评价记录、班级关联无法恢复，请谨慎操作。
        </p>
        <button type="button" class="btn-danger" @click="deleteAccount">
          <Icon icon="mdi:delete-forever" />
          <span>注销账号</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const user = ref<any>(null)
const profile = ref<any>({})
const stats = ref<any>({})
const saving = ref(false)
const changingPwd = ref(false)

const editForm = reactive({
  real_name: '',
  email: '',
  user_number: '',
  phone: '',
})
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

const avatarUrl = computed(() => {
  if (profile.value?.avatar) return `/uploads/avatars/${profile.value.avatar}`
  const saved = localStorage.getItem('user_avatar')
  if (saved) return `/uploads/avatars/${saved}`
  return ''
})
const initial = computed(() =>
  (user.value?.real_name || user.value?.username || 'U').charAt(0).toUpperCase()
)
const displayName = computed(() => {
  if (user.value?.role === 'enterprise' && profile.value.enterprise?.name) {
    return profile.value.enterprise.name
  }
  return user.value?.real_name || user.value?.username || '未命名用户'
})
const roleLabel = computed(() => {
  switch (user.value?.role) {
    case 'student': return '学生账号'
    case 'teacher': return '教师账号'
    case 'enterprise': return '企业账号'
    default: return '个人账号'
  }
})
const joinedOn = computed(() =>
  profile.value.created_at ? String(profile.value.created_at).split('T')[0] : '—'
)

onMounted(async () => {
  const data = localStorage.getItem('user')
  if (!data) { router.push('/login'); return }
  user.value = JSON.parse(data)

  try {
    const res = await api.get(`/api/user/profile/${user.value.id}`)
    if (res.data.success) {
      const p = res.data.data || {}
      profile.value = p
      stats.value = p.stats || {}
      if (user.value.role === 'enterprise') {
        editForm.real_name = (p.enterprise?.contact_person || p.real_name || user.value.real_name || '')
        editForm.phone = (p.enterprise?.contact_phone || p.phone || '')
        editForm.email = (p.enterprise?.contact_email || p.email || '')
      } else {
        editForm.real_name = p.real_name || user.value.real_name || ''
        editForm.email = p.email || ''
        editForm.user_number = p.user_number || ''
      }
    }
  } catch { /* ignore */ }
})

const saveProfile = async () => {
  saving.value = true
  try {
    const payload: any = { email: editForm.email }
    if (user.value.role === 'enterprise') {
      payload.real_name = editForm.real_name
    } else {
      payload.real_name = editForm.real_name
      payload.user_number = editForm.user_number
    }
    await api.put(`/api/user/profile/${user.value.id}`, payload)
    ElMessage.success('资料已更新')
    if (editForm.real_name) {
      user.value.real_name = editForm.real_name
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
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
    await api.put(`/api/user/password/${user.value.id}`, {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码已修改，请重新登录')
    pwdForm.old_password = ''; pwdForm.new_password = ''; pwdForm.confirm_password = ''
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  } finally { changingPwd.value = false }
}

const beforeAvatar = (file: File) => {
  const ok = ['image/png', 'image/jpeg', 'image/gif'].includes(file.type)
  if (!ok) ElMessage.error('仅支持 PNG/JPG/GIF 格式')
  return ok
}
const uploadAvatar = async (options: any) => {
  const fd = new FormData()
  fd.append('file', options.file)
  try {
    const res = await api.post(`/api/user/avatar/${user.value.id}`, fd)
    if (res.data.success) {
      localStorage.setItem('user_avatar', res.data.avatar)
      ElMessage.success('头像已更新')
      setTimeout(() => window.location.reload(), 500)
    }
  } catch {
    ElMessage.error('上传失败')
  }
}

const deleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '确定注销账号？此操作不可撤销。',
      '最后确认',
      { type: 'error', confirmButtonText: '确认注销', cancelButtonText: '取消' },
    )
    await api.delete(`/api/user/account/${user.value.id}`)
    localStorage.clear()
    ElMessage.success('账号已注销')
    router.push('/login')
  } catch { /* user cancelled */ }
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #F7F4EC;
  padding: 32px 24px 80px;
}

/* ====== 单一卡片外壳 ====== */
.unified-card {
  max-width: 1120px;
  margin: 0 auto;
  background: #fff;
  border: 1px solid #E5E1D2;
  border-top: 4px solid #165DFF;
  border-radius: 18px;
  box-shadow:
    0 1px 2px rgba(17, 24, 39, 0.04),
    0 12px 36px rgba(17, 24, 39, 0.06);
  overflow: hidden;
}
.unified-card.role-student    { border-top-color: #165DFF; }
.unified-card.role-teacher    { border-top-color: #FF7A00; }
.unified-card.role-enterprise { border-top-color: #22C55E; }

/* ====== 头部身份条 ====== */
.uc-header {
  padding: 28px 36px 24px;
  background: linear-gradient(180deg, #FBF8F0 0%, #FFFFFF 100%);
  border-bottom: 1px dashed #E5E1D2;
}
.uc-identity {
  display: flex;
  gap: 22px;
  align-items: center;
}
.uc-avatar-upload { cursor: pointer; }
.uc-avatar-wrap { position: relative; }
.uc-avatar {
  background: #165DFF;
  color: #fff;
  font-weight: 700;
  font-family: "Playfair Display", "Noto Serif SC", Georgia, serif;
  font-size: 28px;
  border: 3px solid #fff;
  box-shadow: 0 6px 16px rgba(22, 93, 255, 0.22);
}
.role-teacher .uc-avatar    { background: #FF7A00; box-shadow: 0 6px 16px rgba(255, 122, 0, 0.22); }
.role-enterprise .uc-avatar { background: #22C55E; box-shadow: 0 6px 16px rgba(34, 197, 94, 0.22); }
.uc-avatar-edit {
  position: absolute;
  right: -2px; bottom: -2px;
  width: 26px; height: 26px;
  border-radius: 50%;
  background: #165DFF;
  color: #fff;
  font-size: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(17, 24, 39, 0.12);
}
.role-teacher .uc-avatar-edit    { background: #FF7A00; }
.role-enterprise .uc-avatar-edit { background: #22C55E; }

.uc-id-text { flex: 1; min-width: 0; }
.uc-id-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
}
.uc-name {
  margin: 0;
  font-family: "Playfair Display", "Noto Serif SC", Georgia, serif;
  font-weight: 800;
  font-size: 30px;
  line-height: 1.1;
  color: #111827;
  letter-spacing: 0.01em;
}
.uc-role-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(22, 93, 255, 0.10);
  color: #165DFF;
}
.role-teacher .uc-role-tag    { background: rgba(255, 122, 0, 0.12); color: #FF7A00; }
.role-enterprise .uc-role-tag { background: rgba(34, 197, 94, 0.14); color: #16A34A; }

.uc-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}
.uc-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6B7280;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.uc-meta .ok { color: #16A34A; }

/* ====== 分区外壳 ====== */
.uc-section {
  padding: 22px 36px;
}
.uc-section + .uc-section {
  border-top: 1px dashed #E5E1D2;
}
.uc-section.uc-danger {
  background: #FFFBFB;
  border-top: 1px dashed #FECACA;
}

.uc-sec-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.uc-sec-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0.02em;
}
.uc-sec-title.danger { color: #DC2626; }
.sh-ic {
  width: 28px; height: 28px;
  border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 15px;
}
.ic-blue   { background: rgba(22, 93, 255, 0.10);  color: #165DFF; }
.ic-green  { background: rgba(34, 197, 94, 0.12); color: #16A34A; }
.ic-orange { background: rgba(255, 122, 0, 0.12); color: #FF7A00; }
.ic-red    { background: rgba(220, 38, 38, 0.10); color: #DC2626; }
.uc-sec-tag {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(22, 93, 255, 0.08);
  color: #165DFF;
  letter-spacing: 0.06em;
}
.uc-sec-tag.tag-orange { background: rgba(255, 122, 0, 0.10); color: #FF7A00; }

.uc-divider {
  height: 1px;
  background: repeating-linear-gradient(
    90deg,
    #E5E1D2 0 8px,
    transparent 8px 14px
  );
  margin: 20px 0;
}

/* ====== 通用 info/stat 网格（复用旧样式，去掉独立卡片外壳） ====== */
.info-grid.three {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 18px 20px;
}
.stat-grid.two, .stat-grid.four {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 16px;
}
.stat-grid.four { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 1080px) {
  .stat-grid.four { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 780px) {
  .info-grid.three { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 520px) {
  .info-grid.three, .stat-grid.two, .stat-grid.four { grid-template-columns: 1fr; }
  .uc-header { padding: 24px 20px 20px; }
  .uc-section { padding: 20px; }
  .uc-name { font-size: 24px; }
}

.info-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.info-ic {
  flex: 0 0 36px;
  width: 36px; height: 36px;
  border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 18px;
  background: rgba(22, 93, 255, 0.10);
  color: #165DFF;
}
.info-k {
  margin: 0 0 3px;
  color: #6B7280;
  font-size: 12px;
  letter-spacing: 0.02em;
}
.info-v {
  margin: 0;
  color: #111827;
  font-weight: 600;
  font-size: 14px;
  line-height: 1.55;
  word-break: break-all;
}
.info-v.multi { font-weight: 500; color: #374151; line-height: 1.75; }

.stat-item .stat-label {
  margin: 0 0 4px;
  color: #6B7280;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600;
}
.stat-item .stat-value {
  margin: 0;
  font-size: 14px;
  color: #1F2937;
  font-weight: 600;
}
.stat-item .stat-value.strong {
  color: #111827;
  font-size: 16px;
  font-family: "Playfair Display", "Noto Serif SC", Georgia, serif;
  font-weight: 700;
}

.desc-box {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  background: #F7F4EC;
  border: 1px dashed #E5E1D2;
  border-radius: 12px;
  margin-top: 16px;
}

/* ====== Metric 网格（无外层卡片底色，直接平铺） ====== */
.metric-grid.two,
.metric-grid.three,
.metric-grid.four {
  display: grid;
  gap: 14px;
}
.metric-grid.two  { grid-template-columns: repeat(2, minmax(0,1fr)); }
.metric-grid.three{ grid-template-columns: repeat(3, minmax(0,1fr)); }
.metric-grid.four { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 900px) {
  .metric-grid.four { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 520px) {
  .metric-grid.two,
  .metric-grid.three,
  .metric-grid.four { grid-template-columns: 1fr; }
}
.metric {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #F7F4EC;
  border: 1px solid #E5E1D2;
  border-radius: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(17, 24, 39, 0.06);
}
.metric-ic {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 22px;
  background: rgba(22, 93, 255, 0.12);
  color: #165DFF;
  flex: 0 0 40px;
}
.metric-num {
  margin: 0;
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  color: #111827;
  font-size: 26px;
  line-height: 1.1;
}
.metric-lbl {
  margin: 3px 0 0;
  font-size: 12px;
  color: #6B7280;
  letter-spacing: 0.04em;
}

/* ====== Forms ====== */
.paper-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}
.paper-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: none;
  border: 1px solid #E5E7EB;
  padding: 4px 12px;
  background: #F7F4EC;
  transition: all 0.2s ease;
}
.paper-form :deep(.el-input__wrapper:hover) { border-color: #165DFF; background: #fff; }
.paper-form :deep(.el-input__wrapper.is-focus) {
  border-color: #165DFF;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(22, 93, 255, 0.10);
}

/* ====== Buttons ====== */
.btn-primary, .btn-secondary, .btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-primary {
  background: #165DFF;
  color: #fff;
  border-color: #165DFF;
  box-shadow: 0 8px 16px rgba(22, 93, 255, 0.20);
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 12px 20px rgba(22, 93, 255, 0.28); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.btn-secondary {
  background: #fff;
  color: #FF7A00;
  border-color: #FF7A00;
}
.btn-secondary:hover { background: rgba(255, 122, 0, 0.06); }
.btn-secondary:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-danger {
  background: #DC2626;
  color: #fff;
  border-color: #DC2626;
}
.btn-danger:hover { background: #B91C1C; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }

/* ====== 危险操作 ====== */
.danger-txt {
  margin: 0 0 16px;
  padding: 14px 16px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #991B1B;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.7;
}
</style>
