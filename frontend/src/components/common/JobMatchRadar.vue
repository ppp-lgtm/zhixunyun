<template>
  <div class="job-match-radar w-full h-full">
    <div v-if="!hasData" class="h-full flex flex-col items-center justify-center text-center p-8">
      <div class="w-16 h-16 rounded-2xl bg-line/50 flex items-center justify-center mb-4">
        <Icon icon="mdi:radar" class="text-3xl text-ink-4" />
      </div>
      <p class="font-sub font-semibold text-ink-2 text-[15px] mb-1">暂无对标数据</p>
      <p class="text-[12.5px] text-ink-4 leading-snug">选择岗位并匹配学生后，岗位门槛与学生能力的雷达图将在此叠加展示。</p>
    </div>
    <template v-else>
      <div class="flex items-center justify-between mb-4 px-1">
        <div class="flex items-center gap-2">
          <div class="section-label !mb-0 !text-[10.5px]">RADAR · 双雷达叠加</div>
        </div>
        <div class="flex items-center gap-4 text-[12px] font-sub font-semibold">
          <span class="flex items-center gap-2">
            <span class="inline-block w-4 h-[2.5px] rounded-full bg-seal"></span>
            <span class="text-ink-2">学生能力</span>
          </span>
          <span class="flex items-center gap-2">
            <span class="inline-block w-4 h-[2.5px] border-t-[2.5px] border-dashed border-cobalt"></span>
            <span class="text-ink-2">岗位门槛</span>
          </span>
        </div>
      </div>
      <v-chart :option="option" autoresize style="width: 100%; height: 100%; min-height: 280px" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

interface DimRow {
  name: string
  threshold?: number
  weight?: number
  student_score?: number
  must?: boolean
  passed?: boolean
}

const props = defineProps<{
  dimensions?: DimRow[]
  title?: string
}>()

const hasData = computed(() => {
  return !!(props.dimensions && props.dimensions.length &&
    props.dimensions.some(d => typeof d.threshold === 'number' || typeof d.student_score === 'number'))
})

const option = computed(() => {
  const dims = props.dimensions || []
  const names = dims.map(d => d.name)
  // 取阈值/学生分，统一转成 0-100 范围的显示
  const thresholds = dims.map(d => typeof d.threshold === 'number' ? Math.max(0, Math.min(100, d.threshold)) : 60)
  const studentScores = dims.map(d => typeof d.student_score === 'number' ? Math.max(0, Math.min(100, d.student_score)) : 0)

  const maxVal = 100
  const indicators = names.map(n => ({ name: n, max: maxVal, min: 0 }))

  return {
    backgroundColor: 'transparent',
    color: ['#FF5A1F', '#1E40AF'],
    tooltip: {
      trigger: 'item',
      backgroundColor: '#111827',
      borderColor: 'transparent',
      textStyle: { color: '#F9FAFB', fontSize: 12, fontFamily: 'Inter, ui-sans-serif, system-ui' },
      formatter: (params: any) => {
        const i = params.dataIndex ?? 0
        if (params.seriesName === '学生能力') {
          const items = names.map((n, idx) => {
            const s = studentScores[idx]
            const t = thresholds[idx]
            const delta = s - t
            const tag = delta >= 0
              ? `<span style="color:#11A367">▲${delta}</span>`
              : `<span style="color:#FF5A1F">▼${Math.abs(delta)}</span>`
            return `<div style="display:flex;justify-content:space-between;gap:12px;padding:2px 0"><span>${n}</span><span style="font-family:'JetBrains Mono',monospace">${s} / ${t} ${tag}</span></div>`
          }).join('')
          return `<div style="font-weight:700;margin-bottom:6px;color:#FF5A1F">学生能力 vs 岗位门槛</div>${items}`
        }
        return `<div style="font-weight:700;color:#1E40AF">岗位门槛</div>` +
          names.map((n, idx) => `<div>${n}: ${thresholds[idx]}</div>`).join('')
      }
    },
    radar: {
      indicator: indicators,
      center: ['50%', '52%'],
      radius: '68%',
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#475569',
        fontSize: 12,
        fontWeight: 600,
        fontFamily: 'Inter, ui-sans-serif, system-ui'
      },
      splitLine: {
        lineStyle: { color: ['#E5E7EB', '#D1D5DB', '#B9C0CA', '#94A3B8'], type: 'dashed', width: 1 }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: [
            'rgba(255,255,255,0)',
            'rgba(30,64,175,0.02)',
            'rgba(255,255,255,0)',
            'rgba(255,90,31,0.035)'
          ]
        }
      },
      axisLine: { lineStyle: { color: '#CBD5E1', width: 1 } }
    },
    series: [
      {
        name: '岗位门槛',
        type: 'radar',
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#1E40AF', width: 2.5, type: 'dashed' },
        itemStyle: { color: '#1E40AF', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: {
            type: 'radial', x: 0.5, y: 0.5, r: 0.8,
            colorStops: [
              { offset: 0, color: 'rgba(30,64,175,0.06)' },
              { offset: 1, color: 'rgba(30,64,175,0.18)' }
            ]
          }
        },
        data: [{ value: thresholds, name: '岗位门槛' }]
      },
      {
        name: '学生能力',
        type: 'radar',
        symbol: 'circle',
        symbolSize: 10,
        lineStyle: { color: '#FF5A1F', width: 3 },
        itemStyle: {
          color: '#FF5A1F',
          borderColor: '#fff',
          borderWidth: 2.5,
          shadowColor: 'rgba(255,90,31,0.35)',
          shadowBlur: 8
        },
        areaStyle: {
          color: {
            type: 'radial', x: 0.5, y: 0.5, r: 0.8,
            colorStops: [
              { offset: 0, color: 'rgba(255,90,31,0.10)' },
              { offset: 1, color: 'rgba(255,90,31,0.30)' }
            ]
          }
        },
        z: 5,
        data: [{ value: studentScores, name: '学生能力' }]
      }
    ]
  }
})
</script>

<style scoped>
.job-match-radar { font-family: 'Inter', ui-sans-serif, system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif; }
</style>
