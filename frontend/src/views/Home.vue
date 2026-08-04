<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 欢迎区域（保留作页面 Header，不套卡片） -->
      <div class="mb-8" v-if="user">
        <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold text-surface-800 tracking-tight">
              欢迎回来，{{ user.real_name || user.username }}
            </h1>
            <p class="text-surface-500 mt-1.5 text-base">
              {{ user.role === 'teacher' ? '今天又有新的实训成果等待评价' : '继续努力，不断提升编程技能' }}
            </p>
          </div>
          <div v-if="user?.role === 'student' && pendingCount > 0"
            class="flex items-center gap-3 bg-accent-50 border border-accent-200 rounded-2xl px-5 py-3 animate-scale-in">
            <Icon icon="mdi:alarm" class="text-2xl text-accent-500" />
            <span class="text-accent-700 font-semibold text-sm">还有 {{ pendingCount }} 份待提交任务</span>
            <button class="btn-accent text-white px-4 py-1.5 rounded-lg text-sm font-bold" @click="$router.push('/app/student-tasks')">
              立即查看
            </button>
          </div>
        </div>
      </div>

      <!-- ==================== 教师端 · 单一统一大卡片 ==================== -->
      <section v-if="user && user.role === 'teacher'" class="home-unified role-teacher">
        <!-- 分区1：数据概览（无外层独立卡片，平铺） -->
        <div class="hu-section" v-if="teacherStats">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:chart-box-outline" class="sh-ic ic-amber" /> 数据概览</h3>
            <span class="hu-sec-tag tag-amber">实时代码</span>
          </div>
          <div class="kpi-grid four">
            <div class="kpi-item kpi-amber">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:clipboard-alert-outline" /></div>
                <span class="kpi-chip">待评分</span>
              </div>
              <div class="kpi-num">{{ teacherStats.unscored_count }}</div>
              <div class="kpi-lbl">份待处理</div>
            </div>
            <div class="kpi-item kpi-blue">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:school-outline" /></div>
                <span class="kpi-chip">班级</span>
              </div>
              <div class="kpi-num">{{ teacherStats.class_count }}</div>
              <div class="kpi-lbl">个班级</div>
            </div>
            <div class="kpi-item kpi-emerald">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:account-group-outline" /></div>
                <span class="kpi-chip">学生</span>
              </div>
              <div class="kpi-num">{{ teacherStats.student_count }}</div>
              <div class="kpi-lbl">人</div>
            </div>
            <div class="kpi-item kpi-violet">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:trending-up" /></div>
                <span class="kpi-chip">本月</span>
              </div>
              <div class="kpi-num">{{ teacherStats.month_submissions }}</div>
              <div class="kpi-lbl">份提交</div>
            </div>
          </div>
        </div>

        <!-- 分区2：快捷操作入口（平铺，无外层小卡片） -->
        <div class="hu-section">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:lightning-bolt-outline" class="sh-ic ic-blue" /> 快捷入口</h3>
            <span class="hu-sec-tag">常用功能</span>
          </div>
          <div class="action-grid four">
            <div v-for="(item, idx) in teacherActions" :key="item.title"
                 class="action-item"
                 :style="`animation-delay: ${idx * 0.08}s`"
                 @click="$router.push(item.path)">
              <div class="act-ic"><Icon :icon="item.icon" /></div>
              <div class="act-title">{{ item.title }}</div>
              <div class="act-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>

        <!-- 分区3：最近动态 -->
        <div class="hu-section" v-if="recentActivities.length > 0">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:history" class="sh-ic ic-blue" /> 最近动态</h3>
          </div>
          <div class="activity-list">
            <div v-for="act in recentActivities" :key="act.id" class="act-row">
              <div class="act-row-ic">
                <Icon :icon="act.type === 'submission' ? 'mdi:file-document-outline' : 'mdi:clipboard-text-outline'" />
              </div>
              <div class="act-row-body">
                <p class="act-row-text">
                  <template v-if="act.type === 'submission'">
                    <span class="font-semibold">{{ act.student_name }}</span>
                    在 <span class="font-semibold">{{ act.class_name }}</span>
                    提交了 <span class="font-medium">{{ act.task_title }}</span>
                    <span v-if="act.filename" class="text-surface-400">（{{ act.filename }}）</span>
                  </template>
                  <template v-else>
                    <span class="font-semibold">{{ act.teacher_name }}</span>
                    发布了新任务 <span class="font-medium">{{ act.task_title }}</span>
                  </template>
                </p>
                <p class="act-row-time">{{ act.time }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 分区4：我的班级 -->
        <div class="hu-section hu-last">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:google-classroom" class="sh-ic ic-emerald" /> 我的班级</h3>
            <button class="btn-link-primary" @click="$router.push('/app/class-manage')">
              管理班级 <Icon icon="mdi:chevron-right" class="ml-1" />
            </button>
          </div>

          <div v-if="myClasses.length > 0" class="class-grid three">
            <div v-for="c in myClasses" :key="c.id"
                 class="class-card"
                 @click="$router.push(`/app/class-scores?id=${c.id}`)">
              <div class="class-head">
                <h4 class="class-name">{{ c.name }}</h4>
                <Icon icon="mdi:chevron-right" class="class-arrow" />
              </div>
              <p class="class-course">{{ c.course_name }}</p>
              <div class="class-foot">
                <span class="class-stat"><Icon icon="mdi:account-group" /> {{ c.student_count }}人</span>
              </div>
            </div>
          </div>

          <!-- 空状态（引导三步） -->
          <div v-else class="onboarding">
            <div class="ob-hero">
              <Icon icon="mdi:rocket-launch-outline" class="ob-hero-ic" />
              <h3 class="ob-hero-title">欢迎使用知训云！</h3>
              <p class="ob-hero-desc">只需三步即可开始</p>
            </div>
            <div class="ob-steps">
              <div class="ob-step">
                <div class="ob-step-no">①</div>
                <div class="ob-step-title">创建班级</div>
                <div class="ob-step-desc">生成邀请码</div>
              </div>
              <div class="ob-step">
                <div class="ob-step-no">②</div>
                <div class="ob-step-title">发布任务</div>
                <div class="ob-step-desc">AI辅助生成</div>
              </div>
              <div class="ob-step">
                <div class="ob-step-no">③</div>
                <div class="ob-step-title">查看提交</div>
                <div class="ob-step-desc">AI自动评分</div>
              </div>
            </div>
            <button class="btn-primary ob-cta text-white font-bold" @click="$router.push('/app/class-manage')">
              开始创建班级
            </button>
          </div>
        </div>
      </section>

      <!-- ==================== 学生端 · 单一统一大卡片 ==================== -->
      <section v-if="user && user.role === 'student'" class="home-unified role-student">
        <!-- 分区1：数据概览 -->
        <div class="hu-section" v-if="studentStats">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:chart-box-outline" class="sh-ic ic-amber" /> 学习概况</h3>
            <span class="hu-sec-tag tag-amber">数据看板</span>
          </div>
          <div class="kpi-grid four">
            <div class="kpi-item kpi-amber">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:clock-outline" /></div>
                <span class="kpi-chip">待提交</span>
              </div>
              <div class="kpi-num">{{ studentStats.pending_count }}</div>
              <div class="kpi-lbl">份</div>
            </div>
            <div class="kpi-item kpi-emerald">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:check-circle-outline" /></div>
                <span class="kpi-chip">已完成</span>
              </div>
              <div class="kpi-num">{{ studentStats.completed_count }}</div>
              <div class="kpi-lbl">份</div>
            </div>
            <div class="kpi-item kpi-blue">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:chart-line-variant" /></div>
                <span class="kpi-chip">平均分</span>
              </div>
              <div class="kpi-num">{{ studentStats.avg_score }}</div>
              <div class="kpi-lbl">分</div>
            </div>
            <div class="kpi-item kpi-violet">
              <div class="kpi-top">
                <div class="kpi-ic"><Icon icon="mdi:podium" /></div>
                <span class="kpi-chip">班级排名</span>
              </div>
              <div class="kpi-num">{{ studentStats.rank || '-' }}</div>
              <div class="kpi-lbl">名</div>
            </div>
          </div>
        </div>

        <!-- 分区2：AI 岗位匹配 -->
        <div class="hu-section" v-if="cachedJobMatch || jobMatchLoading">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:briefcase-outline" class="sh-ic ic-violet" /> AI 岗位匹配</h3>
            <span class="hu-sec-tag tag-violet">智能推荐</span>
          </div>
          <div v-if="cachedJobMatch" class="job-match-box">
            <div class="jm-row">
              <div class="jm-job">{{ cachedJobMatch.job }}</div>
              <div class="jm-pct">{{ cachedJobMatch.match }}%</div>
            </div>
            <div class="jm-bar">
              <div class="jm-bar-fill" :style="{ width: cachedJobMatch.match + '%' }"></div>
            </div>
            <p class="jm-advice">{{ cachedJobMatch.advice }}</p>
          </div>
          <div v-else-if="jobMatchLoading" class="jm-loading">
            <div class="spinner"></div>
            <p>AI正在分析...</p>
          </div>
        </div>

        <!-- 分区3：快捷入口 -->
        <div class="hu-section">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:lightning-bolt-outline" class="sh-ic ic-blue" /> 快捷入口</h3>
            <span class="hu-sec-tag">常用功能</span>
          </div>
          <div class="action-grid four">
            <div v-for="(item, idx) in studentActions" :key="item.title"
                 class="action-item"
                 :style="`animation-delay: ${idx * 0.08}s`"
                 @click="$router.push(item.path)">
              <div class="act-ic"><Icon :icon="item.icon" /></div>
              <div class="act-title">{{ item.title }}</div>
              <div class="act-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>

        <!-- 分区4：我的班级 -->
        <div class="hu-section hu-last">
          <div class="hu-sec-head">
            <h3 class="hu-sec-title"><Icon icon="mdi:google-classroom" class="sh-ic ic-emerald" /> 我的班级</h3>
            <button class="btn-link-primary" @click="$router.push('/app/my-classes')">
              加入班级 <Icon icon="mdi:chevron-right" class="ml-1" />
            </button>
          </div>

          <div v-if="studentClasses.length > 0" class="class-grid three">
            <div v-for="c in studentClasses" :key="c.id"
                 class="class-card"
                 @click="$router.push('/app/my-classes')">
              <div class="class-head">
                <h4 class="class-name">{{ c.name }}</h4>
                <Icon icon="mdi:chevron-right" class="class-arrow" />
              </div>
              <p class="class-course">{{ c.course_name }}</p>
              <div class="class-foot">
                <span class="class-stat"><Icon icon="mdi:account-tie" /> {{ c.teacher_name }}</span>
              </div>
            </div>
          </div>

          <!-- 空状态：欢迎引导 -->
          <div v-else class="onboarding ob-student">
            <div class="ob-hero">
              <Icon icon="mdi:school-outline" class="ob-hero-ic ob-emerald" />
              <h3 class="ob-hero-title">欢迎加入知训云！</h3>
              <p class="ob-hero-desc">只需两步即可开始</p>
            </div>
            <div class="ob-steps two">
              <div class="ob-step">
                <div class="ob-step-no ob-emerald-no">①</div>
                <div class="ob-step-title">加入班级</div>
                <div class="ob-step-desc">输入教师邀请码</div>
              </div>
              <div class="ob-step">
                <div class="ob-step-no ob-emerald-no">②</div>
                <div class="ob-step-title">提交作业</div>
                <div class="ob-step-desc">AI自动评分反馈</div>
              </div>
            </div>
            <button class="btn-primary ob-cta text-white font-bold" @click="$router.push('/app/my-classes')">
              去加入班级
            </button>
          </div>
        </div>
      </section>

      <!-- 未登录 -->
      <div v-if="!user" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mx-auto mb-8 shadow-xl shadow-primary-500/20">
            <Icon icon="mdi:clipboard-text-outline" class="text-5xl text-white" />
          </div>
          <h1 class="text-4xl font-bold text-surface-800 mb-4 tracking-tight">实训教学评价系统</h1>
          <p class="text-xl text-surface-500 mb-10 max-w-2xl mx-auto">
            基于大模型技术的智能化实训成果评价平台
          </p>
          <div class="flex items-center justify-center gap-4">
            <button class="btn-primary text-white px-8 py-3 rounded-xl text-lg font-semibold" @click="$router.push('/login')">
              登录
            </button>
            <button class="btn-ghost px-8 py-3 rounded-xl text-lg" @click="$router.push('/login')">
              注册
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const user = ref<any>(null)
const myClasses = ref<any[]>([])
const studentClasses = ref<any[]>([])
const pendingCount = ref(0)
const recentActivities = ref<any[]>([])
const teacherStats = ref<any>(null)
const studentStats = ref<any>(null)
const cachedJobMatch = ref<any>(null)
const jobMatchLoading = ref(false)

onMounted(async () => {
  const data = localStorage.getItem('user')
  if (data) {
    user.value = JSON.parse(data)

    if (user.value.role === 'teacher') {
      await loadTeacherStats()
      await loadRecentActivities()
      try {
        const res = await axios.get(`${API_BASE}/api/classes/?teacher_id=${user.value.id}`)
        if (res.data.success) myClasses.value = res.data.data
      } catch {}
    }

    if (user.value.role === 'student') {
      await loadStudentStats()
      try {
        const res = await axios.get(`${API_BASE}/api/classes/my?student_id=${user.value.id}`)
        if (res.data.success) studentClasses.value = res.data.data
      } catch {}
      try {
        const taskRes = await axios.get(`${API_BASE}/api/tasks/pending?student_id=${user.value.id}`)
        if (taskRes.data.success) {
          pendingCount.value = taskRes.data.data.filter((t: any) => !t.submitted).length
        }
      } catch {}
      const cached = localStorage.getItem('home_job_match')
      if (cached) {
        cachedJobMatch.value = JSON.parse(cached)
      } else {
        loadJobMatchForHome()
      }
    }
  }
})

const loadTeacherStats = async () => {
  try {
    const [overviewRes, classesRes] = await Promise.all([
      axios.get(`${API_BASE}/api/statistics/overview`),
      axios.get(`${API_BASE}/api/classes/?teacher_id=${user.value.id}`)
    ])
    const overview = overviewRes.data.success ? overviewRes.data.data : {}
    const classes = classesRes.data.success ? classesRes.data.data : []
    let totalStudents = 0
    classes.forEach((c: any) => { totalStudents += c.student_count || 0 })
    teacherStats.value = {
      unscored_count: overview.total_submissions || 0,
      class_count: classes.length,
      student_count: totalStudents,
      month_submissions: overview.total_submissions || 0
    }
  } catch {}
}

const loadStudentStats = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/student/${user.value.id}`)
    if (res.data.success) {
      const d = res.data.data
      studentStats.value = {
        pending_count: pendingCount.value,
        completed_count: d.total_count,
        avg_score: d.avg_score,
        rank: '-'
      }
    }
  } catch {}
}

const loadRecentActivities = async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/activities`)
    if (res.data.success) {
      recentActivities.value = res.data.data
    }
  } catch {}
}

