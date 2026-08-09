<template>
  <!-- 学业台账 · ACADEMIC TRANSCRIPT LEDGER -->
  <div class="ms-page">
    <!-- 背景装饰：柔和光晕 + 成绩册印章水印 -->
    <div class="ms-glow ms-glow-cobalt" aria-hidden="true"></div>
    <div class="ms-glow ms-glow-jade" aria-hidden="true"></div>
    <div class="ms-ledger-mark" aria-hidden="true">TRANSCRIPT · LEDGER</div>

    <div class="ms-inner page-enter-stagger">

      <!-- ============== HERO 标题区 ============== -->
      <header class="ms-hero reveal reveal-1">
        <div class="ms-hero-left">
          <span class="ms-hero-chip">
            <span class="ms-hero-chip-num">INDEX</span>
            <span class="ms-hero-chip-text"> ACADEMIC TRANSCRIPT · 学业台账</span>
          </span>
          <h1 class="ms-hero-title">
            我的成绩册
            <span class="ms-hero-underline" aria-hidden="true"></span>
          </h1>
          <p class="ms-hero-sub">
            你的每一次实训成果物都会被 AI、教师{{ enterpriseTotal > 0 ? '、企业三方' : '两方' }}
            多维度加权评分，自动汇总为学业台账。通过成绩趋势与能力成长报告，
            一眼看清你的进步轨迹与薄弱项。
          </p>

          <!-- 3 枚迷你徽章（顶部下方） -->
          <div class="ms-hero-minis" v-if="recordsAll.length">
            <div class="ms-mini-chip tone-cobalt">
              <Icon icon="mdi:folder-text-outline" class="ms-mini-ic" />
              <span class="ms-mini-num">{{ totalRecords }}</span>
              <span class="ms-mini-lbl">评价档案</span>
            </div>
            <div class="ms-mini-chip tone-jade">
              <Icon icon="mdi:chart-arc" class="ms-mini-ic" />
              <span class="ms-mini-num">{{ data.avg_score || '—' }}</span>
              <span class="ms-mini-lbl">综合均分</span>
            </div>
            <div class="ms-mini-chip tone-seal" v-if="recordMax >= 0">
              <Icon icon="mdi:trophy-outline" class="ms-mini-ic" />
              <span class="ms-mini-num">{{ recordMax }}</span>
              <span class="ms-mini-lbl">历史最佳</span>
            </div>
          </div>
        </div>

        <!-- Hero 右侧：装饰性成绩单印章 -->
        <aside class="ms-hero-right" aria-hidden="true" v-if="recordsAll.length">
          <div class="ms-stamp">
            <div class="ms-stamp-corner tl"></div>
            <div class="ms-stamp-corner tr"></div>
            <div class="ms-stamp-corner bl"></div>
            <div class="ms-stamp-corner br"></div>
            <div class="ms-stamp-top">ACADEMIC · REPORT</div>
            <div class="ms-stamp-score-wrap">
              <span class="ms-stamp-score" :class="scoreToneClass(data.avg_score)">{{ data.avg_score || '—' }}</span>
              <span class="ms-stamp-sub">综合均分</span>
            </div>
            <div class="ms-stamp-level" :class="`lvl-${scoreLevelKey(data.avg_score)}`">{{ scoreLevelText(data.avg_score) }}</div>
            <div class="ms-stamp-bottom">
              <span>ZHI XUN YUN</span>
              <span class="ms-stamp-dot">·</span>
              <span>{{ ledgerDateText }}</span>
            </div>
          </div>
        </aside>
      </header>

      <!-- ============== 加载态 ============== -->
      <div v-if="!loaded" class="ms-loading reveal reveal-2">
        <div class="ms-loading-ring"></div>
        <div class="ms-loading-text">
          <div class="ms-loading-title">正在调取学业档案…</div>
          <div class="ms-loading-sub">LOADING · TRANSCRIPT · LEDGER</div>
        </div>
      </div>

      <template v-else-if="recordsAll.length > 0">

        <!-- ============== 4 枚数据邮票 ============== -->
        <section class="ms-stamps reveal reveal-2">
          <div class="ms-stamp-card ms-stamp-card-count"
               @click="scrollToRecords"
               :style="{'--stamp-r': '-1.8deg'}">
            <div class="msc-holes" aria-hidden="true"></div>
            <div class="msc-label">SUBMISSIONS</div>
            <div class="msc-ic-wrap ic-cobalt">
              <Icon icon="mdi:file-document-multiple" class="msc-ic" />
            </div>
            <div class="msc-num">{{ totalRecords }}</div>
            <div class="msc-cn">提交次数</div>
            <div class="msc-foot">次实训评价 · 点击查看记录 ↓</div>
          </div>

          <div class="ms-stamp-card ms-stamp-card-avg"
               :style="{'--stamp-r': '1.2deg'}">
            <div class="msc-holes" aria-hidden="true"></div>
            <div class="msc-label">AVG SCORE</div>
            <div class="msc-ic-wrap ic-jade">
              <Icon icon="mdi:chart-line" class="msc-ic" />
            </div>
            <div class="msc-num" :class="scoreToneClass(data.avg_score)">{{ data.avg_score }}</div>
            <div class="msc-cn">综合均分</div>
            <div class="msc-foot">三栏/两栏加权 · 全时段平均</div>
          </div>

          <div class="ms-stamp-card ms-stamp-card-max"
               :style="{'--stamp-r': '-0.8deg'}">
            <div class="msc-holes" aria-hidden="true"></div>
            <div class="msc-label">BEST SCORE</div>
            <div class="msc-ic-wrap ic-amber">
              <Icon icon="mdi:trophy-outline" class="msc-ic" />
            </div>
            <div class="msc-num tone-amber">{{ recordMax }}</div>
            <div class="msc-cn">历史最佳</div>
            <div class="msc-foot">TOP 1 · {{ recordMaxTitle || '—' }}</div>
          </div>

          <div class="ms-stamp-card ms-stamp-card-weak"
               :style="{'--stamp-r': '1.6deg'}">
            <div class="msc-holes" aria-hidden="true"></div>
            <div class="msc-label">FOCUS · WEAK</div>
            <div class="msc-ic-wrap ic-seal" v-if="data.weakness?.length">
              <Icon icon="mdi:target-variant" class="msc-ic" />
            </div>
            <div class="msc-ic-wrap ic-ink" v-else>
              <Icon icon="mdi:shield-check-outline" class="msc-ic" />
            </div>
            <div class="msc-weak-list" v-if="data.weakness?.length">
              <span v-for="w in data.weakness.slice(0, 3)" :key="w.name"
                    class="msc-weak-chip">
                {{ w.name }}
              </span>
              <span v-if="data.weakness.length > 3" class="msc-weak-more">
                +{{ data.weakness.length - 3 }}
              </span>
            </div>
            <div class="msc-weak-none" v-else>各项均衡 · 无明显薄弱</div>
            <div class="msc-cn msc-cn-weak">{{ data.weakness?.length ? '需加强维度' : '均衡发展' }}</div>
            <div class="msc-foot" v-if="data.weakness?.length">建议针对薄弱项专项训练</div>
            <div class="msc-foot" v-else>继续保持当前学习节奏</div>
          </div>
        </section>

        <!-- ============== 成绩趋势 & 能力成长报告（合并卡 + 切换） ============== -->
        <section class="ms-card mag-card reveal reveal-3">
          <div class="ms-card-top msct-cobalt">
            <div class="msct-eyebrow">
              <span class="msct-num">02</span>
              <span class="msct-text">ANALYSIS · 成绩分析报告</span>
            </div>
            <div class="msct-toggle">
              <button @click="analysisView = 'trend'"
                      class="msct-btn"
                      :class="{active: analysisView === 'trend', 'btn-cobalt': analysisView === 'trend'}">
                <Icon icon="mdi:chart-timeline-variant" inline width="14" class="mr-1" />
                成绩趋势
              </button>
              <button @click="analysisView = 'growth'"
                      class="msct-btn"
                      :class="{active: analysisView === 'growth', 'btn-jade': analysisView === 'growth'}">
                <Icon icon="mdi:trending-up" inline width="14" class="mr-1" />
                能力成长
              </button>
            </div>
          </div>

          <div class="ms-card-body">
            <transition name="fade-slide" mode="out-in">
              <!-- 视图A: 成绩趋势 -->
              <div v-if="analysisView === 'trend'" key="trend-view" class="ms-chart-wrap">
                <div class="msc-title-row">
                  <h3 class="msc-title">历次提交成绩趋势</h3>
                  <div class="msc-legend">
                    <span class="msc-legend-item"><span class="lg-dot lg-cobalt"></span>历次得分</span>
                    <span class="msc-legend-item"><span class="lg-dot lg-jade" style="border-style: dashed"></span>平均分基线</span>
                  </div>
                </div>
                <p class="msc-sub">
                  共 <b class="k-cobalt">{{ totalRecords }}</b> 次评价记录 · 最高分
                  <b class="k-amber">{{ recordMax }}</b> · 均分基线
                  <b class="k-jade">{{ data.avg_score }}</b>
                </p>
                <v-chart :option="lineOption" class="ms-chart" autoresize />
              </div>

              <!-- 视图B: 能力成长报告 -->
              <div v-else-if="growth" key="growth-view" class="ms-growth-wrap">
                <div class="msc-title-row">
                  <h3 class="msc-title">能力成长对比报告</h3>
                  <div class="msc-legend">
                    <span class="msc-legend-item"><span class="lg-dot lg-cobalt"></span>首次提交</span>
                    <span class="msc-legend-item"><span class="lg-dot lg-jade"></span>最新提交</span>
                  </div>
                </div>

                <!-- 3 枚成长统计 -->
                <div class="growth-triplets">
                  <div class="growth-tri tri-blue">
                    <div class="gt-label">首次均分</div>
                    <div class="gt-num">{{ growth.first.total }}<span class="gt-unit">分</span></div>
                    <div class="gt-time">{{ growth.first.time }}</div>
                  </div>
                  <div class="growth-tri tri-green">
                    <div class="gt-label">最新均分</div>
                    <div class="gt-num">{{ growth.latest.total }}<span class="gt-unit">分</span></div>
                    <div class="gt-time">{{ growth.latest.time }}</div>
                  </div>
                  <div class="growth-tri tri-seal">
                    <div class="gt-label">成长幅度</div>
                    <div class="gt-num" :class="growth.total_change >= 0 ? 'num-up' : 'num-down'">
                      {{ growth.total_change >= 0 ? '+' : '' }}{{ growth.total_change }}<span class="gt-unit">分</span>
                    </div>
                    <div class="gt-time">共 {{ growth.total_count }} 次提交</div>
                  </div>
                </div>

                <div class="growth-split">
                  <div class="growth-left">
                    <h4 class="gs-title">
                      <Icon icon="mdi:radar" class="gs-title-ic ic-cobalt" />
                      各维度雷达对比
                    </h4>
                    <v-chart :option="growthRadarOption" class="ms-chart ms-chart-radar" autoresize />
                  </div>
                  <div class="growth-right">
                    <h4 class="gs-title">
                      <Icon icon="mdi:swap-vertical" class="gs-title-ic ic-jade" />
                      维度变化详情
                    </h4>
                    <div class="growth-list">
                      <div v-for="item in growth.changes" :key="item.name"
                           class="growth-row"
                           :class="item.change >= 0 ? 'row-up' : 'row-down'">
                        <div class="gr-left">
                          <div class="gr-name">{{ item.name }}</div>
                          <div class="gr-arrow">
                            <span class="gr-from">{{ item.first_score }}</span>
                            <Icon icon="mdi:arrow-right-thin" class="gr-arrow-ic" />
                            <span class="gr-to">{{ item.latest_score }}</span>
                          </div>
                        </div>
                        <div class="gr-right" :class="item.change >= 0 ? 'ch-up' : 'ch-down'">
                          <Icon :icon="item.change >= 0 ? 'mdi:trending-up' : 'mdi:trending-down'" inline width="16" />
                          <span>{{ item.change >= 0 ? '+' : '' }}{{ item.change }}</span>
                          <em>分</em>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="growth-advice">
                  <Icon icon="mdi:lightbulb-on-outline" class="ga-ic" />
                  <p class="ga-text">{{ growth.advice }}</p>
                </div>
              </div>

              <div v-else key="growth-empty" class="ms-empty-mini">
                <div class="ms-empty-mini-art">
                  <div class="ema-ring"></div>
                  <Icon icon="mdi:chart-box-outline" class="ema-ic" />
                </div>
                <div class="ms-empty-mini-title">成长报告生成中…</div>
                <div class="ms-empty-mini-sub">需要累计 <b>2 次以上</b> 评价记录才能对比成长差异，先去提交一份成果物吧～</div>
                <button class="btn-mag btn-mag-seal" @click="$router.push('/app/upload')">
                  <Icon icon="mdi:inbox-arrow-up-outline" inline width="14" />
                  去上传成果
                </button>
              </div>
            </transition>
          </div>
        </section>

        <!-- ============== 评价记录（简约表格） ============== -->
        <section id="records-anchor" class="records-clean reveal reveal-4">
          <div class="rc-head">
            <div class="rc-head-left">
              <h3 class="rc-title">评价记录</h3>
              <span class="rc-sub">共 {{ totalRecords }} 条记录 · 第 {{ currentPage }} / {{ totalPages }} 页</span>
            </div>
            <div class="rc-head-right">
              <span class="rc-legend"><span class="rc-dot d-ok"></span>≥ 80 优秀</span>
              <span class="rc-legend"><span class="rc-dot d-mid"></span>≥ 60 良好</span>
              <span class="rc-legend"><span class="rc-dot d-low"></span>&lt; 60 待加强</span>
            </div>
          </div>

          <div class="rc-table-wrap">
            <table class="rc-table">
              <thead>
                <tr>
                  <th class="col-seq">#</th>
                  <th class="col-task">任务</th>
                  <th class="col-file">成果物</th>
                  <th class="col-time">提交时间</th>
                  <th class="col-score">AI 评分</th>
                  <th class="col-score">教师评分</th>
                  <th class="col-comment">教师评语</th>
                  <th class="col-act">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, ri) in pageRecords" :key="r.id">
                  <td class="col-seq">{{ ri + 1 + (currentPage - 1) * pageSize }}</td>
                  <td class="col-task" :title="r.task_title || '自由上传评价'">
                    <span class="rc-task-text">{{ r.task_title || '自由上传评价' }}</span>
                  </td>
                  <td class="col-file" :title="r.filename">
                    <Icon :icon="fileExtIcon(r.filename)" class="rc-file-ic" />
                    <span class="rc-file-name">{{ r.filename }}</span>
                  </td>
                  <td class="col-time">{{ r.time || '—' }}</td>
                  <td class="col-score">
                    <span class="rc-score" :class="scoreChipClass(r.total_score)">
                      {{ r.total_score }}
                    </span>
                  </td>
                  <td class="col-score">
                    <template v-if="r.teacher_score != null && r.teacher_score !== ''">
                      <span class="rc-score tsc-amber">{{ r.teacher_score }}</span>
                    </template>
                    <span v-else class="rc-score rc-score-empty">待评</span>
                  </td>
                  <td class="col-comment" :title="r.teacher_comment || ''">
                    <template v-if="r.teacher_comment">{{ r.teacher_comment }}</template>
                    <span v-else class="rc-dim-empty">—</span>
                  </td>
                  <td class="col-act">
                    <button class="rc-act-btn" @click="viewDetail(r)">查看详情</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页：极简 -->
          <div v-if="totalRecords > pageSize" class="rc-pager">
            <button class="rc-page-btn"
                    :disabled="currentPage <= 1"
                    @click="currentPage > 1 && handlePageChange(currentPage - 1)">
              <Icon icon="mdi:chevron-left" />
              上一页
            </button>
            <div class="rc-page-nums">
              <span v-for="p in displayPages" :key="p.num"
                    class="rc-page-num"
                    :class="{active: p.num === currentPage, dot: p.isDot}"
                    @click="!p.isDot && handlePageChange(p.num)">
                {{ p.isDot ? '…' : p.num }}
              </span>
            </div>
            <button class="rc-page-btn"
                    :disabled="currentPage >= totalPages"
                    @click="currentPage < totalPages && handlePageChange(currentPage + 1)">
              下一页
              <Icon icon="mdi:chevron-right" />
            </button>
          </div>
        </section>
      </template>

      <!-- ============== 空态：无任何记录 ============== -->
      <div v-else class="ms-empty reveal reveal-2">
        <div class="ms-empty-art">
          <div class="mea-corner mea-tl"></div>
          <div class="mea-corner mea-tr"></div>
          <div class="mea-corner mea-bl"></div>
          <div class="mea-corner mea-br"></div>
          <div class="mea-ring-1"></div>
          <div class="mea-ring-2"></div>
          <Icon icon="mdi:file-document-off-outline" class="mea-ic" />
        </div>
        <h2 class="ms-empty-title">学业台账尚为空</h2>
        <p class="ms-empty-sub">
          还没有任何实训评价记录。去完成一份成果物上传，由 AI / 教师{{ enterpriseTotal > 0 ? '/ 企业 ' : ' ' }}
          生成你的第一份评价档案，开启你的成长追踪吧。
        </p>
        <div class="ms-empty-actions">
          <button class="btn-mag btn-mag-seal btn-l" @click="$router.push('/app/upload')">
            <Icon icon="mdi:inbox-arrow-up-outline" />
            去上传 · 生成第一份评价
          </button>
          <button class="btn-mag btn-mag-ghost btn-l" @click="$router.push('/app/student-tasks')">
            <Icon icon="mdi:format-list-text" />
            先看看有哪些任务
          </button>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const router = useRouter()
