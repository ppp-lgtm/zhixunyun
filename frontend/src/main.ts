// ✅ 1. 必须第一行引入全局样式！
import './styles/global.css'

// ✅ 2. 引入其他库
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import VueECharts from 'vue-echarts'
import { Icon } from '@iconify/vue'
import App from './App.vue'
import router from './router'

// ✅ 【完整修复】ECharts 按需引入所有用到的部分
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
// 引入图表类型
import { LineChart, RadarChart, BarChart } from 'echarts/charts'
// 引入组件
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  MarkLineComponent,
  LegendComponent
} from 'echarts/components'

// 注册所有
echarts.use([
  CanvasRenderer,
  LineChart,
  RadarChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  MarkLineComponent,
  LegendComponent
])

const app = createApp(App)

// ✅ 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// ✅ 注册Iconify
app.component('Icon', Icon)

// ✅ 注册ECharts
app.component('v-chart', VueECharts)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')