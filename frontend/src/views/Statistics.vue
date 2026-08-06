<template>
  <div class="min-h-full page-enter">
    <div class="max-w-7xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-surface-800 tracking-tight">数据统计</h1>
        <p class="text-surface-500 mt-1">查看实训评价的整体数据与趋势分析</p>
      </div>

      <!-- 加载中 -->
      <div v-if="!loaded" class="min-h-[60vh] flex items-center justify-center">
        <div class="text-center">
          <div class="w-12 h-12 border-[3px] border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-surface-500">加载中...</p>
        </div>
      </div>

      <div v-else>
        <!-- ================================================================ -->
        <!--                      企 业 端（空态）                             -->
        <!--  企业端业务指标集中在「企业总览 / 三方对比 / 岗位匹配」页面，    -->
        <!--  此处没有独立的教学统计视图 → 给出角色不可用提示与快捷跳转       -->
        <!-- ================================================================ -->
        <template v-if="isEnterprise">
          <div class="rounded-3xl border-2 border-line bg-paper p-10 md:p-14 text-center">
            <div class="w-20 h-20 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-amber-100 via-orange-100 to-seal/20 flex items-center justify-center ring-4 ring-white shadow-lg">
              <Icon icon="mdi:chart-box-outline" class="text-5xl text-seal" />
            </div>
            <h2 class="text-2xl font-black text-ink tracking-tight mb-2">数据分析视图暂未开放给企业角色</h2>
            <p class="text-ink-3 max-w-xl mx-auto mb-8 leading-[1.8]">
              企业端的业务统计与数据指标已经分别集成在「企业总览」「三方评价对比」「岗位匹配榜」三张页面中。
              请从左侧导航栏或下方快捷入口进入，无需在此处重复查看。
            </p>
            <div class="flex flex-wrap gap-3 justify-center">
              <router-link to="/app/enterprise/dashboard" class="btn-mag btn-mag-primary">
                <Icon icon="mdi:view-dashboard-outline" class="mr-1.5" inline width="16" /> 企业总览
              </router-link>
              <router-link to="/app/enterprise/compare" class="btn-mag btn-mag-ghost">
                <Icon icon="mdi:scale-balance" class="mr-1.5" inline width="16" /> 三方对比
              </router-link>
              <router-link to="/app/enterprise/matching" class="btn-mag btn-mag-ghost">
                <Icon icon="mdi:account-tie-outline" class="mr-1.5" inline width="16" /> 岗位匹配
              </router-link>
            </div>
          </div>
        </template>

        <!-- ================================================================ -->
        <!--                         教 师 端                                 -->
        <!-- ================================================================ -->
        <template v-else-if="isTeacher">

          <!-- ═══════════════════════════════════════════════════════════ -->
          <!--  分区1：KPI 顶部大卡（提交/评价/平均分/学生人数）+ 筛选器      -->
          <!-- ═══════════════════════════════════════════════════════════ -->
          <section class="st-unified mb-8">
            <div class="st-section">
              <div class="st-sec-head">
                <h3 class="st-sec-title"><Icon icon="mdi:view-dashboard-outline" class="sh-ic ic-cobalt" /> 核心数据总览</h3>
                <div class="st-filters">
                  <!-- 班级筛选器：✅ 100% 自绘按钮 + el-dropdown 菜单（不用 el-select 的显示框，避免任何 EP 黑盒） -->
                  <div class="sf-item">
                    <span class="sf-label">班级</span>
                    <el-dropdown trigger="click"
                      @command="(val: any) => { selectedClassId = Number(val); onClassChange(Number(val)) }">
                      <button type="button"
                        class="filter-trigger filter-trigger--dark w-44"
                        :class="{ 'is-empty': selectedClassLabel?.isPlaceholder ?? true }">
                        <span class="ft-label">{{ selectedClassLabel?.label ?? '全部班级' }}</span>
                        <Icon v-if="!(selectedClassLabel?.isPlaceholder ?? true)"
                          icon="mdi:close-circle" class="ft-clear"
                          @click.stop="selectedClassId = 0; onClassChange(0)" />
                        <Icon v-else icon="mdi:chevron-down" class="ft-caret" />
                      </button>
                      <template #dropdown>
                        <el-dropdown-menu class="stat-ddm stat-ddm--dark">
                          <el-dropdown-item :command="0"
                            :class="{ 'is-active': selectedClassId === 0 }">
                            全部班级
                          </el-dropdown-item>
                          <el-dropdown-item v-for="c in myClasses"
                            :key="'cls-'+c.id"
                            :command="Number(c.id)"
                            :class="{ 'is-active': Number(selectedClassId) === Number(c.id) }">
                            {{ String(c.name ?? c.label ?? c.id) }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>

                  <!-- 课程筛选器：✅ 同款自绘 -->
                  <div class="sf-item">
                    <span class="sf-label">课程</span>
                    <el-dropdown trigger="click"
                      @command="(val: any) => { selectedCourse = val ?? ''; onCourseChange(val ?? '') }">
                      <button type="button"
                        class="filter-trigger filter-trigger--dark w-40"
                        :class="{ 'is-empty': selectedCourseLabel?.isPlaceholder ?? true }">
                        <span class="ft-label">{{ selectedCourseLabel?.label ?? '全部课程' }}</span>
                        <Icon v-if="!(selectedCourseLabel?.isPlaceholder ?? true)"
                          icon="mdi:close-circle" class="ft-clear"
                          @click.stop="selectedCourse = ''; onCourseChange('')" />
                        <Icon v-else icon="mdi:chevron-down" class="ft-caret" />
                      </button>
                      <template #dropdown>
                        <el-dropdown-menu class="stat-ddm stat-ddm--dark">
                          <el-dropdown-item command=""
                            :class="{ 'is-active': !selectedCourse }">
                            全部课程
                          </el-dropdown-item>
                          <el-dropdown-item v-for="c in courseList"
                            :key="'cur-'+String(c.name ?? c.label ?? c)"
                            :command="String(c.name ?? c.label ?? c)"
                            :class="{ 'is-active': String(selectedCourse) === String(c.name ?? c.label ?? c) }">
                            {{ String(c.name ?? c.label ?? c) }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </div>
              <div v-if="overview" class="st-kpi-grid four">
                <div class="st-kpi kpi-cobalt">
                  <div class="kpi-top">
                    <div class="kpi-ic"><Icon icon="mdi:file-document-multiple-outline" /></div>
                    <span class="kpi-chip chip-cobalt">提交</span>
                  </div>
                  <div class="kpi-num">{{ overview.total_submissions || 0 }}</div>
                  <div class="kpi-lbl">提交总数 · 次</div>
                </div>
                <div class="st-kpi kpi-jade">
                  <div class="kpi-top">
                    <div class="kpi-ic"><Icon icon="mdi:star-check-outline" /></div>
                    <span class="kpi-chip chip-jade">评价</span>
                  </div>
                  <div class="kpi-num">{{ overview.total_evaluations || 0 }}</div>
                  <div class="kpi-lbl">评价总数 · 次</div>
                </div>
                <div class="st-kpi kpi-amber">
                  <div class="kpi-top">
                    <div class="kpi-ic"><Icon icon="mdi:chart-line-variant" /></div>
                    <span class="kpi-chip chip-amber">平均</span>
                  </div>
                  <div class="kpi-num">{{ overview.avg_score || 0 }}</div>
                  <div class="kpi-lbl">平均分 · 分</div>
                </div>
                <div class="st-kpi kpi-violet">
                  <div class="kpi-top">
                    <div class="kpi-ic"><Icon icon="mdi:account-group-outline" /></div>
                    <span class="kpi-chip chip-violet">学生</span>
                  </div>
                  <div class="kpi-num">{{ overview.student_count || 0 }}</div>
                  <div class="kpi-lbl">学生人数 · 人</div>
                </div>
              </div>
            </div>
          </section>

          <!-- ═══════════════════════════════════════════════════════════ -->
          <!--  分区2：AI 教学建议（第二顺位） + 班级选择器                   -->
          <!-- ═══════════════════════════════════════════════════════════ -->
          <section class="st-advice mb-8">
            <div class="st-advice-head">
              <div class="sah-left">
                <div class="sah-ic"><Icon icon="mdi:lightbulb-on-outline" /></div>
                <div>
                  <div class="flex items-center gap-3">
                    <h3 class="sah-title">AI 教学建议</h3>
                    <span class="sah-tag">AI 驱动</span>
                  </div>
                  <p class="sah-sub">基于当前班级数据智能分析，精准定位教学改进方向</p>
                </div>
              </div>
              <div class="sah-actions">
                <!-- AI 教学建议 班级筛选器：✅ 自绘按钮 + dropdown（同款） -->
                <div class="sah-filter">
                  <span class="sah-fl-label">选择班级</span>
                  <el-dropdown trigger="click"
                    @command="(val: any) => { selectedClassId = Number(val); onClassChange(Number(val)) }">
                    <button type="button"
                      class="filter-trigger filter-trigger--amber w-48"
                      :class="{ 'is-empty': selectedClassLabel?.isPlaceholder ?? true }">
                      <span class="ft-label">{{ selectedClassLabel?.label ?? '全部班级' }}</span>
                      <Icon v-if="!(selectedClassLabel?.isPlaceholder ?? true)"
                        icon="mdi:close-circle" class="ft-clear"
                        @click.stop="selectedClassId = 0; onClassChange(0)" />
                      <Icon v-else icon="mdi:chevron-down" class="ft-caret" />
                    </button>
                    <template #dropdown>
                      <el-dropdown-menu class="stat-ddm stat-ddm--amber">
                        <el-dropdown-item :command="0"
                          :class="{ 'is-active': selectedClassId === 0 }">
                          全部班级
                        </el-dropdown-item>
                        <el-dropdown-item v-for="c in myClasses"
                          :key="'ai-cls-'+c.id"
                          :command="Number(c.id)"
                          :class="{ 'is-active': Number(selectedClassId) === Number(c.id) }">
                          {{ String(c.name ?? c.label ?? c.id) }}
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
                <button v-if="!teachingAdvice && !adviceLoading"
                  @click="loadTeachingAdvice"
                  class="sah-btn">
                  <Icon icon="mdi:sparkles" /> AI 分析教学建议
                </button>
              </div>
            </div>

            <div v-if="teachingAdvice" class="st-advice-body animate-fade-in-up">
              <Icon icon="mdi:format-quote-open" class="quote-ic" />
              <p class="advice-text">{{ teachingAdvice.advice }}</p>
            </div>

            <div v-else-if="adviceLoading" class="st-advice-empty">
              <div class="w-12 h-12 border-[3px] border-cobalt/20 border-t-cobalt rounded-full animate-spin mx-auto mb-4"></div>
              <p class="empty-title">AI 正在深度分析教学质量数据...</p>
              <p class="empty-sub">综合评估班级成绩、维度得分与提交趋势</p>
            </div>

            <div v-else class="st-advice-empty">
              <p class="empty-title">点击右上角「AI 分析教学建议」生成专属改进方案</p>
            </div>
          </section>

          <!-- ═══════════════════════════════════════════════════════════ -->
          <!--  分区3：图表单卡 — 5 个图表通过 Tab 按钮切换展示              -->
          <!-- ═══════════════════════════════════════════════════════════ -->
          <section class="st-chart mb-8">
            <div class="st-chart-head">
              <div class="sch-left">
                <Icon :icon="activeChartMeta.icon" class="sch-ic" :class="activeChartMeta.icClass" />
                <h3 class="sch-title">{{ activeChartMeta.label }}</h3>
                <span class="sch-tag">共 5 种分析视图 · Tab 切换</span>
              </div>
              <div class="sch-tabs">
                <button v-for="t in chartTabList" :key="t.key"
                  @click="activeChart = t.key"
                  :class="['sch-tab', { 'sch-tab-active': activeChart === t.key }]">
                  <Icon :icon="t.icon" inline width="13" class="mr-1" /> {{ t.label }}
                </button>
              </div>
            </div>

            <div class="st-chart-body">
              <!-- 1. 成绩分布（柱状） -->
              <div v-show="activeChart === 'distribution'" class="chart-wrap">
                <div v-if="distribution.length === 0" class="chart-empty">
                  <Icon icon="mdi:chart-bar" class="text-4xl text-ink-4 mb-3" />
                  <p class="text-ink-4 text-sm">暂无成绩分布数据</p>
                </div>
                <v-chart v-else :option="barOption" autoresize style="height: 420px" class="chart-slot" />
              </div>

              <!-- 2. 各维度平均分（雷达） -->
              <div v-show="activeChart === 'dimension'" class="chart-wrap">
                <div v-if="dimensionAvg.length === 0" class="chart-empty">
                  <Icon icon="mdi:radar" class="text-4xl text-ink-4 mb-3" />
                  <p class="text-ink-4 text-sm">暂无维度平均数据</p>
                </div>
                <v-chart v-else :option="radarOption" autoresize style="height: 420px" class="chart-slot" />
              </div>

              <!-- 3. 班级平均分对比（柱状） -->
              <div v-show="activeChart === 'classCompare'" class="chart-wrap">
                <div v-if="classCompare.length === 0" class="chart-empty">
                  <Icon icon="mdi:trophy-outline" class="text-4xl text-ink-4 mb-3" />
                  <p class="text-ink-4 text-sm">暂无班级对比数据</p>
                </div>
                <v-chart v-else :option="classCompareOption" autoresize style="height: 420px" class="chart-slot" />
              </div>

              <!-- 4. 提交率统计（柱状） -->
              <div v-show="activeChart === 'submitRate'" class="chart-wrap">
                <div v-if="submitRateData.length === 0" class="chart-empty">
                  <Icon icon="mdi:chart-pie" class="text-4xl text-ink-4 mb-3" />
                  <p class="text-ink-4 text-sm">暂无提交率数据</p>
                </div>
                <v-chart v-else :option="submitRateOption" autoresize style="height: 420px" class="chart-slot" />
              </div>

              <!-- 5. 最近评价趋势（折线） -->
              <div v-show="activeChart === 'trend'" class="chart-wrap">
                <div v-if="trend.length === 0" class="chart-empty">
                  <Icon icon="mdi:chart-timeline-variant" class="text-4xl text-ink-4 mb-3" />
                  <p class="text-ink-4 text-sm">暂无趋势数据</p>
                </div>
                <v-chart v-else :option="lineOption" autoresize style="height: 420px" class="chart-slot" />
              </div>
            </div>
          </section>
        </template>

        <!-- ================================================================ -->
        <!--                         学 生 端                                 -->
        <!-- ================================================================ -->
        <template v-if="isStudent">

          <!-- ─────────────────────────────────────────────────────────
               1 · 顶部 HERO 条：个人定位 / 年级 / 学号
               ───────────────────────────────────────────────────────── -->
          <section class="stu-hero mb-8 relative overflow-hidden">
            <div class="stu-hero__bg">
              <div class="gridmesh"></div>
              <div class="orb orb-a"></div>
              <div class="orb orb-b"></div>
              <div class="grain"></div>
            </div>

            <div class="relative z-10 px-8 pt-10 pb-8">
              <!-- HERO 头：身份标签 + 问候语 -->
              <div class="flex flex-col lg:flex-row lg:items-end justify-between gap-6 mb-9">
                <div class="min-w-0">
                  <div class="flex items-center gap-3 mb-4">
                    <span class="eyebrow-tag">
                      <span class="dot"></span> STUDENT · DASHBOARD
                    </span>
                    <span class="eyebrow-tag eyebrow-tag--amber">
                      <Icon icon="mdi:school-outline" class="mr-1" inline width="12" /> {{ studentClassName || '在校学生' }}
                    </span>
                  </div>
                  <h1 class="hero-title">
                    <span class="hero-title__hello">Hi,</span>
                    <span class="hero-title__name"> {{ studentName }} </span>
                    <span class="hero-title__wave" aria-hidden="true">✦</span>
                  </h1>
                  <p class="hero-sub mt-3">
                    以下是你的 <strong>实训数据总览</strong>，让每一次评价都看得见成长。
                  </p>
                </div>

                <!-- 右侧：等级徽章卡 -->
                <div class="grade-plaque">
                  <div class="gp-ring">
                    <div class="gp-core">
                      <div class="gp-grade">{{ gradeLabel }}</div>
                      <div class="gp-lbl">当前评级</div>
                    </div>
                  </div>
                  <div class="gp-right">
                    <div class="gp-score">
                      <span class="gp-num">{{ myStats.avg_score || 0 }}</span>
                      <span class="gp-base">/ 100</span>
                    </div>
                    <div class="gp-avg">综合平均分</div>
                  </div>
                </div>
              </div>

              <!-- 4 KPI 大卡：在纸底上用深色印章压印 -->
              <div class="kpi-row">
                <div class="kpi-card kpi--cobalt">
                  <div class="kpi-card__chip">
                    <Icon icon="mdi:send-circle-outline" class="mr-1" inline width="14" /> SUBMISSION
                  </div>
                  <div class="kpi-card__num"><span>{{ myStats.total_count || 0 }}</span><em>次</em></div>
                  <div class="kpi-card__lbl">累计提交任务</div>
                </div>

                <div class="kpi-card kpi--jade">
                  <div class="kpi-card__chip">
                    <Icon icon="mdi:crown-outline" class="mr-1" inline width="14" /> PEAK
                  </div>
                  <div class="kpi-card__num"><span>{{ myStats.max_score || 0 }}</span><em>分</em></div>
                  <div class="kpi-card__lbl">个人最高分</div>
                </div>

                <div class="kpi-card kpi--amber">
                  <div class="kpi-card__chip">
                    <Icon icon="mdi:chart-timeline-variant" class="mr-1" inline width="14" /> AVG
                  </div>
                  <div class="kpi-card__num"><span>{{ myStats.avg_score || 0 }}</span><em>分</em></div>
                  <div class="kpi-card__lbl">综合平均分</div>
                </div>

                <div class="kpi-card kpi--seal">
                  <div class="kpi-card__chip">
                    <Icon icon="mdi:trending-down" class="mr-1" inline width="14" /> NADIR
                  </div>
                  <div class="kpi-card__num"><span>{{ myStats.min_score || 0 }}</span><em>分</em></div>
                  <div class="kpi-card__lbl">历史最低记录</div>
                </div>
              </div>
            </div>
          </section>

          <!-- ─────────────────────────────────────────────────────────
               2 · 两栏主区：成绩趋势（左） + 能力雷达（右）
               ───────────────────────────────────────────────────────── -->
          <section class="stu-twins mb-8">
            <!-- 左：成绩趋势折线卡 -->
            <div class="twin-card">
              <div class="twin-head">
                <div class="twin-head__left">
                  <div class="twin-icon twin-icon--jade">
                    <Icon icon="mdi:chart-line-variant" class="text-xl" />
                  </div>
                  <div class="twin-head__titles">
                    <div class="twin-head__title">个人成绩趋势</div>
                    <div class="twin-head__sub">Performance · Trendline</div>
                  </div>
                </div>
                <div class="twin-head__badge">
                  <Icon icon="mdi:arrow-top-right-thick" class="mr-1" inline width="13" />
                  {{ trendDelta >= 0 ? '进步中' : '需回稳' }}
                  <b class="ml-1.5">{{ trendDelta >= 0 ? '+' : '' }}{{ trendDelta }}</b>
                </div>
              </div>
              <div class="twin-body">
                <div v-if="myTrend.length === 0" class="twin-empty">
                  <Icon icon="mdi:chart-line-variant" class="text-4xl mb-3 text-ink-4" />
                  <p class="text-ink-4 text-sm">暂无成绩趋势数据，完成一次实训评价即可</p>
                </div>
                <v-chart v-else :option="studentTrendOption" autoresize style="height: 340px" />
              </div>
            </div>

            <!-- 右：能力雷达卡 -->
            <div class="twin-card">
              <div class="twin-head">
                <div class="twin-head__left">
                  <div class="twin-icon twin-icon--amber">
                    <Icon icon="mdi:radar" class="text-xl" />
                  </div>
                  <div class="twin-head__titles">
                    <div class="twin-head__title">各维度能力画像</div>
                    <div class="twin-head__sub">Competency · Radar</div>
                  </div>
                </div>
                <div class="twin-head__badge twin-head__badge--amber">
                  <Icon icon="mdi:hexagon-multiple-outline" class="mr-1" inline width="13" />
                  维度数 <b class="ml-1.5">{{ myRadarData.length || 0 }}</b>
                </div>
              </div>
              <div class="twin-body">
                <div v-if="myRadarData.length === 0" class="twin-empty">
                  <Icon icon="mdi:radar" class="text-4xl mb-3 text-ink-4" />
                  <p class="text-ink-4 text-sm">暂无维度数据，完成一次多维度评价即可</p>
                </div>
                <v-chart v-else :option="studentRadarOption" autoresize style="height: 340px" />
              </div>
            </div>
          </section>

          <!-- ─────────────────────────────────────────────────────────
               3 · 薄弱维度 · 提升清单（印章红色警示）
               ───────────────────────────────────────────────────────── -->
          <section v-if="myStats.weakness?.length" class="stu-weak mb-10">
            <div class="weak-head">
              <div class="weak-head__left">
                <div class="weak-head__seal">
                  <Icon icon="mdi:alert-decagram-outline" class="text-2xl" />
                </div>
                <div>
                  <div class="weak-head__title">薄弱维度 · 提升清单</div>
                  <div class="weak-head__sub">NEEDS IMPROVEMENT · 低于 70 分的能力项</div>
                </div>
              </div>
              <div class="weak-head__count">
                <span>共</span>
                <b>{{ myStats.weakness.length }}</b>
                <span>项</span>
              </div>
            </div>

            <div class="weak-grid">
              <div v-for="(w, idx) in myStats.weakness" :key="w.name" class="weak-item">
                <div class="weak-item__idx">{{ String(idx + 1).padStart(2, '0') }}</div>
                <div class="weak-item__info">
                  <div class="weak-item__name">{{ w.name }}</div>
                  <div class="weak-item__meta">低于 70 分 共 <b>{{ w.count }}</b> 次</div>
                </div>
                <div class="weak-item__bar">
                  <div class="weak-item__bar-track">
                    <div class="weak-item__bar-fill"
                         :style="{ width: Math.min(100, Math.max(6, 100 - (w.count * 18))) + '%' }">
                    </div>
                  </div>
                  <div class="weak-item__bar-label">稳定性指数</div>
                </div>
              </div>
            </div>
          </section>

          <!-- ─────────────────────────────────────────────────────────
               4 · AI 岗位匹配（学生端核心）
               ───────────────────────────────────────────────────────── -->
          <section class="stu-match mb-10">
            <div class="match-head">
              <div class="match-head__left">
                <div>
                  <div class="flex items-center gap-3 mb-1">
                    <h2 class="match-head__title">AI 岗位匹配</h2>
                    <span class="match-head__tag">
                      <Icon icon="mdi:sparkles" class="mr-1" inline width="12" /> AI 驱动
                    </span>
                  </div>
                  <p class="match-head__sub">基于你的实训成绩与维度数据，智能推荐适合的岗位方向</p>
                </div>
              </div>
              <div v-if="!jobMatch && !jobMatchLoading" class="match-head__cta">
                <button @click="loadJobMatch" class="match-cta">
                  <Icon icon="mdi:auto-fix" class="mr-2" inline width="16" />
                  立即分析匹配
                </button>
              </div>
            </div>

            <!-- 加载中 -->
            <div v-if="jobMatchLoading" class="match-skeleton">
              <div class="match-skeleton__ring">
                <div class="match-skeleton__spinner"></div>
              </div>
              <div class="match-skeleton__title">AI 正在深度分析你的能力画像…</div>
              <div class="match-skeleton__sub">综合评估各维度得分、班级排名与成长趋势</div>
            </div>

            <!-- 无结果空态 -->
            <div v-else-if="!jobMatch" class="match-empty">
              <div class="match-empty__illus">
                <Icon icon="mdi:magnify-scan" class="text-5xl" />
              </div>
              <p class="match-empty__text">点击右上角「立即分析匹配」，<br/>让 AI 为你精准匹配岗位方向</p>
            </div>

            <!-- 有结果 -->
            <div v-else class="match-panel animate-fade-in-up">
              <div class="match-panel__hero">
                <div class="match-hero__left">
                  <div class="match-hero__job">
                    <Icon icon="mdi:briefcase" class="mr-2" inline width="22" />
                    {{ jobMatch.job }}
                  </div>
                  <div class="match-hero__tagline">
                    与你当前能力画像高度契合的岗位方向
                  </div>
                </div>
                <div class="match-hero__score">
                  <div class="match-hero__pct">
                    <span class="match-hero__num">{{ jobMatch.match }}</span>
                    <span class="match-hero__pct-sign">%</span>
                  </div>
                  <div class="match-hero__bar">
                    <div class="match-hero__bar-fill" :style="{ width: jobMatch.match + '%' }"></div>
                  </div>
                  <div class="match-hero__bar-lbl">匹配度 · Match Rate</div>
                </div>
              </div>

              <!-- 技能要求清单 -->
              <div class="match-req-title">
                <Icon icon="mdi:target" class="mr-1.5" inline width="14" /> 技能要求对标
              </div>
              <div class="match-req-grid">
                <div v-for="(req, i) in jobMatch.requirements" :key="req.skill" class="req-card">
                  <div class="req-card__idx">{{ String(i + 1).padStart(2, '0') }}</div>
                  <div class="req-card__name">{{ req.skill }}</div>
                  <div class="req-card__val">
                    <span class="req-card__mine">{{ req.student_level }}</span>
                    <span class="req-card__sep">/</span>
                    <span class="req-card__target">{{ req.level }}</span>
                  </div>
                  <div :class="['req-card__tag', req.gap.includes('已达标') ? 'req-card__tag--ok' : 'req-card__tag--miss']">
                    {{ req.gap.includes('已达标') ? '已达标' : '需提升' }}
                  </div>
                  <p class="req-card__gap">{{ req.gap }}</p>
                </div>
              </div>

              <!-- 建议 -->
              <div class="match-advice">
                <Icon icon="mdi:message-quote" class="match-advice__ic" />
                <p>{{ jobMatch.advice }}</p>
              </div>
            </div>
          </section>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { Icon } from '@iconify/vue'
import { API_BASE } from '../config'

const loaded = ref(false)
const isTeacher = ref(false)
const isStudent = ref(false)
const isEnterprise = ref(false)

const overview = ref<any>({})
const distribution = ref<any[]>([])
const trend = ref<any[]>([])
const dimensionAvg = ref<any[]>([])
const selectedClassId = ref(0)
const myClasses = ref<any[]>([])
const classCompare = ref<any[]>([])
const submitRateData = ref<any[]>([])

const myStats = ref<any>({ total_count: 0, avg_score: 0, max_score: 0, min_score: 0, weakness: [] })
const myTrend = ref<any[]>([])
const myRadarData = ref<any[]>([])
const jobMatch = ref<any>(null)
const jobMatchLoading = ref(false)

const teachingAdvice = ref<any>(null)
const adviceLoading = ref(false)

const selectedCourse = ref('')
const courseList = ref<any[]>([])

/* ═══════════════════════════════════════════════════════════
   🎓 学生端看板 · 派生数据（UI 展示层用）
   ═══════════════════════════════════════════════════════════ */
// 学生姓名 / 班级（取 user 缓存，避免二次请求）
const studentName = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}')
    return (u.real_name || u.nickname || u.name || u.username || '同学').toString().trim() || '同学'
  } catch {
    return '同学'
  }
})
const studentClassName = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}')
    return u.class_name || u.className || u.className || u.grade || u.major || ''
  } catch {
    return ''
  }
})
// 根据平均分给评级：不及格 / 及格 / 良好 / 优秀
const gradeLabel = computed(() => {
  const s = Number(myStats.value?.avg_score ?? 0)
  if (s <= 0 || Number.isNaN(s)) return '—'
  if (s >= 90) return 'S'
  if (s >= 80) return 'A'
  if (s >= 70) return 'B'
  if (s >= 60) return 'C'
  return 'D'
})
// 成绩趋势：最后两次的差值（进步 / 退步）
const trendDelta = computed(() => {
  const arr = Array.isArray(myTrend.value) ? myTrend.value : []
  if (arr.length < 2) return 0
  const prev = Number(arr[arr.length - 2]?.score ?? 0)
  const last = Number(arr[arr.length - 1]?.score ?? 0)
  if (!prev || !last) return 0
  return Math.round(last - prev)
})

