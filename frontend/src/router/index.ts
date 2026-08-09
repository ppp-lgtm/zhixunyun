import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 1. 根路径 → 初始页面为 Landing.vue（未登录直接展示品牌页；已登录则在 beforeEach 内跳工作台）
    {
      path: '/',
      name: 'root',
      component: () => import('../views/Landing.vue'),
      meta: { title: '智讯云 · 实训教学 AI 评价' }
    },

    // 2. 登录页
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { title: '登录' }
    },
    // 2.5 Landing Page（保留独立 /landing 路径，便于外链）
    {
      path: '/landing',
      name: 'landing',
      component: () => import('../views/Landing.vue'),
      meta: { title: '智讯云 · 实训教学 AI 评价' }
    },

    // 3. 系统内部（所有原有功能都在这里，路径前面加了 /app）
    {
      path: '/app',
      component: MainLayout,
      children: [
        {
          path: '/app',
          name: 'home',
          component: () => import('../views/Home.vue'),
          meta: { title: '首页' }
        },
        {
          path: 'upload',
          name: 'upload',
          component: () => import('../views/Upload.vue'),
          meta: { title: '上传评价' }
        },
        {
          path: 'result/:id',
          name: 'result',
          component: () => import('../views/Result.vue'),
          meta: { title: '评价结果' }
        },
        {
          path: 'criteria',
          name: 'criteria',
          component: () => import('../views/Criteria.vue'),
          meta: { title: '评价标准配置', role: 'teacher' }
        },
        {
          path: 'statistics',
          name: 'statistics',
          component: () => import('../views/Statistics.vue'),
          meta: { title: '数据统计' }
        },
        {
          path: 'my-scores',
          name: 'my-scores',
          component: () => import('../views/MyScores.vue'),
          meta: { title: '我的成绩', role: 'student' }
        },
        {
          path: 'interview-invitations',
          name: 'interview-invitations',
          component: () => import('../views/InterviewInvitations.vue'),
          meta: { title: '面试邀约', role: 'student' }
        },
        {
          path: 'class-manage',
          name: 'class-manage',
          component: () => import('../views/ClassManage.vue'),
          meta: { title: '班级管理', role: 'teacher' }
        },
        {
          path: 'my-classes',
          name: 'my-classes',
          component: () => import('../views/MyClasses.vue'),
          meta: { title: '我的班级', role: 'student' }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/Profile.vue'),
          meta: { title: '个人中心' }
        },
        {
          path: 'class-scores',
          name: 'class-scores',
          component: () => import('../views/ClassScores.vue'),
          meta: { title: '班级成绩总览', role: 'teacher' }
        },
        {
          path: 'task-manage',
          name: 'task-manage',
          component: () => import('../views/TaskManage.vue'),
          meta: { title: '任务管理', role: 'teacher' }
        },
        {
          path: 'student-tasks',
          name: 'student-tasks',
          component: () => import('../views/StudentTasks.vue'),
          meta: { title: '待提交任务', role: 'student' }
        },

        // ============= 企业端专属（C1） =============
        {
          path: 'enterprise/dashboard',
          name: 'enterprise-dashboard',
          component: () => import('../views/EnterpriseDashboard.vue'),
          meta: { title: '企业总览', role: 'enterprise' }
        },
        {
          path: 'enterprise/jobs',
          name: 'enterprise-jobs',
          component: () => import('../views/EnterpriseJobs.vue'),
          meta: { title: '岗位管理', role: 'enterprise' }
        },
        {
          path: 'enterprise/evaluations',
          name: 'enterprise-evaluations',
          component: () => import('../views/EnterpriseEvaluations.vue'),
          meta: { title: '企业评价', role: 'enterprise' }
        },
        {
          path: 'enterprise/compare',
          name: 'enterprise-compare',
          component: () => import('../views/EnterpriseCompare.vue'),
          meta: { title: '三方对比', role: 'enterprise' }
        },
        {
          path: 'enterprise/matching',
          name: 'enterprise-matching',
          component: () => import('../views/EnterpriseMatching.vue'),
          meta: { title: '岗位匹配', role: 'enterprise' }
        },
        {
          path: 'enterprise/student/:studentId',
          name: 'enterprise-student-profile',
          component: () => import('../views/EnterpriseStudentProfile.vue'),
          meta: { title: '学生画像', role: 'enterprise' }
        }
      ]
    }
  ]
})

// 全局路由守卫：按 meta.role 做角色级访问控制
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 智能实训评价系统` : '智能实训评价系统'

  // 读取当前登录用户（只做一次 JSON 解析，下面多次复用）
  const rawUser = localStorage.getItem('user')
  let user: any = null
  if (rawUser) {
    try { user = JSON.parse(rawUser) } catch { user = null }
  }

  // 根路径分流：已登录按角色跳对应工作台，未登录直接渲染 Landing
  const isRoot = to.path === '/' || to.fullPath === '/'
  if (isRoot) {
    if (user?.role === 'enterprise') return next('/app/enterprise/dashboard')
    if (user) return next('/app')
    // 未登录：根路径本身就是 Landing 组件，直接渲染（避免多余重定向）
    return next()
  }

  // /app（系统首页）：企业角色直接跳企业总览，不再进入教学首页
  if (to.path === '/app' && user?.role === 'enterprise') {
    return next('/app/enterprise/dashboard')
  }

  const requiredRole = to.meta?.role as string | undefined
  if (!requiredRole) {
    next()
    return
  }

  if (!user) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  try {
    if (user.role === requiredRole) {
      next()
    } else if (requiredRole === 'teacher' && user.role === 'enterprise') {
      // 企业账号允许查看班级/任务的只读页
      next()
    } else if (requiredRole === 'student' && user.role === 'enterprise') {
      // 企业账号无法进入学生专用页
      next({ path: '/app/enterprise/dashboard' })
    } else if (requiredRole === 'enterprise' && user.role !== 'enterprise') {
      // 学生/教师无法进入企业页
      next({ path: '/app' })
    } else {
      next({ path: '/app' })
    }
  } catch {
    next({ path: '/login' })
  }
})

export default router