const loadJobMatchForHome = async () => {
  jobMatchLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/statistics/job-match/${user.value.id}`)
    if (res.data.success) {
      cachedJobMatch.value = res.data.data
      localStorage.setItem('home_job_match', JSON.stringify(res.data.data))
    }
  } catch {} finally {
    jobMatchLoading.value = false
  }
}

const teacherActions = [
  { icon: 'mdi:clipboard-text-outline', title: '任务管理', desc: '发布实训任务并查看提交', path: '/app/task-manage' },
  { icon: 'mdi:book-open-page-variant-outline', title: '班级管理', desc: '创建班级和管理学生', path: '/app/class-manage' },
  { icon: 'mdi:chart-bar', title: '数据统计', desc: '教学质量画像与趋势', path: '/app/statistics' },
  { icon: 'mdi:tune-variant', title: '评价标准', desc: '预设评价维度与权重', path: '/app/criteria' }
]

const studentActions = [
  { icon: 'mdi:pencil-box-outline', title: '待提交任务', desc: '查看并提交实训作业', path: '/app/student-tasks' },
  { icon: 'mdi:book-open-page-variant-outline', title: '我的班级', desc: '加入班级查看排名', path: '/app/my-classes' },
  { icon: 'mdi:chart-line-variant', title: '我的成绩', desc: '查看评分与薄弱点', path: '/app/my-scores' },
  { icon: 'mdi:chart-bar', title: '数据统计', desc: '整体教学质量概况', path: '/app/statistics' }
]
</script>

<style scoped>
/* ============ 单一统一大卡片外壳 ============ */
.home-unified {
  max-width: 100%;
  background: #fff;
  border: 1px solid #E5E1D2;
  border-top: 4px solid #165DFF;
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04), 0 12px 36px rgba(17, 24, 39, 0.06);
  overflow: hidden;
  margin-bottom: 32px;
}
.home-unified.role-teacher { border-top-color: #FF7A00; }
.home-unified.role-student { border-top-color: #165DFF; }

/* ============ 分区 ============ */
.hu-section {
  padding: 22px 32px;
  border-bottom: 1px dashed #E5E1D2;
}
.hu-section.hu-last { border-bottom: none; }

.hu-sec-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.hu-sec-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0.02em;
}
.sh-ic {
  width: 28px; height: 28px;
  border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 15px;
}
.ic-amber   { background: rgba(245, 158, 11, 0.12);  color: #D97706; }
.ic-blue    { background: rgba(22, 93, 255, 0.10);  color: #165DFF; }
.ic-emerald { background: rgba(16, 185, 129, 0.12); color: #059669; }
.ic-violet  { background: rgba(124, 58, 237, 0.12); color: #7C3AED; }

.hu-sec-tag {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(22, 93, 255, 0.08);
  color: #165DFF;
  letter-spacing: 0.06em;
}
.hu-sec-tag.tag-amber  { background: rgba(245, 158, 11, 0.10); color: #D97706; }
.hu-sec-tag.tag-violet { background: rgba(124, 58, 237, 0.10); color: #7C3AED; }

.btn-link-primary {
  margin-left: auto;
  font-size: 12.5px;
  font-weight: 600;
  color: #165DFF;
  background: none;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.btn-link-primary:hover { color: #6366F1; }

/* ============ KPI 网格（平铺，无小卡片外壳） ============ */
.kpi-grid { display: grid; gap: 14px; }
.kpi-grid.four { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 1080px) { .kpi-grid.four { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 520px)  { .kpi-grid.four { grid-template-columns: 1fr; } }

.kpi-item {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  background: #F7F4EC;
  position: relative;
  overflow: hidden;
}
.kpi-item::before {
  content: '';
  position: absolute;
  right: -20px; top: -20px;
  width: 80px; height: 80px;
  border-radius: 50%;
  opacity: 0.25;
}
.kpi-amber::before   { background: #F59E0B; }
.kpi-blue::before    { background: #165DFF; }
.kpi-emerald::before { background: #10B981; }
.kpi-violet::before  { background: #7C3AED; }

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
}
.kpi-ic {
  width: 40px; height: 40px;
  border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 20px;
  color: #fff;
}
.kpi-amber   .kpi-ic { background: #D97706; }
.kpi-blue    .kpi-ic { background: #165DFF; }
.kpi-emerald .kpi-ic { background: #059669; }
.kpi-violet  .kpi-ic { background: #7C3AED; }

.kpi-chip {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.65);
  color: #374151;
}
.kpi-num {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 30px;
  line-height: 1.1;
  color: #111827;
  position: relative;
  z-index: 1;
}
.kpi-lbl {
  font-size: 12.5px;
  color: #6B7280;
  margin-top: 4px;
  position: relative;
  z-index: 1;
}

/* ============ 快捷操作入口 ============ */
.action-grid { display: grid; gap: 14px; }
.action-grid.four { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 1080px) { .action-grid.four { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 520px)  { .action-grid.four { grid-template-columns: 1fr; } }

.action-item {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  background: #F7F4EC;
  cursor: pointer;
  transition: all 0.25s ease;
}
.action-item:hover {
  transform: translateY(-1px);
  border-color: #165DFF;
  background: rgba(22, 93, 255, 0.05);
  box-shadow: 0 6px 18px rgba(17, 24, 39, 0.06);
}
.act-ic {
  width: 44px; height: 44px;
  border-radius: 14px;
  background: rgba(22, 93, 255, 0.10);
  color: #165DFF;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 22px;
  margin-bottom: 12px;
  transition: transform 0.25s ease, background 0.25s ease;
}
.action-item:hover .act-ic {
  transform: scale(1.08);
  background: #165DFF;
  color: #fff;
}
.act-title {
  font-weight: 700;
  color: #111827;
  font-size: 15px;
  margin-bottom: 4px;
}
.act-desc {
  font-size: 12.5px;
  color: #6B7280;
  line-height: 1.5;
}

/* ============ 动态列表 ============ */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.act-row {
  display: flex;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  transition: background 0.15s ease;
}
.act-row:hover { background: #F7F4EC; }
.act-row-ic {
  width: 40px; height: 40px;
  border-radius: 12px;
  background: rgba(22, 93, 255, 0.10);
  color: #165DFF;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.act-row-body { flex: 1; min-width: 0; }
.act-row-text {
  margin: 0;
  font-size: 13.5px;
  color: #1F2937;
  line-height: 1.55;
}
.act-row-time {
  margin: 4px 0 0;
  font-size: 11.5px;
  color: #9CA3AF;
}

/* ============ 班级网格 ============ */
.class-grid { display: grid; gap: 14px; }
.class-grid.three { grid-template-columns: repeat(3, minmax(0,1fr)); }
@media (max-width: 1080px) { .class-grid.three { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 640px)  { .class-grid.three { grid-template-columns: 1fr; } }

.class-card {
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  cursor: pointer;
  transition: all 0.25s ease;
}
.class-card:hover {
  border-color: #165DFF;
  background: rgba(22, 93, 255, 0.04);
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(17, 24, 39, 0.06);
}
.class-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.class-name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  transition: color 0.2s ease;
}
.class-card:hover .class-name { color: #165DFF; }
.class-arrow {
  color: #D1D5DB;
  transition: color 0.2s ease, transform 0.2s ease;
}
.class-card:hover .class-arrow { color: #165DFF; transform: translateX(3px); }
.class-course {
  margin: 0 0 12px;
  font-size: 13px;
  color: #6B7280;
}
.class-foot {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12.5px;
  color: #6B7280;
}
.class-stat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

/* ============ 新用户引导 ============ */
.onboarding {
  padding: 28px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
  border: 1px solid rgba(22, 93, 255, 0.12);
  text-align: center;
}
.ob-student {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, rgba(5, 150, 105, 0.06) 100%);
  border-color: rgba(16, 185, 129, 0.18);
}
.ob-hero { margin-bottom: 20px; }
.ob-hero-ic {
  font-size: 48px;
  color: #165DFF;
  margin-bottom: 14px;
}
.ob-hero-ic.ob-emerald { color: #059669; }
.ob-hero-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}
.ob-hero-desc {
  margin: 0;
  font-size: 14px;
  color: #6B7280;
}
.ob-steps {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}
.ob-steps.two .ob-step { width: 220px; }
.ob-step {
  width: 180px;
  padding: 16px;
  background: #fff;
  border: 1px solid #E5E1D2;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
}
.ob-step-no {
  width: 40px; height: 40px;
  border-radius: 12px;
  background: rgba(22, 93, 255, 0.10);
  color: #165DFF;
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 22px;
  line-height: 40px;
  text-align: center;
  margin: 0 auto 10px;
}
.ob-step-no.ob-emerald-no { background: rgba(16, 185, 129, 0.12); color: #059669; }
.ob-step-title {
  font-weight: 700;
  font-size: 14px;
  color: #111827;
  margin-bottom: 4px;
}
.ob-step-desc {
  font-size: 12px;
  color: #9CA3AF;
}
.ob-cta {
  padding: 10px 26px;
  border-radius: 12px;
}

/* ============ AI 岗位匹配 ============ */
.job-match-box {
  padding: 20px 24px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
  border: 1px solid rgba(124, 58, 237, 0.22);
}
.jm-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.jm-job {
  font-weight: 800;
  font-size: 17px;
  color: #111827;
}
.jm-pct {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 28px;
  color: #7C3AED;
}
.jm-bar {
  width: 100%;
  height: 10px;
  background: rgba(124, 58, 237, 0.20);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 12px;
}
.jm-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #7C3AED 0%, #A855F7 100%);
  border-radius: 999px;
  transition: width 1s ease-out;
}
.jm-advice {
  margin: 0;
  font-size: 13px;
  color: #4B5563;
  line-height: 1.7;
}
.jm-loading {
  padding: 28px 0;
  text-align: center;
  font-size: 13.5px;
  color: #9CA3AF;
}
.spinner {
  width: 30px; height: 30px;
  border: 2.5px solid rgba(124, 58, 237, 0.22);
  border-top-color: #7C3AED;
  border-radius: 50%;
  margin: 0 auto 10px;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ============ 通用按钮 ============ */
.btn-primary {
  background: #165DFF;
  color: #fff;
  border: 1px solid #165DFF;
  border-radius: 12px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 6px 14px rgba(22, 93, 255, 0.22);
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 10px 20px rgba(22, 93, 255, 0.28); }
</style>