// 图表 Tab 切换
const activeChart = ref<'distribution' | 'dimension' | 'classCompare' | 'submitRate' | 'trend'>('distribution')
const chartTabList = [
  { key: 'distribution',    label: '成绩分布',      icon: 'mdi:chart-bar',            icClass: 'ic-cobalt' },
  { key: 'dimension',       label: '维度能力',      icon: 'mdi:radar',                icClass: 'ic-amber'  },
  { key: 'classCompare',    label: '班级对比',      icon: 'mdi:trophy-outline',       icClass: 'ic-jade'   },
  { key: 'submitRate',      label: '提交率',        icon: 'mdi:chart-donut',          icClass: 'ic-blue'   },
  { key: 'trend',           label: '评价趋势',      icon: 'mdi:chart-timeline-variant', icClass: 'ic-violet' }
] as const
const activeChartMeta = computed(() => chartTabList.find(t => t.key === activeChart.value) ?? chartTabList[0])

// ══════════════════════════════════════════════════════════════════
// 🎯 自绘筛选器按钮的显示文字（100% 可控，不依赖 Element Plus 内部回显）
//    带双保险：① computed 必返回 { label: string, isPlaceholder: boolean }
//             ② 模板访问处仍用可选链 + fallback
// ══════════════════════════════════════════════════════════════════
const EMPTY_LABEL = { label: '—', isPlaceholder: true } as const

