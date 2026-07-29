<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 面包屑 + Title 区域 -->
      <div class="mb-10">
        <div class="flex items-center gap-2 text-sm text-surface-500 mb-3">
          <Icon icon="mdi:home-outline" class="text-base" />
          <span>/</span>
          <span>企业中心</span>
          <span>/</span>
          <span class="text-surface-800 font-medium">岗位管理</span>
        </div>
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 class="text-3xl font-bold text-surface-800 tracking-tight">岗位管理</h1>
            <p class="text-surface-500 mt-1">发布和管理你的招聘岗位，寻找优秀实习生</p>
          </div>
          <button class="btn-primary text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 self-start md:self-auto"
            @click="showCreate = true">
            <Icon icon="mdi:plus" />
            新建岗位
          </button>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="card p-6 mb-8">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2 flex-1 min-w-[200px]">
            <Icon icon="mdi:magnify" class="text-surface-400 text-lg" />
            <el-input v-model="searchText" placeholder="搜索岗位名称、技能标签..." size="large" class="modern-input" />
          </div>
          <el-select v-model="filterStatus" placeholder="招聘状态" size="large" class="w-40 modern-select">
            <el-option label="全部状态" value="" />
            <el-option label="招聘中" value="active" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已截止" value="closed" />
          </el-select>
          <el-select v-model="filterLocation" placeholder="工作地点" size="large" class="w-40 modern-select">
            <el-option label="全部地点" value="" />
            <el-option label="北京" value="beijing" />
            <el-option label="上海" value="shanghai" />
            <el-option label="深圳" value="shenzhen" />
            <el-option label="杭州" value="hangzhou" />
          </el-select>
          <button class="btn-ghost px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
            <Icon icon="mdi:filter-variant-remove" />
            重置
          </button>
        </div>
      </div>

      <!-- 岗位卡片列表 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div
          v-for="job in jobList"
          :key="job.id"
          class="card hover:shadow-xl hover:-translate-y-1 overflow-hidden transition-all duration-300"
        >
          <!-- 卡片顶部渐变条 -->
          <div :class="job.gradientBar" class="h-3"></div>

          <div class="p-8">
            <!-- 岗位头部信息 -->
            <div class="flex items-start justify-between mb-5">
              <div class="flex items-center gap-3">
                <div :class="job.logoBg" class="w-14 h-14 rounded-2xl flex items-center justify-center">
                  <Icon :icon="job.logo" class="text-3xl" :class="job.logoColor" />
                </div>
                <div>
                  <h3 class="text-xl font-bold text-surface-800">{{ job.name }}</h3>
                  <p class="text-sm text-surface-500 mt-0.5">{{ job.company }}</p>
                </div>
              </div>
              <span :class="job.statusClass" class="px-3 py-1.5 rounded-full text-xs font-bold flex-shrink-0">
                {{ job.status }}
              </span>
            </div>

            <!-- 薪资范围 -->
            <div class="mb-5">
              <span class="text-3xl font-black text-primary-600">{{ job.salary }}</span>
              <span class="text-sm text-surface-400 ml-2">· {{ job.salaryType }}</span>
            </div>

            <!-- 关键信息 -->
            <div class="space-y-2.5 mb-6 text-sm">
              <div class="flex items-center gap-2 text-surface-600">
                <Icon icon="mdi:map-marker-outline" class="text-primary-500" />
                <span>{{ job.location }} · {{ job.address }}</span>
              </div>
              <div class="flex items-center gap-2 text-surface-600">
                <Icon icon="mdi:briefcase-clock-outline" class="text-primary-500" />
                <span>{{ job.type }} · {{ job.experience }}</span>
              </div>
              <div class="flex items-center gap-2 text-surface-600">
                <Icon icon="mdi:calendar-outline" class="text-primary-500" />
                <span>创建于 {{ job.createdAt }}</span>
              </div>
            </div>

            <!-- 技能标签 -->
            <div class="flex flex-wrap gap-2 mb-6">
              <span
                v-for="tag in job.tags"
                :key="tag"
                class="px-3 py-1.5 bg-primary-50 text-primary-600 rounded-lg text-xs font-semibold"
              >
                {{ tag }}
              </span>
            </div>

            <!-- 匹配数据 -->
            <div class="flex items-center gap-6 p-4 bg-surface-50 rounded-2xl mb-6">
              <div class="text-center">
                <div class="text-2xl font-black text-surface-800">{{ job.matchCount }}</div>
                <div class="text-xs text-surface-500 mt-0.5">已匹配</div>
              </div>
              <div class="w-px h-10 bg-surface-200"></div>
              <div class="text-center">
                <div class="text-2xl font-black text-emerald-600">{{ job.viewCount }}</div>
                <div class="text-xs text-surface-500 mt-0.5">浏览量</div>
              </div>
              <div class="w-px h-10 bg-surface-200"></div>
              <div class="text-center">
                <div class="text-2xl font-black text-amber-600">{{ job.applyCount }}</div>
                <div class="text-xs text-surface-500 mt-0.5">待评价</div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex flex-wrap gap-2.5">
              <button class="flex-1 min-w-[90px] px-4 py-2.5 bg-primary-50 text-primary-600 rounded-xl font-semibold hover:bg-primary-100 transition-colors text-sm flex items-center justify-center gap-1.5">
                <Icon icon="mdi:pencil-outline" class="text-base" />
                编辑
              </button>
              <button class="flex-1 min-w-[90px] px-4 py-2.5 bg-violet-50 text-violet-600 rounded-xl font-semibold hover:bg-violet-100 transition-colors text-sm flex items-center justify-center gap-1.5">
                <Icon icon="mdi:account-multiple-check-outline" class="text-base" />
                查看匹配
              </button>
              <button class="flex-1 min-w-[90px] px-4 py-2.5 bg-red-50 text-red-500 rounded-xl font-semibold hover:bg-red-100 transition-colors text-sm flex items-center justify-center gap-1.5">
                <Icon icon="mdi:delete-outline" class="text-base" />
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建岗位弹窗 -->
    <el-dialog v-model="showCreate" title="新建招聘岗位" width="650px" class="modern-dialog">
      <el-form :model="form" label-width="110px" class="modern-form">
        <el-form-item label="岗位名称" required>
          <el-input v-model="form.name" placeholder="如：全栈开发工程师" size="large" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="招聘公司">
              <el-input v-model="form.company" placeholder="请输入公司名称" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作地点">
              <el-select v-model="form.location" placeholder="请选择" size="large" class="w-full modern-select">
                <el-option label="北京" value="北京" />
                <el-option label="上海" value="上海" />
                <el-option label="深圳" value="深圳" />
                <el-option label="杭州" value="杭州" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="薪资范围">
              <el-input v-model="form.salary" placeholder="如：20-40K" size="large" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作类型">
              <el-select v-model="form.type" placeholder="请选择" size="large" class="w-full modern-select">
                <el-option label="实习" value="实习" />
                <el-option label="全职" value="全职" />
                <el-option label="校招" value="校招" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="技能标签">
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            placeholder="输入后回车添加标签"
            size="large"
            class="w-full modern-select"
          >
            <el-option label="Vue.js" value="Vue.js" />
            <el-option label="React" value="React" />
            <el-option label="TypeScript" value="TypeScript" />
            <el-option label="Node.js" value="Node.js" />
            <el-option label="Java" value="Java" />
            <el-option label="Python" value="Python" />
          </el-select>
        </el-form-item>
        <el-form-item label="岗位描述">
          <el-input v-model="form.description" type="textarea" :rows="4" size="large" placeholder="请输入岗位要求和职责..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button class="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            @click="showCreate = false">
            取消
          </button>
          <button class="px-6 py-2.5 bg-gradient-to-r from-primary-500 to-indigo-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
            @click="handleCreate">
            创建岗位
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'

