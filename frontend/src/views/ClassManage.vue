<template>
  <div class="page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 class="text-3xl font-bold text-surface-800 tracking-tight">班级管理</h1>
          <p class="text-surface-500 mt-1">管理你的实训班级与学生</p>
        </div>
        <button class="btn-primary text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2"
          @click="showCreate = true">
          <Icon icon="mdi:plus" />
          创建班级
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-12 h-12 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-gray-500">加载中...</p>
        </div>
      </div>

      <!-- 班级列表 -->
      <div v-else-if="classes.length > 0">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div
            v-for="c in classes"
            :key="c.id"
            class="card hover:shadow-xl hover:-translate-y-1 overflow-hidden"
          >
            <!-- 卡片顶部渐变条 -->
            <div :class="c.status === 'active' ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-gray-400 to-gray-500'"
              class="h-3"></div>
            
            <div class="p-8">
              <!-- 班级基本信息 -->
              <div class="flex items-start justify-between mb-6">
                <div>
                  <h3 class="text-2xl font-bold text-gray-900 mb-2">{{ c.name }}</h3>
                  <p class="text-gray-500 text-lg">{{ c.course_name }}</p>
                </div>
                <span :class="c.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-600'"
                  class="px-3 py-1.5 rounded-full text-sm font-bold">
                  {{ c.status === 'active' ? '进行中' : '已归档' }}
                </span>
              </div>

              <!-- 详细信息 -->
              <div class="space-y-3 mb-6 text-gray-600">
                <div class="flex items-center gap-2">
                  <Icon icon="mdi:map-marker" class="text-primary-500" />
                  <span>{{ c.grade }} | {{ c.major }} | {{ c.semester }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <Icon icon="mdi:account-tie" class="text-primary-500" />
                  <span>教师：{{ c.teacher_name }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <Icon icon="mdi:account-group" class="text-primary-500" />
                  <span>学生：{{ c.student_count }}人</span>
                </div>
                <div class="flex items-center gap-2">
                  <Icon icon="mdi:key" class="text-orange-500" />
                  <span>邀请码：</span>
                  <span class="px-2 py-1 bg-orange-50 text-orange-600 rounded-lg text-sm font-bold">{{ c.invite_code }}</span>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex flex-wrap gap-2">
                <button class="flex-1 min-w-[80px] px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors text-sm"
                  @click="viewDetail(c)">
                  详情
                </button>
                <button class="flex-1 min-w-[80px] px-4 py-2 bg-primary-50 text-primary-500 rounded-lg font-medium hover:bg-primary-100 transition-colors text-sm"
                  @click="openEdit(c)">
                  编辑
                </button>
                <button class="flex-1 min-w-[80px] px-4 py-2 bg-green-50 text-green-500 rounded-lg font-medium hover:bg-green-100 transition-colors text-sm"
                  @click="openScores(c.id)">
                  成绩
                </button>
                <button class="flex-1 min-w-[80px] px-4 py-2 bg-orange-50 text-orange-500 rounded-lg font-medium hover:bg-orange-100 transition-colors text-sm"
                  @click="copyCode(c.invite_code)">
                  复制
                </button>
                <button class="flex-1 min-w-[80px] px-4 py-2 bg-red-50 text-red-500 rounded-lg font-medium hover:bg-red-100 transition-colors text-sm"
                  @click="deleteClass(c.id)">
                  解散
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-24 h-24 rounded-3xl bg-surface-50 flex items-center justify-center mx-auto mb-6 border border-surface-100">
            <Icon icon="mdi:book-open-page-variant-outline" class="text-5xl text-surface-300" />
          </div>
          <p class="text-surface-500 text-lg font-medium mb-8">暂无班级，创建第一个班级吧</p>
          <button class="btn-primary text-white px-8 py-3 rounded-xl font-bold"
            @click="showCreate = true">
            + 创建班级
          </button>
        </div>
      </div>
    </div>

    <!-- 创建班级弹窗（优化样式） -->
    <el-dialog v-model="showCreate" title="创建班级" width="600px" class="modern-dialog">
      <el-form :model="form" label-width="100px" class="modern-form">
        <el-form-item label="班级名称" required>
          <el-input v-model="form.name" placeholder="如：软件技术2401班" size="large" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="年级">
              <el-input v-model="form.grade" placeholder="如：2024级" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="专业">
              <el-input v-model="form.major" placeholder="如：软件技术" size="large" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学期">
              <el-input v-model="form.semester" placeholder="如：2025-2026-1" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程名称">
              <el-input v-model="form.course_name" placeholder="如：Web前端开发实训" size="large" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" size="large" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button class="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            @click="showCreate = false">
            取消
          </button>
          <button class="px-6 py-2.5 bg-gradient-to-r from-primary-500 to-indigo-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
            @click="createClass" :disabled="saving">
            <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
            创建
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑班级弹窗（优化样式） -->
    <el-dialog v-model="showEdit" title="编辑班级" width="600px" class="modern-dialog">
      <el-form :model="editForm" label-width="100px" class="modern-form">
        <el-form-item label="班级名称" required>
          <el-input v-model="editForm.name" placeholder="如：软件技术2401班" size="large" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="年级">
              <el-input v-model="editForm.grade" placeholder="如：2024级" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="专业">
              <el-input v-model="editForm.major" placeholder="如：软件技术" size="large" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学期">
              <el-input v-model="editForm.semester" placeholder="如：2025-2026-1" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程名称">
              <el-input v-model="editForm.course_name" placeholder="如：Web前端开发实训" size="large" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" size="large" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button class="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            @click="showEdit = false">
            取消
          </button>
          <button class="px-6 py-2.5 bg-gradient-to-r from-primary-500 to-indigo-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
            @click="saveEdit" :disabled="saving">
            <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
            保存
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 班级详情弹窗（优化样式） -->
    <el-dialog v-model="showDetail" :title="detailClass?.name" width="800px" class="modern-dialog">
      <div v-if="detailClass">
        <div class="flex justify-end mb-6">
          <button class="bg-gradient-to-r from-primary-500 to-indigo-600 text-white px-6 py-2.5 rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
            @click="openScores(detailClass.id)">
            <Icon icon="mdi:chart-bar" />
             成绩总览
          </button>
        </div>

        <el-descriptions border :column="2" class="modern-descriptions">
          <el-descriptions-item label="年级">{{ detailClass.grade }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ detailClass.major }}</el-descriptions-item>
          <el-descriptions-item label="学期">{{ detailClass.semester }}</el-descriptions-item>
          <el-descriptions-item label="课程">{{ detailClass.course_name }}</el-descriptions-item>
          <el-descriptions-item label="教师">{{ detailClass.teacher_name }}</el-descriptions-item>
          <el-descriptions-item label="邀请码">
            <span class="px-3 py-1.5 bg-orange-50 text-orange-600 rounded-lg text-sm font-bold">{{ detailClass.invite_code }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="mt-8">
          <h4 class="text-xl font-bold text-gray-900 mb-4">学生列表（{{ detailClass.student_count }}人）</h4>
          <div class="border border-gray-100 rounded-2xl overflow-hidden">
            <el-table :data="detailClass.students || []" style="width: 100%" :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }" max-height="350">
              <el-table-column prop="student_name" label="姓名" />
              <el-table-column prop="student_number" label="学号" />
              <el-table-column prop="joined_at" label="加入时间" width="180" />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <button class="px-4 py-1.5 bg-red-50 text-red-500 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors"
                    @click="removeStudent(row.id)">
                    移除
                  </button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 【完全保留你原有的所有业务逻辑，一行未改！只做视觉升级】
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const classes = ref<any[]>([])
const showCreate = ref(false)
const showEdit = ref(false)
const showDetail = ref(false)
const detailClass = ref<any>(null)

const form = reactive({
  name: '', grade: '', major: '', semester: '',
  course_name: '', description: ''
})

const editForm = reactive({
  id: 0, name: '', grade: '', major: '', semester: '',
  course_name: '', description: ''
})

onMounted(() => loadClasses())

const loadClasses = async () => {
  loading.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await api.get(`/api/classes/?teacher_id=${user.id}`)
    if (res.data.success) classes.value = res.data.data
  } catch {} finally { loading.value = false }
}