const loaded = ref(false)
const data = ref<any>({ records: [], weakness: [], total_count: 0, avg_score: 0 })
const growth = ref<any>(null)
const currentPage = ref(1)
const pageSize = 5
const totalRecords = ref(0)
const analysisView = ref<'trend' | 'growth'>('trend')

/* ============== 【原业务逻辑 100% 保留】 ============== */
const loadRecords = async (page = 1) => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  if (!user.id) return

  try {
    const res = await api.get(`/api/statistics/student/${user.id}?page=${page}&page_size=${pageSize}`)
    if (res.data.success) {
      data.value = res.data.data
      totalRecords.value = res.data.data.total_count

      try {
        const tRes = await api.get(`/api/statistics/student/${user.id}/teacher-scores`)
        if (tRes.data.success) {
          const teacherMap: any = {}
          tRes.data.data.forEach((t: any) => {
            teacherMap[t.submission_id] = { total_score: t.total_score, comment: t.comment }
          })
          data.value.records.forEach((r: any) => {
            const t = teacherMap[r.id]
            r.teacher_score = t ? t.total_score : null
            r.teacher_comment = t ? t.comment : null
          })
        }
      } catch {}
    }
  } catch (err) {
    console.error(err)
  }
}

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  if (!user.id) { router.push('/login'); return }

  loaded.value = false
  await loadRecords(currentPage.value)

  try {
    const growthRes = await api.get(`/api/statistics/student/${user.id}/growth`)
    if (growthRes.data.success) growth.value = growthRes.data.data
  } catch {}

  loaded.value = true
})

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadRecords(page)
}

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#111827' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: data.value.records.map((r: any) => r.time).reverse(),
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisLabel: { color: '#6b7280' }
  },
  yAxis: {
    type: 'value', name: '分数', min: 0, max: 100,
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisLabel: { color: '#6b7280' },
    splitLine: { lineStyle: { color: '#f3f4f6' } }
  },
  series: [{
    type: 'line',
    data: data.value.records.map((r: any) => r.total_score).reverse(),
    smooth: true, symbol: 'circle', symbolSize: 10,
    lineStyle: { width: 4, color: '#3D5AFE' },
    itemStyle: { color: '#3D5AFE', borderColor: '#fff', borderWidth: 3 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(61, 90, 254, 0.32)' },
          { offset: 1, color: 'rgba(61, 90, 254, 0.04)' }
        ]
      }
    },
    markLine: {
      data: [{ type: 'average', name: '平均值' }],
      lineStyle: { color: '#1DB955', width: 2, type: 'dashed' },
      label: { color: '#1DB955', fontWeight: 600 }
    }
  }]
}))

