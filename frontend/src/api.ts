/**
 * 共享 API 客户端 — 自动附加 JWT token 到所有请求。
 * 所有需要认证的 API 调用应使用此实例代替裸 axios。
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { API_BASE } from './config'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// 请求拦截器：自动附加 Authorization 头
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一处理 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      // 如果不是登录页面的 401，提示并跳转登录
      const isLoginRequest = error.config?.url?.includes('/api/auth/login') ||
        error.config?.url?.includes('/api/enterprise/login')
      if (!isLoginRequest) {
        const detail = error.response?.data?.detail || error.response?.data?.error || ''
        if (detail) {
          // 有具体错误消息时只显示消息，不跳转（可能是 token 过期后的正常报错）
          // 只有在无具体消息时才认为是未登录
          if (detail.includes('缺少') || detail.includes('过期') || detail.includes('登录')) {
            ElMessage.warning('登录已过期，请重新登录')
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
          }
        }
      }
    }
    return Promise.reject(error)
  },
)

export default api
