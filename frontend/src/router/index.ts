import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 1. 官网首页（根路径）
    {
      path: '/',
      name: 'landing',
      component: () => import('../views/LandingPage.vue'),
      meta: { title: '智能实训评价系统' }
    },

    // 2. 登录页
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { title: '登录' }
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
          meta: { title: '评价标准配置' }
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
          meta: { title: '我的成绩' }
        },
        {
          path: 'class-manage',
          name: 'class-manage',
          component: () => import('../views/ClassManage.vue'),
          meta: { title: '班级管理' }
        },
        {
          path: 'my-classes',
          name: 'my-classes',
          component: () => import('../views/MyClasses.vue'),
          meta: { title: '我的班级' }
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
          meta: { title: '班级成绩总览', needAuth: true }
        },
        {
          path: 'task-manage',
          name: 'task-manage',
          component: () => import('../views/TaskManage.vue'),
          meta: { title: '任务管理' }
        },
        {
          path: 'student-tasks',
          name: 'student-tasks',
          component: () => import('../views/StudentTasks.vue'),
          meta: { title: '待提交任务' }
        }
      ]
    }
  ]
})

// 全局路由守卫（可选：如果需要登录后才能进系统）
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 智能实训评价系统` : '智能实训评价系统'
  next()
})

export default router