const growthRadarOption = computed(() => {
  if (!growth.value) return {}
  const dims = growth.value.changes.map((c: any) => c.name)
  return {
    tooltip: {},
    legend: { data: ['首次提交', '最新提交'], top: 0 },
    radar: {
      indicator: dims.map((d: string) => ({ name: d, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#374151', fontSize: 12, fontWeight: 600 }
    },
    series: [
      {
        type: 'radar',
        name: '首次提交',
        data: [{ value: growth.value.changes.map((c: any) => c.first_score), name: '首次提交' }],
        lineStyle: { color: '#6FA8FF', width: 2 },
        areaStyle: { color: 'rgba(61, 90, 254, 0.15)' },
        itemStyle: { color: '#3D5AFE' }
      },
      {
        type: 'radar',
        name: '最新提交',
        data: [{ value: growth.value.changes.map((c: any) => c.latest_score), name: '最新提交' }],
        lineStyle: { color: '#46D17F', width: 2 },
        areaStyle: { color: 'rgba(29, 185, 85, 0.2)' },
        itemStyle: { color: '#1DB955' }
      }
    ]
  }
})

const viewDetail = (row: any) => {
  // 1) 先保存 eval_result 快照（Result.vue 中的 onMounted/activated 会读取）
  localStorage.setItem('eval_result', JSON.stringify({
    submission_id: row.id,
    filename: row.filename,
    evaluation: { total: row.total_score, scores: row.scores, comment: row.comment },
    completeness: { steps: row.step_completeness || [], issues: row.logic_issues || [], summary: row.comment || '' }
  }))
  // 2) 通过命名路由跳 /app/result/:id，把 submission_id 作为路由参数带上
  //    —— 即使 localStorage 因路由切换时序读不到，也能靠 route.params.id 兜底拉详情
  router.push({ name: 'result', params: { id: row.id } })
}

/* ============== 【增量：展示辅助函数 / 计算属性（纯UI，不影响业务）】 ============== */

/* 1. 快捷取 records 全量（API返回的 records） */
const recordsAll = computed<any[]>(() => data.value.records || [])
/* 2. 当前页展示的 records（分页用的就是 recordsAll，因为 API 已经分页） */
const pageRecords = computed<any[]>(() => recordsAll.value)
/* 3. 历史最高分 + 对应任务标题 */
const recordMax = computed<number>(() => {
  if (!recordsAll.value.length) return -1
  return Math.max(...recordsAll.value.map((r: any) => Number(r.total_score) || 0))
})
const recordMaxTitle = computed<string>(() => {
  if (recordMax.value < 0) return ''
  const top = recordsAll.value.find((r: any) => Number(r.total_score) === recordMax.value)
  return top?.task_title || top?.filename || '—'
})
/* 4. 企业级任务数量（用于 Hero 文案显示"三方"/"两方"） */
const enterpriseTotal = computed<number>(() => {
  return recordsAll.value.filter((r: any) => !!r.is_enterprise_project).length
})
/* 5. 总页数 */
const totalPages = computed<number>(() => Math.max(1, Math.ceil(totalRecords.value / pageSize)))
/* 6. 展示的页码（含省略号） */
const displayPages = computed<{ num: number; isDot: boolean }[]>(() => {
  const cur = currentPage.value
  const tot = totalPages.value
  if (tot <= 7) return Array.from({ length: tot }, (_, i) => ({ num: i + 1, isDot: false }))
  const res: any[] = [{ num: 1, isDot: false }]
  if (cur > 3) res.push({ num: 0, isDot: true })
  const s = Math.max(2, cur - 1)
  const e = Math.min(tot - 1, cur + 1)
  for (let i = s; i <= e; i++) res.push({ num: i, isDot: false })
  if (cur < tot - 2) res.push({ num: 0, isDot: true })
  res.push({ num: tot, isDot: false })
  return res
})
/* 7. 今日文本（用于印章/页脚） */
const ledgerDateText = computed<string>(() => {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`
})
/* 8. 分数 → 色调类（优秀/良好/待加强） */
const scoreLevelKey = (score: any) => {
  const s = Number(score)
  if (!Number.isFinite(s)) return 'none'
  if (s >= 80) return 'a'
  if (s >= 60) return 'b'
  return 'c'
}
const scoreLevelText = (score: any) => {
  const k = scoreLevelKey(score)
  return { a: '优秀 · A', b: '良好 · B', c: '待加强 · C', none: '未评' }[k] || ''
}
const scoreToneClass = (score: any) => {
  const k = scoreLevelKey(score)
  return { a: 'tone-jade', b: 'tone-amber', c: 'tone-seal', none: 'tone-ink' }[k] || 'tone-ink'
}
const scoreChipClass = (score: any) => {
  const k = scoreLevelKey(score)
  return { a: 'tsc-jade', b: 'tsc-amber', c: 'tsc-seal', none: 'tsc-empty' }[k] || 'tsc-empty'
}
const dimChipTone = (score: any) => {
  const k = scoreLevelKey(score)
  return { a: 'dim-jade', b: 'dim-amber', c: 'dim-seal', none: 'dim-ink' }[k] || 'dim-ink'
}
/* 9. 文件扩展名 → 图标/色调（和 Upload 页一致） */
const fileExt = (name: string) => {
  const i = (name || '').lastIndexOf('.')
  return i >= 0 ? name.slice(i + 1).toUpperCase() : 'FILE'
}
const fileExtTone = (name: string) => {
  const ext = fileExt(name)
  if (['PDF'].includes(ext)) return 'seal'
  if (['DOCX', 'DOC', 'TXT', 'MD'].includes(ext)) return 'cobalt'
  if (['PNG', 'JPG', 'JPEG', 'GIF', 'WEBP', 'BMP'].includes(ext)) return 'violet'
  if (['ZIP', 'RAR', '7Z', 'TAR', 'GZ'].includes(ext)) return 'amber'
  if (['PY', 'JS', 'TS', 'JAVA', 'CPP', 'C', 'H', 'CS', 'GO', 'RS', 'PHP', 'HTML', 'CSS', 'VUE', 'JSX', 'TSX'].includes(ext)) return 'jade'
  return 'ink'
}
const fileExtIcon = (name: string) => {
  const ext = fileExt(name)
  if (['PDF'].includes(ext)) return 'mdi:file-pdf-box'
  if (['DOCX', 'DOC', 'TXT', 'MD'].includes(ext)) return 'mdi:file-word-outline'
  if (['PNG', 'JPG', 'JPEG', 'GIF', 'WEBP', 'BMP'].includes(ext)) return 'mdi:file-image-outline'
  if (['ZIP', 'RAR', '7Z', 'TAR', 'GZ'].includes(ext)) return 'mdi:folder-zip-outline'
  if (['PY', 'JS', 'TS', 'JAVA', 'CPP', 'C', 'H', 'CS', 'GO', 'RS', 'PHP', 'HTML', 'CSS', 'VUE', 'JSX', 'TSX'].includes(ext)) return 'mdi:file-code-outline'
  return 'mdi:file-document-outline'
}
/* 10. 滚动到记录区 */
const scrollToRecords = () => {
  const el = document.getElementById('records-anchor')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
/* ============================================================
   My Scores Page · 学业台账 ACADEMIC TRANSCRIPT LEDGER
   美学：Editorial Magazine × Transcript × Academic Ledger
   ============================================================ */

/* ── 1. 页面整体与背景 ── */
.ms-page {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  padding: 56px 24px 80px;
  background:
    linear-gradient(180deg, rgba(255, 246, 238, 0.85) 0%, var(--paper) 32%, var(--paper) 100%);
}

.ms-glow {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  filter: blur(110px);
  opacity: 0.5;
  border-radius: 50%;
}
.ms-glow-cobalt {
  top: -200px; right: -40px;
  width: 540px; height: 540px;
  background: radial-gradient(circle, var(--cobalt) 0%, transparent 65%);
}
.ms-glow-jade {
  top: 30%; left: -140px;
  width: 460px; height: 460px;
  background: radial-gradient(circle, var(--jade) 0%, transparent 65%);
  opacity: 0.26;
}
.ms-ledger-mark {
  position: fixed;
  left: -6px; top: 42%;
  z-index: 0;
  pointer-events: none;
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 108px;
  letter-spacing: 6px;
  color: transparent;
  -webkit-text-stroke: 2px rgba(255, 90, 31, 0.06);
  transform: rotate(-90deg);
  transform-origin: left center;
  white-space: nowrap;
}

.ms-inner {
  position: relative;
  z-index: 2;
  max-width: 1360px;
  margin: 0 auto;
}

/* ── 2. 入场交错揭示 ── */
.page-enter-stagger .reveal {
  opacity: 0;
  transform: translateY(18px);
  animation: ms-reveal 720ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.reveal-1 { animation-delay: 40ms; }
.reveal-2 { animation-delay: 140ms; }
.reveal-3 { animation-delay: 240ms; }
.reveal-4 { animation-delay: 320ms; }
.reveal-5 { animation-delay: 420ms; }
@keyframes ms-reveal {
  to { opacity: 1; transform: translateY(0); }
}

/* ── 3. HERO 标题区 ── */
.ms-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(300px, 0.8fr);
  gap: 36px;
  align-items: stretch;
  margin-bottom: 42px;
}
.ms-hero-left { position: relative; }

.ms-hero-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 8px 10px;
  border: 1px solid rgba(255, 90, 31, 0.32);
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.1), rgba(139, 92, 246, 0.05));
  border-radius: 999px;
  margin-bottom: 22px;
}
.ms-hero-chip-num {
  font-family: var(--ff-mono);
  font-weight: 700;
  font-size: 10.5px;
  letter-spacing: 2px;
  color: #fff;
  background: linear-gradient(135deg, var(--seal), var(--seal-dark));
  padding: 4px 10px;
  border-radius: 999px;
  box-shadow: 0 6px 14px -8px rgba(255, 90, 31, 0.8);
}
.ms-hero-chip-text {
  font-family: var(--ff-sub);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--seal-dark);
}

.ms-hero-title {
  font-family: var(--ff-display);
  font-size: clamp(42px, 5.6vw, 76px);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin-bottom: 18px;
  position: relative;
  display: inline-block;
}
.ms-hero-underline {
  position: absolute;
  left: -4px; right: -12px; bottom: -14px;
  height: 14px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(29, 185, 85, 0.2) 12%,
    rgba(255, 90, 31, 0.45) 50%,
    rgba(61, 90, 254, 0.3) 88%,
    transparent 100%);
  border-radius: 999px;
  z-index: -1;
  filter: blur(1px);
}

.ms-hero-sub {
  font-family: var(--ff-body);
  font-size: 15.5px;
  line-height: 1.85;
  color: var(--ink-3);
  max-width: 680px;
  margin: 22px 0 26px;
  font-weight: 400;
  letter-spacing: 0.005em;
}

/* Hero 迷你徽章 3 枚 */
.ms-hero-minis {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.ms-mini-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px 9px 10px;
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  background: #fff;
  box-shadow: 0 10px 24px -18px rgba(15, 17, 21, 0.3);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ms-mini-chip:hover { transform: translateY(-2px); }
.ms-mini-chip.tone-cobalt { border-color: rgba(61, 90, 254, 0.25); background: linear-gradient(135deg, rgba(61, 90, 254, 0.07), #fff); }
.ms-mini-chip.tone-jade   { border-color: rgba(29, 185, 85, 0.25); background: linear-gradient(135deg, rgba(29, 185, 85, 0.08), #fff); }
.ms-mini-chip.tone-seal   { border-color: rgba(255, 90, 31, 0.28); background: linear-gradient(135deg, rgba(255, 90, 31, 0.09), #fff); }
.ms-mini-ic {
  font-size: 17px;
  flex-shrink: 0;
}
.ms-mini-chip.tone-cobalt .ms-mini-ic { color: var(--cobalt-dark); }
.ms-mini-chip.tone-jade   .ms-mini-ic { color: var(--jade-dark); }
.ms-mini-chip.tone-seal   .ms-mini-ic { color: var(--seal-dark); }
.ms-mini-num {
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 20px;
  line-height: 1;
  color: var(--ink);
}
.ms-mini-lbl {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--ink-3);
}

/* Hero 右侧装饰印章（成绩单） */
.ms-hero-right {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.ms-stamp {
  position: relative;
  width: 100%;
  max-width: 280px;
  aspect-ratio: 3/4;
  padding: 22px 18px;
  border-radius: 22px;
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.35) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #FFFCF0 0%, #FFE9CC 55%, #FFD0A1 100%);
  border: 2.5px solid var(--seal);
  box-shadow:
    0 18px 40px -20px rgba(255, 90, 31, 0.35),
    inset 0 0 0 5px rgba(255, 255, 255, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  text-align: center;
  transform: rotate(4deg);
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ms-stamp:hover {
  transform: rotate(0deg) translateY(-4px) scale(1.02);
  box-shadow:
    0 26px 52px -22px rgba(255, 90, 31, 0.45),
    inset 0 0 0 5px rgba(255, 255, 255, 0.5);
}
.ms-stamp-corner {
  position: absolute;
  width: 18px; height: 18px;
  border: 2px solid var(--seal);
  opacity: 0.65;
}
.ms-stamp-corner.tl { left: 10px; top: 10px; border-right: none; border-bottom: none; border-top-left-radius: 6px; }
.ms-stamp-corner.tr { right: 10px; top: 10px; border-left: none; border-bottom: none; border-top-right-radius: 6px; }
.ms-stamp-corner.bl { left: 10px; bottom: 10px; border-right: none; border-top: none; border-bottom-left-radius: 6px; }
.ms-stamp-corner.br { right: 10px; bottom: 10px; border-left: none; border-top: none; border-bottom-right-radius: 6px; }
.ms-stamp-top {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 2.5px;
  color: var(--seal-dark);
  text-transform: uppercase;
}
.ms-stamp-score-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.ms-stamp-score {
  font-family: var(--ff-display);
  font-size: 76px;
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -0.02em;
}
.ms-stamp-score.tone-jade  { color: var(--jade-dark); text-shadow: 0 4px 12px rgba(29, 185, 85, 0.3); }
.ms-stamp-score.tone-amber { color: var(--amber-dark); text-shadow: 0 4px 12px rgba(244, 183, 64, 0.3); }
.ms-stamp-score.tone-seal  { color: var(--seal-dark);  text-shadow: 0 4px 12px rgba(255, 90, 31, 0.3); }
.ms-stamp-sub {
  font-family: var(--ff-sub);
  font-size: 11px;
  letter-spacing: 3px;
  color: var(--seal-dark);
  opacity: 0.85;
}
.ms-stamp-level {
  font-family: var(--ff-display);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 2px;
  padding: 6px 18px;
  border-radius: 999px;
}
.ms-stamp-level.lvl-a { background: linear-gradient(135deg, var(--jade), #18A049); color: #fff; }
.ms-stamp-level.lvl-b { background: linear-gradient(135deg, var(--amber), #E6A836); color: #3D2A00; }
.ms-stamp-level.lvl-c { background: linear-gradient(135deg, var(--seal), var(--seal-dark)); color: #fff; }
.ms-stamp-level.lvl-none { background: rgba(15, 17, 21, 0.1); color: var(--ink-3); }
.ms-stamp-bottom {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--ff-mono);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--seal-dark);
  opacity: 0.85;
}
.ms-stamp-dot { opacity: 0.5; }

/* ── 4. 加载态 ── */
.ms-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  padding: 100px 20px;
}
.ms-loading-ring {
  width: 58px; height: 58px;
  border: 4px solid var(--paper-3);
  border-top-color: var(--cobalt);
  border-right-color: var(--seal);
  border-radius: 50%;
  animation: ms-spin 1s linear infinite;
  flex-shrink: 0;
}
@keyframes ms-spin { to { transform: rotate(360deg); } }
.ms-loading-text {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.ms-loading-title {
  font-family: var(--ff-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
}
.ms-loading-sub {
  font-family: var(--ff-sub);
  font-size: 11px;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: 0.8;
}

/* ── 5. 4 枚邮票数据卡 ── */
.ms-stamps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}
.ms-stamp-card {
  position: relative;
  padding: 20px 16px 18px;
  border-radius: 22px;
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.35) 0 2px, transparent 2px 6px),
    linear-gradient(160deg, #fff 0%, #FDF6EB 55%, #FBEBD5 100%);
  border: 1.5px solid var(--line);
  box-shadow:
    0 16px 36px -18px rgba(15, 17, 21, 0.22),
    inset 0 0 0 5px rgba(255, 255, 255, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: default;
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  transform: rotate(var(--stamp-r, 0deg));
  text-align: center;
}
.ms-stamp-card:hover {
  transform: rotate(0deg) translateY(-5px) scale(1.02);
  box-shadow:
    0 26px 48px -22px rgba(15, 17, 21, 0.32),
    inset 0 0 0 5px rgba(255, 255, 255, 0.5);
}
.ms-stamp-card-count { cursor: pointer; }
.ms-stamp-card-count:hover {
  border-color: var(--cobalt);
}
.ms-stamp-card-count:active { transform: rotate(0deg) translateY(-2px) scale(1.005); }

.msc-holes {
  position: absolute;
  left: 8px; right: 8px; top: 6px; bottom: 6px;
  border: 1px dashed rgba(15, 17, 21, 0.08);
  border-radius: 16px;
  pointer-events: none;
}
.msc-label {
  font-family: var(--ff-sub);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2.4px;
  text-transform: uppercase;
  color: var(--ink-3);
  opacity: 0.8;
  margin-bottom: 2px;
}
.msc-ic-wrap {
  width: 44px; height: 44px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  margin: 4px 0 6px;
  position: relative;
  z-index: 1;
}
.msc-ic { font-size: 22px; }
.ic-cobalt { background: rgba(61, 90, 254, 0.1);  color: var(--cobalt-dark); }
.ic-jade   { background: rgba(29, 185, 85, 0.12); color: var(--jade-dark); }
.ic-amber  { background: rgba(244, 183, 64, 0.18); color: var(--amber-dark); }
.ic-seal   { background: rgba(255, 90, 31, 0.1);  color: var(--seal-dark); }
.ic-ink    { background: rgba(42, 47, 58, 0.08);  color: var(--ink-2); }

.msc-num {
  font-family: var(--ff-display);
  font-size: 40px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.01em;
  color: var(--ink);
  z-index: 1;
}
.msc-num.tone-jade  { color: var(--jade-dark); }
.msc-num.tone-amber { color: var(--amber-dark); }
.msc-num.tone-seal  { color: var(--seal-dark); }
.msc-num.tone-cobalt{ color: var(--cobalt-dark); }

.msc-cn {
  font-family: var(--ff-body);
  font-size: 12.5px;
  font-weight: 700;
  color: var(--ink-2);
  margin-top: 2px;
  letter-spacing: 0.2px;
}
.msc-cn-weak { margin-top: -2px; }

.msc-foot {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  color: var(--ink-3);
  opacity: 0.85;
  line-height: 1.4;
  margin-top: 4px;
  letter-spacing: 0.2px;
}

/* 薄弱维度 chip list */
.msc-weak-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 5px;
  max-width: 100%;
  z-index: 1;
  margin: 4px 0 2px;
  min-height: 30px;
}
.msc-weak-chip {
  padding: 4px 9px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 90, 31, 0.12), rgba(255, 90, 31, 0.06));
  border: 1px solid rgba(255, 90, 31, 0.3);
  color: var(--seal-dark);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1px;
}
.msc-weak-more {
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--paper-2);
  color: var(--ink-3);
  font-size: 11px;
  font-weight: 700;
  font-family: var(--ff-mono);
}
.msc-weak-none {
  font-family: var(--ff-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--jade-dark);
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(29, 185, 85, 0.1);
  border: 1px dashed rgba(29, 185, 85, 0.35);
}

/* ── 6. 通用杂志卡片（分析卡、台账表格卡） ── */
.mag-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, #FFFCF5 100%);
  border: 1px solid var(--line);
  border-radius: 26px;
  overflow: hidden;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 22px 54px -30px rgba(15, 17, 21, 0.3);
  margin-bottom: 30px;
}
.ms-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px 26px 16px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.ms-card-top::before {
  content: '';
  position: absolute;
  left: 0; top: 0; right: 0; height: 4px;
}
.ms-card-top::after {
  content: '';
  position: absolute;
  right: -50px; top: -50px;
  width: 160px; height: 160px;
  border-radius: 50%;
  opacity: 0.08;
  pointer-events: none;
}
.msct-cobalt::before { background: linear-gradient(90deg, var(--cobalt), #6FC3FF); }
.msct-cobalt::after  { background: radial-gradient(circle, var(--cobalt), transparent 60%); }
.msct-amber::before  { background: linear-gradient(90deg, var(--amber), #FFD583); }
.msct-amber::after   { background: radial-gradient(circle, var(--amber), transparent 60%); }

.msct-eyebrow {
  display: inline-flex;
  align-items: baseline;
  gap: 10px;
}
.msct-num {
  font-family: var(--ff-mono);
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 1px;
  width: 30px; height: 30px;
  border-radius: 10px;
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.msct-cobalt .msct-num { background: linear-gradient(135deg, var(--cobalt), var(--cobalt-dark)); }
.msct-amber  .msct-num { background: linear-gradient(135deg, var(--amber), #C98A1C); }
.msct-text {
  font-family: var(--ff-sub);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--ink-2);
}

.msct-toggle {
  display: inline-flex;
  padding: 4px;
  border-radius: 14px;
  background: var(--paper-2);
  border: 1px solid var(--line-soft);
  gap: 4px;
  box-shadow: inset 0 1px 2px rgba(15, 17, 21, 0.04);
}
.msct-btn {
  padding: 7px 14px 7px 12px;
  border-radius: 10px;
  font-family: var(--ff-sub);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-3);
  border: none;
  background: transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.msct-btn:hover { color: var(--ink-2); }
.msct-btn.active {
  color: #fff;
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 8px 20px -10px rgba(15, 17, 21, 0.35);
}
.msct-btn.btn-cobalt {
  background: linear-gradient(135deg, var(--cobalt), #2E4BE0);
}
.msct-btn.btn-jade {
  background: linear-gradient(135deg, var(--jade), #159240);
}

/* 台账卡 inline 等级图例 */
.msct-legend-inline {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}
.mli-chip {
  padding: 5px 11px;
  border-radius: 999px;
  font-family: var(--ff-sub);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 1px;
  border: 1px solid;
}
.mli-chip.mli-green { color: var(--jade-dark);  border-color: rgba(29, 185, 85, 0.35); background: rgba(29, 185, 85, 0.1); }
.mli-chip.mli-amber { color: var(--amber-dark); border-color: rgba(244, 183, 64, 0.45); background: rgba(244, 183, 64, 0.13); }
.mli-chip.mli-red   { color: var(--seal-dark);  border-color: rgba(255, 90, 31, 0.38); background: rgba(255, 90, 31, 0.1); }

.ms-card-body {
  padding: 4px 26px 26px;
}
.ms-card-body-table { padding-bottom: 20px; }

/* ── 7. 成绩趋势卡（内部） ── */
.ms-chart-wrap {
  display: flex;
  flex-direction: column;
  min-height: 420px;
}
.msc-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 4px;
  padding-top: 18px;
}
.msc-title {
  font-family: var(--ff-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.005em;
}
.msc-legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.msc-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--ink-3);
  font-family: var(--ff-sub);
  letter-spacing: 0.2px;
}
.lg-dot {
  width: 14px; height: 14px;
  border-radius: 4px;
  border: 2.5px solid;
  display: inline-block;
}
.lg-dot.lg-cobalt { border-color: var(--cobalt); background: rgba(61, 90, 254, 0.25); }
.lg-dot.lg-jade   { border-color: var(--jade);   background: rgba(29, 185, 85, 0.2); }

.msc-sub {
  font-size: 13px;
  color: var(--ink-3);
  margin: 4px 0 16px;
  line-height: 1.7;
}
.msc-sub b { font-weight: 800; }
.k-cobalt { color: var(--cobalt-dark); }
.k-jade   { color: var(--jade-dark); }
.k-amber  { color: var(--amber-dark); }

.ms-chart {
  width: 100%;
  height: 360px;
  flex: 1;
}
.ms-chart-radar { height: 380px; }

/* ── 8. 能力成长报告 ── */
.ms-growth-wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 18px;
}
.growth-triplets {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.growth-tri {
  padding: 16px 14px;
  border-radius: 18px;
  text-align: center;
  border: 1px solid;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.growth-tri:hover { transform: translateY(-3px); }
.tri-blue  { background: linear-gradient(135deg, rgba(61, 90, 254, 0.1), #fff); border-color: rgba(61, 90, 254, 0.25); }
.tri-green { background: linear-gradient(135deg, rgba(29, 185, 85, 0.12), #fff); border-color: rgba(29, 185, 85, 0.25); }
.tri-seal  { background: linear-gradient(135deg, rgba(255, 90, 31, 0.12), #fff); border-color: rgba(255, 90, 31, 0.28); }
.gt-label {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  opacity: 0.85;
  margin-bottom: 8px;
}
.tri-blue  .gt-label { color: var(--cobalt-dark); }
.tri-green .gt-label { color: var(--jade-dark); }
.tri-seal  .gt-label { color: var(--seal-dark); }
.gt-num {
  font-family: var(--ff-display);
  font-size: 38px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.01em;
}
.tri-blue  .gt-num { color: var(--cobalt-dark); }
.tri-green .gt-num { color: var(--jade-dark); }
.tri-seal  .gt-num.num-up   { color: var(--jade-dark); }
.tri-seal  .gt-num.num-down { color: var(--seal-dark); }
.gt-unit {
  font-family: var(--ff-body);
  font-size: 15px;
  font-weight: 700;
  opacity: 0.75;
  margin-left: 3px;
}
.gt-time {
  font-family: var(--ff-mono);
  font-size: 10.5px;
  color: var(--ink-3);
  margin-top: 8px;
  opacity: 0.9;
}

.growth-split {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 24px;
  align-items: start;
}
.gs-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--ff-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 12px;
}
.gs-title-ic {
  font-size: 16px;
  width: 28px; height: 28px;
  border-radius: 9px;
  display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.gs-title-ic.ic-cobalt { background: rgba(61, 90, 254, 0.1);  color: var(--cobalt-dark); }
.gs-title-ic.ic-jade   { background: rgba(29, 185, 85, 0.12); color: var(--jade-dark); }

.growth-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  max-height: 380px;
  overflow-y: auto;
  padding-right: 4px;
}
/* growth-list 自定义滚动条 */
.growth-list::-webkit-scrollbar { width: 5px; }
.growth-list::-webkit-scrollbar-track { background: var(--paper-2); border-radius: 999px; margin: 4px 0; }
.growth-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--jade), var(--cobalt));
  border-radius: 999px;
  opacity: 0.6;
}

.growth-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  background: #fff;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.growth-row:hover { transform: translateY(-2px); box-shadow: 0 10px 24px -16px rgba(15, 17, 21, 0.3); }
.growth-row.row-up    { background: linear-gradient(135deg, rgba(29, 185, 85, 0.08), #fff); border-color: rgba(29, 185, 85, 0.22); }
.growth-row.row-down  { background: linear-gradient(135deg, rgba(255, 90, 31, 0.08), #fff); border-color: rgba(255, 90, 31, 0.22); }

.gr-left { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.gr-name {
  font-family: var(--ff-body);
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
}
.gr-arrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--ff-mono);
  font-size: 11px;
  color: var(--ink-3);
}
.gr-from { padding: 2px 7px; border-radius: 7px; background: rgba(61, 90, 254, 0.08); color: var(--cobalt-dark); }
.gr-arrow-ic { opacity: 0.7; }
.gr-to { padding: 2px 7px; border-radius: 7px; background: rgba(29, 185, 85, 0.1); color: var(--jade-dark); }

.gr-right {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 999px;
  font-family: var(--ff-display);
  font-size: 18px;
  font-weight: 800;
  flex-shrink: 0;
}
.gr-right em {
  font-style: normal;
  font-size: 11px;
  opacity: 0.85;
  font-family: var(--ff-body);
  font-weight: 600;
  margin-left: 1px;
}
.gr-right.ch-up   { background: rgba(29, 185, 85, 0.12); color: var(--jade-dark); }
.gr-right.ch-down { background: rgba(255, 90, 31, 0.12); color: var(--seal-dark); }

.growth-advice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 16px;
  background: linear-gradient(90deg, rgba(61, 90, 254, 0.08), rgba(29, 185, 85, 0.08));
  border: 1px solid rgba(61, 90, 254, 0.2);
}
.ga-ic {
  font-size: 20px;
  color: var(--amber-dark);
  flex-shrink: 0;
  margin-top: 2px;
}
.ga-text {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.75;
  color: var(--ink-2);
  font-weight: 500;
}

/* 成长报告 - 空态 */
.ms-empty-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 20px 44px;
  text-align: center;
}
.ms-empty-mini-art {
  position: relative;
  width: 110px; height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}
.ema-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px dashed;
  border-color: rgba(61, 90, 254, 0.25) rgba(29, 185, 85, 0.2) rgba(255, 90, 31, 0.22) rgba(244, 183, 64, 0.3);
  animation: ms-spin 30s linear infinite;
}
.ema-ic {
  font-size: 50px;
  color: var(--ink-3);
  opacity: 0.55;
  z-index: 1;
}
.ms-empty-mini-title {
  font-family: var(--ff-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
}
.ms-empty-mini-sub {
  max-width: 460px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--ink-3);
  margin-bottom: 10px;
}
.ms-empty-mini-sub b { color: var(--amber-dark); font-weight: 800; }

/* 通用 mag 按钮（空态用） */
.btn-mag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 11px 20px;
  border-radius: 14px;
  font-family: var(--ff-sub);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.2px;
  border: 1.5px solid;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}
.btn-mag.btn-l { padding: 13px 24px; font-size: 14px; border-radius: 16px; }
.btn-mag-seal {
  background: linear-gradient(135deg, var(--seal) 0%, var(--seal-dark) 55%, #A1280A 100%);
  color: #fff;
  border-color: var(--seal);
  box-shadow:
    0 12px 28px -14px rgba(255, 90, 31, 0.75),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.btn-mag-seal:hover { transform: translateY(-3px); box-shadow: 0 20px 38px -16px rgba(255, 90, 31, 0.85); }
.btn-mag-seal:active { transform: translateY(1px); }
.btn-mag-ghost {
  background: #fff;
  color: var(--ink-2);
  border-color: var(--line);
}
.btn-mag-ghost:hover {
  background: var(--paper-2);
  border-color: rgba(15, 17, 21, 0.22);
  transform: translateY(-2px);
  box-shadow: 0 10px 22px -14px rgba(15, 17, 21, 0.3);
}

/* 合并卡片：切换视图的进入/离开过渡 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 260ms ease, transform 260ms ease;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(7px); }
.fade-slide-leave-to   { opacity: 0; transform: translateY(-7px); }

/* ── 9. 评价记录（简约表格） ── */
.records-clean {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 30px;
}

/* 表头行 */
.rc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 18px 24px;
  border-bottom: 1px solid #f3f4f6;
}
.rc-head-left {
  display: flex;
  align-items: baseline;
  gap: 14px;
  flex-wrap: wrap;
}
.rc-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #111827;
  letter-spacing: 0.1px;
}
.rc-sub {
  font-size: 12.5px;
  color: #6b7280;
}
.rc-head-right {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.rc-legend {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}
.rc-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.rc-dot.d-ok  { background: #10b981; }
.rc-dot.d-mid { background: #f59e0b; }
.rc-dot.d-low { background: #ef4444; }

/* 表格容器 */
.rc-table-wrap {
  overflow-x: auto;
}
.rc-table-wrap::-webkit-scrollbar { height: 6px; }
.rc-table-wrap::-webkit-scrollbar-track { background: #f9fafb; }
.rc-table-wrap::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 999px;
}

/* 表格主体 */
.rc-table {
  width: 100%;
  min-width: 1000px;
  border-collapse: collapse;
  font-size: 13.5px;
  color: #111827;
}
.rc-table thead th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
  letter-spacing: 0.1px;
  white-space: nowrap;
}
.rc-table thead th.col-seq    { width: 56px; text-align: center; }
.rc-table thead th.col-score  { width: 92px; text-align: left; }
.rc-table thead th.col-time   { width: 168px; }
.rc-table thead th.col-act    { width: 104px; text-align: center; }

.rc-table tbody td {
  padding: 13px 16px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
  line-height: 1.4;
}
.rc-table tbody tr:last-child td { border-bottom: none; }
.rc-table tbody tr:hover { background: #fafbfc; }

/* 序号列 */
.rc-table td.col-seq {
  text-align: center;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-weight: 500;
  font-size: 12.5px;
  color: #9ca3af;
}

/* 任务列 */
.rc-task-text {
  display: block;
  font-weight: 500;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

/* 文件列 */
.rc-table td.col-file {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.rc-file-ic {
  font-size: 15px;
  color: #6b7280;
  flex-shrink: 0;
}
.rc-file-name {
  font-size: 13px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

/* 时间列 */
.rc-table td.col-time {
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 12.5px;
  color: #374151;
  letter-spacing: 0.1px;
  white-space: nowrap;
}

/* 分数列 */
.rc-score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 4px 10px;
  border-radius: 8px;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 13.5px;
  font-weight: 600;
}
.rc-score.tsc-jade  { background: #ecfdf5; color: #047857; }
.rc-score.tsc-amber { background: #fffbeb; color: #b45309; }
.rc-score.tsc-seal  { background: #fef2f2; color: #b91c1c; }
.rc-score.tsc-empty { background: #f9fafb; color: #9ca3af; }
.rc-score-empty {
  background: #f9fafb;
  color: #9ca3af;
  font-weight: 500;
  font-size: 12.5px;
  font-family: inherit;
}

/* 维度明细 */
.rc-dims-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 6px;
  font-size: 12.5px;
  color: #374151;
  max-width: 320px;
}
.rc-dim-item {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
}
.rc-dim-name {
  font-style: normal;
  font-weight: 500;
  color: #4b5563;
}
.rc-dim-score {
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-weight: 600;
  font-size: 12px;
}
.rc-dim-score.dim-jade  { color: #047857; }
.rc-dim-score.dim-amber { color: #b45309; }
.rc-dim-score.dim-seal  { color: #b91c1c; }
.rc-dim-score.dim-ink   { color: #6b7280; }
.rc-dim-sep {
  color: #d1d5db;
  margin: 0 1px;
}
.rc-dim-empty {
  color: #d1d5db;
  font-size: 14px;
}

/* 评语列 */
.rc-table td.col-comment {
  font-size: 12.5px;
  color: #4b5563;
  max-width: 220px;
}
.rc-table td.col-comment {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 操作列 */
.rc-table td.col-act {
  text-align: center;
}
.rc-act-btn {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 7px;
  background: transparent;
  border: 1px solid #e5e7eb;
  color: #374151;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s ease;
}
.rc-act-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  color: #111827;
}

/* 极简分页 */
.rc-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 18px 24px 20px;
  border-top: 1px solid #f3f4f6;
  background: #fcfcfd;
}
.rc-page-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #374151;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s ease;
}
.rc-page-btn:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #111827;
}
.rc-page-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.rc-page-nums {
  display: inline-flex;
  gap: 4px;
}
.rc-page-num {
  min-width: 32px;
  height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-weight: 500;
  font-size: 12.5px;
  color: #374151;
  cursor: pointer;
  transition: all 0.18s ease;
  user-select: none;
  background: #fff;
  border: 1px solid transparent;
}
.rc-page-num:hover:not(.active):not(.dot) {
  background: #f9fafb;
  border-color: #e5e7eb;
}
.rc-page-num.active {
  background: #111827;
  color: #fff;
  border-color: #111827;
}
.rc-page-num.dot {
  cursor: default;
  color: #9ca3af;
  background: transparent;
  border: none;
  padding: 0 4px;
}

/* ── 10. 空态（无任何记录） ── */
.ms-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 90px 24px 70px;
  text-align: center;
}
.ms-empty-art {
  position: relative;
  width: 170px; height: 170px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}
.mea-corner {
  position: absolute;
  width: 28px; height: 28px;
  border: 2px solid;
  opacity: 0.65;
  border-color: rgba(255, 90, 31, 0.5);
}
.mea-corner.mea-tl { left: 0;    top: 0;    border-right: none; border-bottom: none; border-top-left-radius: 10px; }
.mea-corner.mea-tr { right: 0;   top: 0;    border-left: none;  border-bottom: none; border-top-right-radius: 10px; }
.mea-corner.mea-bl { left: 0;    bottom: 0; border-right: none; border-top: none;    border-bottom-left-radius: 10px; }
.mea-corner.mea-br { right: 0;   bottom: 0; border-left: none;  border-top: none;    border-bottom-right-radius: 10px; }
.mea-ring-1, .mea-ring-2 {
  position: absolute;
  border-radius: 50%;
  border: 2px dashed;
}
.mea-ring-1 {
  inset: 14px;
  border-color: rgba(61, 90, 254, 0.25);
  animation: ms-spin 36s linear infinite;
}
.mea-ring-2 {
  inset: 38px;
  border-color: rgba(255, 90, 31, 0.28);
  animation: ms-spin 48s linear infinite reverse;
}
.mea-ic {
  font-size: 72px;
  color: var(--ink-3);
  opacity: 0.5;
  z-index: 1;
}
.ms-empty-title {
  font-family: var(--ff-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--ink);
  margin: 0;
  letter-spacing: -0.005em;
}
.ms-empty-sub {
  max-width: 560px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--ink-3);
  margin: 0 0 8px;
}
.ms-empty-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

/* ── 11. 页脚 ── */
.ms-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  margin-top: 10px;
  background: rgba(255, 253, 248, 0.75);
  backdrop-filter: blur(4px);
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  font-family: var(--ff-sub);
  font-size: 12px;
  color: var(--ink-3);
  font-weight: 500;
}
.msf-left, .msf-right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.msf-left b { font-family: var(--ff-display); font-weight: 800; color: var(--ink-2); font-size: 13.5px; }
.msf-ic { color: var(--seal-dark); font-size: 15px; opacity: 0.85; }
.msf-dot { opacity: 0.5; margin: 0 2px; }
.msf-k {
  font-family: var(--ff-mono);
  font-weight: 700;
  color: var(--cobalt-dark);
  padding: 2px 8px;
  border-radius: 7px;
  background: rgba(61, 90, 254, 0.08);
  border: 1px solid rgba(61, 90, 254, 0.18);
}

/* ── 12. 响应式 ── */
@media (max-width: 1280px) {
  .ms-stamps { grid-template-columns: repeat(2, 1fr); }
  .growth-split { grid-template-columns: 1fr; }
}
@media (max-width: 1100px) {
  .ms-hero { grid-template-columns: 1fr; gap: 26px; }
  .ms-hero-right { order: -1; }
  .ms-stamp { max-width: 240px; aspect-ratio: auto; min-height: 300px; }
}
@media (max-width: 860px) {
  .ms-page { padding: 30px 14px 56px; }
  .ms-hero { gap: 22px; margin-bottom: 28px; }
  .ms-hero-title { font-size: 46px; }
  .ms-stamps { gap: 16px; margin-bottom: 24px; }
  .ms-stamp-card { transform: rotate(0deg); }
  .ms-stamp-card:hover { transform: translateY(-3px) scale(1.01); }
  .mag-card { margin-bottom: 24px; border-radius: 22px; }
  .ms-card-top { padding: 16px 18px 14px; }
  .ms-card-body { padding: 2px 18px 20px; }
  .records-clean { margin-bottom: 24px; border-radius: 12px; }
  .rc-head { padding: 16px 18px; }
  .growth-triplets { grid-template-columns: 1fr; }
  .ms-foot { padding: 14px 16px; font-size: 11.5px; flex-direction: column; align-items: flex-start; }
}
@media (max-width: 640px) {
  .ms-hero-title { font-size: 38px; }
  .ms-hero-underline { display: none; }
  .ms-ledger-mark { display: none; }
  .ms-stamps { grid-template-columns: 1fr; }
  .ms-hero-minis { flex-direction: column; }
  .ms-mini-chip { justify-content: space-between; width: 100%; }
  .msc-title-row { flex-direction: column; align-items: flex-start; }
  .msct-toggle { width: 100%; }
  .msct-btn { flex: 1; justify-content: center; }
  .msct-legend-inline { width: 100%; }
  .rc-head { flex-direction: column; align-items: flex-start; gap: 10px; }
  .rc-head-right { width: 100%; justify-content: flex-start; }
  .rc-pager { flex-direction: column; align-items: stretch; gap: 12px; padding: 16px 18px; }
  .rc-page-nums { justify-content: center; }
  .rc-page-btn { justify-content: center; }
  .ms-empty-actions { flex-direction: column; width: 100%; }
  .ms-empty-actions .btn-mag { width: 100%; justify-content: center; }
}
</style>