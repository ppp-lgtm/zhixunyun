// 后端 API 基础地址。
// 支持通过 VITE_API_BASE 环境变量在开发/部署时覆盖；默认使用本机 127.0.0.1:8000。
// 开发用例：  VITE_API_BASE=http://127.0.0.1:8023 npm run dev
// 打包用例：  VITE_API_BASE=https://your-backend.example.com npm run build
const envBase = (import.meta as any).env?.VITE_API_BASE as string | undefined
export const API_BASE = (envBase || 'http://127.0.0.1:8000').replace(/\/+$/, '')