const selectedClassLabel = computed<{ label: string; isPlaceholder: boolean }>(() => {
  try {
    const v = selectedClassId.value
    const empty = v === 0 || v === '0' || v === null || v === undefined || v === ''
    if (empty) return { label: '全部班级', isPlaceholder: true }
    const classes = Array.isArray(myClasses.value) ? myClasses.value : []
    const matched = classes.find((c: any) => Number(c?.id) === Number(v))
    const label = matched?.name ?? matched?.label ?? matched?.title ?? matched?.className
                ?? (typeof v === 'string' ? v : String(v))
    return { label: label || String(v), isPlaceholder: false }
  } catch {
    return EMPTY_LABEL
  }
})

const selectedCourseLabel = computed<{ label: string; isPlaceholder: boolean }>(() => {
  try {
    const v = selectedCourse.value
    const empty = v === '' || v === null || v === undefined
    if (empty) return { label: '全部课程', isPlaceholder: true }
    const courses = Array.isArray(courseList.value) ? courseList.value : []
    const matched = courses.find((c: any) => String(c?.name ?? c?.label ?? c) === String(v))
    const label = matched?.name ?? matched?.label ?? matched?.title ?? matched?.courseName
                ?? (typeof v === 'string' ? v : String(v))
    return { label: label || String(v), isPlaceholder: false }
  } catch {
    return EMPTY_LABEL
  }
})

const loadCourses = async () => {
  try {
    const res = await api.get(`/api/statistics/courses`)
    if (res.data.success) courseList.value = res.data.data
  } catch {}
}

const onCourseChange = () => {
  onClassChange(selectedClassId.value)
}

const loadTeachingAdvice = async () => {
  adviceLoading.value = true
  const params = selectedClassId.value > 0 ? `?class_id=${selectedClassId.value}` : ''
  try {
    const res = await api.get(`/api/statistics/teaching-advice${params}`)
    if (res.data.success) teachingAdvice.value = res.data.data
  } catch {} finally { adviceLoading.value = false }
}

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  isTeacher.value = user.role === 'teacher'
  isStudent.value = user.role === 'student'
  isEnterprise.value = user.role === 'enterprise'

  if (isTeacher.value) {
    await loadClasses()
    await onClassChange(0)
    await loadClassCompare()
    await loadCourses()
  } else if (isStudent.value) {
    await loadStudentStats()
  }
  // enterprise：暂无独立统计视图，直接 loaded 显示下方"角色不可用"空态
  loaded.value = true
})

const loadClasses = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(`/api/classes/?teacher_id=${user.id}`)
    if (res.data.success) myClasses.value = res.data.data
  } catch {}
}