const searchText = ref('')
const filterStatus = ref('')
const filterLocation = ref('')
const showCreate = ref(false)

const form = reactive({
  name: '',
  company: '',
  location: '',
  salary: '',
  type: '',
  tags: [] as string[],
  description: ''
})

const jobList = ref([
  {
    id: 1,
    name: '全栈开发工程师',
    company: '字节跳动',
    location: '北京',
    address: '海淀区知春路',
    salary: '25-45K',
    salaryType: '15薪',
    type: '全职',
    experience: '应届生/1-3年',
    createdAt: '2025-07-15',
    matchCount: 48,
    viewCount: 1256,
    applyCount: 12,
    status: '招聘中',
    statusClass: 'bg-green-50 text-green-600',
    gradientBar: 'bg-gradient-to-r from-blue-500 to-indigo-600',
    logo: 'mdi:language-css3',
    logoBg: 'bg-gradient-to-br from-blue-100 to-blue-200',
    logoColor: 'text-blue-600',
    tags: ['Vue.js', 'React', 'Node.js', 'TypeScript', 'MySQL']
  },
  {
    id: 2,
    name: '高级前端工程师',
    company: '腾讯科技',
    location: '深圳',
    address: '南山区科技园',
    salary: '20-40K',
    salaryType: '16薪',
    type: '校招',
    experience: '应届生',
    createdAt: '2025-07-20',
    matchCount: 36,
    viewCount: 982,
    applyCount: 8,
    status: '招聘中',
    statusClass: 'bg-green-50 text-green-600',
    gradientBar: 'bg-gradient-to-r from-emerald-500 to-green-600',
    logo: 'mdi:vuejs',
    logoBg: 'bg-gradient-to-br from-emerald-100 to-emerald-200',
    logoColor: 'text-emerald-600',
    tags: ['Vue.js', 'TypeScript', 'Webpack', '小程序', 'CSS3']
  },
  {
    id: 3,
    name: '后端开发工程师',
    company: '阿里巴巴',
    location: '杭州',
    address: '余杭区西溪园区',
    salary: '22-42K',
    salaryType: '16薪',
    type: '全职',
    experience: '1-3年',
    createdAt: '2025-07-10',
    matchCount: 52,
    viewCount: 1580,
    applyCount: 15,
    status: '即将截止',
    statusClass: 'bg-amber-50 text-amber-600',
    gradientBar: 'bg-gradient-to-r from-orange-500 to-red-500',
    logo: 'mdi:language-java',
    logoBg: 'bg-gradient-to-br from-orange-100 to-orange-200',
    logoColor: 'text-orange-600',
    tags: ['Java', 'Spring Boot', 'MySQL', 'Redis', '微服务']
  }
])

const handleCreate = () => {
  if (!form.name) {
    ElMessage.warning('请输入岗位名称')
    return
  }
  ElMessage.success('岗位创建成功！')
  showCreate.value = false
  form.name = ''
  form.company = ''
  form.location = ''
  form.salary = ''
  form.type = ''
  form.tags = []
  form.description = ''
}
</script>

<style scoped>
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
.modern-input :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
}
.modern-select :deep(.el-select__wrapper) {
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e5e7eb;
}
</style>
