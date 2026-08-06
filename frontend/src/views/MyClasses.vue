<template>
  <div class="page-enter">
    <div class="max-w-5xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">我的班级</h1>
        <p class="text-surface-500 mt-1">加入班级并查看你的班级排名</p>
      </div>

      <!-- 加入班级卡片 -->
      <div class="bg-white rounded-3xl border border-gray-100 shadow-xl p-8 mb-10">
        <div class="flex flex-col md:flex-row md:items-center gap-6">
          <div class="flex-1">
            <h3 class="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
              <span class="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center">
                <Icon icon="mdi:key" class="text-xl text-orange-500" />
              </span>
              加入班级
            </h3>
            <p class="text-gray-500">输入教师提供的6位邀请码加入班级</p>
          </div>
          <div class="flex gap-3 w-full md:w-auto">
            <el-input v-model="inviteCode" placeholder="请输入6位邀请码" maxlength="6" size="large" class="flex-1 md:w-64 modern-input" />
            <button class="bg-gradient-to-r from-orange-500 to-amber-600 text-white px-8 py-3 rounded-xl font-bold text-lg hover:shadow-lg hover:shadow-orange-500/30 transition-all"
              @click="joinClass" :disabled="joining">
              <span v-if="joining" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"></span>
              加入班级
            </button>
          </div>
        </div>
      </div>

      <!-- 已加入的班级 -->
      <div v-if="myClasses.length > 0">
        <h3 class="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <span class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
            <Icon icon="mdi:book-open-page-variant" class="text-xl text-primary-500" />
          </span>
          已加入的班级
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div
            v-for="c in myClasses"
            :key="c.id"
            class="bg-white rounded-3xl border border-gray-100 shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
          >
            <!-- 卡片顶部渐变条 -->
            <div class="h-3 bg-gradient-to-r from-primary-500 to-indigo-600"></div>
            
            <div class="p-8">
              <div class="mb-6">
                <h3 class="text-2xl font-bold text-gray-900 mb-2">{{ c.name }}</h3>
                <p class="text-primary-500 text-lg font-medium">{{ c.course_name }}</p>
              </div>

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
              </div>

              <button class="w-full bg-gradient-to-r from-orange-500 to-amber-600 text-white px-6 py-3 rounded-xl font-bold text-lg hover:shadow-lg hover:shadow-orange-500/30 transition-all flex items-center justify-center gap-2"
                @click="showRanking(c)">
                <Icon icon="mdi:trophy" />
                 班级排名
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="min-h-[40vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-32 h-32 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-6">
            <Icon icon="mdi:book-open-page-variant" class="text-5xl text-gray-300" />
          </div>
          <p class="text-gray-500 text-xl mb-8">还没加入任何班级，输入邀请码加入吧</p>
        </div>
      </div>
    </div>

    <!-- 班级排名弹窗（优化样式） -->
    <el-dialog v-model="showRank" title="班级排名" width="700px" class="modern-dialog">
      <div v-if="ranking">
        <!-- 排名统计卡片 -->
        <div class="grid grid-cols-3 gap-4 mb-8">
          <div class="bg-gradient-to-br from-primary-500 to-indigo-600 rounded-2xl p-6 text-white text-center">
            <div class="text-white/80 text-sm font-medium mb-2">我的排名</div>
            <div class="text-4xl font-black">{{ ranking.my_rank }}<span class="text-lg font-normal">/ {{ ranking.total_students }}</span></div>
          </div>
          <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white text-center">
            <div class="text-white/80 text-sm font-medium mb-2">我的平均分</div>
            <div class="text-4xl font-black">{{ ranking.my_avg }}<span class="text-lg font-normal">分</span></div>
          </div>
          <div class="bg-gradient-to-br from-orange-500 to-amber-600 rounded-2xl p-6 text-white text-center">
            <div class="text-white/80 text-sm font-medium mb-2">班级平均分</div>
            <div class="text-4xl font-black">{{ ranking.class_avg }}<span class="text-lg font-normal">分</span></div>
          </div>
        </div>

        <!-- 排名表格 -->
        <div class="border border-gray-100 rounded-2xl overflow-hidden">
          <el-table :data="ranking.ranking" style="width: 100%" :header-cell-style="{ background: '#f9fafb', color: '#111827', fontWeight: 700 }" max-height="400" class="modern-table">
            <el-table-column label="排名" width="100" align="center">
              <template #default="{ $index }">
                <div v-if="$index === 0" class="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-400 to-amber-500 flex items-center justify-center text-white text-xl shadow-lg mx-auto">
                  1
                </div>
                <div v-else-if="$index === 1" class="w-10 h-10 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 flex items-center justify-center text-white text-xl shadow-lg mx-auto">
                  2
                </div>
                <div v-else-if="$index === 2" class="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center text-white text-xl shadow-lg mx-auto">
                  3
                </div>
                <span v-else class="text-xl font-bold text-gray-500">{{ $index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="student_name" label="姓名">
              <template #default="{ row }">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-indigo-600 flex items-center justify-center text-white font-bold">
                    {{ row.student_name?.charAt(0) }}
                  </div>
                  <span class="font-medium text-gray-900">{{ row.student_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="avg_score" label="平均分" width="140" align="center">
              <template #default="{ row }">
                <span :class="row.avg_score >= 80 ? 'text-green-600' : row.avg_score >= 60 ? 'text-orange-500' : 'text-red-500'"
                  class="text-xl font-black">
                  {{ row.avg_score }}<span class="text-sm font-normal">分</span>
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="submit_count" label="提交数" width="100" align="center">
              <template #default="{ row }">
                <span :class="row.submit_count > 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'"
                  class="px-3 py-1.5 rounded-full text-sm font-bold">
                  {{ row.submit_count }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const inviteCode = ref('')
const joining = ref(false)
const myClasses = ref<any[]>([])
const showRank = ref(false)
const ranking = ref<any>(null)

onMounted(async () => {
  await loadMyClasses()
  // 加载完整用户信息
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(`/api/user/profile/${user.id}`)
    if (res.data.success) {
      user.user_number = res.data.data.user_number || ''
      localStorage.setItem('user', JSON.stringify(user))
    }
  } catch {}
})

const loadMyClasses = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(`/api/classes/my?student_id=${user.id}`)
    if (res.data.success) myClasses.value = res.data.data
  } catch {}
}

const joinClass = async () => {
  if (!inviteCode.value.trim()) { ElMessage.warning('请输入邀请码'); return }
  joining.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    await api.post(`/api/classes/join`, {
      invite_code: inviteCode.value.trim().toUpperCase(),
      student_id: user.id,
      student_name: user.real_name || user.username,
      student_number: user.user_number || ''
    })
    ElMessage.success('加入成功')
    inviteCode.value = ''
    loadMyClasses()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '加入失败')
  } finally { joining.value = false }
}

const showRanking = async (c: any) => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(
      `/api/statistics/class/${c.id}/ranking?student_id=${user.id}`
    )
    if (res.data.success) {
      ranking.value = res.data.data
      showRank.value = true
    }
  } catch {}
}
</script>

<style scoped>
/* 表单样式优化 */
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

/* 表格样式优化 */
.modern-table :deep(.el-table__header-wrapper th) {
  background-color: #f9fafb;
  color: #111827;
  font-weight: 700;
}
.modern-table :deep(.el-table__row:hover) {
  background-color: #f9fafb;
}
</style>