const loadClassCompare = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await api.get(`/api/classes/?teacher_id=${user.id}`)
    if (!res.data.success) return
    const classes = res.data.data
    const result = []
    for (const c of classes) {
      try {
        const sRes = await api.get(`/api/statistics/class/${c.id}`)
        if (sRes.data.success) {
          result.push({
            name: c.name,
            avg: sRes.data.data.class_avg,
            count: sRes.data.data.total_submissions,
            students: sRes.data.data.total_students
          })
        }
      } catch {}
    }
    classCompare.value = result
    submitRateData.value = result.map(r => ({
      name: r.name,
      rate: r.students > 0 ? Math.round((r.count / r.students) * 100) : 0
    }))
  } catch {}
}

const onClassChange = async (val: number) => {
  loaded.value = false
  let params = ''
  if (val && val > 0) params += `class_id=${val}`
  if (selectedCourse.value) params += (params ? '&' : '') + `course=${encodeURIComponent(selectedCourse.value)}`
  if (params) params = '?' + params

  try {
    const [res1, res2, res3, res4] = await Promise.all([
      api.get(`/api/statistics/overview${params}`),
      api.get(`/api/statistics/score-distribution${params}`),
      api.get(`/api/statistics/trend${params}`),
      api.get(`/api/statistics/dimension-avg${params}`)
    ])
    overview.value = res1.data.data
    distribution.value = res2.data.data
    trend.value = res3.data.data
    dimensionAvg.value = res4.data.data
  } catch {} finally { loaded.value = true }
}

const loadStudentStats = async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(`/api/statistics/student/${user.id}`)
    if (res.data.success) {
      const d = res.data.data
      myStats.value = {
        total_count: d.total_count,
        avg_score: d.avg_score,
        max_score: d.records.length > 0 ? Math.max(...d.records.map((r: any) => r.total_score)) : 0,
        min_score: d.records.length > 0 ? Math.min(...d.records.map((r: any) => r.total_score)) : 0,
        weakness: d.weakness
      }
      myTrend.value = d.records.map((r: any) => ({ time: r.time, score: r.total_score })).reverse()
      const dimMap: any = {}
      const dimCount: any = {}
      d.records.forEach((r: any) => {
        r.scores.forEach((s: any) => {
          dimMap[s.name] = (dimMap[s.name] || 0) + s.score
          dimCount[s.name] = (dimCount[s.name] || 0) + 1
        })
      })
      myRadarData.value = Object.keys(dimMap).map(name => ({
        name,
        avg: Math.round(dimMap[name] / dimCount[name])
      }))
    }
  } catch {}
}

const loadJobMatch = async () => {
  jobMatchLoading.value = true
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  try {
    const res = await api.get(`/api/statistics/job-match/${user.id}`)
    if (res.data.success) jobMatch.value = res.data.data
  } catch {} finally { jobMatchLoading.value = false }
}

const barOption = computed(() => {
  if (!distribution.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: distribution.value.map(d => d.range), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '人数', axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'bar', data: distribution.value.map(d => d.count), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#4F46E5' }, { offset: 1, color: '#818CF8' }] }, borderRadius: [8, 8, 0, 0] }, barWidth: '50%' }]
  }
})

const radarOption = computed(() => {
  if (!dimensionAvg.value?.length) return {}
  const filtered = dimensionAvg.value.filter(d => d.avg >= 20)
  if (!filtered.length) return {}
  return {
    tooltip: { backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    radar: { indicator: filtered.map(d => ({ name: d.name, max: 100 })), shape: 'polygon', splitNumber: 4, axisName: { color: '#334155', fontSize: 13, fontWeight: 600 }, splitLine: { lineStyle: { color: '#E2E8F0' } }, splitArea: { areaStyle: { color: ['#F8FAFC', '#fff'] } }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    series: [{ type: 'radar', data: [{ value: filtered.map(d => d.avg), name: '平均分', areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5, colorStops: [{ offset: 0, color: 'rgba(245, 158, 11, 0.25)' }, { offset: 1, color: 'rgba(245, 158, 11, 0.04)' }] } }, lineStyle: { color: '#F59E0B', width: 3 }, itemStyle: { color: '#F59E0B', borderColor: '#fff', borderWidth: 3 } }] }]
  }
})

const classCompareOption = computed(() => {
  if (!classCompare.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: classCompare.value.map(c => c.name), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '平均分', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'bar', data: classCompare.value.map(c => c.avg), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#10B981' }, { offset: 1, color: '#059669' }] }, borderRadius: [8, 8, 0, 0] }, barWidth: '40%' }]
  }
})

const submitRateOption = computed(() => {
  if (!submitRateData.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: submitRateData.value.map(r => r.name), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '提交率(%)', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'bar', data: submitRateData.value.map(r => r.rate), itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3B82F6' }, { offset: 1, color: '#2563EB' }] }, borderRadius: [8, 8, 0, 0] }, barWidth: '40%' }]
  }
})

const lineOption = computed(() => {
  if (!trend.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: trend.value.map(t => t.time), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '分数', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'line', data: trend.value.map(t => t.score), smooth: true, symbol: 'circle', symbolSize: 10, lineStyle: { width: 4, color: '#8B5CF6' }, itemStyle: { color: '#8B5CF6', borderColor: '#fff', borderWidth: 3 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(139, 92, 246, 0.3)' }, { offset: 1, color: 'rgba(139, 92, 246, 0.05)' }] } } }]
  }
})

const myLineOption = computed(() => {
  if (!myTrend.value?.length) return {}
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: myTrend.value.map(t => t.time), axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' } },
    yAxis: { type: 'value', name: '分数', min: 0, max: 100, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#64748B' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
    series: [{ type: 'line', data: myTrend.value.map(t => t.score), smooth: true, symbol: 'circle', symbolSize: 10, lineStyle: { width: 4, color: '#10B981' }, itemStyle: { color: '#10B981', borderColor: '#fff', borderWidth: 3 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }, { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }] } } }]
  }
})

const myRadarOption = computed(() => {
  if (!myRadarData.value?.length) return {}
  const filtered = myRadarData.value.filter(d => d.avg >= 20)
  if (!filtered.length) return {}
  return {
    tooltip: { backgroundColor: '#fff', borderColor: '#E2E8F0', textStyle: { color: '#1E293B' } },
    radar: { indicator: filtered.map(d => ({ name: d.name, max: 100 })), shape: 'polygon', splitNumber: 4, axisName: { color: '#334155', fontSize: 13, fontWeight: 600 }, splitLine: { lineStyle: { color: '#E2E8F0' } }, splitArea: { areaStyle: { color: ['#F8FAFC', '#fff'] } }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    series: [{ type: 'radar', data: [{ value: filtered.map(d => d.avg), name: '我的能力', areaStyle: { color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5, colorStops: [{ offset: 0, color: 'rgba(245, 158, 11, 0.25)' }, { offset: 1, color: 'rgba(245, 158, 11, 0.04)' }] } }, lineStyle: { color: '#F59E0B', width: 3 }, itemStyle: { color: '#F59E0B', borderColor: '#fff', borderWidth: 3 } }] }]
  }
})

/* ═══════════════════════════════════════════════════════════
   🎨 学生端看板专用图表 option（和纸色板 + 琥珀/翡翠主色）
   ═══════════════════════════════════════════════════════════ */
// 学生端成绩趋势 · 定制：纸色网格线 + jade 渐变填充 + 更大的节点
const studentTrendOption = computed(() => {
  if (!myTrend.value?.length) return {}
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFBF2',
      borderColor: 'var(--line)',
      borderWidth: 1,
      textStyle: { color: 'var(--ink-2)', fontFamily: 'var(--ff-body)', fontSize: 13 },
      axisPointer: { type: 'line', lineStyle: { color: 'var(--seal)', type: 'dashed', width: 1.5 } },
    },
    grid: { left: 24, right: 24, top: 36, bottom: 28, containLabel: true },
    xAxis: {
      type: 'category',
      data: myTrend.value.map((t: any) => t.time),
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'var(--line)', width: 1.5 } },
      axisTick: { show: false },
      axisLabel: {
        color: 'var(--ink-4)',
        fontFamily: 'var(--ff-sub)',
        fontSize: 12,
        letterSpacing: 0.5,
      },
    },
    yAxis: {
      type: 'value',
      name: '分',
      nameTextStyle: { color: 'var(--ink-4)', fontFamily: 'var(--ff-sub)', fontSize: 11, padding: [0, 44, 0, 0] },
      min: 0, max: 100,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: 'var(--ink-4)', fontFamily: 'var(--ff-sub)', fontSize: 12 },
      splitLine: { lineStyle: { color: 'var(--paper-3)', type: 'dashed' } },
    },
    series: [{
      type: 'line',
      data: myTrend.value.map((t: any) => t.score),
      smooth: true,
      symbol: 'circle',
      symbolSize: 12,
      lineStyle: { width: 4, color: 'var(--jade)' },
      itemStyle: { color: 'var(--jade)', borderColor: '#FFFBF2', borderWidth: 4, shadowColor: 'rgba(29, 185, 85, 0.35)', shadowBlur: 10 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(29, 185, 85, 0.28)' },
            { offset: 0.5, color: 'rgba(29, 185, 85, 0.10)' },
            { offset: 1, color: 'rgba(29, 185, 85, 0.00)' },
          ],
        },
      },
      markLine: {
        silent: true,
        symbol: ['none', 'none'],
        lineStyle: { color: 'var(--seal)', type: 'dashed', width: 1.5 },
        label: {
          formatter: '及格线 60',
          position: 'insideEndTop',
          color: 'var(--seal-dark)',
          fontFamily: 'var(--ff-sub)',
          fontSize: 11,
          backgroundColor: 'rgba(255, 90, 31, 0.08)',
          borderColor: 'rgba(255, 90, 31, 0.25)',
          borderWidth: 1,
          padding: [4, 8],
          borderRadius: 8,
        },
        data: [{ yAxis: 60 }],
      },
    }],
  }
})

// 学生端能力雷达 · 定制：琥珀琥珀琥珀！
const studentRadarOption = computed(() => {
  if (!myRadarData.value?.length) return {}
  const filtered = myRadarData.value.filter((d: any) => Number(d.avg) >= 20)
  if (!filtered.length) return {}
  return {
    tooltip: {
      backgroundColor: '#FFFBF2',
      borderColor: 'var(--line)',
      borderWidth: 1,
      textStyle: { color: 'var(--ink-2)', fontFamily: 'var(--ff-body)', fontSize: 13 },
    },
    radar: {
      center: ['50%', '54%'],
      radius: '66%',
      indicator: filtered.map((d: any) => ({ name: d.name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: 'var(--ink-3)',
        fontFamily: 'var(--ff-display)',
        fontSize: 13,
        fontWeight: 700,
        letterSpacing: 0.5,
      },
      splitLine: { lineStyle: { color: 'var(--paper-3)', width: 1.2 } },
      splitArea: {
        areaStyle: {
          color: ['#FFFBF2', 'var(--paper-2)', '#FFFBF2', 'var(--paper-2)'],
        },
      },
      axisLine: { lineStyle: { color: 'var(--amber)', width: 1.5, opacity: 0.6 } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: filtered.map((d: any) => d.avg),
        name: '我的能力',
        symbol: 'circle',
        symbolSize: 9,
        lineStyle: { color: 'var(--amber-dark)', width: 3 },
        itemStyle: {
          color: 'var(--amber)',
          borderColor: '#FFFBF2',
          borderWidth: 3,
          shadowColor: 'rgba(244, 183, 64, 0.45)',
          shadowBlur: 10,
        },
        areaStyle: {
          color: {
            type: 'radial', x: 0.5, y: 0.5, r: 0.5,
            colorStops: [
              { offset: 0, color: 'rgba(244, 183, 64, 0.45)' },
              { offset: 1, color: 'rgba(244, 183, 64, 0.08)' },
            ],
          },
        },
      }],
    }],
  }
})
</script>