const createClass = async () => {
  if (!form.name) { ElMessage.warning('请输入班级名称'); return }
  saving.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    await api.post(`/api/classes/`, {
      ...form,
      teacher_id: user.id,
      teacher_name: user.real_name || user.username
    })
    ElMessage.success('班级创建成功')
    showCreate.value = false
    form.name = ''; form.grade = ''; form.major = ''; form.semester = ''
    form.course_name = ''; form.description = ''
    loadClasses()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '未知错误'
    ElMessage.error('创建失败：' + msg)
  } finally { saving.value = false }
}

const openEdit = (c: any) => {
  editForm.id = c.id
  editForm.name = c.name
  editForm.grade = c.grade
  editForm.major = c.major
  editForm.semester = c.semester
  editForm.course_name = c.course_name
  editForm.description = c.description
  showEdit.value = true
}

const saveEdit = async () => {
  if (!editForm.name) { ElMessage.warning('请输入班级名称'); return }
  saving.value = true
  try {
    await api.put(`/api/classes/${editForm.id}`, {
      name: editForm.name,
      grade: editForm.grade,
      major: editForm.major,
      semester: editForm.semester,
      course_name: editForm.course_name,
      description: editForm.description
    })
    ElMessage.success('班级信息已更新')
    showEdit.value = false
    loadClasses()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error || e?.message || '未知错误'
    ElMessage.error('保存失败：' + msg)
  } finally { saving.value = false }
}

const openScores = (classId: number) => {
  showDetail.value = false
  router.push(`/app/class-scores?id=${classId}`)
}

const viewDetail = async (c: any) => {
  try {
    const res = await api.get(`/api/classes/${c.id}/detail`)
    if (res.data.success) {
      detailClass.value = res.data.data
      showDetail.value = true
    }
  } catch {}
}

const copyCode = (code: string) => {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success(`邀请码 ${code} 已复制到剪贴板`)
  })
}

const deleteClass = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定解散该班级？所有学生将被移除。', '警告', { type: 'warning' })
    await api.delete(`/api/classes/${id}`)
    ElMessage.success('班级已解散')
    loadClasses()
  } catch {}
}

const removeStudent = async (memberId: number) => {
  try {
    await ElMessageBox.confirm('确定移除该学生？', '提示', { type: 'warning' })
    await api.delete(`/api/classes/${detailClass.value.id}/students/${memberId}`)
    ElMessage.success('已移除')
    viewDetail(detailClass.value)
  } catch {}
}
</script>

<style scoped>
/* 弹窗和表单样式优化 */
.modern-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
}
.modern-form :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;
}
.modern-form :deep(.el-input__wrapper):hover {
  border-color: #165DFF;
}
.modern-form :deep(.el-input__wrapper.is-focus) {
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}
.modern-form :deep(.el-textarea__inner) {
  border-radius: 0.75rem;
  border-color: #e5e7eb;
  transition: all 0.3s;
}
.modern-form :deep(.el-textarea__inner):focus {
  border-color: #165DFF;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}

/* 描述列表优化 */
.modern-descriptions :deep(.el-descriptions__label) {
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
}
.modern-descriptions :deep(.el-descriptions__body) {
  color: #111827;
}
</style>