<style scoped>
/* ============ 通用统一大卡基底 ============ */
.st-unified,
.st-advice,
.st-chart {
  max-width: 100%;
  background: #fff;
  border: 1px solid #E5E1D2;
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04), 0 12px 36px rgba(17, 24, 39, 0.06);
  overflow: hidden;
}
.st-unified { border-top: 4px solid #165DFF; }
.st-advice  { border-top: 4px solid #F59E0B; background: linear-gradient(180deg, rgba(245,158,11,0.04) 0%, #fff 55%); }
.st-chart   { border-top: 4px solid #8B5CF6; }

.st-section { padding: 24px 32px; }

.st-sec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.st-sec-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0.02em;
}
.sh-ic {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
.ic-cobalt { background: rgba(22,93,255,0.10); color: #165DFF; }
.ic-amber  { background: rgba(245,158,11,0.12); color: #D97706; }
.ic-jade   { background: rgba(16,185,129,0.12); color: #059669; }
.ic-blue   { background: rgba(59,130,246,0.12); color: #2563EB; }
.ic-violet { background: rgba(139,92,246,0.12); color: #7C3AED; }

/* ═══════════════════════════════════════════════════════════
   🎯 自绘筛选器按钮（替换 el-select 显示框，100% 可控无黑盒）
   ═══════════════════════════════════════════════════════════ */
.filter-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 34px 6px 12px !important;
  border-radius: 8px !important;
  border: 1px solid !important;
  text-align: left !important;
  cursor: pointer;
  transition: all 0.18s ease;
  line-height: 1.3 !important;
  height: 36px !important;
  min-height: 36px !important;
  user-select: none;
  outline: none !important;
}
.filter-trigger:focus { outline: none !important; }
.filter-trigger .ft-label {
  display: block;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13.5px !important;
  line-height: 1.3 !important;
}
.filter-trigger .ft-caret,
.filter-trigger .ft-clear {
  position: absolute;
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  font-size: 15px;
  line-height: 1;
  pointer-events: auto;
}
.filter-trigger .ft-clear {
  color: #9CA3AF;
  opacity: 0.85;
  font-size: 17px;
}
.filter-trigger .ft-clear:hover { color: #EF4444; opacity: 1; }
.filter-trigger .ft-caret { color: #6B7280; }

/* Dark 主题（KPI 卡）：白底实黑字 */
.filter-trigger--dark {
  background-color: #ffffff !important;
  border-color: #C7CBD1 !important;
}
.filter-trigger--dark:hover {
  border-color: #165DFF !important;
  box-shadow: 0 0 0 2px rgba(22,93,255,0.08);
}
.filter-trigger--dark .ft-label {
  color: #111827 !important;   /* 纯黑 + 700 字重 → 绝对不可能看不见 */
  font-weight: 700 !important;
}
.filter-trigger--dark.is-empty .ft-label {
  color: #6B7280 !important;
  font-weight: 500 !important;
}

/* Amber 主题（AI 卡）：米黄底深橙粗字 */
.filter-trigger--amber {
  background-color: #FFFBEB !important;
  border-color: #F59E0B !important;
}
.filter-trigger--amber:hover {
  border-color: #D97706 !important;
  box-shadow: 0 0 0 2px rgba(245,158,11,0.15);
}
.filter-trigger--amber .ft-label {
  color: #78350F !important;
  font-weight: 700 !important;
}
.filter-trigger--amber.is-empty .ft-label {
  color: #B45309 !important;
  font-weight: 500 !important;
}

/* 下拉菜单样式 */
.stat-ddm {
  border-radius: 12px !important;
  border: 1px solid #E5E1D2 !important;
  padding: 6px !important;
  box-shadow: 0 10px 32px rgba(17,24,39,0.1) !important;
  min-width: 180px !important;
}
.stat-ddm :deep(.el-dropdown-menu__item),
.stat-ddm .el-dropdown-menu__item {
  border-radius: 8px !important;
  padding: 9px 12px !important;
  font-size: 13.5px !important;
  color: #1F2937 !important;
  font-weight: 500 !important;
  line-height: 1.3 !important;
  margin-bottom: 2px;
}
.stat-ddm .el-dropdown-menu__item:last-child { margin-bottom: 0; }
.stat-ddm .el-dropdown-menu__item:hover { background-color: #F3F4F6 !important; }
.stat-ddm--dark  .el-dropdown-menu__item.is-active { background-color: rgba(22,93,255,0.08) !important; color: #165DFF !important; font-weight: 700 !important; }
.stat-ddm--amber .el-dropdown-menu__item.is-active { background-color: rgba(245,158,11,0.1) !important; color: #B45309 !important; font-weight: 700 !important; }

.st-filters {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.sf-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 14px;
  background: #F7F4EC;
  border: 1px solid #E5E1D2;
  border-radius: 12px;
}
.sf-label {
  font-size: 12.5px;
  font-weight: 700;
  color: #374151;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* ============ 残：旧的 el-select 样式（仍保留未筛选器未来如需，且与新的自绘按钮不冲突） ============ */
.sf-select :deep(.el-input__wrapper) {
  background: #fff !important;
  box-shadow: 0 0 0 1px #D1D5DB inset !important;
  border-radius: 8px;
  padding: 0 12px !important;
  min-height: 32px !important;
}
.sf-select :deep(.el-input__inner) {
  color: #111827 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  height: 32px !important;
  line-height: 32px !important;
}
.sf-select :deep(.el-input__inner::placeholder) {
  color: #6B7280 !important;
  font-size: 13px !important;
}
.sf-select :deep(.el-select__selected-item),
.sf-select :deep(.el-select__selection-item) {
  color: #111827 !important;
  font-size: 13px !important;
  font-weight: 600 !important;
}
.sf-select :deep(.el-select__placeholder) {
  color: #6B7280 !important;
  font-size: 13px !important;
}
.sf-select :deep(.el-select__caret) {
  color: #4B5563 !important;
}
.sf-select :deep(.el-select__caret) {
  color: #4B5563 !important;
}

/* ============ AI 教学建议特殊样式 ============ */
.sah-fl-select :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #F59E0B inset !important;
  background: #FFFBEB !important;
}
.sah-fl-select :deep(.el-input__inner) {
  color: #78350F !important;
}
.sah-fl-select :deep(.el-select__selected-item),
.sah-fl-select :deep(.el-select__selection-item) {
  color: #78350F !important;
  font-weight: 700 !important;
}
.sah-fl-select :deep(.el-select__placeholder) {
  color: #B45309 !important;
}
.sah-fl-select :deep(.el-select__caret) {
  color: #B45309 !important;
}

/* ============ KPI 网格 ============ */
.st-kpi-grid { display: grid; gap: 14px; }
.st-kpi-grid.four { grid-template-columns: repeat(4, minmax(0,1fr)); }
@media (max-width: 1080px) { .st-kpi-grid.four { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 560px)  { .st-kpi-grid.four { grid-template-columns: 1fr; } }

.st-kpi {
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid #E5E1D2;
  background: #F7F4EC;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
}
.st-kpi::before {
  content: '';
  position: absolute;
  right: -26px;
  top: -26px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  opacity: 0.18;
}
.kpi-cobalt::before { background: #165DFF; }
.kpi-jade::before   { background: #10B981; }
.kpi-amber::before  { background: #F59E0B; }
.kpi-violet::before { background: #8B5CF6; }

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}
.kpi-ic {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}
.kpi-cobalt .kpi-ic { background: #165DFF; }
.kpi-jade   .kpi-ic { background: #10B981; }
.kpi-amber  .kpi-ic { background: #D97706; }
.kpi-violet .kpi-ic { background: #8B5CF6; }

.kpi-chip {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  letter-spacing: 0.04em;
}
.chip-cobalt { background: rgba(22,93,255,0.12); color: #165DFF; border: 1px solid rgba(22,93,255,0.28); }
.chip-jade   { background: rgba(16,185,129,0.12); color: #059669; border: 1px solid rgba(16,185,129,0.28); }
.chip-amber  { background: rgba(245,158,11,0.12); color: #D97706; border: 1px solid rgba(245,158,11,0.30); }
.chip-violet { background: rgba(139,92,246,0.12); color: #7C3AED; border: 1px solid rgba(139,92,246,0.30); }

.kpi-num {
  font-family: "Playfair Display", Georgia, serif;
  font-weight: 800;
  font-size: 36px;
  line-height: 1.05;
  color: #111827;
  position: relative;
  z-index: 1;
}
.kpi-cobalt .kpi-num { background: linear-gradient(135deg,#165DFF 0%, #6366F1 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.kpi-jade   .kpi-num { background: linear-gradient(135deg,#10B981 0%, #059669 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.kpi-amber  .kpi-num { background: linear-gradient(135deg,#D97706 0%, #B45309 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.kpi-violet .kpi-num { background: linear-gradient(135deg,#8B5CF6 0%, #6D28D9 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }

.kpi-lbl {
  margin-top: 5px;
  font-size: 12.5px;
  color: #6B7280;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

/* ============ AI 教学建议 ============ */
.st-advice-head {
  padding: 24px 32px 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.sah-left { display: flex; align-items: center; gap: 14px; }
.sah-ic {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: rgba(245,158,11,0.15);
  color: #D97706;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.sah-title {
  margin: 0;
  font-size: 19px;
  font-weight: 800;
  color: #111827;
}
.sah-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(245,158,11,0.12);
  color: #D97706;
  border: 1px solid rgba(245,158,11,0.30);
  letter-spacing: 0.04em;
}
.sah-sub { margin: 5px 0 0; font-size: 13px; color: #6B7280; }

.sah-actions {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.sah-filter {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 14px;
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(217,119,6,0.28);
  border-radius: 12px;
  backdrop-filter: blur(6px);
}
.sah-fl-label {
  font-size: 12.5px;
  font-weight: 700;
  color: #92400E;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.sah-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(245,158,11,0.35);
  transition: all 0.2s ease;
  white-space: nowrap;
}
.sah-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(245,158,11,0.45); }

.st-advice-body {
  margin: 20px 32px 32px;
  padding: 24px 26px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(245,158,11,0.06) 0%, rgba(217,119,6,0.06) 100%);
  border: 1px solid rgba(245,158,11,0.22);
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.quote-ic {
  font-size: 30px;
  color: #D97706;
  opacity: 0.55;
  flex-shrink: 0;
}
.advice-text {
  margin: 2px 0 0;
  font-size: 15px;
  color: #1F2937;
  font-weight: 500;
  line-height: 1.9;
}
.st-advice-empty {
  margin: 18px 32px 32px;
  padding: 36px 20px;
  text-align: center;
  border-radius: 14px;
  background: #F7F4EC;
  border: 1px dashed #E5E1D2;
}
.st-advice-empty .empty-title {
  margin: 0;
  font-size: 14px;
  color: #374151;
  font-weight: 600;
}
.st-advice-empty .empty-sub {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: #9CA3AF;
}

/* ============ 图表单卡 + Tab 切换 ============ */
.st-chart-head {
  padding: 22px 32px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.sch-left {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}
.sch-ic {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.sch-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #111827;
}
.sch-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(139,92,246,0.10);
  color: #7C3AED;
  letter-spacing: 0.04em;
}

.sch-tabs {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px;
  background: #F7F4EC;
  border: 1px solid #E5E1D2;
  border-radius: 12px;
}
.sch-tab {
  padding: 7px 14px;
  font-size: 12.5px;
  font-weight: 600;
  color: #6B7280;
  background: transparent;
  border: none;
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.18s ease;
  white-space: nowrap;
}
.sch-tab:hover { color: #374151; background: rgba(255,255,255,0.6); }
.sch-tab-active {
  background: #fff !important;
  color: #7C3AED !important;
  box-shadow: 0 2px 8px rgba(139,92,246,0.18);
  border: 1px solid rgba(139,92,246,0.25);
}

.st-chart-body {
  padding: 20px 32px 32px;
}
.chart-wrap {
  padding: 8px 4px 2px;
}
.chart-slot { width: 100%; }
.chart-empty {
  height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: #F7F4EC;
  border: 1px dashed #E5E1D2;
  border-radius: 14px;
}
.text-ink-4 { color: #9CA3AF; }
.mb-3 { margin-bottom: 12px; }
.text-sm { font-size: 13px; }
.text-4xl { font-size: 36px; }
.mr-1 { margin-right: 4px; }
.ml-1 { margin-left: 4px; }
.mx-auto { margin-left: auto; margin-right: auto; }

.animate-fade-in-up {
  animation: fadeInUp 0.45s ease-out both;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ═══════════════════════════════════════════════════════════════
   🎓 学生端数据看板 · 独立设计语言
   · 和纸 / 印章 / 杂志排版美学
   · 主色：琥珀 + 翡翠 + 印章红（与全局 tokens 一致）
   · 字体：display 用于展示字，sub 用于小字标签，body 用于正文
   ═══════════════════════════════════════════════════════════════ */

/* ---------- 1. HERO 顶部个人信息卡 ---------- */
.stu-hero {
  position: relative;
  border-radius: 28px;
  background:
    radial-gradient(1200px 280px at 0% 0%, rgba(61, 90, 254, 0.10) 0%, transparent 55%),
    radial-gradient(900px 280px at 100% 0%, rgba(244, 183, 64, 0.14) 0%, transparent 55%),
    linear-gradient(180deg, #FFFBF2 0%, #F6F3EC 100%);
  border: 1px solid var(--line);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 22px 56px -32px rgba(23, 47, 168, 0.25);
}
.stu-hero__bg { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.stu-hero__bg .gridmesh {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(to right, rgba(61, 90, 254, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(61, 90, 254, 0.05) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse at 50% 0%, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at 50% 0%, black 30%, transparent 80%);
}
.stu-hero__bg .orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.55;
}
.stu-hero__bg .orb-a {
  width: 280px; height: 280px;
  right: -80px; top: -100px;
  background: radial-gradient(circle, #F4B740 0%, transparent 70%);
  animation: orbFloat 14s ease-in-out infinite;
}
.stu-hero__bg .orb-b {
  width: 320px; height: 320px;
  left: -120px; bottom: -140px;
  background: radial-gradient(circle, #3D5AFE 0%, transparent 70%);
  animation: orbFloat 18s ease-in-out infinite reverse;
}
.stu-hero__bg .grain {
  position: absolute; inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.1  0 0 0 0 0.1  0 0 0 0 0.3  0 0 0 0.05 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
  opacity: 0.6;
  mix-blend-mode: multiply;
}
@keyframes orbFloat {
  0%, 100% { transform: translate3d(0,0,0) scale(1); }
  50%      { transform: translate3d(0, -18px, 0) scale(1.06); }
}

/* 身份标签 · 胶囊 */
.eyebrow-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  border-radius: 999px;
  font-family: var(--ff-sub);
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--cobalt-dark);
  background: var(--cobalt-soft);
  border: 1px solid rgba(61, 90, 254, 0.22);
  text-transform: uppercase;
}
.eyebrow-tag .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--cobalt);
  box-shadow: 0 0 0 3px rgba(61, 90, 254, 0.18);
  animation: pulseDot 2.4s ease-in-out infinite;
}
.eyebrow-tag--amber {
  color: var(--amber-dark);
  background: var(--amber-soft);
  border-color: rgba(244, 183, 64, 0.28);
}
.eyebrow-tag--amber .dot { display: none; }
@keyframes pulseDot {
  0%,100% { box-shadow: 0 0 0 3px rgba(61, 90, 254, 0.18); }
  50%     { box-shadow: 0 0 0 6px rgba(61, 90, 254, 0.06); }
}

/* 标题排版 */
.hero-title {
  margin: 0;
  font-family: var(--ff-display);
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1.02;
  letter-spacing: -0.02em;
  color: var(--ink);
  display: inline-flex;
  align-items: baseline;
  flex-wrap: wrap;
}
.hero-title__hello {
  font-weight: 500;
  color: var(--ink-3);
  font-family: var(--ff-body);
  font-size: 0.6em;
  margin-right: 0.05em;
}
.hero-title__name {
  font-weight: 900;
  background: linear-gradient(135deg, var(--ink) 0%, var(--cobalt-dark) 60%, var(--seal) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  padding: 0 0.08em;
}
.hero-title__wave {
  color: var(--amber);
  margin-left: 0.3em;
  font-size: 0.7em;
  animation: waveHand 3.2s ease-in-out infinite;
  transform-origin: 70% 70%;
  display: inline-block;
}
@keyframes waveHand {
  0%,60%,100% { transform: rotate(0deg); }
  10% { transform: rotate(14deg); }
  20% { transform: rotate(-8deg); }
  30% { transform: rotate(14deg); }
  40% { transform: rotate(-4deg); }
  50% { transform: rotate(10deg); }
}
.hero-sub {
  margin: 0;
  font-family: var(--ff-body);
  font-size: 15.5px;
  color: var(--ink-3);
  max-width: 520px;
  line-height: 1.7;
}
.hero-sub strong {
  font-family: var(--ff-display);
  color: var(--ink);
  font-weight: 700;
  padding: 1px 8px;
  background: linear-gradient(180deg, transparent 60%, rgba(244, 183, 64, 0.38) 60%);
  border-radius: 4px;
}

/* 等级印章卡 */
.grade-plaque {
  display: inline-flex;
  align-items: center;
  gap: 20px;
  padding: 14px 22px 14px 14px;
  border-radius: 24px;
  background:
    linear-gradient(180deg, #FFFFFF 0%, #FFFBF2 100%);
  border: 1px solid var(--line);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 1) inset,
    0 18px 36px -18px rgba(23, 47, 168, 0.25);
  position: relative;
}
.grade-plaque::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 24px;
  padding: 1px;
  background: linear-gradient(135deg, var(--seal) 0%, var(--amber) 40%, var(--cobalt) 100%);
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
  opacity: 0.55;
  pointer-events: none;
}
.gp-ring {
  width: 80px; height: 80px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  flex-shrink: 0;
  background: conic-gradient(from 180deg, var(--seal) 0%, var(--amber) 45%, var(--cobalt) 100%);
  padding: 2.5px;
  box-shadow: 0 8px 20px -8px rgba(255, 90, 31, 0.4);
}
.gp-core {
  width: 100%; height: 100%;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, #FFFFFF 0%, #FFFBF2 50%, #F6F3EC 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}
.gp-grade {
  font-family: var(--ff-display);
  font-weight: 900;
  font-size: 32px;
  line-height: 1;
  background: linear-gradient(135deg, var(--seal) 0%, var(--cobalt-dark) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.gp-lbl {
  font-family: var(--ff-sub);
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--ink-4);
}
.gp-right { min-width: 130px; }
.gp-score {
  display: flex;
  align-items: baseline;
  gap: 2px;
  font-family: var(--ff-display);
  color: var(--ink);
  line-height: 1;
  margin-bottom: 6px;
}
.gp-num {
  font-size: 40px;
  font-weight: 900;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--ink) 0%, var(--cobalt) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.gp-base {
  font-family: var(--ff-sub);
  font-size: 16px;
  color: var(--ink-4);
  font-weight: 600;
  padding-bottom: 4px;
}
.gp-avg {
  font-family: var(--ff-sub);
  font-size: 11.5px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-4);
  padding-left: 2px;
}
@media (max-width: 560px) {
  .grade-plaque { flex-direction: column; align-items: flex-start; gap: 10px; padding: 14px; width: 100%; }
  .gp-right { min-width: 0; width: 100%; text-align: center; }
  .gp-ring { margin: 0 auto; }
}

/* ---------- HERO KPI 4 卡 ---------- */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 1024px) { .kpi-row { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 520px)  { .kpi-row { grid-template-columns: 1fr; } }

.kpi-card {
  position: relative;
  border-radius: 20px;
  padding: 20px 22px 22px;
  background:
    linear-gradient(180deg, #FFFFFF 0%, #FFFBF2 100%);
  border: 1px solid var(--line);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 14px 28px -22px rgba(23, 47, 168, 0.25);
  overflow: hidden;
  transition: transform 0.35s cubic-bezier(.22,.9,.2,1), box-shadow 0.35s ease;
}
.kpi-card::before {
  content: '';
  position: absolute;
  right: -48px; top: -48px;
  width: 180px; height: 180px;
  border-radius: 50%;
  opacity: 0.18;
  transition: transform 0.6s ease, opacity 0.4s ease;
}
.kpi-card::after {
  content: '';
  position: absolute;
  left: 0; top: 0;
  width: 4px; height: 100%;
  opacity: 0.9;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 26px 40px -24px rgba(23, 47, 168, 0.32);
}
.kpi-card:hover::before { transform: scale(1.15); opacity: 0.26; }

.kpi-card__chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-family: var(--ff-sub);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin-bottom: 14px;
  position: relative;
  z-index: 1;
}
.kpi-card__num {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-family: var(--ff-display);
  line-height: 1;
  position: relative;
  z-index: 1;
  margin-bottom: 10px;
}
.kpi-card__num span {
  font-size: 42px;
  font-weight: 900;
  letter-spacing: -0.03em;
}
.kpi-card__num em {
  font-style: normal;
  font-family: var(--ff-sub);
  font-weight: 600;
  font-size: 15px;
  opacity: 0.7;
  padding-bottom: 4px;
}
.kpi-card__lbl {
  position: relative;
  z-index: 1;
  font-family: var(--ff-body);
  font-size: 13px;
  color: var(--ink-4);
  letter-spacing: 0.01em;
}

/* 主题色 */
.kpi--cobalt::before { background: var(--cobalt); }
.kpi--cobalt::after  { background: linear-gradient(180deg, var(--cobalt) 0%, var(--cobalt-dark) 100%); }
.kpi--cobalt .kpi-card__chip { background: var(--cobalt-soft); color: var(--cobalt-dark); }
.kpi--cobalt .kpi-card__num  { color: var(--cobalt-dark); }

.kpi--jade::before { background: var(--jade); }
.kpi--jade::after  { background: linear-gradient(180deg, var(--jade) 0%, var(--jade-dark) 100%); }
.kpi--jade .kpi-card__chip { background: var(--jade-soft); color: var(--jade-dark); }
.kpi--jade .kpi-card__num  { color: var(--jade-dark); }

.kpi--amber::before { background: var(--amber); }
.kpi--amber::after  { background: linear-gradient(180deg, var(--amber) 0%, var(--amber-dark) 100%); }
.kpi--amber .kpi-card__chip { background: var(--amber-soft); color: var(--amber-dark); }
.kpi--amber .kpi-card__num  { color: var(--amber-dark); }

.kpi--seal::before { background: var(--seal); }
.kpi--seal::after  { background: linear-gradient(180deg, var(--seal) 0%, var(--seal-dark) 100%); }
.kpi--seal .kpi-card__chip { background: var(--seal-soft); color: var(--seal-dark); }
.kpi--seal .kpi-card__num  { color: var(--seal-dark); }

/* ---------- 2. 双栏主图卡片 ---------- */
.stu-twins {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 1024px) { .stu-twins { grid-template-columns: 1fr; } }

.twin-card {
  position: relative;
  border-radius: 24px;
  background:
    linear-gradient(180deg, #FFFFFF 0%, #FFFBF2 70%, #F6F3EC 100%);
  border: 1px solid var(--line);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 22px 48px -30px rgba(23, 47, 168, 0.28);
  overflow: hidden;
  padding: 24px 26px 26px;
}
.twin-card::after {
  content: '';
  position: absolute;
  left: 26px; right: 26px; top: 86px;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--line) 20%, var(--line) 80%, transparent 100%);
  opacity: 0.7;
}
.twin-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 22px;
  position: relative;
  z-index: 1;
}
.twin-head__left {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.twin-icon {
  width: 48px; height: 48px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 18px -10px currentColor;
}
.twin-icon--jade   { background: var(--jade-soft);   color: var(--jade-dark); }
.twin-icon--amber  { background: var(--amber-soft);  color: var(--amber-dark); }
.twin-head__titles { min-width: 0; }
.twin-head__title {
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 18px;
  line-height: 1.2;
  color: var(--ink);
  letter-spacing: -0.01em;
  margin: 0 0 3px;
}
.twin-head__sub {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-4);
}
.twin-head__badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--jade-soft);
  color: var(--jade-dark);
  font-family: var(--ff-sub);
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  white-space: nowrap;
  border: 1px solid rgba(29, 185, 85, 0.2);
}
.twin-head__badge b {
  font-family: var(--ff-display);
  font-size: 15px;
  font-weight: 900;
  color: inherit;
}
.twin-head__badge--amber {
  background: var(--amber-soft);
  color: var(--amber-dark);
  border-color: rgba(244, 183, 64, 0.25);
}
.twin-body {
  position: relative;
  z-index: 1;
  padding-top: 4px;
}
.twin-empty {
  min-height: 340px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 10px;
}

/* ---------- 3. 薄弱维度清单卡 ---------- */
.stu-weak {
  position: relative;
  border-radius: 24px;
  background:
    linear-gradient(180deg, #FFFBF2 0%, #FFE6DA 100%);
  border: 1px solid rgba(255, 90, 31, 0.25);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.8) inset,
    0 24px 48px -30px rgba(255, 90, 31, 0.35);
  overflow: hidden;
  padding: 26px 28px 28px;
}
.stu-weak::before {
  content: '';
  position: absolute;
  right: -60px; top: -60px;
  width: 280px; height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 90, 31, 0.22) 0%, transparent 70%);
  pointer-events: none;
}
.weak-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
  position: relative;
  z-index: 1;
}
.weak-head__left {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}
.weak-head__seal {
  width: 54px; height: 54px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 30%, #FFFFFF 0%, var(--seal-soft) 60%, #FFD6BF 100%);
  color: var(--seal-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow:
    0 0 0 3px rgba(255, 255, 255, 0.8) inset,
    0 10px 24px -10px rgba(255, 90, 31, 0.5);
  border: 1.5px solid rgba(255, 90, 31, 0.3);
}
.weak-head__title {
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 20px;
  line-height: 1.2;
  color: var(--seal-dark);
  letter-spacing: -0.01em;
  margin: 0 0 4px;
}
.weak-head__sub {
  font-family: var(--ff-sub);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--seal);
  opacity: 0.85;
}
.weak-head__count {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 16px;
  background: #FFFFFF;
  border: 1px solid rgba(255, 90, 31, 0.25);
  box-shadow: 0 8px 18px -10px rgba(255, 90, 31, 0.35);
  color: var(--seal-dark);
  font-family: var(--ff-sub);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  flex-shrink: 0;
}
.weak-head__count b {
  font-family: var(--ff-display);
  font-size: 24px;
  font-weight: 900;
  line-height: 1;
  color: var(--seal);
}
.weak-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 14px;
  position: relative;
  z-index: 1;
}
@media (max-width: 820px) { .weak-grid { grid-template-columns: 1fr; } }
.weak-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 16px 18px;
  background: linear-gradient(180deg, #FFFFFF 0%, #FFFBF2 100%);
  border-radius: 18px;
  border: 1px solid rgba(255, 90, 31, 0.18);
  box-shadow: 0 10px 24px -18px rgba(255, 90, 31, 0.35);
  transition: transform 0.3s cubic-bezier(.22,.9,.2,1), box-shadow 0.3s ease;
}
.weak-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 32px -20px rgba(255, 90, 31, 0.45);
}
.weak-item__idx {
  width: 40px; height: 40px;
  border-radius: 14px;
  background: var(--seal-soft);
  color: var(--seal-dark);
  font-family: var(--ff-display);
  font-weight: 900;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  letter-spacing: -0.02em;
  flex-shrink: 0;
}
.weak-item__info { min-width: 0; }
.weak-item__name {
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 15.5px;
  color: var(--ink);
  margin-bottom: 4px;
  line-height: 1.25;
}
.weak-item__meta {
  font-family: var(--ff-body);
  font-size: 12.5px;
  color: var(--ink-4);
}
.weak-item__meta b { color: var(--seal-dark); font-weight: 800; font-family: var(--ff-display); }
.weak-item__bar { width: 120px; flex-shrink: 0; }
.weak-item__bar-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 90, 31, 0.12);
  overflow: hidden;
  margin-bottom: 6px;
}
.weak-item__bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--seal) 0%, var(--amber) 100%);
  box-shadow: 0 0 8px rgba(255, 90, 31, 0.35);
  transition: width 0.8s cubic-bezier(.22,.9,.2,1);
}
.weak-item__bar-label {
  font-family: var(--ff-sub);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--seal);
  opacity: 0.85;
}
@media (max-width: 520px) {
  .weak-item { grid-template-columns: auto 1fr; }
  .weak-item__bar { grid-column: 1 / -1; width: 100%; }
}

/* ---------- 4. AI 岗位匹配卡 ---------- */
.stu-match {
  position: relative;
  border-radius: 28px;
  background:
    radial-gradient(900px 260px at 0% 0%, rgba(61, 90, 254, 0.08) 0%, transparent 60%),
    radial-gradient(700px 260px at 100% 100%, rgba(244, 183, 64, 0.10) 0%, transparent 60%),
    linear-gradient(180deg, #FFFFFF 0%, #FFFBF2 100%);
  border: 1px solid var(--line);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 26px 64px -34px rgba(23, 47, 168, 0.30);
  overflow: hidden;
  padding: 28px 30px 30px;
}
.match-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}
.match-head__left {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}
.match-head__title {
  margin: 0;
  font-family: var(--ff-display);
  font-weight: 900;
  font-size: 24px;
  color: var(--ink);
  letter-spacing: -0.02em;
  line-height: 1.15;
}
.match-head__tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--cobalt-soft) 0%, var(--amber-soft) 100%);
  color: var(--cobalt-dark);
  font-family: var(--ff-sub);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  border: 1px solid rgba(61, 90, 254, 0.15);
}
.match-head__sub {
  margin: 0;
  font-family: var(--ff-body);
  font-size: 14px;
  color: var(--ink-3);
  line-height: 1.6;
  max-width: 540px;
}
.match-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 22px;
  border-radius: 16px;
  background:
    linear-gradient(135deg, var(--cobalt) 0%, var(--seal) 100%);
  color: #FFFFFF;
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 15px;
  letter-spacing: 0.01em;
  border: none;
  cursor: pointer;
  box-shadow:
    0 0 0 3px rgba(255, 255, 255, 0.9) inset,
    0 14px 28px -12px rgba(61, 90, 254, 0.55);
  transition: transform 0.3s cubic-bezier(.22,.9,.2,1), box-shadow 0.3s ease, filter 0.3s ease;
  white-space: nowrap;
}
.match-cta:hover {
  transform: translateY(-2px);
  box-shadow:
    0 0 0 3px rgba(255, 255, 255, 0.9) inset,
    0 22px 36px -14px rgba(255, 90, 31, 0.45);
  filter: saturate(1.1);
}
.match-cta:active { transform: translateY(0); }
@media (max-width: 760px) {
  .match-head { flex-direction: column; align-items: stretch; }
  .match-cta { align-self: flex-start; }
}

/* 加载中骨架 */
.match-skeleton {
  padding: 60px 20px;
  text-align: center;
}
.match-skeleton__ring {
  position: relative;
  width: 72px; height: 72px;
  margin: 0 auto 22px;
  border-radius: 50%;
  background:
    conic-gradient(from 0deg, var(--cobalt-soft), var(--amber-soft));
  padding: 3px;
}
.match-skeleton__spinner {
  width: 100%; height: 100%;
  border-radius: 50%;
  background: #FFFBF2;
  position: relative;
}
.match-skeleton__spinner::after {
  content: '';
  position: absolute;
  left: 50%; top: 50%;
  width: 48px; height: 48px;
  margin: -24px 0 0 -24px;
  border-radius: 50%;
  border: 3px solid var(--cobalt-soft);
  border-top-color: var(--cobalt);
  border-right-color: var(--amber);
  animation: matchSpin 1s linear infinite;
}
@keyframes matchSpin { to { transform: rotate(360deg); } }
.match-skeleton__title {
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 17px;
  color: var(--ink);
  margin: 0 0 6px;
}
.match-skeleton__sub {
  font-family: var(--ff-body);
  font-size: 13.5px;
  color: var(--ink-4);
  margin: 0;
}

/* 空态 */
.match-empty {
  padding: 56px 20px;
  text-align: center;
}
.match-empty__illus {
  width: 104px; height: 104px;
  margin: 0 auto 22px;
  border-radius: 28px;
  background:
    radial-gradient(circle at 30% 30%, #FFFFFF 0%, var(--cobalt-soft) 60%, var(--amber-soft) 100%);
  color: var(--cobalt-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 0 0 3px rgba(255, 255, 255, 0.9) inset,
    0 18px 36px -16px rgba(61, 90, 254, 0.4);
}
.match-empty__text {
  margin: 0;
  font-family: var(--ff-body);
  font-size: 15px;
  line-height: 1.7;
  color: var(--ink-3);
}

/* 匹配结果面板 */
.match-panel { padding-top: 4px; }
.match-panel__hero {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
  padding: 22px 24px 24px;
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgba(61, 90, 254, 0.08) 0%, rgba(255, 90, 31, 0.08) 100%);
  border: 1px solid rgba(61, 90, 254, 0.14);
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}
.match-panel__hero::before {
  content: '';
  position: absolute;
  right: -80px; bottom: -90px;
  width: 280px; height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(244, 183, 64, 0.2) 0%, transparent 70%);
  pointer-events: none;
}
@media (max-width: 820px) {
  .match-panel__hero { grid-template-columns: 1fr; }
}
.match-hero__left { position: relative; z-index: 1; min-width: 0; }
.match-hero__job {
  display: inline-flex;
  align-items: center;
  font-family: var(--ff-display);
  font-weight: 900;
  font-size: 28px;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 0 0 10px;
  padding: 6px 16px 6px 12px;
  background: linear-gradient(180deg, #FFFFFF 0%, rgba(255, 255, 255, 0.6) 100%);
  border-radius: 14px;
  border: 1px solid rgba(61, 90, 254, 0.16);
  box-shadow: 0 10px 22px -14px rgba(61, 90, 254, 0.35);
  max-width: 100%;
}
.match-hero__tagline {
  font-family: var(--ff-body);
  font-size: 14px;
  color: var(--ink-3);
  line-height: 1.7;
  margin: 0;
  max-width: 480px;
  padding-left: 4px;
}
.match-hero__score {
  position: relative;
  z-index: 1;
  padding: 10px 4px 4px;
}
.match-hero__pct {
  display: flex;
  align-items: baseline;
  gap: 2px;
  font-family: var(--ff-display);
  line-height: 1;
  margin-bottom: 14px;
}
.match-hero__num {
  font-size: 68px;
  font-weight: 900;
  letter-spacing: -0.04em;
  background: linear-gradient(135deg, var(--seal) 0%, var(--cobalt) 60%, var(--jade-dark) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.match-hero__pct-sign {
  font-size: 32px;
  font-weight: 900;
  color: var(--seal);
  padding-bottom: 10px;
}
.match-hero__bar {
  width: 100%;
  height: 14px;
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(23, 47, 168, 0.08) 0%, rgba(23, 47, 168, 0.03) 100%);
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(23, 47, 168, 0.08) inset;
  margin-bottom: 8px;
}
.match-hero__bar-fill {
  height: 100%;
  border-radius: 999px;
  background:
    linear-gradient(90deg, var(--cobalt) 0%, var(--seal) 55%, var(--amber) 100%);
  box-shadow: 0 0 16px rgba(255, 90, 31, 0.35);
  transition: width 1s cubic-bezier(.22,.9,.2,1);
  position: relative;
}
.match-hero__bar-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255,255,255,0.45) 0%, rgba(255,255,255,0) 45%);
}
.match-hero__bar-lbl {
  font-family: var(--ff-sub);
  font-size: 10.5px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--ink-4);
  padding-left: 2px;
}

/* 技能要求卡片列表 */
.match-req-title {
  display: inline-flex;
  align-items: center;
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 16px;
  color: var(--ink);
  letter-spacing: 0.01em;
  margin: 0 0 16px;
  padding-left: 6px;
}
.match-req-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 14px;
  margin-bottom: 22px;
}
@media (max-width: 820px) { .match-req-grid { grid-template-columns: 1fr; } }

.req-card {
  position: relative;
  padding: 16px 18px;
  border-radius: 18px;
  background:
    linear-gradient(180deg, #FFFFFF 0%, #FFFBF2 100%);
  border: 1px solid var(--line);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 12px 26px -18px rgba(23, 47, 168, 0.3);
  overflow: hidden;
  transition: transform 0.3s cubic-bezier(.22,.9,.2,1), box-shadow 0.3s ease;
}
.req-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--cobalt) 0%, var(--seal) 100%);
  opacity: 0.6;
}
.req-card:hover {
  transform: translateY(-3px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 20px 34px -22px rgba(61, 90, 254, 0.4);
}
.req-card__idx {
  position: absolute;
  right: 14px; top: 14px;
  font-family: var(--ff-display);
  font-weight: 900;
  font-size: 36px;
  line-height: 1;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--cobalt) 0%, var(--seal) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  opacity: 0.12;
  pointer-events: none;
}
.req-card__name {
  font-family: var(--ff-display);
  font-weight: 800;
  font-size: 16px;
  color: var(--ink);
  margin-bottom: 8px;
  padding-left: 4px;
  line-height: 1.25;
  max-width: calc(100% - 40px);
  position: relative;
  z-index: 1;
}
.req-card__val {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 3px 12px;
  border-radius: 10px;
  background: var(--paper-2);
  margin: 0 0 8px 4px;
  font-family: var(--ff-display);
  position: relative;
  z-index: 1;
}
.req-card__mine {
  font-weight: 900;
  font-size: 20px;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--ink);
}
.req-card__sep {
  color: var(--ink-4);
  font-weight: 700;
  font-size: 14px;
}
.req-card__target {
  color: var(--ink-3);
  font-weight: 600;
  font-size: 15px;
  padding-bottom: 1px;
}
.req-card__tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-family: var(--ff-sub);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0 0 10px 4px;
  position: relative;
  z-index: 1;
}
.req-card__tag--ok {
  background: var(--jade-soft);
  color: var(--jade-dark);
  border: 1px solid rgba(29, 185, 85, 0.22);
}
.req-card__tag--miss {
  background: var(--seal-soft);
  color: var(--seal-dark);
  border: 1px solid rgba(255, 90, 31, 0.22);
}
.req-card__gap {
  margin: 0;
  padding-left: 4px;
  font-family: var(--ff-body);
  font-size: 13px;
  line-height: 1.7;
  color: var(--ink-3);
  position: relative;
  z-index: 1;
}

/* AI 建议卡 */
.match-advice {
  position: relative;
  padding: 22px 24px 22px 54px;
  border-radius: 20px;
  background:
    linear-gradient(180deg, #FFFBF2 0%, #F6F3EC 100%);
  border: 1px dashed rgba(61, 90, 254, 0.3);
  overflow: hidden;
}
.match-advice__ic {
  position: absolute;
  left: 18px; top: 22px;
  width: 28px; height: 28px;
  color: var(--cobalt);
  opacity: 0.8;
}
.match-advice::after {
  content: '';
  position: absolute;
  right: -40px; bottom: -50px;
  width: 220px; height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(244, 183, 64, 0.18) 0%, transparent 70%);
  pointer-events: none;
}
.match-advice p {
  margin: 0;
  position: relative;
  z-index: 1;
  font-family: var(--ff-body);
  font-size: 14.5px;
  line-height: 1.85;
  color: var(--ink-2);
}
</style>

<style>
/* ============ 全局 el-select 样式修复 ============ */
/* 确保所有 stat-select 类的 el-select 正常显示文字 */
.stat-select .el-input__wrapper {
  background-color: #ffffff !important;
  box-shadow: 0 0 0 1px #D1D5DB inset !important;
  padding: 0 12px !important;
  min-height: 32px !important;
  border-radius: 8px !important;
}
.stat-select .el-input__inner {
  color: #111827 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  height: 32px !important;
  line-height: 32px !important;
}
.stat-select .el-input__inner::placeholder {
  color: #6B7280 !important;
  font-size: 13px !important;
}
.stat-select .el-select__placeholder,
.stat-select .el-select__selected-item,
.stat-select .el-select__selection-item,
.stat-select .el-select__selection,
.stat-select .el-select__selection-text,
.stat-select .el-select__tags .el-select__tags-text {
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.25 !important;
  color: #111827 !important;
}
.stat-select .el-select__caret,
.stat-select .el-input__suffix-inner .el-select__caret {
  color: #4B5563 !important;
}

/* ============ 深色主题（核心数据总览 KPI 卡） ============ */
.stat-select-dark .el-input__wrapper {
  background: #fff !important;
}
.stat-select-dark .el-input__inner {
  color: #111827 !important;
}
.stat-select-dark .el-select__placeholder,
.stat-select-dark .el-select__selected-item,
.stat-select-dark .el-select__selection-item {
  color: #111827 !important;
}

/* ============ 琥珀主题（AI 教学建议卡） ============ */
.stat-select-amber .el-input__wrapper {
  box-shadow: 0 0 0 1px #F59E0B inset !important;
  background: #FFFBEB !important;
}
.stat-select-amber .el-input__inner {
  color: #78350F !important;
}
.stat-select-amber .el-select__placeholder,
.stat-select-amber .el-select__selected-item,
.stat-select-amber .el-select__selection-item {
  color: #78350F !important;
  font-weight: 700 !important;
}
.stat-select-amber .el-select__caret {
  color: #B45309 !important;
}

/* ============ 下拉面板样式 ============ */
.el-select-dropdown__item {
  color: #1F2937 !important;
  font-weight: 500 !important;
  font-size: 13px !important;
}
.el-select-dropdown__item.is-selected {
  color: #165DFF !important;
  font-weight: 700 !important;
  background-color: rgba(22, 93, 255, 0.06) !important;
}
.el-select-dropdown__item:hover {
  background-color: rgba(22, 93, 255, 0.04) !important;
}

/* ============ 确保 EP 内部文字完全可见 ============ */
/* 覆盖任何可能的 opacity:0 或 visibility:hidden */
.el-select .el-input__inner,
.el-select .el-select__selected-item,
.el-select .el-select__selection-item,
.el-select .el-select__selection,
.el-select .el-select__selection-text,
.el-select .el-select__tags .el-select__tags-text {
  opacity: 1 !important;
  visibility: visible !important;
  display: inline-block !important;
}

/* 确保 placeholder 可见 */
.el-select .el-select__placeholder {
  opacity: 1 !important;
  visibility: visible !important;
}
</style>